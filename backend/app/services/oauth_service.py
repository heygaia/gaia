from datetime import datetime, timezone
from typing import Optional

from app.config.loggers import app_logger as logger
from app.db.mongodb.collections import users_collection
from app.utils.email_utils import send_welcome_email, add_contact_to_resend
from fastapi import HTTPException


async def store_user_info(name: str, email: str, picture_url: Optional[str]):
    """
    Stores user info from Google callback.

    - Updates existing users or creates new ones
    - Stores profile picture URL directly without processing

    Args:
        name (str): The user's name.
        email (str): The user's email.
        picture_url (str): The URL of the profile picture from Google.

    Returns:
        The user's MongoDB _id.

    Raises:
        HTTPException: If any step in the process fails.
    """
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    current_time = datetime.now(timezone.utc)

    # Check if user already exists
    existing_user = await users_collection.find_one({"email": email})

    if existing_user:
        update_data = {
            "name": name,
            "updated_at": current_time,
        }

        # Update picture URL if provided, otherwise keep existing or set empty
        if picture_url:
            update_data["picture"] = picture_url
        elif not existing_user.get("picture"):
            update_data["picture"] = ""

        await users_collection.update_one({"email": email}, {"$set": update_data})
        return existing_user["_id"]
    else:
        user_data = {
            "name": name,
            "email": email,
            "picture": picture_url or "",
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

        # Add contact to Resend audience
        try:
            await add_contact_to_resend(email, name)
            logger.info(f"Contact added to Resend audience for new user: {email}")
        except Exception as e:
            logger.error(
                f"Failed to add contact to Resend audience for {email}: {str(e)}"
            )
            # Don't raise exception - user creation should still succeed

        return result.inserted_id
