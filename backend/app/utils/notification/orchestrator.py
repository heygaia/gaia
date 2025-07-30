import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Request

from app.config.loggers import app_logger as logger
from app.models.notification.notification_models import (
    ActionResult,
    BulkActions,
    ChannelDeliveryStatus,
    NotificationRecord,
    NotificationRequest,
    NotificationStatus,
)
from app.utils.common_utils import websocket_manager
from app.utils.notification.actions import (
    ActionHandler,
    ApiCallActionHandler,
    ModalActionHandler,
    RedirectActionHandler,
)
from app.utils.notification.channels import (
    ChannelAdapter,
    EmailChannelAdapter,
    InAppChannelAdapter,
)
from app.utils.notification.storage import (
    MongoDBNotificationStorage,
)


class NotificationOrchestrator:
    """
    Core notification orchestration engine.

    This class manages the complete lifecycle of notifications including:
    - Creation and validation
    - Delivery through multiple channels
    - Action execution
    - Bulk operations
    - Status management
    """

    def __init__(self, storage=MongoDBNotificationStorage()):
        self.storage = storage
        self.channel_adapters: Dict[str, ChannelAdapter] = {}
        self.action_handlers: Dict[str, ActionHandler] = {}

        # Register default components
        self._register_default_components()

    # INITIALIZATION & REGISTRATION METHODS
    def _register_default_components(self) -> None:
        """Register default adapters, handlers, and sources"""
        # Channel adapters
        self.register_channel_adapter(InAppChannelAdapter())
        self.register_channel_adapter(adapter=EmailChannelAdapter())

        # Action handlers
        self.register_action_handler(ApiCallActionHandler())
        self.register_action_handler(RedirectActionHandler())
        self.register_action_handler(ModalActionHandler())

    def register_channel_adapter(self, adapter: ChannelAdapter) -> None:
        """Register a new channel adapter"""
        self.channel_adapters[adapter.channel_type] = adapter
        logger.info(f"Registered channel adapter: {adapter.channel_type}")

    def register_action_handler(self, handler: ActionHandler) -> None:
        """Register a new action handler"""
        self.action_handlers[handler.action_type] = handler
        logger.info(f"Registered action handler: {handler.action_type}")

    # NOTIFICATION CREATION & MANAGEMENT
    async def create_notification(
        self, request: NotificationRequest
    ) -> NotificationRecord | None:
        """
        Create and process a new notification.

        Args:
            request: The notification request containing all notification data

        Returns:
            NotificationRecord if created successfully, None if duplicate
        """
        logger.info(f"Creating notification {request.id} for user {request.user_id}")

        # Create notification record
        notification_record = NotificationRecord(
            id=request.id,
            user_id=request.user_id,
            status=NotificationStatus.PENDING,
            created_at=request.created_at,
            original_request=request,
        )

        # Save to storage
        await self.storage.save_notification(notification_record)

        # Deliver the notification
        await self._deliver_notification(notification_record)

        return notification_record

    # NOTIFICATION DELIVERY SYSTEM
    async def _deliver_notification(self, notification: NotificationRecord) -> None:
        """
        Deliver notification through all configured channels.

        Args:
            notification: The notification record to deliver
        """
        logger.info(f"Delivering notification {notification.id}")

        delivery_tasks = []
        for channel_config in notification.original_request.channels:
            adapter = self.channel_adapters.get(channel_config.channel_type)
            if adapter and adapter.can_handle(notification.original_request):
                task = self._deliver_via_channel(notification, adapter)
                delivery_tasks.append(task)

        # Execute all deliveries concurrently
        if delivery_tasks:
            delivery_results = await asyncio.gather(
                *delivery_tasks, return_exceptions=True
            )

            # Process delivery results
            channel_statuses = []
            for result in delivery_results:
                if isinstance(result, ChannelDeliveryStatus):
                    channel_statuses.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Delivery failed: {result}")

            # Update the notification record with delivery results
            await self.storage.update_notification(
                notification.id,
                {
                    "channels": [status.model_dump() for status in channel_statuses],
                    "status": NotificationStatus.DELIVERED,
                    "delivered_at": datetime.now(timezone.utc),
                },
            )

            # Update the local notification object for broadcasting
            notification.channels = channel_statuses
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.now(timezone.utc)

            # Broadcast real-time update to user
            await websocket_manager.broadcast_to_user(
                notification.user_id,
                {
                    "type": "notification.delivered",
                    "notification": await self._serialize_notification(notification),
                },
            )

    async def _deliver_via_channel(
        self, notification: NotificationRecord, adapter: ChannelAdapter
    ) -> ChannelDeliveryStatus:
        """
        Deliver notification via a specific channel.

        Args:
            notification: The notification to deliver
            adapter: The channel adapter to use for delivery

        Returns:
            ChannelDeliveryStatus indicating success or failure
        """
        try:
            content = await adapter.transform(notification.original_request)
            return await adapter.deliver(content, notification.user_id)
        except Exception as e:
            logger.error(f"Channel delivery failed: {e}")
            return ChannelDeliveryStatus(
                channel_type=adapter.channel_type,
                status=NotificationStatus.PENDING,
                error_message=str(e),
            )

    # ACTION EXECUTION SYSTEM
    async def execute_action(
        self,
        notification_id: str,
        action_id: str,
        user_id: str,
        request: Optional[Request],
    ) -> ActionResult:
        """
        Execute a notification action.

        Args:
            notification_id: ID of the notification containing the action
            action_id: ID of the specific action to execute
            user_id: ID of the user executing the action
            request: Optional FastAPI request object for context

        Returns:
            ActionResult containing execution status and results
        """
        logger.info(f"Executing action {action_id} for notification {notification_id}")

        # Get notification
        notification = await self.storage.get_notification(notification_id, user_id)
        if not notification:
            return ActionResult(
                success=False, message="Notification not found", error_code="NOT_FOUND"
            )

        # Find action
        action = notification.get_action_by_id(action_id)
        if not action:
            return ActionResult(
                success=False, message="Action not found", error_code="ACTION_NOT_FOUND"
            )

        # Check if action can be executed
        if not action.is_executable():
            return ActionResult(
                success=False,
                message=(
                    "Action has already been executed"
                    if action.executed
                    else "Action is disabled"
                ),
                error_code=(
                    "ACTION_ALREADY_EXECUTED" if action.executed else "ACTION_DISABLED"
                ),
            )

        # Get handler
        handler = self.action_handlers.get(action.type.value)
        if not handler or not handler.can_handle(action):
            return ActionResult(
                success=False,
                message=f"No handler available for action type: {action.type}",
                error_code="NO_HANDLER",
            )

        # Execute the action
        result = await handler.execute(action, notification, user_id, request=request)

        # If action was successful, mark it as executed
        if result.success:
            notification.mark_action_as_executed(action_id)

            # Update the notification in storage with the executed action
            await self.storage.update_notification(
                notification_id,
                {
                    "original_request": notification.original_request.model_dump(),
                    "updated_at": notification.updated_at,
                },
            )

        # Update notification if needed (additional updates from handler)
        if result.update_notification:
            await self.storage.update_notification(
                notification_id, result.update_notification
            )
            logger.info(f"Broadcasting notification {notification.id} to user {notification.user_id}")
            # Broadcast update to user via websocket
            await websocket_manager.broadcast_to_user(
                user_id,
                {
                    "type": "notification.updated",
                    "notification_id": notification_id,
                    "updates": result.update_notification,
                },
            )

        # Handle follow-up actions if any
        if result.next_actions:
            await self._handle_follow_up_actions(result.next_actions, user_id)

        return result

    def _find_action_in_notification(
        self, notification: NotificationRecord, action_id: str
    ):
        """Find a specific action within a notification."""
        for action in notification.original_request.content.actions or []:
            if action.id == action_id:
                return action
        return None

    async def _handle_follow_up_actions(
        self, next_actions: List[Any], user_id: str
    ) -> None:
        """Handle any follow-up actions that need to be executed."""
        for next_action in next_actions:
            # Create new notification with next action
            # Implementation depends on specific requirements
            logger.info(f"Processing follow-up action for user {user_id}")
            pass

    # NOTIFICATION STATUS MANAGEMENT
    async def mark_as_read(
        self, notification_id: str, user_id: str
    ) -> NotificationRecord | None:
        """
        Mark notification as read.

        Args:
            notification_id: ID of the notification to mark as read
            user_id: ID of the user marking the notification

        Returns:
            Updated notification record if successful, None otherwise
        """
        notification = await self.storage.get_notification(notification_id, user_id)
        if not notification:
            return None

        logger.info(
            f"Marking notification {notification_id} as read for user {user_id}"
        )

        await self.storage.update_notification(
            notification_id,
            {
                "status": NotificationStatus.READ.value,
                "read_at": datetime.now(timezone.utc),
            },
        )

        # Get the updated notification
        updated_notification = await self.storage.get_notification(
            notification_id, user_id
        )

        # Broadcast update via websocket
        await websocket_manager.broadcast_to_user(
            user_id, {"type": "notification.read", "notification_id": notification_id}
        )

        return updated_notification

    async def archive_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Archive a notification.

        Args:
            notification_id: ID of the notification to archive
            user_id: ID of the user archiving the notification

        Returns:
            True if successfully archived, False otherwise
        """
        notification = await self.storage.get_notification(notification_id, user_id)
        if not notification:
            return False

        logger.info(f"Archiving notification {notification_id} for user {user_id}")

        await self.storage.update_notification(
            notification_id,
            {
                "status": NotificationStatus.ARCHIVED,
                "archived_at": datetime.now(timezone.utc),
            },
        )

        return True

    # NOTIFICATION RETRIEVAL & QUERIES
    async def get_user_notifications(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
        channel_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user with optional filtering.

        Args:
            user_id: ID of the user whose notifications to retrieve
            status: Optional status filter
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip (for pagination)
            channel_type: Optional channel type filter

        Returns:
            List of serialized notifications
        """
        notifications = await self.storage.get_user_notifications(
            user_id, status, limit, offset, channel_type
        )
        return [await self._serialize_notification(n) for n in notifications]

    async def get_notification(
        self, notification_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific notification by ID for a user.

        Args:
            notification_id: ID of the notification to retrieve
            user_id: ID of the user requesting the notification

        Returns:
            Serialized notification if found, None otherwise
        """
        notification = await self.storage.get_notification(notification_id, user_id)
        if not notification:
            return None
        return await self._serialize_notification(notification)

    # BULK OPERATIONS
    async def bulk_actions(
        self, notification_ids: List[str], user_id: str, action: BulkActions
    ) -> Dict[str, bool]:
        """
        Perform bulk actions on multiple notifications.

        Args:
            notification_ids: List of notification IDs to operate on
            user_id: ID of the user performing the bulk action
            action: The type of bulk action to perform

        Returns:
            Dictionary mapping notification IDs to success/failure status
        """
        results = {}

        for notification_id in notification_ids:
            try:
                if action == BulkActions.MARK_READ:
                    result = await self.mark_as_read(notification_id, user_id)
                    success = result is not None
                elif action == BulkActions.ARCHIVE:
                    success = await self.archive_notification(notification_id, user_id)
                else:
                    success = False

                results[notification_id] = success
            except Exception as e:
                logger.error(f"Bulk action failed for {notification_id}: {e}")
                results[notification_id] = False

        return results

    # UTILITY & SERIALIZATION METHODS
    async def _serialize_notification(
        self, notification: NotificationRecord
    ) -> Dict[str, Any]:
        """
        Serialize notification for API response.

        Args:
            notification: The notification record to serialize

        Returns:
            Dictionary representation suitable for API responses
        """
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "status": notification.status.value,
            "created_at": notification.created_at.isoformat(),
            "delivered_at": (
                notification.delivered_at.isoformat()
                if notification.delivered_at
                else None
            ),
            "read_at": (
                notification.read_at.isoformat() if notification.read_at else None
            ),
            "snoozed_until": (
                notification.snoozed_until.isoformat()
                if notification.snoozed_until
                else None
            ),
            "content": {
                "title": notification.original_request.content.title,
                "body": notification.original_request.content.body,
                "actions": [
                    {
                        "id": action.id,
                        "type": action.type.value,
                        "label": action.label,
                        "style": action.style.value,
                        "requires_confirmation": action.requires_confirmation,
                        "confirmation_message": action.confirmation_message,
                        "config": action.config.model_dump() if action.config else None,
                        "executed": action.executed,
                        "executed_at": (
                            action.executed_at.isoformat()
                            if action.executed_at
                            else None
                        ),
                        "disabled": action.disabled,
                    }
                    for action in (notification.original_request.content.actions or [])
                ],
            },
            "source": notification.original_request.source,
            "metadata": notification.original_request.metadata,
            "channels": [
                {
                    "channel_type": ch.channel_type,
                    "status": ch.status.value,
                    "delivered_at": (
                        ch.delivered_at.isoformat() if ch.delivered_at else None
                    ),
                    "error_message": ch.error_message,
                }
                for ch in notification.channels
            ],
        }
