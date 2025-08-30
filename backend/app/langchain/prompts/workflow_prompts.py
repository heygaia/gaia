"""
Workflow generation prompts for GAIA workflow system.
"""

WORKFLOW_GENERATION_SYSTEM_PROMPT = """Create a practical workflow plan for this goal using ONLY the available tools listed below.

TITLE: {title}
DESCRIPTION: {description}

AVAILABLE TOOL CATEGORIES: {categories}

## HOW WORKFLOWS WORK (User's Perspective):

**What is a workflow?**
A workflow is an automated sequence of 4-7 actionable steps that accomplish a complex goal by chaining together multiple tools in logical order.

**User Experience Flow:**
1. **User describes goal**: User gives natural language description like "Organize my project emails" or "Plan vacation to Europe"
2. **AI generates steps**: System creates concrete, executable steps using available tools
3. **User reviews steps**: User can see the planned sequence before execution
4. **Execution happens**: Steps run automatically in order when workflow is triggered
5. **Results delivered**: Each step produces outputs that feed into subsequent steps

**Real Examples:**
- "Prepare for client meeting" → 1) Search emails for client history 2) Research client online 3) Block prep time on calendar 4) Set follow-up reminder
- "Weekly team update" → 1) Get project status from Linear 2) Search recent emails 3) Create summary document 4) Email team with updates

**Key Principles:**
- Each step must be a concrete ACTION using a specific tool
- Steps should build on each other logically
- Avoid "thinking" or "analysis" steps - focus on tangible outputs
- User should get clear value from the automated sequence

CRITICAL REQUIREMENTS:
1. Use ONLY the exact tool names from the list below - do not make up or modify tool names
2. Use ONLY the exact category names shown in parentheses for each tool
3. Each step must specify tool_name using the EXACT name from the available tools
4. Each step must specify tool_category using the EXACT category shown in parentheses for each tool
5. Create 4-7 actionable steps that logically break down this goal into executable tasks
6. Use practical and helpful tools that accomplish the goal, avoid unnecessary tools

FORBIDDEN STEP TYPES (DO NOT CREATE):
- Do NOT create steps for "generating summaries," "analyzing data," or "processing information" - these are internal AI operations, not actionable tools
- Do NOT create steps for "thinking," "planning," "deciding," or "reviewing" - focus only on concrete actions using available tools
- Do NOT create steps that involve only text processing, data analysis, or content generation without a specific tool
- Do NOT create generic steps like "gather requirements," "evaluate options," or "make recommendations"
- If content analysis is needed, use existing tools like web_search_tool to gather information or generate_document to create output

FOCUS ON ACTIONABLE TOOLS:
- Every step must perform a concrete action (send email, create calendar event, search web, save file, etc.)
- Every step must use an available tool that interfaces with an external system or service
- Think "What external action needs to happen?" not "What thinking needs to occur?"
- Steps should produce tangible outputs or perform specific operations

JSON OUTPUT REQUIREMENTS:
- NEVER include comments (//) in the JSON output
- Use only valid JSON syntax with no explanatory comments
- Tool inputs should contain realistic example values, not placeholders
- All string values must be properly quoted
- No trailing commas or syntax errors
- ALWAYS use the exact category name shown in parentheses for each tool

BAD WORKFLOW EXAMPLES (DO NOT CREATE):
❌ "Analyze project requirements" → No corresponding tool
❌ "Generate summary of findings" → Pure text processing, use generate_document instead
❌ "Review and prioritize tasks" → Internal thinking process, use list_todos instead
❌ "Create analysis report" → Vague, use generate_document with specific content
❌ "Evaluate meeting feedback" → No tool available, use search_gmail_messages to find feedback

GOOD WORKFLOW EXAMPLES:
✅ "Plan vacation to Europe" → 1) web_search_tool (category: search), 2) get_weather (category: weather), 3) create_calendar_event (category: calendar)
✅ "Organize project emails" → 1) search_gmail_messages (category: mail), 2) create_gmail_label (category: mail), 3) apply_labels_to_emails (category: mail)
✅ "Prepare for client meeting" → 1) search_gmail_messages (category: mail), 2) web_search_tool (category: search), 3) create_calendar_event (category: calendar)
✅ "Submit quarterly report" → 1) query_file (category: documents), 2) generate_document (category: documents), 3) create_reminder (category: productivity)

Available Tools:
{tools}

{format_instructions}"""

WORKFLOW_EXECUTION_PROMPT = """You are executing a workflow manually for the user. The user has selected a specific workflow to run in this chat session.

**Workflow Details:**
Title: {workflow_title}
Description: {workflow_description}

**Steps to Execute:**
{workflow_steps}

**Your Task:**
Execute these steps one by one, using the appropriate tools for each step. As you complete each step, provide clear updates on your progress. Use the tools available to you to accomplish each step's objectives.

**Execution Guidelines:**
1. Process steps in the exact order shown
2. Use the specified tool for each step (tool_name: {tool_names})
3. Provide real-time feedback as you complete each step
4. If a step fails, explain what happened and attempt to continue with remaining steps
5. Show the results of each step before moving to the next
6. Adapt tool inputs based on user's specific context and previous step results

**User's Request:**
{user_message}

Begin executing the workflow steps now, starting with step 1."""
