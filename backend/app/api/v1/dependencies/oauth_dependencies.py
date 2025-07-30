import time
from datetime import datetime
from datetime import timezone as tz
from zoneinfo import ZoneInfo
from typing import Optional

import httpx
from fastapi import Cookie, Header, HTTPException

from app.config.settings import settings
from app.db.mongodb.collections import users_collection
from app.db.redis import get_cache, set_cache
from app.config.loggers import auth_logger as logger

http_async_client = httpx.AsyncClient()


# Thresholds & cache expiry (in seconds)
TOKEN_REFRESH_THRESHOLD = 300  # 5 minutes
USER_CACHE_EXPIRY = 3600  # 1 hour
TOKEN_CACHE_EXPIRY = 3600  # 1 hour
REFRESH_TOKEN_CACHE_EXPIRY = 86400  # 24 hours (refresh tokens typically last longer)


async def get_user_info(access_token: str) -> dict:
    try:
        response = await http_async_client.get(
            settings.GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"HTTP error during user info retrieval: {e}")
        raise HTTPException(status_code=500, detail="Error contacting Google API")
    except httpx.HTTPStatusError as e:
        logger.warning(f"Token verification failed: {e.response.text}")
        raise HTTPException(status_code=401, detail="Invalid or expired access token")


async def refresh_access_token(refresh_token: str) -> dict:
    # Validate required fields
    if not all(
        [
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_CLIENT_SECRET,
            settings.GOOGLE_TOKEN_URL,
        ]
    ):
        logger.error("Missing required credentials for token refresh")
        raise HTTPException(
            status_code=500,
            detail="Missing required credentials for token refresh. Ensure client_id, client_secret, and token_uri are set.",
        )

    try:
        response = await http_async_client.post(
            settings.GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        response.raise_for_status()
        token_data = response.json()
        return {
            "access_token": token_data.get("access_token"),
            "expires_in": token_data.get("expires_in", 3600),
        }
    except httpx.RequestError as e:
        logger.error(f"Token refresh request error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")
    except httpx.HTTPStatusError as e:
        logger.error(f"Token refresh HTTP error: {e.response.text}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")


async def get_valid_access_token(
    refresh_token: str, user_email: Optional[str] = None
) -> tuple[str, int]:
    """
    Refreshes the access token using the refresh token.
    Returns a tuple of the new access token and its expires_in value.

    If user_email is provided, checks for cached token first.
    """
    # Check if we have a cached token for this user
    if user_email:
        cache_key = f"user_token:{user_email}"
        cached_token_data = await get_cache(cache_key)
        if cached_token_data and "access_token" in cached_token_data:
            current_time = int(time.time())
            # Only use cached token if it's not about to expire
            if (
                cached_token_data.get("expires_at", 0)
                > current_time + TOKEN_REFRESH_THRESHOLD
            ):
                logger.debug(f"Using cached access token for user {user_email}")
                return (
                    cached_token_data["access_token"],
                    cached_token_data.get("expires_at", 0) - current_time,
                )

    try:
        token_data = await refresh_access_token(refresh_token)
        new_access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)

        # Cache the new token if we have user email
        if user_email:
            cache_key = f"user_token:{user_email}"
            expires_at = int(time.time()) + expires_in
            await set_cache(
                cache_key,
                {
                    "access_token": new_access_token,
                    "expires_at": expires_at,
                    "refresh_token": refresh_token,
                },
                TOKEN_CACHE_EXPIRY,
            )

        return new_access_token, expires_in
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")


async def cache_refresh_token(user_email: str, refresh_token: str) -> None:
    """
    Cache the refresh token for a user for future use.
    Refresh tokens typically have a much longer lifespan than access tokens.
    """
    if not user_email or not refresh_token:
        return

    cache_key = f"user_refresh:{user_email}"
    await set_cache(
        cache_key,
        {"refresh_token": refresh_token, "cached_at": int(time.time())},
        REFRESH_TOKEN_CACHE_EXPIRY,
    )
    logger.debug(f"Cached refresh token for user {user_email}")


async def get_cached_refresh_token(user_email: Optional[str]) -> Optional[str]:
    """
    Retrieve a cached refresh token for a user.
    """
    if not user_email:
        return None

    cache_key = f"user_refresh:{user_email}"
    cached_data = await get_cache(cache_key)
    if cached_data and "refresh_token" in cached_data:
        logger.debug(f"Using cached refresh token for user {user_email}")
        return cached_data["refresh_token"]

    return None


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    refresh_token: Optional[str] = Cookie(None),
):
    """
    Retrieves the current user by validating or refreshing the access token.
    Uses caching to improve performance.
    """
    if not access_token and not refresh_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_email = None
        user_info = None

        if access_token:
            try:
                user_info = await get_user_info(access_token)
                user_email = user_info.get("email")

                # If we have a valid access token and a refresh token, cache the refresh token
                if user_email and refresh_token:
                    await cache_refresh_token(user_email, refresh_token)

            except HTTPException:
                logger.info("Access token invalid or expired")

        # If the access token is invalid/expired, try to use or refresh a token
        if not user_email:
            # Try to get a cached refresh token if none was provided and we have some user info
            if not refresh_token and user_info and user_info.get("email"):
                temp_email = user_info.get("email")
                if temp_email:  # This check ensures temp_email is not None
                    cached_refresh_token = await get_cached_refresh_token(temp_email)
                    if cached_refresh_token:
                        refresh_token = cached_refresh_token
                        logger.info(f"Using cached refresh token for user {temp_email}")

            if not refresh_token:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Use user_email for cache lookup if we have it
            temp_email = user_email if user_email else None

            # Get a valid access token
            new_access_token, expires_in = await get_valid_access_token(
                refresh_token, temp_email
            )
            access_token = new_access_token

            # Get user info with the new access token
            user_info = await get_user_info(access_token)
            user_email = user_info.get("email")

            # Now that we have the email, cache the refresh token if email is not None
            if user_email:
                await cache_refresh_token(user_email, refresh_token)

                # Update token cache using the retrieved email
                cache_key = f"user_token:{user_email}"
                expires_at = int(time.time()) + expires_in
                await set_cache(
                    cache_key,
                    {
                        "access_token": access_token,
                        "expires_at": expires_at,
                        "refresh_token": refresh_token,
                    },
                    TOKEN_CACHE_EXPIRY,
                )

        if not user_email:
            raise HTTPException(status_code=400, detail="Email not found")

        # Check and update user cache
        cache_key = f"user_cache:{user_email}"
        cached_user_data = await get_cache(cache_key)
        if cached_user_data:
            # Update user's last activity
            await users_collection.update_one(
                {"email": user_email},
                {"$set": {"last_active_at": datetime.now(tz.utc)}},
            )
            # Update with new tokens if available but keep other cached data
            updated = False
            if access_token and access_token != cached_user_data.get("access_token"):
                cached_user_data["access_token"] = access_token
                updated = True
            if updated:
                # Update the cache with new data
                await set_cache(cache_key, cached_user_data, USER_CACHE_EXPIRY)
            return cached_user_data

        user_data = await users_collection.find_one({"email": user_email})
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Update user's last activity
        await users_collection.update_one(
            {"email": user_email}, {"$set": {"last_active_at": datetime.now(tz.utc)}}
        )

        user_info_to_cache = {
            "user_id": str(user_data.get("_id")),
            "email": user_email,
            "name": user_data.get("name"),
            "picture": user_data.get("picture"),
            "access_token": access_token,
            "cached_at": int(time.time()),
        }

        # Include refresh token in user cache if available
        if refresh_token:
            user_info_to_cache["refresh_token"] = refresh_token

        await set_cache(cache_key, user_info_to_cache, USER_CACHE_EXPIRY)

        return user_info_to_cache

    except HTTPException as http_err:
        logger.warning(f"Authentication error: {http_err.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(status_code=500, detail="Authentication processing failed")


def get_user_timezone(
    x_timezone: str = Header(
        default="UTC", alias="x-timezone", description="User's timezone identifier"
    ),
) -> datetime:
    """
    Get the current time in the user's timezone.
    Uses the x-timezone header to determine the user's timezone.

    Args:
        x_timezone (str): The timezone identifier from the request header.
    Returns:
        datetime: The current time in the user's timezone.
    """
    user_tz = ZoneInfo(x_timezone)
    now = datetime.now(user_tz)

    logger.debug(f"User timezone: {user_tz}, Current time: {now}")
    return now
