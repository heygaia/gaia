"""Workflow utility functions for GAIA workflow system."""

from datetime import datetime, timezone
from typing import Any, Dict

from app.config.loggers import general_logger as logger
from app.db.mongodb.collections import workflows_collection
from app.db.utils import serialize_document


async def handle_workflow_error(
    workflow_id: str,
    user_id: str,
    error: Exception,
    deactivate: bool = False,
) -> None:
    """Centralized error handling for workflow operations."""
    try:
        update_data: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
        if deactivate:
            update_data["activated"] = False

        await workflows_collection.find_one_and_update(
            {"_id": workflow_id, "user_id": user_id},
            {"$set": update_data},
        )
        logger.error(f"Workflow {workflow_id} error: {error}")
    except Exception as update_error:
        logger.error(
            f"Failed to update workflow {workflow_id} error state: {update_error}"
        )


def ensure_trigger_config_object(trigger_config):
    """Convert dict to TriggerConfig object if needed."""
    if isinstance(trigger_config, dict):
        from app.models.workflow_models import TriggerConfig

        return TriggerConfig(**trigger_config)
    return trigger_config


def transform_workflow_document(doc: dict) -> dict:
    """Transform workflow document with trigger_config handling."""
    transformed_doc = serialize_document(doc)

    if "trigger_config" in transformed_doc and isinstance(
        transformed_doc["trigger_config"], dict
    ):
        transformed_doc["trigger_config"] = ensure_trigger_config_object(
            transformed_doc["trigger_config"]
        )

    return transformed_doc
