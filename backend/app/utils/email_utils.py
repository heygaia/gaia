"""
Email utilities for sending various types of emails.

This module provides functions for sending different types of emails including:
- Support and feature request emails
- User onboarding emails (welcome, pro subscription)
- User engagement emails (inactive user notifications)

All emails use Jinja2 templates for HTML generation and Resend for email delivery.
"""

import os
from datetime import datetime, time
from typing import List, Optional
from zoneinfo import ZoneInfo

import resend
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config.loggers import app_logger as logger
from app.config.settings import settings
from app.models.support_models import SupportEmailNotification, SupportRequestType

# ============================================================================
# EMAIL SERVICE CONFIGURATION
# ============================================================================

# Initialize Resend with API key
resend.api_key = settings.RESEND_API_KEY

# Get the directory where templates are stored
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

# Initialize Jinja2 environment for template rendering
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


# ============================================================================
# SUPPORT & FEATURE REQUEST EMAILS
# ============================================================================


async def send_support_team_notification(
    notification_data: SupportEmailNotification,
) -> None:
    """
    Send email notification to support team when a new support/feature request is created.

    Args:
        notification_data: Support email notification data containing ticket details

    Raises:
        Exception: If email sending fails
    """
    try:
        subject = f"[{notification_data.ticket_id}] New {notification_data.type.value.title()} Request: {notification_data.title}"
        html_content = generate_support_team_email_html(notification_data)

        for support_email in notification_data.support_emails:
            try:
                resend.Emails.send(
                    {
                        "from": "GAIA Support <support@heygaia.io>",
                        "to": [support_email],
                        "subject": subject,
                        "html": html_content,
                        "reply_to": notification_data.user_email,
                    }
                )
                logger.info(f"Support notification sent to {support_email}")
            except Exception as e:
                logger.error(
                    f"Failed to send support email to {support_email}: {str(e)}"
                )
    except Exception as e:
        logger.error(f"Error sending support team notifications: {str(e)}")
        raise


async def send_support_to_user_email(
    notification_data: SupportEmailNotification,
) -> None:
    """
    Send confirmation email to user that their support request has been received.

    Args:
        notification_data: Support email notification data containing ticket details

    Raises:
        Exception: If email sending fails
    """
    try:
        subject = f"[{notification_data.ticket_id}] Your {notification_data.type.value} request has been received"
        html_content = generate_support_to_user_email_html(notification_data)

        resend.Emails.send(
            {
                "from": "GAIA support <support@heygaia.io>",
                "to": [notification_data.user_email],
                "subject": subject,
                "html": html_content,
            }
        )
        logger.info(f"Confirmation email sent to user {notification_data.user_email}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email to user: {str(e)}")
        raise


def generate_support_team_email_html(data: SupportEmailNotification) -> str:
    """
    Generate HTML email content for support team notifications using Jinja2 template.

    Args:
        data: Support email notification data

    Returns:
        str: Rendered HTML email content

    Raises:
        Exception: If template rendering fails
    """
    try:
        template = jinja_env.get_template("support_to_admin.html")

        request_type_label = (
            "Support Request"
            if data.type == SupportRequestType.SUPPORT
            else "Feature Request"
        )

        # Render template with data
        html_content = template.render(
            request_type_label=request_type_label,
            ticket_id=data.ticket_id,
            title=data.title,
            description=data.description,
            user_name=data.user_name,
            user_email=data.user_email,
            admin_url=f"{settings.FRONTEND_URL}/admin/support/{data.ticket_id}",
            attachments=data.attachments,
        )

        return html_content
    except Exception as e:
        logger.error(f"Error generating support team email HTML: {str(e)}")
        raise


def generate_support_to_user_email_html(data: SupportEmailNotification) -> str:
    """
    Generate HTML email content for user confirmation emails using Jinja2 template.

    Args:
        data: Support email notification data

    Returns:
        str: Rendered HTML email content

    Raises:
        Exception: If template rendering fails
    """
    try:
        template = jinja_env.get_template("support_to_user.html")

        request_type_label = (
            "Support Request"
            if data.type == SupportRequestType.SUPPORT
            else "Feature Request"
        )

        # Render template with data
        html_content = template.render(
            request_type_label=request_type_label,
            user_name=data.user_name,
            ticket_id=data.ticket_id,
            title=data.title,
            description=data.description,
            expected_response_time="24 hours",
            attachments=data.attachments,
        )

        return html_content
    except Exception as e:
        logger.error(f"Error generating support to user email HTML: {str(e)}")
        raise


async def send_pro_subscription_email(
    user_name: str,
    user_email: str,
    discord_url: str = "https://discord.heygaia.io",
    whatsapp_url: str = "https://whatsapp.heygaia.io",
    twitter_url: str = "https://twitter.com/_heygaia",
) -> None:
    """Send welcome email to user who upgraded to Pro subscription."""
    try:
        subject = "Welcome to GAIA Pro! 🚀"
        html_content = generate_pro_subscription_html(
            user_name=user_name,
            discord_url=discord_url,
            whatsapp_url=whatsapp_url,
            twitter_url=twitter_url,
        )

        resend.Emails.send(
            {
                "from": "Aryan from GAIA <aryan@heygaia.io>",
                "to": [user_email],
                "subject": subject,
                "html": html_content,
                "reply_to": "aryan@heygaia.io",
            }
        )
        logger.info(f"Pro subscription welcome email sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send pro subscription email to {user_email}: {str(e)}")
        raise


async def send_welcome_email(user_email: str, user_name: Optional[str] = None) -> None:
    """Send welcome email to new user using Jinja2 template."""
    try:
        subject = "From the founder of GAIA, personally"
        html_content = generate_welcome_email_html(user_name)

        if html_content is None:
            raise ValueError("Failed to generate email HTML content")

        resend.Emails.send(
            {
                "from": "Aryan from GAIA <aryan@heygaia.io>",
                "to": [user_email],
                "subject": subject,
                "html": html_content,
                "reply_to": "aryan@heygaia.io",
            }
        )
        logger.info(f"Welcome email sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user_email}: {str(e)}")
        raise


def generate_welcome_email_html(user_name: Optional[str] = None) -> str | None:
    """Generate HTML email content for welcome email using Jinja2 template."""
    try:
        template = jinja_env.get_template("welcome.html")

        # Render template with data
        html_content = template.render(
            user_name=user_name,
            contact_email="aryan@heygaia.io",
            discord_url="https://discord.gg/gaia",
            whatsapp_url="https://chat.whatsapp.com/gaia",
            twitter_url="https://twitter.com/heygaia",
        )

        return html_content
    except Exception as e:
        logger.error(f"Error generating welcome email HTML: {str(e)}")
        raise


async def send_inactive_user_email(
    user_email: str, user_name: Optional[str] = None
) -> None:
    """Send email to inactive user using Jinja2 template."""
    try:
        subject = "We miss you at GAIA 🌱"
        html_content = generate_inactive_user_email_html(user_name)

        resend.Emails.send(
            {
                "from": "Aryan from GAIA <aryan@heygaia.io>",
                "to": [user_email],
                "subject": subject,
                "html": html_content,
                "reply_to": "aryan@heygaia.io",
            }
        )
        logger.info(f"Inactive user email sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send inactive user email to {user_email}: {str(e)}")
        raise


def generate_pro_subscription_html(
    user_name: str, discord_url: str, whatsapp_url: str, twitter_url: str
) -> str:
    """Generate HTML email for pro subscription welcome using the Jinja2 template."""
    try:
        template = jinja_env.get_template("subscribed.html")
        html_content = template.render(
            user_name=user_name,
            discord_url=discord_url,
            whatsapp_url=whatsapp_url,
            twitter_url=twitter_url,
        )
        return html_content
    except Exception as e:
        logger.error(f"Error generating pro subscription email HTML: {str(e)}")
        raise


def generate_inactive_user_email_html(user_name: Optional[str] = None) -> str:
    """Generate HTML email content for inactive user email using Jinja2 template."""
    try:
        template = jinja_env.get_template("inactive.html")

        # Render template with data
        html_content = template.render(
            user_name=user_name,
            contact_email="aryan@heygaia.io",
        )

        return html_content
    except Exception as e:
        logger.error(f"Error generating inactive user email HTML: {str(e)}")
        raise


async def build_gmail_query_with_epoch(
    user_id: str,
    start_from: Optional[str],  # format: "YYYY/MM/DD"
    end_to: Optional[str],  # format: "YYYY/MM/DD"
) -> List[str]:
    """
    Build Gmail search query with epoch-based after/before.

    - If `start_from` is provided, it is treated as:
        'start_from 23:59:59' in user timezone → used as `after:<epoch>` (exclusive)
    - If `end_to` is provided, it is treated as:
        'end_to 23:59:59' in user timezone → used as `before:<epoch>` (inclusive)

    Gmail treats `after:` as exclusive and `before:` as exclusive,
    so to make end inclusive, we add 1 second to the before epoch.
    """
    from app.services.user_service import get_user_by_id

    user = await get_user_by_id(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found for building Gmail query")
    user_tz = ZoneInfo(user.get("timezone", "UTC"))

    query_parts = []

    if start_from:
        date = datetime.strptime(start_from, "%Y/%m/%d")
        dt = datetime.combine(date, time(23, 59, 59), tzinfo=user_tz)
        after_epoch = int(dt.timestamp())
        query_parts.append(f"after:{after_epoch}")

    if end_to:
        date = datetime.strptime(end_to, "%Y/%m/%d")
        dt = datetime.combine(date, time(23, 59, 59), tzinfo=user_tz)
        before_epoch = int(dt.timestamp()) + 1  # to make it inclusive
        query_parts.append(f"before:{before_epoch}")

    return query_parts
