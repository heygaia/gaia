"""
Workflow generation prompts for GAIA workflow system.
"""

WORKFLOW_GENERATION_SYSTEM_PROMPT = """Create a practical workflow plan for this goal using ONLY the available tools listed below.

TITLE: {title}
DESCRIPTION: {description}{previous_context}

CRITICAL REQUIREMENTS:
1. Use ONLY the exact tool names from the list below - do not make up or modify tool names
2. Choose tools that are logically appropriate for the goal
3. Each step must specify tool_name using the EXACT name from the available tools
4. Consider the tool category when selecting appropriate tools
5. Create 4-7 actionable steps that logically break down this goal into executable tasks
6. Use practical and helpful tools that accomplish the goal, avoid unnecessary tools

JSON OUTPUT REQUIREMENTS:
- NEVER include comments (//) in the JSON output
- Use only valid JSON syntax with no explanatory comments
- Tool inputs should contain realistic example values, not placeholders
- All string values must be properly quoted
- No trailing commas or syntax errors

GOOD WORKFLOW EXAMPLES:
- "Plan vacation to Europe" → 1) web_search_tool (research destinations), 2) get_weather (check climate), 3) create_calendar_event (schedule trip dates)
- "Organize project emails" → 1) search_gmail_messages (find project emails), 2) create_gmail_label (create organization), 3) apply_labels_to_emails (organize them)
- "Prepare for client meeting" → 1) search_gmail_messages (find relevant emails), 2) web_search_tool (research client), 3) create_calendar_event (block preparation time)
- "Submit quarterly report" → 1) query_file (review previous reports), 2) generate_document (create new report), 3) create_reminder (set deadline reminder)

Available Tools: {tools}

{format_instructions}"""
