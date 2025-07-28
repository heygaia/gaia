from datetime import datetime, timezone

import requests
from fastapi import HTTPException

from app.config.loggers import app_logger as logger
from app.db.mongodb.collections import users_collection
from app.utils.oauth_utils import upload_user_picture
from app.utils.email_utils import send_welcome_email


async def store_user_info(
    name: str, email: str, picture_url: str, user_timezone: str = "UTC"
):
    """
    Stores user info from Google callback with Cloudinary-hosted profile pictures.

    - Downloads and uploads external images to Cloudinary
    - Updates existing users or creates new ones
    - Ensures profile pictures are always stored on Cloudinary
    - Stores user timezone during initial signup

    Args:
        name (str): The user's name.
        email (str): The user's email.
        picture_url (str): The URL of the profile picture from Google.
        user_timezone (str): The user's timezone identifier (e.g., "America/New_York"). Defaults to "UTC".

    Returns:
        The user's MongoDB _id.

    Raises:
        HTTPException: If any step in the process fails.
    """
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    expected_prefix = "https://res.cloudinary.com"
    current_time = datetime.now(timezone.utc)

    # Check if user already exists
    existing_user = await users_collection.find_one({"email": email})

    # Process the picture URL
    cloudinary_picture_url = None

    # Only process picture if:
    # 1. User is new (no existing_user), OR
    # 2. User exists but has no picture stored, OR
    # 3. User exists but the Google picture URL has changed
    should_process_picture = False

    if existing_user:
        current_picture = existing_user.get("picture", "")
        # If user has no picture, or if Google is providing a picture, we might need to process
        if not current_picture and picture_url:
            should_process_picture = True
            logger.info(
                f"User {email} has no picture stored, will process Google picture"
            )
        else:
            logger.info(f"User {email} already has picture stored, skipping re-upload")
    else:
        # New user - process picture if provided
        should_process_picture = bool(picture_url)
        if should_process_picture:
            logger.info(f"New user {email}, will process Google picture")

    if (
        should_process_picture
        and picture_url
        and not picture_url.startswith(expected_prefix)
    ):
        try:
            response = requests.get(picture_url, timeout=10)
            response.raise_for_status()
            image_bytes = response.content

            public_id = f"user_{email.replace('@', '_at_').replace('.', '_dot_')}"

            cloudinary_picture_url = await upload_user_picture(image_bytes, public_id)

        except requests.RequestException as e:
            logger.error(
                f"Error downloading image from URL {picture_url}: {str(e)}",
                exc_info=True,
            )
            # Keep cloudinary_picture_url as None to indicate failure
    elif picture_url and picture_url.startswith(expected_prefix):
        # Picture is already on Cloudinary
        cloudinary_picture_url = picture_url

    if existing_user:
        update_data = {
            "name": name,
            "updated_at": current_time,
        }

        # Only update picture if:
        # 1. We have a new Cloudinary URL (successful upload)
        # 2. OR the user has no picture and we couldn't get one from Google
        # 3. OR Google no longer provides a picture (clear it)
        current_picture = existing_user.get("picture", "")
        if cloudinary_picture_url is not None:
            update_data["picture"] = cloudinary_picture_url
        elif not picture_url and current_picture:
            # Google no longer provides a picture, clear it
            update_data["picture"] = ""
        # If user already has a picture and we didn't process a new one, keep the existing picture

        await users_collection.update_one({"email": email}, {"$set": update_data})
        return existing_user["_id"]
    else:
        # Validate timezone before storing
        try:
            from zoneinfo import ZoneInfo

            ZoneInfo(user_timezone)  # This will raise an exception if invalid
        except Exception as e:
            logger.warning(
                f"Invalid timezone '{user_timezone}' for user {email}, using UTC: {e}"
            )
            user_timezone = "UTC"

        user_data = {
            "name": name,
            "email": email,
            "picture": cloudinary_picture_url or "",
            "timezone": user_timezone,
            "created_at": current_time,
            "updated_at": current_time,
        }

        result = await users_collection.insert_one(user_data)

        # Send welcome email to new user
        try:
            await send_welcome_email(email, name)
            logger.info(f"Welcome email sent to new user: {email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            # Don't raise exception - user creation should still succeed

        return result.inserted_id
