"""LangChain tools for managing AI-powered workflows (AI_AGENT reminders only).
Each workflow is triggered by a scheduled task and executed using available tools.
"""

CREATE_WORKFLOW = """
Create a scheduled AI workflow.

This sets up a task that runs an LLM-powered action on a schedule. Each run starts a new thread with the given instructions.

⚠️ IMPORTANT:
- This is for **automated tasks that require the AI to process or generate something** on its own.
- Use this when the scheduled action involves **using tools, calling APIs, summarizing content, generating reports, sending emails**, or anything that needs reasoning or execution by the AI.
- This is NOT a static reminder. For reminders, use `CREATE_REMINDER` tool.

Example Use Cases:
- "Every day at 6PM, summarize all my emails."
- "Every Monday at 9AM, generate a market overview using the web search tool."
- "At 7AM daily, create a to-do list based on calendar events."

Scheduling:
- Use `scheduled_at` (ISO 8601) for first run (optional if using `repeat`). Should be in future
- Use `repeat` (cron format) for recurring workflows.
- Optionally limit recurrence:
    • `max_occurrences`: how many times to run
    • `stop_after`: ISO timestamp cutoff. Should be in future

🔧 CRON SYNTAX REFERENCE:
Format: "minute hour day_of_month month day_of_week"
- minute: 0-59
- hour: 0-23 (24-hour format)
- day_of_month: 1-31
- month: 1-12
- day_of_week: 0-7 (0 and 7 are Sunday)

Special Characters:
- * : any value
- , : value list separator
- - : range of values
- / : step values

Instructions:
- Must be fully self-contained
- Include all necessary context, tool usage, input formats, and output expectations
- If required tools aren’t available, creation must fail with a clear error
- Ensure that cron job is correct and is following the syntax above. Do not include seconds in the cron expression.

Payload:
- Format: {"instructions": str}

Args:
    repeat (str, optional): Cron string for recurrence
    scheduled_at (str, optional): ISO timestamp for first execution
    max_occurrences (int, optional): Run count limit
    stop_after (str, optional): Absolute end time
    payload (dict): LLM instructions

Returns:
    str: Success or error message
"""

LIST_USER_WORKFLOWS = """
List all AI agent workflows created by the user.

Args:
    status (str, optional): Filter by workflow state (e.g., "scheduled", "completed")

Returns:
    list[dict]: All matching workflows
"""

GET_WORKFLOW = """
Fetch the full details of a specific AI agent workflow.

Args:
    workflow_id (str): ID of the workflow

Returns:
    dict: Workflow details or error
"""

DELETE_WORKFLOW = """
Cancel a scheduled workflow.

Prevents any further executions.

Args:
    workflow_id (str): ID of the workflow

Returns:
    dict: Success or error message
"""

UPDATE_WORKFLOW = """
Update the schedule or instructions of an AI agent workflow.

Args:
    workflow_id (str): ID of the workflow
    repeat (str, optional): New cron schedule
    max_occurrences (int, optional): Updated run cap
    stop_after (str, optional): New end timestamp
    payload (dict, optional): Updated instructions

Returns:
    dict: Update result or error
"""

SEARCH_WORKFLOWS = """
Search AI agent workflows using a query.

Matches content inside instructions or metadata.

Args:
    query (str): Search term or keyword

Returns:
    list[dict]: Matching workflows or error
"""
