"""
Clean workflow API router for GAIA workflow system.
Provides CRUD operations, execution, and status endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies.oauth_dependencies import get_current_user
from app.decorators import tiered_rate_limit
from app.config.loggers import general_logger as logger
from app.models.workflow_models import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowStatusResponse,
)
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.post("/workflows", response_model=WorkflowResponse)
@tiered_rate_limit("workflow_operations")
async def create_workflow(
    request: CreateWorkflowRequest, user: dict = Depends(get_current_user)
):
    """Create a new workflow."""
    try:
        workflow = await WorkflowService.create_workflow(request, user["user_id"])
        return WorkflowResponse(
            workflow=workflow, message="Workflow created successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow",
        )


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(user: dict = Depends(get_current_user)):
    """List all workflows for the current user."""
    try:
        workflows = await WorkflowService.list_workflows(user["user_id"])
        return WorkflowListResponse(workflows=workflows)

    except Exception as e:
        logger.error(f"Error listing workflows for user {user['user_id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list workflows",
        )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, user: dict = Depends(get_current_user)):
    """Get a specific workflow by ID."""
    try:
        workflow = await WorkflowService.get_workflow(workflow_id, user["user_id"])
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        return WorkflowResponse(
            workflow=workflow, message="Workflow retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow",
        )


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    request: UpdateWorkflowRequest,
    user: dict = Depends(get_current_user),
):
    """Update an existing workflow."""
    try:
        workflow = await WorkflowService.update_workflow(
            workflow_id, request, user["user_id"]
        )
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        return WorkflowResponse(
            workflow=workflow, message="Workflow updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workflow",
        )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, user: dict = Depends(get_current_user)):
    """Delete a workflow."""
    try:
        success = await WorkflowService.delete_workflow(workflow_id, user["user_id"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        return {"message": "Workflow deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workflow",
        )


@router.post(
    "/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResponse
)
@tiered_rate_limit("workflow_operations")
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
    user: dict = Depends(get_current_user),
):
    """Execute a workflow (run now)."""
    try:
        result = await WorkflowService.execute_workflow(
            workflow_id, request, user["user_id"]
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow",
        )


@router.get("/workflows/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str, user: dict = Depends(get_current_user)):
    """Get the current status of a workflow (for polling)."""
    try:
        status_response = await WorkflowService.get_workflow_status(
            workflow_id, user["user_id"]
        )
        return status_response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting workflow status {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow status",
        )


@router.post("/workflows/{workflow_id}/activate", response_model=WorkflowResponse)
async def activate_workflow(workflow_id: str, user: dict = Depends(get_current_user)):
    """Activate a workflow (enable its trigger)."""
    try:
        workflow = await WorkflowService.activate_workflow(workflow_id, user["user_id"])
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        return WorkflowResponse(
            workflow=workflow, message="Workflow activated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate workflow",
        )


@router.post("/workflows/{workflow_id}/deactivate", response_model=WorkflowResponse)
async def deactivate_workflow(workflow_id: str, user: dict = Depends(get_current_user)):
    """Deactivate a workflow (disable its trigger)."""
    try:
        workflow = await WorkflowService.deactivate_workflow(
            workflow_id, user["user_id"]
        )
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        return WorkflowResponse(
            workflow=workflow, message="Workflow deactivated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate workflow",
        )


@router.post(
    "/workflows/{workflow_id}/regenerate-steps", response_model=WorkflowResponse
)
@tiered_rate_limit("workflow_operations")
async def regenerate_workflow_steps(
    workflow_id: str, user: dict = Depends(get_current_user)
):
    """Regenerate steps for an existing workflow."""
    try:
        workflow = await WorkflowService.regenerate_workflow_steps(
            workflow_id, user["user_id"]
        )
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        return WorkflowResponse(
            workflow=workflow, message="Workflow steps regenerated successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error regenerating workflow steps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate workflow steps",
        )


@router.post("/workflows/from-todo", response_model=WorkflowResponse)
@tiered_rate_limit("workflow_operations")
async def create_workflow_from_todo(
    request: dict,  # {todo_id: str, todo_title: str, todo_description?: str}
    user: dict = Depends(get_current_user),
):
    """Create a workflow from a todo item."""
    try:
        todo_id = request.get("todo_id")
        todo_title = request.get("todo_title")
        todo_description = request.get("todo_description", "")

        if not todo_id or not todo_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="todo_id and todo_title are required",
            )

        # Create workflow using modern workflow system
        from app.models.workflow_models import (
            CreateWorkflowRequest,
            TriggerConfig,
            TriggerType,
        )

        workflow_request = CreateWorkflowRequest(
            title=f"Todo: {todo_title}",
            description=todo_description or f"Workflow for todo: {todo_title}",
            trigger_config=TriggerConfig(type=TriggerType.MANUAL, enabled=True),
            generate_immediately=True,  # Generate steps immediately for todos
        )

        workflow = await WorkflowService.create_workflow(
            workflow_request, user["user_id"]
        )

        return WorkflowResponse(
            workflow=workflow, message="Workflow created from todo successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow from todo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow from todo",
        )
