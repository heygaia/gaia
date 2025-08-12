from datetime import datetime
from functools import lru_cache
from typing import Optional
from urllib.parse import urlencode

import httpx
from app.api.v1.dependencies.oauth_dependencies import (
    get_current_user,
    get_user_timezone,
)
from app.config.loggers import auth_logger as logger
from app.config.oauth_config import (
    OAUTH_INTEGRATIONS,
    IntegrationConfigResponse,
    get_integration_by_id,
    get_integration_scopes,
)
from app.config.settings import settings
from app.config.token_repository import token_repository
from app.models.user_models import (
    OnboardingPreferences,
    OnboardingRequest,
    OnboardingResponse,
    UserUpdateResponse,
)
from app.services.oauth_service import store_user_info
from app.services.onboarding_service import (
    complete_onboarding,
    get_user_onboarding_status,
    update_onboarding_preferences,
)
from app.services.user_service import update_user_profile
from app.utils.oauth_utils import fetch_user_info_from_google, get_tokens_from_code
from app.utils.watch_mail import watch_mail
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse, RedirectResponse
from workos import WorkOSClient

router = APIRouter()
http_async_client = httpx.AsyncClient()

workos = WorkOSClient(
    api_key=settings.WORKOS_API_KEY, client_id=settings.WORKOS_CLIENT_ID
)


@lru_cache(maxsize=1)
def _build_integrations_config():
    """
    Build and cache the integrations configuration response.
    This function is cached using lru_cache for performance.
    """
    integration_configs = []
    for integration in OAUTH_INTEGRATIONS:
        config = IntegrationConfigResponse(
            id=integration.id,
            name=integration.name,
            description=integration.description,
            icons=integration.icons,
            category=integration.category,
            provider=integration.provider,
            available=integration.available,
            loginEndpoint=(
                f"oauth/login/integration/{integration.id}"
                if integration.available
                else None
            ),
            isSpecial=integration.is_special,
            displayPriority=integration.display_priority,
            includedIntegrations=integration.included_integrations,
        )
        integration_configs.append(config.model_dump())

    return {"integrations": integration_configs}


def clear_integrations_cache():
    """
    Clear the integrations configuration cache.
    Call this function when the integration configuration changes.
    """
    _build_integrations_config.cache_clear()


# @router.get("/login/google")
# async def login_google():
#     """Basic Google OAuth for signup - only requests essential scopes."""
#     scopes = [
#         "openid",
#         "profile",
#         "email",
#     ]
#     params = {
#         "response_type": "code",
#         "client_id": settings.GOOGLE_CLIENT_ID,
#         "redirect_uri": settings.GOOGLE_CALLBACK_URL,
#         "scope": " ".join(scopes),
#         "access_type": "offline",
#         "prompt": "select_account",  # Only force account selection for initial login
#     }
#     auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
#     return RedirectResponse(url=auth_url)


@router.get("/login/workos")
async def login_workos():
    """
    Start the WorkOS SSO authentication flow.

    Returns:
        RedirectResponse: Redirects the user to the WorkOS SSO authorization URL
    """
    # Add any needed parameters for your SSO implementation
    authorization_url = workos.user_management.get_authorization_url(
        provider="authkit",
        redirect_uri=settings.WORKOS_REDIRECT_URI,
    )

    return RedirectResponse(url=authorization_url)


@router.get("/workos/callback")
async def workos_callback(
    code: Optional[str] = None,
) -> RedirectResponse:
    """
    Handle the WorkOS SSO callback.

    Args:
        background_tasks: FastAPI background tasks
        code: Authorization code from WorkOS
        error: Error message (if any)access_token

    Returns:
        RedirectResponse to the frontend with auth tokens
    """
    try:
        # Validate code parameter
        if not code:
            logger.error("No authorization code received from WorkOS")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=missing_code"
            )

        auth_response = workos.user_management.authenticate_with_code(
            code=code,
            session={
                "seal_session": True,
                "cookie_password": settings.WORKOS_COOKIE_PASSWORD,
            },
        )

        # Extract user information
        email = auth_response.user.email
        first = auth_response.user.first_name or ""
        last = auth_response.user.last_name or ""
        name = f"{first} {last}".strip()
        picture_url = auth_response.user.profile_picture_url

        # Store user info in our database
        await store_user_info(name, email, picture_url)

        # Set cookies and redirect to frontend
        redirect_url = settings.FRONTEND_URL
        response = RedirectResponse(url=f"{redirect_url}/redirect")

        # Set cookies with appropriate security settings
        response.set_cookie(
            key="wos_session",
            value=auth_response.sealed_session or auth_response.access_token,
            httponly=True,
            secure=settings.ENV == "production",
            samesite="lax",
        )

        return response

    except HTTPException as e:
        logger.error(f"HTTP error during WorkOS : {e.detail}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error={e.detail}")

    except Exception as e:
        logger.error(f"Unexpected error during WorkOS callback: {str(e)}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=server_error")


@router.get("/login/integration/{integration_id}")
async def login_integration(
    integration_id: str, user: dict = Depends(get_current_user)
):
    """Dynamic OAuth login for any configured integration."""
    # Get the integration configuration
    integration = get_integration_by_id(integration_id)
    if not integration:
        raise HTTPException(
            status_code=404, detail=f"Integration {integration_id} not found"
        )

    if not integration.available:
        raise HTTPException(
            status_code=400, detail=f"Integration {integration_id} is not available yet"
        )

    # Handle different OAuth providers
    if integration.provider == "google":
        # Get base scopes
        base_scopes = ["openid", "profile", "email"]

        # Get new integration scopes
        new_scopes = get_integration_scopes(integration_id)

        # Get existing scopes from user's current token
        existing_scopes = []
        user_id = user.get("user_id")

        if user_id:
            try:
                token = await token_repository.get_token(
                    str(user_id), "google", renew_if_expired=False
                )
                existing_scopes = str(token.get("scope", "")).split()
            except Exception as e:
                logger.warning(f"Could not get existing scopes: {e}")

        # Combine all scopes (base + existing + new), removing duplicates
        all_scopes = list(set(base_scopes + existing_scopes + new_scopes))

        params = {
            "response_type": "code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_CALLBACK_URL,
            "scope": " ".join(all_scopes),
            "access_type": "offline",
            "prompt": "consent",  # Only force consent for additional scopes
            "include_granted_scopes": "true",  # Include previously granted scopes
            "login_hint": user.get("email"),
        }
        auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
        return RedirectResponse(url=auth_url)

    # Add other providers here (GitHub, Notion, etc.)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth provider {integration.provider} not implemented",
        )


@router.get("/google/callback", response_class=RedirectResponse)
async def callback(
    background_tasks: BackgroundTasks,
    code: Optional[str] = None,
    error: Optional[str] = None,
) -> RedirectResponse:
    try:
        # Handle OAuth errors (e.g., user canceled)
        if error:
            logger.warning(f"OAuth error: {error}")
            if error == "access_denied":
                # User canceled OAuth flow
                redirect_url = f"{settings.FRONTEND_URL}/redirect?oauth_error=cancelled"
            else:
                # Other OAuth errors
                redirect_url = f"{settings.FRONTEND_URL}/redirect?oauth_error={error}"
            return RedirectResponse(url=redirect_url)

        # Check if we have the authorization code
        if not code:
            logger.error("No authorization code provided")
            redirect_url = f"{settings.FRONTEND_URL}/redirect?oauth_error=no_code"
            return RedirectResponse(url=redirect_url)

        # Get tokens from authorization code
        tokens = await get_tokens_from_code(code)
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token and not refresh_token:
            raise HTTPException(
                status_code=400, detail="Missing access or refresh token"
            )

        # Get user info using access token
        user_info = await fetch_user_info_from_google(access_token)
        user_email = user_info.get("email")
        user_name = user_info.get("name")
        user_picture = user_info.get("picture")

        if not user_email:
            raise HTTPException(status_code=400, detail="Email not found in user info")

        # Store user info and get user_id
        user_id = await store_user_info(user_name, user_email, user_picture)

        # Store token in the repository
        await token_repository.store_token(
            user_id=str(user_id),
            provider="google",
            token_data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": tokens.get("token_type", "Bearer"),
                "expires_in": tokens.get("expires_in", 3600),  # Default 1 hour,
                "scope": tokens.get("scope", ""),
            },
        )

        # Redirect URL can include tokens if needed
        redirect_url = f"{settings.FRONTEND_URL}/redirect"
        response = RedirectResponse(url=redirect_url)

        # Add background task to register user to watch emails
        background_tasks.add_task(
            watch_mail,
            email=user_email,
            access_token=access_token,
            user_id=user_id,
            refresh_token=refresh_token,
        )

        return response

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=dict)
async def get_me(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """
    Returns the current authenticated user's details.
    Uses the dependency injection to fetch user data.
    """
    # fetch_last_week_emails.delay(user)

    # Get onboarding status
    onboarding_status = await get_user_onboarding_status(user["user_id"])

    return {
        "message": "User retrieved successfully",
        **user,
        "onboarding": onboarding_status,
    }


@router.get("/integrations/config")
async def get_integrations_config():
    """
    Get the configuration for all integrations.
    This endpoint is public and returns integration metadata.
    Uses lru_cache for improved performance.
    """
    cached_config = _build_integrations_config()
    return JSONResponse(content=cached_config)


@router.get("/integrations/status")
async def get_integrations_status(
    user: dict = Depends(get_current_user),
):
    """
    Get the integration status for the current user based on OAuth scopes.
    """
    try:
        authorized_scopes = []
        user_id = user.get("user_id")

        # Get token from repository
        try:
            if not user_id:
                logger.warning("User ID not found in user object")
                raise ValueError("User ID not found")

            token = await token_repository.get_token(
                str(user_id), "google", renew_if_expired=True
            )
            authorized_scopes = str(token.get("scope", "")).split()

        except Exception as e:
            logger.warning(f"Error retrieving token from repository: {e}")
            # Continue with empty scopes

        # Dynamically check each integration's status
        integration_statuses = []
        for integration in OAUTH_INTEGRATIONS:
            is_connected = False

            # Check connection based on provider
            if integration.provider == "google" and authorized_scopes:
                # Check if all required scopes are present
                required_scopes = get_integration_scopes(integration.id)
                is_connected = all(
                    scope in authorized_scopes for scope in required_scopes
                )

                # Special handling for unified integrations
                if integration.is_special and integration.included_integrations:
                    # For unified integrations, check if ALL included integrations are connected
                    included_connected = []
                    for included_id in integration.included_integrations:
                        included_integration = get_integration_by_id(included_id)
                        if included_integration:
                            included_scopes = get_integration_scopes(included_id)
                            included_is_connected = all(
                                scope in authorized_scopes for scope in included_scopes
                            )
                            included_connected.append(included_is_connected)

                    # Unified integration is connected only if ALL included ones are connected
                    is_connected = (
                        all(included_connected) if included_connected else False
                    )

            # Add other provider checks here (GitHub, Notion, etc.)

            integration_statuses.append(
                {"integrationId": integration.id, "connected": is_connected}
            )

        return JSONResponse(
            content={
                "integrations": integration_statuses,
                "debug": {
                    "authorized_scopes": authorized_scopes,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error checking integration status: {e}")
        # Return all disconnected on error
        return JSONResponse(
            content={
                "integrations": [
                    {"integrationId": i.id, "connected": False}
                    for i in OAUTH_INTEGRATIONS
                ]
            }
        )


@router.patch("/me", response_model=UserUpdateResponse)
async def update_me(
    name: Optional[str] = Form(None),
    picture: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
):
    """
    Update the current user's profile information.
    Supports updating name and profile picture.
    """
    user_id = user.get("user_id")

    if not user_id or not isinstance(user_id, str):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Process profile picture if provided
    picture_data = None
    if picture and picture.size and picture.size > 0:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if picture.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
            )

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if picture.size > max_size:
            raise HTTPException(
                status_code=400, detail="File size too large. Maximum size is 5MB"
            )

        picture_data = await picture.read()

    # Update user profile
    updated_user = await update_user_profile(
        user_id=user_id, name=name, picture_data=picture_data
    )

    return UserUpdateResponse(**updated_user)


@router.post("/onboarding", response_model=OnboardingResponse)
async def complete_user_onboarding(
    onboarding_data: OnboardingRequest,
    user: dict = Depends(get_current_user),
    user_time: datetime = Depends(get_user_timezone),
):
    """
    Complete user onboarding by storing preferences.
    This endpoint should be called when the user completes the onboarding flow.
    """
    try:
        updated_user = await complete_onboarding(
            user["user_id"], onboarding_data, user_timezone=user_time
        )

        return OnboardingResponse(
            success=True, message="Onboarding completed successfully", user=updated_user
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error completing onboarding: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to complete onboarding")


@router.get("/onboarding/status", response_model=dict)
async def get_onboarding_status(user: dict = Depends(get_current_user)):
    """
    Get the current user's onboarding status and preferences.
    """
    status = await get_user_onboarding_status(user["user_id"])
    return status


@router.patch("/onboarding/preferences", response_model=dict)
async def update_user_preferences(
    preferences: OnboardingPreferences, user: dict = Depends(get_current_user)
):
    """
    Update user's onboarding preferences.
    This can be used from the settings page to update preferences after onboarding.
    """
    try:
        updated_user = await update_onboarding_preferences(user["user_id"], preferences)

        return {
            "success": True,
            "message": "Preferences updated successfully",
            "user": updated_user,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.patch("/name", response_model=UserUpdateResponse)
async def update_user_name(
    name: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """
    Update the user's name. This is the consolidated endpoint for name updates.
    """
    try:
        user_id = user.get("user_id")

        if not user_id or not isinstance(user_id, str):
            raise HTTPException(status_code=400, detail="Invalid user ID")

        updated_user = await update_user_profile(user_id=user_id, name=name)
        return UserUpdateResponse(**updated_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating user name: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update name")


@router.post("/logout")
async def logout(
    request: Request,
):
    """
    Logout user and return logout URL for frontend redirection.
    """
    wos_session = request.cookies.get("wos_session")

    if not wos_session:
        raise HTTPException(status_code=401, detail="No active session")

    try:
        session = workos.user_management.load_sealed_session(
            sealed_session=wos_session,
            cookie_password=settings.WORKOS_COOKIE_PASSWORD,
        )

        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")

        logout_url = session.get_logout_url()

        # Create response with logout URL
        response = JSONResponse(content={"logout_url": logout_url})

        # Clear the session cookie
        response.delete_cookie(
            "wos_session",
            httponly=True,
            path="/",
            secure=settings.ENV == "production",
            samesite="lax",
        )

        return response

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")
