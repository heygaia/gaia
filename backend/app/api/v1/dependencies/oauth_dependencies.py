from datetime import datetime
from zoneinfo import ZoneInfo

from app.config.loggers import auth_logger as logger
from fastapi import Depends, Header, HTTPException, Request, WebSocket, status


async def get_current_user(request: Request):
    """
    Retrieves the current user from request state.
    Authentication is handled by the WorkOSAuthMiddleware.

    Args:
        request: FastAPI request object with authenticated user in state

    Returns:
        User data dictionary with authentication info

    Raises:
        HTTPException: On authentication failure
    """
    if not hasattr(request.state, "authenticated") or not request.state.authenticated:
        logger.info("No authenticated user found in request state")
        raise HTTPException(
            status_code=401, detail="Unauthorized: Authentication required"
        )
    if not request.state.user:
        logger.error("User marked as authenticated but no user data found")
        raise HTTPException(status_code=401, detail="Unauthorized: User data missing")

    # Return user info from request state
    return request.state.user


async def get_current_user_ws(websocket: WebSocket):
    """
    Authenticate a user from a WebSocket connection using cookies.
    This is a special version of get_current_user for WebSocket connections.

    Args:
        websocket: The WebSocket connection with cookies

    Returns:
        User data dictionary with authentication info

    Raises:
        WebSocketException: Connection will be closed on auth failure
    """
    from app.utils.auth_utils import authenticate_workos_session

    # Extract the session cookie from WebSocket
    wos_session = websocket.cookies.get("wos_session")

    if not wos_session:
        logger.info("No session cookie in WebSocket request")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return {}

    # Use shared authentication logic
    user_info, _ = await authenticate_workos_session(session_token=wos_session)

    if not user_info:
        logger.warning("WebSocket authentication failed")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return {}

    return user_info


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


async def get_user_timezone_from_preferences(
    user: dict = Depends(get_current_user),
) -> str:
    """
    Get the user's timezone from their stored preferences.
    Falls back to UTC if no timezone is set.

    Args:
        user: User data from get_current_user dependency

    Returns:
        User's timezone string (e.g., 'America/New_York', 'UTC')
    """
    try:
        # Only check the root level timezone field
        timezone = user.get("timezone")
        logger.debug(f"User timezone from user.timezone: {timezone}")

        if timezone and timezone.strip():
            logger.debug(f"Using user's stored timezone: {timezone}")
            return timezone.strip()

        # Fallback to UTC
        logger.debug("No user timezone found, falling back to UTC")
        return "UTC"

    except Exception as e:
        logger.warning(f"Error getting user timezone from preferences: {e}")
        return "UTC"
