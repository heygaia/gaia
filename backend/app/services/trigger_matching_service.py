"""
Gmail trigger matching service for workflow automation.

This service matches incoming Gmail webhook events to workflows with email triggers,
handling pattern matching and triggering workflow execution.
"""

import re
from typing import Dict, List, Any

from app.config.loggers import general_logger as logger
from app.db.mongodb.collections import workflows_collection
from app.models.workflow_models import Workflow, TriggerType


class GmailTriggerMatchingService:
    """Service for matching Gmail events to workflows with email triggers."""

    async def process_gmail_event(
        self, user_id: str, email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process incoming email webhook event and find matching workflows.

        Args:
            user_id: User ID from webhook
            email_data: Email data from webhook

        Returns:
            Processing result with matching workflows and metadata
        """
        try:
            logger.info(f"Finding workflow matches for Gmail event, user {user_id}")

            # Find workflows with email triggers for this user
            matching_workflows = await self._find_matching_workflows(
                user_id, email_data
            )

            logger.info(
                f"Found {len(matching_workflows)} matching workflows for user {user_id}"
            )

            return {
                "status": "success",
                "matches_found": len(matching_workflows),
                "matching_workflows": matching_workflows,
                "message": f"Found {len(matching_workflows)} matching workflows",
            }

        except Exception as e:
            logger.error(f"Error finding workflow matches for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "matches_found": 0,
                "matching_workflows": [],
                "message": f"Failed to find workflow matches: {str(e)}",
            }

    async def _find_matching_workflows(
        self, user_id: str, email_data: Dict[str, Any]
    ) -> List[Workflow]:
        """
        Find workflows with email triggers that match the incoming email.

        Args:
            user_id: User ID to filter workflows
            email_data: Email data to match against

        Returns:
            List of matching workflows
        """
        try:
            # Query for active workflows with email triggers
            query = {
                "user_id": user_id,
                "activated": True,
                "trigger_config.type": TriggerType.EMAIL,
                "trigger_config.enabled": True,
            }

            cursor = workflows_collection.find(query)
            matching_workflows = []

            async for workflow_doc in cursor:
                try:
                    # Convert MongoDB document to Workflow object
                    workflow_doc["id"] = workflow_doc.get("_id")
                    if "_id" in workflow_doc:
                        del workflow_doc["_id"]

                    workflow = Workflow(**workflow_doc)

                    # Check if email matches workflow trigger patterns
                    if await self._email_matches_trigger(workflow, email_data):
                        matching_workflows.append(workflow)

                except Exception as e:
                    logger.error(f"Error processing workflow document: {e}")
                    continue

            return matching_workflows

        except Exception as e:
            logger.error(f"Error finding matching workflows: {e}")
            return []

    async def _email_matches_trigger(
        self, workflow: Workflow, email_data: Dict[str, Any]
    ) -> bool:
        """
        Check if an email matches a workflow's trigger patterns.

        Args:
            workflow: Workflow with trigger configuration
            email_data: Email data from webhook

        Returns:
            True if email matches trigger patterns
        """
        try:
            trigger_config = workflow.trigger_config

            # Extract email attributes
            sender = email_data.get("sender", "").lower()
            subject = email_data.get("subject", "")
            body = email_data.get("message_text", "")

            # Check sender patterns
            if trigger_config.sender_patterns:
                if not self._matches_patterns(sender, trigger_config.sender_patterns):
                    return False

            # Check subject patterns
            if trigger_config.subject_patterns:
                if not self._matches_patterns(subject, trigger_config.subject_patterns):
                    return False

            # Check body keywords with similarity search
            if trigger_config.body_keywords:
                if not await self._matches_body_keywords(
                    body, trigger_config.body_keywords
                ):
                    return False

            # If no specific patterns are configured, match all emails
            if (
                not trigger_config.sender_patterns
                and not trigger_config.subject_patterns
                and not trigger_config.body_keywords
            ):
                logger.debug(
                    f"No patterns configured for workflow {workflow.id}, matching all emails"
                )
                return True

            # If we reach here, all specified patterns matched successfully
            logger.debug(f"All patterns matched for workflow {workflow.id}")
            return True

        except Exception as e:
            logger.error(f"Error checking email match for workflow {workflow.id}: {e}")
            return False

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """
        Check if text matches any of the given patterns.

        Args:
            text: Text to match against
            patterns: List of patterns (supports regex and simple string matching)

        Returns:
            True if text matches any pattern
        """
        if not patterns:
            return True

        for pattern in patterns:
            try:
                # Try regex matching first
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                # Fall back to simple string matching if regex is invalid
                if pattern.lower() in text.lower():
                    return True

        return False

    async def _matches_body_keywords(self, body: str, keywords: List[str]) -> bool:
        """
        Check if email body matches any of the keywords using string matching.

        Args:
            body: Email body text
            keywords: List of keywords to search for

        Returns:
            True if any keyword matches body content
        """
        if not keywords or not body:
            return False

        try:
            # Simple string matching (case-insensitive)
            for keyword in keywords:
                if keyword.lower() in body.lower():
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking body keywords: {e}")
            return False
