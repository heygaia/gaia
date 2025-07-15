"""LangChain tools for managing scheduled reminders (STATIC only)."""

CREATE_REMINDER = """
Create a static reminder — a scheduled notification with a title and body.

⚠️ IMPORTANT:
- This is for **simple alerts or reminders only**, with no AI processing or actions.
- Use this when the user just wants to be **notified** about something with a title and message.
- This is NOT for tasks that involve summarization, tool usage, or AI actions. For those, use `CREATE_WORKFLOW` tool.

Example Use Cases:
- "Remind me to call mom at 7PM."
- "Notify me about my flight check-in tomorrow at 6AM."
- "Every Sunday at 8PM, remind me to prepare for Monday."

Scheduling:
- Use `scheduled_at` (ISO 8601) for first run (optional if using `repeat`). Should be in future
- Use `repeat` (cron format) for recurring reminders.
- Optionally limit recurrence:
    • `max_occurrences`: number of times to run
    • `stop_after`: ISO timestamp after which reminder stops. Should be in future

Payload:
- Format: {"title": str, "body": str}

Args:
    repeat (str, optional): Cron string for recurrence
    scheduled_at (str, optional): ISO start time
    max_occurrences (int, optional): Max number of runs
    stop_after (str, optional): End time
    payload (dict): Reminder content (title and body)

Returns:
    str: Success or error message
"""

LIST_USER_REMINDERS = """
List all static reminders created by the user.

Args:
    status (str, optional): Filter by state (e.g., "scheduled", "completed")

Returns:
    list[dict]: All matching static reminders
"""

GET_REMINDER = """
Fetch the details of a static reminder by ID.

Args:
    reminder_id (str): ID of the reminder

Returns:
    dict: Reminder details or error
"""

DELETE_REMINDER = """
Cancel a static reminder.

Prevents future execution.

Args:
    reminder_id (str): ID of the reminder to cancel

Returns:
    dict: Success or error confirmation
"""

UPDATE_REMINDER = """
Update an existing static reminder’s timing or content.

Args:
    reminder_id (str): ID of the reminder
    repeat (str, optional): New cron pattern
    max_occurrences (int, optional): New run limit
    stop_after (str, optional): New end timestamp
    payload (dict, optional): New title/body content

Returns:
    dict: Update result or error
"""

SEARCH_REMINDERS = """
Search static reminders using a text query.

Searches titles and body fields.

Args:
    query (str): Search term (e.g., "meeting", "medication")

Returns:
    list[dict]: Matching reminders or error
"""
