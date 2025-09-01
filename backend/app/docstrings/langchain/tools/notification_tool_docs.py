"""Documentation for notification tools."""

GET_UNREAD_NOTIFICATIONS = """Get user's unread notifications

This tool retrieves only unread notifications for the user. This is specifically designed to show notifications that need user attention. Unread notifications can include:
- Email suggestions and drafts
- Calendar event suggestions
- Todo item suggestions
- System reminders
- Integration prompts
- Support ticket updates

The tool supports limiting the number of results for better performance.

When to use:
- User asks about notifications, alerts, or updates
- User wants to see what's new or what needs attention
- User asks about pending items or suggestions
- User wants to check system messages
- User wants to see unread notifications specifically

Parameters:
- limit: Maximum number of notifications to return (default: 20, max: 50)
- offset: Skip this many notifications for pagination (default: 0)

Returns a list of unread notifications with their content, actions, and metadata.
"""

MARK_NOTIFICATION_READ = """Mark notification as read

This tool marks a specific notification as read, updating its status and removing it from unread counts.

When to use:
- User acknowledges a notification
- User interacts with a notification
- User dismisses a notification

Parameters:
- notification_id: The unique identifier of the notification to mark as read

Returns success status and updated notification details.
"""

EXECUTE_NOTIFICATION_ACTION = """Execute a notification action

This tool executes a specific action associated with a notification, such as:
- Creating a calendar event
- Composing an email
- Adding a todo item
- Opening a modal or form
- Making an API call

When to use:
- User wants to act on a notification
- User accepts a suggestion from a notification
- User clicks an action button in a notification

Parameters:
- notification_id: The unique identifier of the notification
- action_id: The unique identifier of the action to execute

Returns the result of the action execution.
"""
