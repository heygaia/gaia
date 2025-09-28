"""
Sync service for handling synchronization between different entities.
This module prevents circular imports by centralizing sync logic.
"""

from typing import Optional
import uuid
from datetime import datetime

from bson import ObjectId

from app.config.loggers import goals_logger as logger
from app.db.mongodb.collections import goals_collection, todos_collection
from app.db.redis import delete_cache, delete_cache_by_pattern
from app.models.todo_models import Priority, TodoCreate, UpdateTodoRequest, SubTask


async def sync_goal_node_completion(
    goal_id: str, node_id: str, is_complete: bool, user_id: str
) -> bool:
    """
    Sync completion status from goal roadmap node to subtask in todo.

    Args:
        goal_id (str): The goal ID
        node_id (str): The node ID in the roadmap
        is_complete (bool): The completion status
        user_id (str): The user ID

    Returns:
        bool: True if sync was successful
    """
    try:
        # Get the goal and find the node
        goal = await goals_collection.find_one(
            {"_id": ObjectId(goal_id), "user_id": user_id}
        )
        if not goal:
            return False

        # Find the node and get its subtask_id
        roadmap = goal.get("roadmap", {})
        nodes = roadmap.get("nodes", [])

        target_node = None
        for node in nodes:
            if node.get("id") == node_id:
                target_node = node
                break

        if not target_node:
            return False

        node_data = target_node.get("data", {})
        subtask_id = node_data.get("subtask_id")
        todo_id = goal.get("todo_id")
        if not subtask_id or not todo_id:
            return False

        # Get the current todo to update its subtasks
        todo = await todos_collection.find_one(
            {"_id": ObjectId(todo_id), "user_id": user_id}
        )
        if not todo:
            return False

        # Update the specific subtask completion status
        subtasks = todo.get("subtasks", [])
        updated = False
        for subtask in subtasks:
            if subtask.get("id") == subtask_id:
                subtask["completed"] = is_complete
                updated = True
                break

        if not updated:
            return False

        # Update the todo with modified subtasks
        await todos_collection.update_one(
            {"_id": ObjectId(todo_id)},
            {"$set": {"subtasks": subtasks, "updated_at": datetime.now()}},
        )

        # Invalidate todo-related caches since we updated subtasks
        await _invalidate_todo_caches(user_id, todo.get("project_id"), todo_id)

        # Also invalidate goal caches since goal progress might have changed
        await _invalidate_goal_caches(user_id, goal_id)

        logger.info(
            f"Synced completion status for node {node_id} <-> subtask {subtask_id}: {is_complete}"
        )
        return True

    except Exception as e:
        logger.error(f"Error syncing goal node completion: {str(e)}")
        return False


async def sync_subtask_to_goal_completion(
    todo_id: str, subtask_id: str, is_complete: bool, user_id: str
) -> bool:
    """
    Sync completion status from subtask back to goal roadmap node.

    Args:
        todo_id (str): The todo ID
        subtask_id (str): The subtask ID
        is_complete (bool): The completion status
        user_id (str): The user ID

    Returns:
        bool: True if sync was successful
    """
    try:
        # Find the goal that contains this todo_id
        goal = await goals_collection.find_one({"user_id": user_id, "todo_id": todo_id})

        if not goal:
            return False

        # Find and update the specific node by subtask_id
        roadmap = goal.get("roadmap", {})
        nodes = roadmap.get("nodes", [])

        updated = False
        for node in nodes:
            if node.get("data", {}).get("subtask_id") == subtask_id:
                node["data"]["isComplete"] = is_complete
                updated = True
                break

        if not updated:
            return False

        # Update the goal with the modified roadmap
        await goals_collection.update_one(
            {"_id": goal["_id"]}, {"$set": {"roadmap.nodes": nodes}}
        )

        # Invalidate goal caches
        goal_id = str(goal["_id"])
        await _invalidate_goal_caches(user_id, goal_id)

        # Also invalidate todo caches since this sync was triggered by a todo change
        todo_project_id = goal.get("todo_project_id")
        await _invalidate_todo_caches(user_id, todo_project_id, todo_id)

        logger.info(
            f"Synced subtask {subtask_id} completion back to goal {goal_id}: {is_complete}"
        )
        return True

    except Exception as e:
        logger.error(f"Error syncing subtask to goal completion: {str(e)}")
        return False


async def create_goal_project_and_todo(
    goal_id: str, goal_title: str, roadmap_data: dict, user_id: str
) -> str:
    """
    Create a todo in the shared 'Goals' project with subtasks for roadmap nodes.

    Args:
        goal_id (str): The goal ID
        goal_title (str): The goal title
        roadmap_data (dict): The roadmap data with nodes and edges
        user_id (str): The user ID

    Returns:
        str: The Goals project ID
    """
    try:
        # Import here to avoid circular imports
        from app.services.todos.todo_service import TodoService

        # Get or create the shared "Goals" project
        project_id = await _get_or_create_goals_project(user_id)

        # Create subtasks for each roadmap node
        nodes = roadmap_data.get("nodes", [])
        subtasks = []

        for node in nodes:
            node_data = node.get("data", {})

            # Skip start/end nodes typically used in flowcharts
            if node_data.get("type") in ["start", "end"]:
                continue

            # Generate subtask ID and store in node for syncing
            subtask_id = str(uuid.uuid4())
            node_data["subtask_id"] = subtask_id

            # Create subtask
            subtask = SubTask(
                id=subtask_id,
                title=node_data.get("title", node_data.get("label", "Untitled Task")),
                completed=node_data.get("isComplete", False),
            )
            subtasks.append(subtask)

        # Create a single todo with all roadmap nodes as subtasks
        todo = TodoCreate(
            title=goal_title,
            description=f"Goal: {goal_title}",
            project_id=project_id,
            priority=Priority.HIGH,
            due_date=None,
            due_date_timezone=None,
        )

        created_todo = await TodoService.create_todo(todo, user_id)

        # Now add subtasks if we have any
        if subtasks:
            await TodoService.update_todo(
                created_todo.id,
                UpdateTodoRequest(
                    title=None,
                    description=None,
                    labels=None,
                    due_date=None,
                    due_date_timezone=None,
                    priority=None,
                    project_id=None,
                    completed=None,
                    subtasks=subtasks,
                    workflow=None,
                    workflow_status=None,
                ),
                user_id,
            )

        # Update the goal with the modified roadmap (now contains subtask_ids) and todo info
        await goals_collection.update_one(
            {"_id": ObjectId(goal_id)},
            {
                "$set": {
                    "roadmap": roadmap_data,
                    "todo_project_id": project_id,
                    "todo_id": created_todo.id,
                }
            },
        )

        # Invalidate caches since we created new todos, projects, and updated goals
        await _invalidate_goal_caches(user_id, goal_id)
        await _invalidate_todo_caches(user_id, project_id, created_todo.id)
        await _invalidate_project_caches(user_id, project_id)

        logger.info(
            f"Added goal todo {created_todo.id} with {len(subtasks)} subtasks to Goals project {project_id} for goal {goal_id}"
        )
        return project_id

    except Exception as e:
        logger.error(f"Error creating goal todo in Goals project: {str(e)}")
        raise


async def _get_or_create_goals_project(user_id: str) -> str:
    """Get or create the shared 'Goals' project for a user."""
    from app.db.mongodb.collections import projects_collection

    existing = await projects_collection.find_one(
        {"user_id": user_id, "name": "Goals", "color": "#8B5CF6"}
    )

    if existing:
        return str(existing["_id"])

    goals_project = {
        "user_id": user_id,
        "name": "Goals",
        "description": "All your goals and roadmaps",
        "color": "#8B5CF6",  # Purple color for goals
        "is_default": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = await projects_collection.insert_one(goals_project)
    project_id = str(result.inserted_id)

    # Invalidate project caches since we created a new project
    await _invalidate_project_caches(user_id, project_id)

    return project_id


async def _invalidate_todo_caches(
    user_id: str, project_id: Optional[str] = None, todo_id: Optional[str] = None
):
    """
    Invalidate todo-related caches.
    This function uses the same logic as TodoService._invalidate_cache to ensure consistency.
    """
    try:
        # Always invalidate stats since they might change
        await delete_cache(f"stats:{user_id}")

        # Invalidate specific todo cache
        if todo_id:
            await delete_cache(f"todo:{user_id}:{todo_id}")

        # Invalidate project-specific caches
        if project_id:
            await delete_cache_by_pattern(f"todos:{user_id}:project:{project_id}:*")
            await delete_cache(f"projects:{user_id}")
            await delete_cache_by_pattern(f"*:project:{project_id}*")

        # Invalidate main list cache
        await delete_cache_by_pattern(f"todos:{user_id}:page:*")
        await delete_cache_by_pattern(f"todos:{user_id}*")
        await delete_cache_by_pattern(f"todo:{user_id}:*")

        logger.info(
            f"Todo caches invalidated for user {user_id}, project {project_id}, todo {todo_id}"
        )

    except Exception as e:
        logger.error(f"Error invalidating todo caches: {str(e)}")


async def _invalidate_goal_caches(user_id: str, goal_id: Optional[str] = None):
    """
    Invalidate goal-related caches.
    """
    try:
        # Always invalidate user's goals list cache
        cache_key_goals = f"goals_cache:{user_id}"
        await delete_cache(cache_key_goals)

        # Invalidate goal statistics cache
        cache_key_stats = f"goal_stats_cache:{user_id}"
        await delete_cache(cache_key_stats)

        # Invalidate specific goal cache if provided
        if goal_id:
            cache_key_goal = f"goal_cache:{goal_id}"
            await delete_cache(cache_key_goal)

        logger.info(f"Goal caches invalidated for user {user_id}, goal {goal_id}")

    except Exception as e:
        logger.error(f"Error invalidating goal caches: {str(e)}")


async def _invalidate_project_caches(user_id: str, project_id: Optional[str] = None):
    """
    Invalidate project-related caches.
    """
    try:
        # Invalidate user's projects list
        await delete_cache(f"projects:{user_id}")

        # Invalidate specific project cache if provided
        if project_id:
            await delete_cache_by_pattern(f"*:project:{project_id}*")

        logger.info(
            f"Project caches invalidated for user {user_id}, project {project_id}"
        )

    except Exception as e:
        logger.error(f"Error invalidating project caches: {str(e)}")
