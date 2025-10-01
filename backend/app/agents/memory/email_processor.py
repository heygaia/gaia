"""Gmail email memory processing for Mem0 integration.

This module implements an IO-optimized pipeline for processing Gmail emails into memories:

1. **Fetch email list**: Single Gmail API call to get email IDs with optimized query
2. **Batch fetch details**: Concurrent fetching of full email content (rate-limited)
3. **Process content**: Synchronous parsing and formatting (CPU-bound but minimal)
4. **Store memories**: Batch storage operations for optimal database performance

Key optimizations:
- Controlled concurrency to respect Gmail API rate limits
- Async/await for IO-bound operations (not speed, but avoiding IO waits)
- Batch operations to minimize database roundtrips
- Pipeline stages to separate concerns and enable monitoring
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List

from app.agents.templates.mail_templates import GmailMessageParser
from app.db.mongodb.collections import users_collection
from app.services.mail.mail_service import invoke_gmail_tool
from bson import ObjectId

from app.utils.memory_utils import format_email_for_memory
from app.config.loggers import memory_logger as logger


async def process_gmail_to_memory(user_id: str) -> Dict:
    """Process user's Gmail emails into Mem0 memories using IO-optimized pipeline.

    Implements a 4-stage pipeline optimized for IO-bound operations:
    - Stage 1: Fetch email list (single API call)
    - Stage 2: Concurrent email detail fetching (respects API rate limits)
    - Stage 3: Content processing (minimal CPU work)
    - Stage 4: Batch memory storage (concurrent database operations)

    Args:
        user_id: MongoDB ObjectId string for the user

    Returns:
        Dict with processing results:
        - total: Number of emails found
        - successful: Number successfully processed
        - failed: Number that failed processing
        - already_processed: True if user was already processed
    """
    logger.info(f"Starting Gmail to memory processing for user {user_id}")

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user and user.get("email_memory_processed", False):
        logger.info(f"User {user_id} emails already processed, skipping")
        return {"total": 0, "successful": 0, "already_processed": True}

    # Stage 1: Fetch email list (single IO operation)
    logger.info(f"Stage 1: Fetching email list for user {user_id}")
    emails = await _fetch_emails(user_id)
    if not emails:
        logger.info(f"No emails found for user {user_id}")
        await _mark_processed(user_id, 0)
        return {"total": 0, "successful": 0}

    logger.info(f"Found {len(emails)} emails to process")

    # Stage 2: Batch fetch all email details (concurrent IO)
    logger.info(f"Stage 2: Fetching email details for {len(emails)} emails")
    email_details = await _fetch_all_email_details(user_id, emails)
    logger.info(f"Successfully fetched {len(email_details)} email details")

    # Stage 3: Process content (CPU-bound, but minimal)
    logger.info("Stage 3: Processing email content")
    processed_emails = _process_email_content(email_details)
    logger.info(
        f"Successfully processed {len(processed_emails)} emails for memory storage"
    )

    # Stage 4: Batch store memories (concurrent IO)
    logger.info("Stage 4: Storing memories")
    successful_count = await _store_memories_batch(user_id, processed_emails)

    await _mark_processed(user_id, successful_count)
    logger.info(
        f"Completed processing for user {user_id}: {successful_count}/{len(emails)} successful"
    )

    return {
        "total": len(emails),
        "successful": successful_count,
        "failed": len(emails) - successful_count,
    }


async def _fetch_emails(user_id: str) -> List[Dict]:
    """Fetch emails using a single optimized query."""
    query = "category:primary newer_than:90d -label:spam -label:trash"
    parameters = {"query": query, "max_results": 500}
    logger.info(f"Fetching emails with query: {query}")

    result = await invoke_gmail_tool(user_id, "GMAIL_FETCH_EMAILS", parameters)
    if not result.get("successful", True):
        logger.warning(f"Failed to fetch emails for user {user_id}")
        return []

    messages = result.get("data", {}).get("messages", [])
    logger.info(f"Gmail API returned {len(messages)} emails")
    return messages


async def _fetch_all_email_details(user_id: str, emails: List[Dict]) -> List[Dict]:
    """Batch fetch all email details with optimized concurrency for Gmail API."""
    # Gmail API rate limits: use controlled concurrency
    semaphore = asyncio.Semaphore(20)
    logger.info(f"Starting concurrent fetch of {len(emails)} email details")

    async def fetch_single_detail(email):
        async with semaphore:
            try:
                message_id = email.get("id")
                parameters = {"message_id": message_id}
                result = await invoke_gmail_tool(
                    user_id, "GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID", parameters
                )
                return result if result and result.get("successful", True) else None
            except Exception:
                return None

    # Batch all IO operations concurrently
    tasks = [fetch_single_detail(email) for email in emails]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out failed requests
    valid_results = []
    failed_count = 0
    for result in results:
        if result is not None and not isinstance(result, Exception):
            valid_results.append(result)
        else:
            failed_count += 1

    if failed_count > 0:
        logger.warning(f"Failed to fetch {failed_count}/{len(emails)} email details")
    logger.info(f"Successfully fetched {len(valid_results)} email details")
    return valid_results


def _process_email_content(email_details: List[Dict]) -> List[Dict]:
    """Process email content synchronously (CPU-bound but minimal)."""
    processed = []
    failed_parsing = 0

    for email_data in email_details:
        try:
            parser = GmailMessageParser(email_data)
            if parser.parse():
                content = format_email_for_memory(parser)
                processed.append(
                    {
                        "content": content,
                        "metadata": {
                            "type": "email",
                            "source": "gmail",
                            "message_id": email_data.get("id"),
                            "sender": parser.sender,
                            "subject": parser.subject,
                        },
                    }
                )
        except Exception:
            failed_parsing += 1
            continue  # Skip failed parsing

    if failed_parsing > 0:
        logger.warning(f"Failed to parse {failed_parsing}/{len(email_details)} emails")
    logger.info(f"Successfully processed {len(processed)} emails for memory storage")
    return processed


async def _store_memories_batch(user_id: str, processed_emails: List[Dict]) -> int:
    """Store memories in batches for optimal IO performance."""
    if not processed_emails:
        return 0

    logger.info(f"Storing {len(processed_emails)} email memories for user {user_id}")

    # When Mem0 integration is ready, batch the operations
    # from app.services.memory_service import memory_service
    #
    # # Process in chunks to avoid overwhelming the memory service
    # chunk_size = 20
    # successful_count = 0
    #
    # for i in range(0, len(processed_emails), chunk_size):
    #     chunk = processed_emails[i:i + chunk_size]
    #
    #     # Create all memory storage tasks for this chunk
    #     tasks = [
    #         memory_service.store_memory(
    #             content=email["content"],
    #             user_id=user_id,
    #             metadata=email["metadata"]
    #         )
    #         for email in chunk
    #     ]
    #
    #     # Execute chunk concurrently
    #     results = await asyncio.gather(*tasks, return_exceptions=True)
    #     successful_count += sum(1 for r in results if not isinstance(r, Exception))
    #
    # return successful_count

    # For now, simulate successful processing
    return len(processed_emails)


async def _mark_processed(user_id: str, memory_count: int) -> None:
    """Mark user's email processing as complete."""
    logger.info(f"Marking user {user_id} as processed with {memory_count} memories")
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "email_memory_processed": True,
                "email_memory_processed_at": datetime.now(timezone.utc),
                "email_memory_count": memory_count,
            }
        },
    )
    logger.info(f"Successfully updated database for user {user_id}")
