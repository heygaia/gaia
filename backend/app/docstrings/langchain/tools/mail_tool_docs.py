LIST_GMAIL_LABELS = """
    List all Gmail labels for the authenticated user.

    This tool retrieves all Gmail labels (system and user-created) for organizing and
    filtering emails.

    When to use:
    - When planning email organization or categorization tasks
    - Before applying labels to verify label IDs exist
    - When user asks about available email categories/folders
    - Before creating new labels to avoid duplicates

    Input: No parameters required (authentication handled automatically)

    Output:
    - Dictionary with "labels" containing label objects (id, name, type)
    - Error message if operation fails

    Limitations: Requires Gmail authentication via config.
    """


LIST_GMAIL_MESSAGES = """
    List Gmail messages in the user's inbox.

    This tool fetches messages from the Gmail inbox with details like sender,
    subject, snippet, and timestamp.

    When to use:
    - When user wants to check their recent emails
    - When building an email overview or summary
    - When you need email IDs for other operations (like marking as read)
    - When user asks about their inbox contents

    Input:
    - max_results: Optional, number of messages to return (default: 20)
    - page_token: Optional, for pagination through large inboxes

    Output:
    - Dictionary with "messages" containing email details
    - nextPageToken for pagination if more results exist
    - Error message if operation fails

    Limitations: Only shows inbox messages, not all emails.
    """

SEARCH_GMAIL_MESSAGES = """
Search Gmail messages — from basic inbox listing to advanced filtering.

This tool retrieves messages from the user's Gmail account. It supports everything from simply listing recent inbox emails to executing advanced, fine-grained searches using Gmail-style queries and structured filters.

When to use:
- User wants to see their recent or unread emails
- User asks for a summary or overview of the inbox
- You need to fetch message IDs for further actions (e.g., mark as read)
- Filtering by sender, subject, recipient, or keywords
- Searching for emails within a specific date range
- Locating messages with or without attachments
- Finding specific content in the entire mailbox, not just inbox

Input parameters:
- query: Optional Gmail-style search string (e.g., `from:alice`, `subject:invoice`)
- sender / recipient / subject: Optional structured filters
- has_attachment: True/False to filter emails with or without attachments
- date_from / date_to: Optional date range filter (YYYY/MM/DD)
    - `date_from` is exclusive (starts after this date at 23:59:59)
    - `date_to` is inclusive (includes up to this date at 23:59:59)
    - Dates are adjusted to the user's timezone
- is_read: Optional True/False to filter by read/unread status
- max_results: Optional, defaults to 20
- page_token: Optional for pagination

Output:
- A dictionary with:
    - "messages": List of matched messages (sender, subject, snippet, timestamp, etc.)
    - "nextPageToken": Present if there are more results
    - "error": Present if the operation fails

Usage tips:
- For a simple inbox fetch, leave all filters empty (or just set `max_results`)
- If no messages are found, try adjusting filters or simplifying the query
- You can combine freeform queries with structured filters for better results

Limitations:
- Message previews (snippets) are short and may not show full content
- Some advanced filters may require trial and error for best results
"""

COMPOSE_EMAIL = """
    Compose, write, or draft an email message based on the user's request.

    This tool helps create emails of any type - from simple personal messages to detailed professional communications.

    When to use:
    - User wants to compose, write, send, or draft any email
    - User mentions writing to someone via email
    - User asks to email someone (e.g., "email John", "send an email to Sarah")
    - User provides email content or instructions (e.g., "tell her I love her", "ask about the meeting")
    - User needs help with any email-related task

    The tool will:
    - Create appropriate email content based on the context
    - Handle both brief personal messages and detailed professional emails
    - Automatically resolve recipient names to email addresses when possible
    - Adapt tone and style to match the user's intent

    Input requirements:
    - Body content or instructions for what to write
    - Subject line or topic
    - Optional: recipient name or query to search for their email

    Note: The tool can handle any email request, from "email mom happy birthday" to complex business proposals.
    """

STAR_EMAILS = """
    Star Gmail messages.

    This tool adds the STARRED label to specified messages, making them appear
    starred in Gmail. Starring highlights important emails.

    When to use:
    - When user wants to highlight important emails
    - When marking high-priority messages
    - When implementing favoriting functionality
    - When user explicitly asks to star messages

    Input:
    - message_ids: Required list of Gmail message IDs to star

    Output:
    - Dictionary with success status and affected message IDs
    - Error message if operation fails

    Limitations: Some Gmail views might display starred emails differently.
    """

UNSTAR_EMAILS = """
    Unstar Gmail messages.

    This tool removes the STARRED label from specified messages, removing their star
    status in Gmail.

    When to use:
    - When user wants to remove star status from emails
    - After processing previously starred emails
    - When cleaning up starred emails in bulk
    - When user explicitly asks to unstar messages

    Input:
    - message_ids: Required list of Gmail message IDs to unstar

    Output:
    - Dictionary with success status and affected message IDs
    - Error message if operation fails

    Limitations: Only affects starred messages, no effect on unstarred ones.
    """

ARCHIVE_EMAILS = """
    Archive Gmail messages.

    This tool removes the INBOX label from specified messages, archiving them in Gmail.
    Archiving keeps emails accessible but removes them from the inbox view.

    When to use:
    - When user wants to clean up their inbox
    - After emails have been processed and no longer need attention
    - When implementing "archive" or "clean up" functionality
    - When user explicitly asks to archive messages

    Input:
    - message_ids: Required list of Gmail message IDs to archive

    Output:
    - Dictionary with success status and affected message IDs
    - Error message if operation fails

    Limitations: Archived emails remain searchable and retain other labels.
    """

GET_EMAIL_THREAD = """
    Get complete email thread.

    This tool fetches all messages in a specified Gmail thread, showing the complete
    conversation history in chronological order.

    When to use:
    - When user wants to see an entire email conversation
    - When analyzing email threads or discussions
    - When preparing responses that require conversation context
    - When user asks about previous messages in a thread
    - When summarizing multi-message conversations

    Input:
    - thread_id: Required, the Gmail thread ID to fetch

    Output:
    - Dictionary with thread_id and messages array containing all emails
    - Error message if operation fails

    Limitations: Long threads may contain large amounts of data; specific messages
    still need to be processed individually for detailed operations.
    """

CREATE_GMAIL_LABEL = """
    Create a new Gmail label.

    This tool creates a new label in the user's Gmail account for email organization.
    Labels in Gmail function like folders but allow emails to have multiple labels.

    When to use:
    - When user wants to create new email categories
    - When setting up email organization systems
    - Before applying non-existent labels to emails
    - When user explicitly asks to create a label

    Input:
    - name: Required, name for the new label
    - label_list_visibility: Optional, controls visibility in label list
    - message_list_visibility: Optional, controls visibility next to messages
    - background_color/text_color: Optional, visual customization (hex codes)

    Output:
    - Dictionary with success status and created label object
    - Error message if operation fails

    Limitations: Cannot create system labels; duplicate names will be rejected.
    """

UPDATE_GMAIL_LABEL = """
    Update an existing Gmail label.

    This tool modifies properties of an existing label in the user's Gmail account,
    such as its name, visibility, or colors.

    When to use:
    - When user wants to rename or modify label properties
    - When changing label visibility settings
    - When adjusting label colors for visual organization
    - When user explicitly asks to update a label

    Input:
    - label_id: Required, ID of the label to update
    - name: Optional, new name for the label
    - label_list_visibility/message_list_visibility: Optional visibility settings
    - background_color/text_color: Optional, visual customization (hex codes)

    Output:
    - Dictionary with success status and updated label object
    - Error message if operation fails

    Limitations: System labels like INBOX, SENT, etc. cannot be modified.
    """

DELETE_GMAIL_LABEL = """
    Delete a Gmail label.

    This tool removes an existing label from the user's Gmail account. Emails with
    this label will lose it, but the emails themselves will not be deleted.

    When to use:
    - When user wants to remove unused or obsolete labels
    - When reorganizing email categorization systems
    - When cleaning up label clutter
    - When user explicitly asks to delete a label

    Input:
    - label_id: Required, ID of the label to delete

    Output:
    - Dictionary with success status and deleted label ID
    - Error message if operation fails

    Limitations: System labels like INBOX, SENT, etc. cannot be deleted;
    deletion is permanent and cannot be undone.
    """

APPLY_LABELS_TO_EMAILS = """
    Apply labels to Gmail messages.

    This tool adds specified labels to given messages, enabling organization
    and categorization of emails. Multiple labels can be applied to the same emails.

    When to use:
    - When user wants to categorize or organize emails
    - When implementing auto-filing or tagging systems
    - When user needs to batch-process email organization
    - When user explicitly asks to label messages

    Input:
    - message_ids: Required list of Gmail message IDs to label
    - label_ids: Required list of label IDs to apply

    Output:
    - Dictionary with success status and details of labeled messages
    - Error message if operation fails

    Limitations: Requires valid label IDs obtained from list_gmail_labels or create_gmail_label.
    """

REMOVE_LABELS_FROM_EMAILS = """
    Remove labels from Gmail messages.

    This tool removes specified labels from given messages. This is useful for
    declassifying emails or changing their categorization.

    When to use:
    - When user wants to reorganize email categories
    - When emails no longer belong to certain groups
    - When implementing label management features
    - When user explicitly asks to remove labels from messages

    Input:
    - message_ids: Required list of Gmail message IDs to modify
    - label_ids: Required list of label IDs to remove

    Output:
    - Dictionary with success status and details of modified messages
    - Error message if operation fails

    Limitations: Removing the INBOX label has the effect of archiving emails;
    system labels have special behavior.
    """

CREATE_EMAIL_DRAFT = """
    Create a draft email.

    This tool creates a draft email in the user's Gmail account without sending it.
    Drafts can be reviewed, edited, and sent later.

    When to use:
    - When user wants to compose an email but not send it immediately
    - When preparing emails that need review before sending
    - When creating templates for future use
    - When AI-generated content needs human approval
    - When user explicitly asks to draft an email

    Input:
    - to: Required list of recipient email addresses
    - subject: Required email subject line
    - body: Required email content
    - cc/bcc: Optional additional recipients
    - is_html: Optional boolean, whether body contains HTML formatting

    Output:
    - Dictionary with success status and draft object with ID
    - Error message if operation fails

    Limitations: Draft remains in the user's account until explicitly sent or deleted.
    """

LIST_EMAIL_DRAFTS = """
    List all draft emails.

    This tool fetches all draft emails stored in the user's Gmail account.
    Pagination support is available for accounts with many drafts.

    When to use:
    - When user wants to see their saved drafts
    - When managing draft emails
    - Before updating or sending drafts (to get their IDs)
    - When user asks about incomplete or unsent emails
    - When implementing draft management functionality

    Input:
    - max_results: Optional, number of drafts to return (default: 20)
    - page_token: Optional, for pagination through many drafts

    Output:
    - Dictionary with "drafts" containing draft objects
    - nextPageToken for pagination if more results exist
    - Error message if operation fails

    Limitations: Draft content is summarized; use get_email_draft for complete details.
    """

GET_EMAIL_DRAFT = """
    Get a specific draft email.

    This tool fetches the full content and details of a specific draft email from the
    user's Gmail account, allowing for review before editing or sending.

    When to use:
    - When user wants to review a specific draft
    - Before updating or sending a draft
    - When implementing draft editing features
    - When user asks to see the content of a saved draft
    - After list_email_drafts to get complete details

    Input:
    - draft_id: Required, ID of the draft to fetch

    Output:
    - Dictionary with "draft" containing full message details
    - Error message if operation fails

    Limitations: Requires a valid draft ID from list_email_drafts.
    """


UPDATE_EMAIL_DRAFT = """
    Update a draft email.

    This tool modifies an existing draft email in the user's Gmail account,
    allowing for changes to recipients, subject, body, or other properties.

    When to use:
    - When user wants to edit a previously saved draft
    - When correcting or improving email content
    - When adding or changing recipients
    - After AI-generated content needs human adjustments
    - When user explicitly asks to update a draft

    Input:
    - draft_id: Required, ID of the draft to update
    - to: Required list of recipient email addresses
    - subject: Required email subject line
    - body: Required email content
    - cc/bcc: Optional additional recipients
    - is_html: Optional boolean, whether body contains HTML formatting

    Output:
    - Dictionary with success status and updated draft object
    - Error message if operation fails

    Limitations: All recipient/subject/body fields must be provided with each update,
    even those that aren't changing.
    """

DELETE_EMAIL_DRAFT = """
    Delete a draft email.

    This tool deletes an existing draft email from the user's Gmail account,
    permanently removing it from the Drafts folder.

    When to use:
    - When user wants to remove a draft that's no longer needed
    - When cleaning up outdated draft emails
    - When user has created an improved version of a draft
    - When user explicitly asks to delete a draft

    Input:
    - draft_id: Required, ID of the draft to delete

    Output:
    - Dictionary with success status
    - Error message if operation fails

    Limitations: Deletion is permanent and cannot be undone; requires a valid
    draft ID from list_email_drafts.
    """

SEND_EMAIL_DRAFT = """
    Send a draft email.

    This tool sends an existing draft email from the user's Gmail account,
    delivering it to all recipients specified in the draft.

    When to use:
    - When user wants to send a finalized draft
    - After reviewing and confirming draft content
    - To deliver emails that were prepared in advance
    - When user explicitly asks to send a draft

    Input:
    - draft_id: Required, ID of the draft to send

    Output:
    - Dictionary with success status and sent message details
    - Error message if operation fails

    Limitations: Once sent, emails cannot be unsent; draft is automatically
    moved to Sent folder after sending.
    """

GET_GMAIL_CONTACTS = """
    Get a list of email contacts from Gmail history based on a search query.

    This tool searches through Gmail messages and extracts unique contacts (email addresses
    and names) from people you've previously communicated with.

    When to use:
    - When user wants to find email addresses of specific people
    - When user mentions names but needs their email addresses
    - When creating contact lists or groups
    - When user needs to remember someone's email address
    - When searching for people by name or email

    Input:
    - query: Search query to filter contacts (e.g., name, email, or keywords)
    - max_results: Optional, maximum number of messages to analyze (default: 30)

    Output:
    - Dictionary with "contacts" containing list of contact objects with:
      - name: The contact's name (if available)
      - email: The contact's email address
    - Error message if operation fails

    Limitations: Only extracts contacts from message headers based on search results.
    Quality depends on the format of email addresses in headers and search effectiveness.
    """
