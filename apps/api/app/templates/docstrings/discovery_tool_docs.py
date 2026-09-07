"""Docstrings for the comms-tier discovery tools.

Retrieval matches on these, so each one leads with the user phrasings that
should reach it rather than with a description of the implementation.
"""

FIND_INTEGRATION = """
INTEGRATIONS (FIND): find out whether GAIA has an integration, without connecting anything.

Use this tool when the user asks:
- "Is there a Notion integration?"
- "Do you support Slack?"
- "What can you connect to?"
- "What can you connect to for project management?"
- "Do you work with Airtable?"
- "Can you read my email?"
- "Is there an integration for my CRM?"

PARAMETERS:
- `query` (str): a product name ("notion", "slack") or a capability ("email",
  "crm", "project management"). Matched against integration names,
  descriptions and categories.

BEHAVIOR:
- Searches GAIA's built-in integration catalogue first. These are the only ones
  a connect card can be shown for.
- Tops up from the public community marketplace when there is room.
- Reports the user's REAL connection status for built-in integrations.

RETURN VALUE:
`{"integrations": [...], "query": ...}` with up to 5 rows:
- id: the exact id to pass to `show_connect_card` (e.g. "gmail")
- name: display name
- description: one line
- connected: whether the user already connected it
- source: "platform" (connectable here) or "community" (marketplace listing)

An empty list means GAIA does not have it; say so plainly and never invent an
integration that is not in the results. If a `source: "platform"` row is not
connected and the user wants it, call `show_connect_card` with its id IN THE
SAME REPLY.
"""

SEARCH_PUBLIC_WORKFLOWS = """
WORKFLOWS (SEARCH PUBLIC TEMPLATES): find ready-made public workflow templates.

Use this tool when the user asks:
- "Any public workflow for a weekly investor update?"
- "Is there a ready-made workflow for X?"
- "Do you have a template for daily standup notes?"
- "What workflows can I start from?"
- "Any prebuilt automation for my inbox?"

PARAMETERS:
- `query` (str): the outcome the user wants ("weekly investor update",
  "morning briefing", "triage my inbox").

BEHAVIOR:
- Searches the featured (explore) and community public workflow templates by
  title, description and the integration they are built around.

RETURN VALUE:
`{"workflows": [...], "query": ..., "explore_url": ...}` with up to 5 rows:
- title: the template name
- description: one line on what it does
- source_integration: the integration it is built around, or null
- slug: its handle on the explore page, or null

IMPORTANT: there is NO in-chat action that adds a public workflow. The user
adds it themselves on the explore page, so give them `explore_url` and never
claim you added, created or activated the template. If a row's
`source_integration` is not connected, you may show its connect card with
`show_connect_card` in the same reply.
"""

SHOW_CONNECT_CARD = """
INTEGRATIONS (SHOW CONNECT CARD): put the connect button in front of the user now.

Use this tool the moment your reply is going to mention connecting an
integration. It renders the connect card in THIS reply, so the ask and the tap
are one message.

Use it when the user asks:
- "Connect my Gmail"
- "Link my Notion account"
- "Set up my calendar"
And use it whenever you are about to say that something needs an integration
the user has not connected.

PARAMETERS:
- `integration_id` (str): the exact integration id, e.g. "gmail", "notion",
  "googlecalendar". Get it from `find_integration` when unsure; a wrong id
  shows the user nothing.

BEHAVIOR:
- Shows the connect card, or the reconnect card when their grant expired.
- On text-only platforms (bots) there is no card, so a single-use connect link
  valid for one hour comes back instead.

RETURN VALUE:
A one-line confirmation that the card is in this reply, followed by an
instruction on how to word your reply. Follow it exactly: when a card was
shown, put NO URL in your reply; when a link came back, include it verbatim.

Never tell the user to connect something without calling this tool in the same
reply, and never say the card is on its way or ask whether to send it.
"""
