SUGGEST_FOLLOW_UP_ACTIONS = """
Based on the conversation so far, suggest 2-4 relevant follow-up actions that the user might want to do next.

This tool provides contextual suggestions for what the user might want to do next,
making the conversation flow more natural and productive.

HOW FOLLOW-UP ACTIONS WORK:
- Follow-up actions appear as clickable buttons/chips in the user interface
- When a user clicks on a follow-up action, the EXACT text of that action is sent as their next message
- The action text becomes the user's input, so it must be a complete, actionable request
- These are NOT just descriptions or suggestions - they are actual commands the user will send

CRITICAL INTERACTION FLOW:
- User clicks action → Action text sent as user message → You respond → User can then provide more details
- Actions should be INITIATING commands that start a process, not requests for the user to provide info
- After you respond to an action, the user can naturally continue the conversation with additional details

GOOD FLOW EXAMPLES:
✓ User clicks "Create calendar event" → You ask for details → User provides details
✓ User clicks "Set reminder" → You ask when/what for → User specifies
✓ User clicks "Add to shopping list" → You ask what items → User lists items

BAD FLOW EXAMPLES:
✗ "Provide event details" (puts burden on user immediately, breaks flow)
✗ "Tell me more" (too vague, user already expects you to act)
✗ "Enter reminder text" (asking user to provide info rather than starting action)

When to use:
- After completing a task or providing information
- When the response might lead to natural next steps
- To guide users toward related functionality
- To enhance user engagement and discoverability

Input:
- actions: Array of follow-up action suggestions (2-4 recommended)

Each action should be:
- A concise command that initiates an action (3-4 words preferred)
- Something that starts a process rather than asks user for immediate input
- Contextually relevant to what just happened
- Clear about what the user wants you to do
- Under 30 characters for optimal UI display

GOOD EXAMPLES:
- "Create reminder"
- "Set calendar event"
- "Add to list"
- "Show weather forecast"
- "Schedule meeting"
- "Send email"

BAD EXAMPLES:
- "Provide more details" (asks user for input immediately)
- "Tell me about this" (too vague)
- "Enter event information" (puts burden on user)
- "What else do you need?" (not actionable)

Consider:
- What tools or features were just used
- What specific data was generated or retrieved
- Natural next actions that can be initiated from current context
- Related functionality that logically follows
- Actions that START processes rather than ask for user input

DESIGN PRINCIPLE: Actions should be INITIATORS, not REQUESTERS
- Focus on what the user wants to DO next, not what they need to PROVIDE
- The action starts the process, then you can ask for details in your response
- Keep actions short and punchy (3-4 words ideal)

Important: If there are no genuinely relevant or helpful follow-up actions based on the current context,
return an empty array. Do not force suggestions or create generic actions just to fill the array.
Quality over quantity - only suggest actions that would truly be useful to the user at this moment.

{format_instructions}

Conversation context: {conversation_summary}

Available tools: {tool_names}
"""
