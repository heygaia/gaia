"""
Waitlist routes for the GAIA API.

This module contains routes related to the waitlist functionality of the GAIA API.
"""

from fastapi import APIRouter, Request
from app.models.general_models import WaitlistItem
from app.services.waitlist_service import (
    get_waitlist_members_service,
    waitlist_signup_service,
)

router = APIRouter()


@router.get("/waitlist")
async def get_waitlist_members():
    """
    Retrieve the list of waitlist members.

    Returns:
        dict: A dictionary containing the count and emails of waitlist members.
    """
    # await clean_and_update_waitlist_members()

    return await get_waitlist_members_service()


@router.post("/waitlist")
async def waitlist_signup(item: WaitlistItem, request: Request):
    """
    Sign up a new member to the waitlist.

    Args:
        item (WaitlistItem): The waitlist item containing the member's information.
        request (Request): The FastAPI request object for extracting client info.

    Returns:
        dict: A message indicating the result of the signup operation.
    """
    return await waitlist_signup_service(item, request)
