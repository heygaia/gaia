"""Memory management API routes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies.oauth_dependencies import get_current_user
from app.decorators import tiered_rate_limit
from app.models.memory_models import (
    CreateMemoryRequest,
    CreateMemoryResponse,
    DeleteMemoryResponse,
    MemorySearchResult,
)
from app.services.memory_service import memory_service

router = APIRouter()


@router.get("", response_model=MemorySearchResult)
async def get_all_memories(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user),
):
    """
    Get all memories for the current user with pagination.

    Args:
        page: Page number (default: 1)
        page_size: Number of memories per page (default: 20)
        user: Current authenticated user

    Returns:
        MemorySearchResult with paginated memories
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    result = await memory_service.get_all_memories(
        user_id=user_id, page=page, page_size=page_size
    )

    return result


@router.post("", response_model=CreateMemoryResponse)
@tiered_rate_limit("memory")
async def create_memory(
    request: CreateMemoryRequest,
    user: dict = Depends(get_current_user),
):
    """
    Create a new memory for the current user.

    Args:
        request: Memory creation request
        user: Current authenticated user

    Returns:
        CreateMemoryResponse with success status
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    memory_entry = await memory_service.store_memory(
        content=request.content, user_id=user_id, metadata=request.metadata
    )

    if memory_entry:
        return CreateMemoryResponse(
            success=True,
            memory_id=memory_entry.id,
            message="Memory created successfully",
        )
    else:
        return CreateMemoryResponse(success=False, message="Failed to create memory")


@router.delete("/{memory_id}", response_model=DeleteMemoryResponse)
@tiered_rate_limit("memory")
async def delete_memory(
    memory_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Delete a specific memory.

    Args:
        memory_id: ID of the memory to delete
        user: Current authenticated user

    Returns:
        DeleteMemoryResponse with success status
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    success = await memory_service.delete_memory(memory_id=memory_id, user_id=user_id)

    if success:
        return DeleteMemoryResponse(success=True, message="Memory deleted successfully")
    else:
        return DeleteMemoryResponse(success=False, message="Failed to delete memory")


@router.delete("", response_model=DeleteMemoryResponse)
@tiered_rate_limit("memory")
async def clear_all_memories(
    user: dict = Depends(get_current_user),
):
    """
    Clear all memories for the current user.

    Args:
        user: Current authenticated user

    Returns:
        DeleteMemoryResponse with success status
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    try:
        # Get all memories and delete them one by one
        # (Mem0 doesn't have a bulk delete, so we iterate)
        all_memories = await memory_service.get_all_memories(
            user_id=user_id,
            page=1,
            page_size=100,  # Get first 100 memories
        )

        deleted_count = 0
        # Create deletion tasks for all memories in the current page
        deletion_tasks = []
        for memory in all_memories.memories:
            if memory.id:
                task = memory_service.delete_memory(
                    memory_id=memory.id, user_id=user_id
                )
                deletion_tasks.append(task)

        # Execute all deletion tasks concurrently and collect results
        if deletion_tasks:
            results = await asyncio.gather(*deletion_tasks)
            deleted_count += sum(1 for result in results if result)

        # Handle remaining memories if more than 100
        while all_memories.has_next:
            all_memories = await memory_service.get_all_memories(
                user_id=user_id, page=all_memories.page + 1, page_size=100
            )
            for memory in all_memories.memories:
                if memory.id:
                    success = await memory_service.delete_memory(
                        memory_id=memory.id, user_id=user_id
                    )
                    if success:
                        deleted_count += 1

        return DeleteMemoryResponse(
            success=True, message=f"Cleared {deleted_count} memories successfully"
        )
    except Exception as e:
        return DeleteMemoryResponse(
            success=False, message=f"Failed to clear memories: {str(e)}"
        )
