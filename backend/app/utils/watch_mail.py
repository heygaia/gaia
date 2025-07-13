import asyncio
from datetime import datetime, timedelta, timezone

import httpx

from app.config.loggers import app_logger as logger
from app.config.oauth_config import (
    get_integration_by_id,
)
from app.config.settings import settings
from app.db.mongodb.collections import users_collection
from app.db.redis import set_cache
from app.services.mail_service import get_gmail_service
from app.services.user_service import update_user_profile
from app.utils.oauth_utils import get_tokens_by_user_id

http_async_client = httpx.AsyncClient()


async def watch_mail(
    email: str,
    access_token: str,
    refresh_token: str,
    user_id: str,
) -> None:
    """
    Set up Gmail push notifications for the user's inbox.
    Requires user's OAuth access token and Pub/Sub topic name.
    """
    try:
        logger.info(f"Starting to watch emails for user ({email})")

        # Get scopes from access_token
        authorized_scopes = []
        token_info_response = await http_async_client.get(
            f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
        )
        if token_info_response.status_code == 200:
            token_data = token_info_response.json()
            authorized_scopes = token_data.get("scope", "").split()

        gmail_integration = get_integration_by_id(integration_id="gmail")

        if not gmail_integration:
            raise ValueError("Gmail integration not found in settings")

        is_connected = all(
            scope.scope in authorized_scopes for scope in gmail_integration.scopes
        )

        if not is_connected:
            raise ValueError(
                "Gmail integration is not connected. Please connect Gmail integration first."
            )

        # Build Credentials object from access token
        # Build Gmail API client
        service = get_gmail_service(
            access_token=access_token,
            refresh_token=refresh_token,
        )

        # Gmail Watch Request body
        request_body = {
            "labelIds": ["INBOX"],
            "topicName": settings.GCP_TOPIC_NAME,  # Pub/Sub topic name
            "labelFilterBehavior": "INCLUDE",
        }

        # Make API call
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: service.users().watch(userId="me", body=request_body).execute(),
        )

        if not response or "historyId" not in response:
            raise ValueError("Invalid response from Gmail API")

        logger.info(
            f"Successfully started watching emails for user ({email}). "
            f"History ID: {response.get('historyId')}"
        )

        await update_user_profile(
            user_id=user_id,
            data={
                "gmail_history_id": response["historyId"],
                "gmail_watch_enabled": True,
            },
        )

        # Optionally, store the history ID in Redis for quick access
        await set_cache(
            f"gmail_history_id:{email}",
            response["historyId"],
            ttl=7 * 24 * 60 * 60,  # 7 Days
        )

        # TODO: Process all the mails from the last history ID

    except Exception as e:
        logger.error(
            f"Failed to start watching emails for user ({email}): {str(e)}",
            exc_info=True,
        )


async def renew_gmail_watch_for_user(user: dict) -> dict:
    """
    Renew Gmail watch for a single user.

    Args:
        user: User document from MongoDB

    Returns:
        Dict with status and user info
    """
    user_id = str(user["_id"])
    user_email = user["email"]

    try:
        access_token, refresh_token, tokens_valid = await get_tokens_by_user_id(user_id)
        if not tokens_valid:
            logger.warning(f"Invalid tokens for user {user_email}")
            return {
                "status": "failed",
                "user_email": user_email,
                "error": "Invalid tokens",
            }

        service = get_gmail_service(
            access_token=access_token,
            refresh_token=refresh_token,
        )

        if not service:
            logger.error(f"Failed to get Gmail service for {user_email}")
            return {
                "status": "failed",
                "user_email": user_email,
                "error": "Failed to get Gmail service",
            }

        # Renew the Gmail watch
        await watch_mail(
            email=user_email,
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
        )

        logger.info(f"Renewed Gmail watch for {user_email}")
        return {"status": "success", "user_email": user_email}

    except Exception as e:
        logger.error(f"Failed to renew Gmail watch for {user_email}: {str(e)}")
        return {"status": "failed", "user_email": user_email, "error": str(e)}


async def renew_gmail_watch_subscriptions(ctx: dict, max_concurrent: int = 100) -> str:
    """
    Renew Gmail watch API subscriptions for active users with controlled concurrency.
    Only renews for users who have been active in the last 7 days.

    Args:
        ctx: ARQ context
        max_concurrent: Maximum number of concurrent operations

    Returns:
        Processing result message
    """
    logger.info(
        "Renewing Gmail watch subscriptions for active users (with concurrency control)"
    )

    semaphore = asyncio.Semaphore(max_concurrent)

    async def renew_with_semaphore(user: dict) -> dict:
        async with semaphore:
            return await renew_gmail_watch_for_user(user)

    try:
        # Find users active in the last 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        active_users = await users_collection.find(
            {
                "last_active_at": {"$gte": seven_days_ago},
                "is_active": {"$ne": False},
                "gmail_watch_enabled": {
                    "$ne": False
                },  # Only users with Gmail watch enabled
            }
        ).to_list(length=None)

        if not active_users:
            message = "No active users found for Gmail watch renewal"
            logger.info(message)
            return message

        logger.info(f"Found {len(active_users)} active users for Gmail watch renewal")

        # Create tasks with semaphore control
        tasks = [renew_with_semaphore(user) for user in active_users]

        # Process all users in parallel with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        renewed_count = 0
        failed_count = 0
        error_details = []

        for result in results:
            if isinstance(result, Exception):
                failed_count += 1
                error_details.append(f"Unexpected error: {str(result)}")
            elif isinstance(result, dict):
                if result.get("status") == "success":
                    renewed_count += 1
                else:
                    failed_count += 1
                    error_details.append(
                        f"User {result.get('user_email')}: {result.get('error')}"
                    )
            else:
                failed_count += 1
                error_details.append(f"Unexpected result type: {type(result)}")

        # Log error summary
        if error_details and len(error_details) <= 10:
            logger.warning(f"Gmail watch renewal errors: {error_details}")
        elif len(error_details) > 10:
            logger.warning(
                f"Gmail watch renewal had {len(error_details)} errors (first 5): {error_details[:5]}"
            )

        message = f"Gmail watch renewal: {renewed_count} successful, {failed_count} failed out of {len(active_users)} active users (max_concurrent: {max_concurrent})"
        logger.info(message)
        return message

    except Exception as e:
        error_msg = f"Failed to renew Gmail watch subscriptions: {str(e)}"
        logger.error(error_msg)
        raise
