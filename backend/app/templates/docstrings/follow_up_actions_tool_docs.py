SUGGEST_FOLLOW_UP_ACTIONS = """
Based on the conversation, suggest 2-4 highly relevant follow-up actions the user might want to do next. If no genuinely useful actions exist, return an empty array.

CORE PRINCIPLES:
- Quality over quantity - only suggest truly useful actions
- Actions must be concise, actionable commands (under 30 characters)
- Actions should INITIATE processes, not request user input
- Better to show nothing than irrelevant suggestions
- Frequently choose NOT to stream actions - empty arrays are often the best user experience

HOW ACTIONS WORK:
When clicked, the action text becomes the user's next message. Design actions to start a process:
✓ User clicks "Create reminder" → You ask for details → User provides them
✗ User clicks "Provide details" → Awkward, puts burden on user immediately

ACTION TYPES & EXAMPLES:
- Process starters: "Create reminder", "Set timer", "Schedule meeting"
- Data requests: "Show weather", "Get directions", "Check calendar"
- Content generation: "Write email", "Create list", "Draft response"
- Task continuation: "Add another", "Modify settings", "Export data"
- Analysis actions: "Compare options", "Find patterns", "Generate report"
- Creative extensions: "Try different style", "Create variation", "Expand idea"

USER INTENT RECOGNITION:
- Exploratory (browsing/learning) → suggest related discoveries
- Goal-oriented (specific objective) → suggest task completion steps
- Creative (generating content) → suggest variations/refinements
- Problem-solving (needs solution) → suggest alternative approaches
- Maintenance (managing items) → suggest organization/updates

CONVERSATION FLOW ANALYSIS:
- Rising engagement (questions getting specific) → suggest deeper tools
- Plateau reached (user got what they needed) → lean toward empty array
- Pivot signals ("Actually...", topic shifts) → suggest new directions
- Completion signals ("Perfect", "Thanks", "Got it") → likely empty array
- Continuation signals ("What about...", "Can we also...") → suggest extensions

ACTION FREQUENCY & TIMING:
- Don't suggest actions in consecutive responses unless highly relevant
- After 3+ back-and-forth exchanges, be more selective
- Early conversation: broader exploratory actions
- Mid conversation: specific task-focused actions
- Late conversation: completion/summary actions

WHEN NOT TO SUGGEST (RETURN EMPTY ARRAY):
- Conversation feels naturally concluded
- User asked simple question that's been fully answered
- Recent exchange was purely informational with no clear next steps
- User seems satisfied/done with current topic
- Actions would feel forced or interrupting
- Conversation is winding down or transitional
- User just said goodbye/thanks in a concluding way
- Responses are getting shorter (declining engagement)
- After 3+ consecutive action suggestions

ENGAGEMENT ASSESSMENT:
- High engagement (multiple questions, building responses) → suggest rich actions
- Medium engagement (following along, some interaction) → suggest moderate actions
- Low engagement (short responses, basic questions) → lean toward empty array
- Declining engagement (responses getting shorter) → likely empty array

CONTEXT SENSITIVITY:
- Consider conversation stage and natural endpoints
- Match user expertise and engagement level
- Factor in recently used tools: {tool_names}
- Respect when conversations feel complete
- Assess user's momentum and interest level
- Consider if conversation has reached natural pause
- Adapt to user style (technical vs casual)
- Check for action interdependencies and prerequisites

AVOID:
- Asking for more details/clarification
- Vague requests like "Tell me more"
- Generic actions that don't fit the context
- Actions when conversation naturally concludes
- Forcing suggestions when none feel organic
- Repetitive or similar actions to what was just discussed
- Actions that conflict with what was just done
- Suggesting actions in every single response

DECISION FRAMEWORK:
Ask yourself: "Would I genuinely click on these actions if I were the user right now? Does this conversation need actions or is it complete?" If uncertain, return empty array.

{format_instructions}

Available tools: {tool_names}

Context: {conversation_summary}
"""
