"""
Comprehensive database indexes for all MongoDB collections.
Follows MongoDB indexing best practices for optimal query performance.

Index Strategy:
- User-centric compound indexes for multi-tenant queries
- Sparse indexes for optional fields to reduce storage
- Text search indexes for content discovery
- Unique constraints for data integrity
- ESR (Equality, Sort, Range) ordering for compound indexes
"""

import asyncio
from typing import Dict, List

from app.config.loggers import app_logger as logger
from app.db.mongodb.collections import (
    blog_collection,
    calendars_collection,
    conversations_collection,
    files_collection,
    goals_collection,
    mail_collection,
    notes_collection,
    notifications_collection,
    payments_collection,
    plans_collection,
    projects_collection,
    reminders_collection,
    subscriptions_collection,
    todos_collection,
    usage_snapshots_collection,
    users_collection,
)


async def create_all_indexes():
    """
    Create all database indexes for optimal performance.
    This is the main function called during application startup.

    Indexes are created with best practices:
    - User-specific compound indexes for multi-tenant queries
    - Date-based sorting indexes for pagination
    - Text search indexes for full-text search
    - Unique indexes for data integrity    - Compound indexes ordered by: equality → range → sort
    """
    try:
        logger.info("Starting comprehensive database index creation...")

        # Create all indexes concurrently for better performance
        index_tasks = [
            create_user_indexes(),
            create_conversation_indexes(),
            create_todo_indexes(),
            create_project_indexes(),
            create_goal_indexes(),
            create_note_indexes(),
            create_file_indexes(),
            create_mail_indexes(),
            create_calendar_indexes(),
            create_blog_indexes(),
            create_notification_indexes(),
            create_reminder_indexes(),
            create_payment_indexes(),
            create_usage_indexes(),
        ]

        # Execute all index creation tasks concurrently
        results = await asyncio.gather(*index_tasks, return_exceptions=True)

        collection_names = [
            "users",
            "conversations",
            "todos",
            "projects",
            "goals",
            "notes",
            "files",
            "mail",
            "calendar",
            "blog",
            "notifications",
            "reminders",
            "payments",
            "usage",
        ]

        index_results = {}
        for i, (collection_name, result) in enumerate(zip(collection_names, results)):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to create indexes for {collection_name}: {str(result)}"
                )
                index_results[collection_name] = f"FAILED: {str(result)}"
            else:
                index_results[collection_name] = "SUCCESS"

        # Log summary
        successful = sum(1 for result in index_results.values() if result == "SUCCESS")
        total = len(index_results)

        logger.info(
            f"Database index creation completed: {successful}/{total} collections successful"
        )

        # Log any failures
        failed_collections = [
            name for name, result in index_results.items() if result != "SUCCESS"
        ]
        if failed_collections:
            logger.warning(
                f"Failed to create indexes for collections: {failed_collections}"
            )

    except Exception as e:
        logger.error(f"Critical error during database index creation: {str(e)}")
        raise


async def create_user_indexes():
    """Create indexes for users collection."""
    try:
        # Create all user indexes concurrently
        await asyncio.gather(
            # Email unique index (primary lookup method)
            users_collection.create_index("email", unique=True),
            # Onboarding status with creation date
            users_collection.create_index(
                [("onboarding.completed", 1), ("created_at", -1)]
            ),
            # Cache cleanup index (sparse since not all users have cached_at)
            users_collection.create_index("cached_at", sparse=True),
            # Activity tracking index for inactive user queries
            users_collection.create_index("last_active_at", sparse=True),
            # Inactive email tracking index (sparse since not all users have this field)
            users_collection.create_index("last_inactive_email_sent", sparse=True),
        )

        logger.info("Created user indexes")

    except Exception as e:
        logger.error(f"Error creating user indexes: {str(e)}")
        raise


async def create_conversation_indexes():
    """Create indexes for conversations collection."""
    try:
        # Create all conversation indexes concurrently
        await asyncio.gather(
            # Primary compound index for user conversations with sorting (most critical)
            conversations_collection.create_index([("user_id", 1), ("createdAt", -1)]),
            # For specific conversation lookups (extremely critical for performance)
            conversations_collection.create_index(
                [("user_id", 1), ("conversation_id", 1)]
            ),
            # For starred conversations queries
            conversations_collection.create_index(
                [("user_id", 1), ("starred", 1), ("createdAt", -1)]
            ),
            # For message pinning operations (nested array queries)
            conversations_collection.create_index(
                [("user_id", 1), ("messages.message_id", 1)]
            ),
            # For message pinning aggregations
            conversations_collection.create_index(
                [("user_id", 1), ("messages.pinned", 1)]
            ),
        )

        logger.info("Created conversation indexes")

    except Exception as e:
        logger.error(f"Error creating conversation indexes: {str(e)}")
        raise


async def create_todo_indexes():
    """Create indexes for todos collection."""
    try:
        # Create all todo indexes concurrently
        await asyncio.gather(
            # Primary compound index for user todos with sorting
            todos_collection.create_index([("user_id", 1), ("created_at", -1)]),
            # Project-based queries
            todos_collection.create_index([("user_id", 1), ("project_id", 1)]),
            # Enhanced compound indexes for complex filtering
            todos_collection.create_index(
                [("user_id", 1), ("completed", 1), ("created_at", -1)]
            ),
            todos_collection.create_index(
                [("user_id", 1), ("priority", 1), ("created_at", -1)]
            ),
            todos_collection.create_index([("user_id", 1), ("due_date", 1)]),
            # For overdue queries (critical for performance) - sparse for due_date
            todos_collection.create_index(
                [("user_id", 1), ("due_date", 1), ("completed", 1)], sparse=True
            ),
            # For project + completion status queries
            todos_collection.create_index(
                [("user_id", 1), ("project_id", 1), ("completed", 1)]
            ),
            # For label-based filtering (sparse since not all todos have labels)
            todos_collection.create_index([("user_id", 1), ("labels", 1)], sparse=True),
            # Text search index for title and description
            todos_collection.create_index([("title", "text"), ("description", "text")]),
            # For subtask operations (sparse since not all todos have subtasks)
            todos_collection.create_index(
                [("user_id", 1), ("subtasks.id", 1)], sparse=True
            ),
        )

        logger.info("Created todo indexes")

    except Exception as e:
        logger.error(f"Error creating todo indexes: {str(e)}")
        raise


async def create_project_indexes():
    """Create indexes for projects collection."""
    try:
        # Create all project indexes concurrently
        await asyncio.gather(
            # Primary compound index for user projects
            projects_collection.create_index([("user_id", 1), ("created_at", -1)]),
            # For default project lookup
            projects_collection.create_index([("user_id", 1), ("is_default", 1)]),
            # For project name searches
            projects_collection.create_index([("user_id", 1), ("name", 1)]),
        )

        logger.info("Created project indexes")

    except Exception as e:
        logger.error(f"Error creating project indexes: {str(e)}")
        raise


async def create_goal_indexes():
    """Create indexes for goals collection."""
    try:
        # Create all goal indexes concurrently
        await asyncio.gather(
            # Primary index for user goals
            goals_collection.create_index([("user_id", 1), ("created_at", -1)]),
            # For progress tracking
            goals_collection.create_index([("user_id", 1), ("progress", 1)]),
            # For todo integration queries
            goals_collection.create_index([("user_id", 1), ("todo_project_id", 1)]),
            goals_collection.create_index([("user_id", 1), ("todo_id", 1)]),
        )

        logger.info("Created goal indexes")

    except Exception as e:
        logger.error(f"Error creating goal indexes: {str(e)}")
        raise


async def create_note_indexes():
    """Create indexes for notes collection."""
    try:
        # Create all note indexes concurrently
        await asyncio.gather(
            # For user-specific note queries
            notes_collection.create_index([("user_id", 1), ("created_at", -1)]),
            # For individual note lookups
            notes_collection.create_index([("user_id", 1), ("_id", 1)]),
            # For auto-created notes filtering (sparse since not all notes have this field)
            notes_collection.create_index(
                [("user_id", 1), ("auto_created", 1)], sparse=True
            ),
            # Text search index for content search
            notes_collection.create_index([("plaintext", "text"), ("title", "text")]),
        )

        logger.info("Created note indexes")

    except Exception as e:
        logger.error(f"Error creating note indexes: {str(e)}")
        raise


async def create_file_indexes():
    """Create indexes for files collection."""
    try:
        # Create all file indexes concurrently
        await asyncio.gather(
            # For user file queries
            files_collection.create_index([("user_id", 1), ("uploaded_at", -1)]),
            # For specific file lookups (critical)
            files_collection.create_index([("user_id", 1), ("file_id", 1)]),
            # For conversation-based file queries
            files_collection.create_index([("user_id", 1), ("conversation_id", 1)]),
            # For file type filtering
            files_collection.create_index([("user_id", 1), ("content_type", 1)]),
        )

        logger.info("Created file indexes")

    except Exception as e:
        logger.error(f"Error creating file indexes: {str(e)}")
        raise


async def create_mail_indexes():
    """Create indexes for mail collection."""
    try:
        # Create all mail indexes concurrently
        await asyncio.gather(
            # Unique index for email IDs
            mail_collection.create_index([("user_id", 1)]),
            # For thread-based queries
            mail_collection.create_index([("message_id", 1)]),
        )

        logger.info("Created mail indexes")

    except Exception as e:
        logger.error(f"Error creating mail indexes: {str(e)}")
        raise


async def create_calendar_indexes():
    """Create indexes for calendar collection."""
    try:
        # Create all calendar indexes concurrently
        await asyncio.gather(
            # For user calendar preferences
            calendars_collection.create_index("user_id"),
            # For event queries
            calendars_collection.create_index([("user_id", 1), ("event_date", 1)]),
            # For calendar selection queries
            calendars_collection.create_index(
                [("user_id", 1), ("selected_calendars", 1)]
            ),
        )

        logger.info("Created calendar indexes")

    except Exception as e:
        logger.error(f"Error creating calendar indexes: {str(e)}")
        raise


async def create_blog_indexes():
    """Create indexes for blog collection."""
    try:
        # Create all blog indexes concurrently
        await asyncio.gather(
            # Unique slug index
            blog_collection.create_index("slug", unique=True),
            # Date-based sorting
            blog_collection.create_index([("date", -1)]),
            # Category filtering
            blog_collection.create_index("category"),
            # Author queries
            blog_collection.create_index("authors"),
            # Compound index for published blogs
            blog_collection.create_index([("date", -1), ("category", 1)]),
            # Text search index
            blog_collection.create_index(
                [
                    ("title", "text"),
                    ("content", "text"),
                    ("description", "text"),
                    ("tags", "text"),
                ]
            ),
        )

        logger.info("Created blog indexes")

    except Exception as e:
        logger.error(f"Error creating blog indexes: {str(e)}")
        raise


async def create_notification_indexes():
    """Create indexes for notifications collection."""
    try:
        # Create all notification indexes concurrently
        await asyncio.gather(
            # For user-specific notifications
            notifications_collection.create_index([("user_id", 1), ("created_at", -1)]),
            # For unread notifications
            notifications_collection.create_index(
                [("user_id", 1), ("read", 1), ("created_at", -1)]
            ),
            # For notification type filtering
            notifications_collection.create_index([("user_id", 1), ("type", 1)]),
        )

        logger.info("Created notification indexes")

    except Exception as e:
        logger.error(f"Error creating notification indexes: {str(e)}")
        raise


async def create_reminder_indexes():
    """Create indexes for the reminders collection."""
    try:
        await asyncio.gather(
            reminders_collection.create_index([("user_id", 1)]),
            reminders_collection.create_index([("status", 1)]),
            reminders_collection.create_index([("scheduled_at", 1)]),
            reminders_collection.create_index([("type", 1)]),
            reminders_collection.create_index([("user_id", 1), ("status", 1)]),
            reminders_collection.create_index([("status", 1), ("scheduled_at", 1)]),
            reminders_collection.create_index([("user_id", 1), ("type", 1)]),
        )
        logger.info("Reminder indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating reminder indexes: {e}")
        raise


async def create_payment_indexes():
    """Create indexes for payment-related collections."""
    try:
        # Create payment collection indexes
        await asyncio.gather(
            # Payment indexes
            payments_collection.create_index("user_id"),
            payments_collection.create_index("razorpay_payment_id", unique=True),
            payments_collection.create_index("subscription_id", sparse=True),
            payments_collection.create_index("order_id", sparse=True),
            payments_collection.create_index("status"),
            payments_collection.create_index([("user_id", 1), ("created_at", -1)]),
            # Subscription indexes
            subscriptions_collection.create_index("user_id"),
            subscriptions_collection.create_index(
                "razorpay_subscription_id", unique=True
            ),
            subscriptions_collection.create_index("plan_id"),
            subscriptions_collection.create_index("status"),
            subscriptions_collection.create_index([("user_id", 1), ("status", 1)]),
            subscriptions_collection.create_index("current_end", sparse=True),
            subscriptions_collection.create_index("charge_at", sparse=True),
            # Plan indexes
            plans_collection.create_index("razorpay_plan_id", unique=True),
            plans_collection.create_index("is_active"),
            plans_collection.create_index([("is_active", 1), ("amount", 1)]),
        )

        logger.info("Created payment indexes")

    except Exception as e:
        logger.error(f"Error creating payment indexes: {str(e)}")
        raise


async def create_usage_indexes():
    """
    Create indexes for usage_snapshots collection for optimal query performance.
    Includes TTL index for automatic cleanup after 90 days.

    Query patterns:
    - Find latest usage by user_id (sorted by created_at desc)
    - Find usage history by user_id and date range
    - Automatic cleanup via TTL index
    """
    try:
        await asyncio.gather(
            # Primary query: get latest usage by user
            usage_snapshots_collection.create_index(
                [("user_id", 1), ("created_at", -1)], name="user_latest_usage"
            ),
            # Usage history queries by user and date range
            usage_snapshots_collection.create_index(
                [("user_id", 1), ("created_at", 1)], name="user_usage_history"
            ),
            # TTL index for automatic cleanup after 90 days (7,776,000 seconds)
            usage_snapshots_collection.create_index(
                "created_at",
                name="created_at_ttl",
                expireAfterSeconds=7776000,  # 90 days
            ),
            # Plan type filtering
            usage_snapshots_collection.create_index(
                "plan_type", name="plan_type_filter"
            ),
        )

        logger.info("Created usage indexes with TTL cleanup (90 days)")

    except Exception as e:
        logger.error(f"Error creating usage indexes: {str(e)}")
        raise


async def get_index_status() -> Dict[str, List[str]]:
    """
    Get the current index status for all collections.
    Useful for monitoring and debugging index usage.

    Returns:
        Dict mapping collection names to lists of index names
    """
    try:
        collections = {
            "users": users_collection,
            "conversations": conversations_collection,
            "todos": todos_collection,
            "projects": projects_collection,
            "goals": goals_collection,
            "notes": notes_collection,
            "files": files_collection,
            "mail": mail_collection,
            "calendar": calendars_collection,
            "blog": blog_collection,
            "notifications": notifications_collection,
            "reminders": reminders_collection,
        }

        # Get all collection indexes concurrently
        async def get_collection_indexes(name: str, collection):
            try:
                indexes = await collection.list_indexes().to_list(length=None)
                return name, [idx.get("name", "unnamed") for idx in indexes]
            except Exception as e:
                logger.error(f"Failed to get indexes for {name}: {str(e)}")
                return name, [f"ERROR: {str(e)}"]

        # Execute all index status queries concurrently
        tasks = [
            get_collection_indexes(name, collection)
            for name, collection in collections.items()
        ]
        results = await asyncio.gather(*tasks)

        # Convert results to dictionary
        index_status = dict(results)

        return index_status

    except Exception as e:
        logger.error(f"Error getting index status: {str(e)}")
        return {"error": [str(e)]}


async def log_index_summary():
    """Log a summary of all collection indexes for monitoring purposes."""
    try:
        index_status = await get_index_status()

        logger.info("=== DATABASE INDEX SUMMARY ===")

        total_indexes = 0
        for collection_name, indexes in index_status.items():
            if not indexes or (len(indexes) == 1 and indexes[0].startswith("ERROR")):
                logger.warning(f"{collection_name}: No indexes or error")
            else:
                index_count = len(indexes)
                total_indexes += index_count
                logger.info(
                    f"INDEX CREATED: {collection_name}: {index_count} indexes - {', '.join(indexes)}"
                )

        logger.info(f"Total indexes across all collections: {total_indexes}")
        logger.info("=== END INDEX SUMMARY ===")

    except Exception as e:
        logger.error(f"Error logging index summary: {str(e)}")
