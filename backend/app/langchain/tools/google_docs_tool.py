from typing import Annotated, Dict, Optional, Union

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from app.config.loggers import chat_logger as logger
from app.decorators import with_rate_limiting, require_integration, with_doc
from app.docstrings.langchain.tools.google_docs_tool_docs import (
    CREATE_GOOGLE_DOC,
    LIST_GOOGLE_DOCS,
    GET_GOOGLE_DOC,
    UPDATE_GOOGLE_DOC,
    FORMAT_GOOGLE_DOC,
    SHARE_GOOGLE_DOC,
    SEARCH_GOOGLE_DOCS,
)

from app.langchain.templates.google_docs_templates import (
    GOOGLE_DOCS_CREATE_TEMPLATE,
    GOOGLE_DOCS_LIST_TEMPLATE,
    GOOGLE_DOCS_GET_TEMPLATE,
    GOOGLE_DOCS_UPDATE_TEMPLATE,
    GOOGLE_DOCS_FORMAT_TEMPLATE,
    GOOGLE_DOCS_SHARE_TEMPLATE,
    GOOGLE_DOCS_SEARCH_TEMPLATE,
)
from app.services.google_docs_service import (
    create_google_doc,
    list_google_docs,
    get_google_doc,
    update_google_doc_content,
    format_google_doc,
    share_google_doc,
    search_google_docs,
)


def get_auth_from_config(config: RunnableConfig) -> Dict[str, str]:
    """Extract access and refresh tokens from the config."""
    if not config:
        logger.error("Google Docs tool called without config")
        return {"access_token": "", "refresh_token": ""}

    configurable = config.get("configurable", {})
    return {
        "access_token": configurable.get("access_token", ""),
        "refresh_token": configurable.get("refresh_token", ""),
    }


@tool
@with_rate_limiting("google_docs_operations")
@with_doc(CREATE_GOOGLE_DOC)
@require_integration("google_docs")
async def create_google_doc_tool(
    config: RunnableConfig,
    title: Annotated[str, "Title of the new Google Doc"],
    content: Annotated[Optional[str], "Initial content for the document"] = None,
) -> str:
    """Create a new Google Doc with the specified title and optional initial content."""
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return "Authentication credentials not provided"

        # Send progress update
        writer = get_stream_writer()
        writer({"progress": f"Creating Google Doc '{title}'..."})

        result = await create_google_doc(
            refresh_token=auth["refresh_token"],
            access_token=auth["access_token"],
            title=title,
            content=content,
        )

        # Send structured data to frontend
        writer = get_stream_writer()
        writer(
            {
                "google_docs_data": {
                    "document": {
                        "id": result["document_id"],
                        "title": result["title"],
                        "url": result["url"],
                        "content": content or "Empty document created",
                        "type": "google_doc",
                    },
                    "action": "create",
                    "message": f"Created Google Doc: {result['title']}",
                    "type": "create",
                }
            }
        )

        logger.info(f"Created Google Doc: {result['document_id']}")

        # Return formatted response using template
        return GOOGLE_DOCS_CREATE_TEMPLATE.format(
            title=result["title"],
            document_id=result["document_id"],
            url=result["url"],
            content=(
                f"Initial content: {content}"
                if content
                else "Empty document ready for editing."
            ),
        )

    except Exception as e:
        logger.error(f"Error creating Google Doc: {e}")
        return f"Error creating Google Doc: {str(e)}"


@tool
@with_rate_limiting("google_docs_operations")
@with_doc(LIST_GOOGLE_DOCS)
@require_integration("google_docs")
async def list_google_docs_tool(
    config: RunnableConfig,
    limit: Annotated[int, "Maximum number of documents to return"] = 50,
    query: Annotated[Optional[str], "Search query to filter documents"] = None,
) -> str:
    """List the user's Google Docs with optional filtering."""
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return "Authentication credentials not provided"

        docs = await list_google_docs(
            refresh_token=auth["refresh_token"],
            access_token=auth["access_token"],
            limit=limit,
            query=query,
        )

        # Send structured data to frontend
        writer = get_stream_writer()

        # Format documents for better frontend display
        formatted_docs = []
        for doc in docs:
            formatted_docs.append(
                {
                    "id": doc["document_id"],
                    "title": doc["title"],
                    "url": doc["url"],
                    "created_time": doc.get("created_time"),
                    "modified_time": doc.get("modified_time"),
                    "type": "google_doc",
                }
            )

        writer(
            {
                "google_docs_data": {
                    "documents": formatted_docs,
                    "count": len(docs),
                    "query": query,
                    "action": "list",
                    "message": f"Found {len(docs)} document{'s' if len(docs) != 1 else ''}"
                    + (f" matching '{query}'" if query else ""),
                    "type": "list",
                }
            }
        )

        logger.info(f"Listed {len(docs)} Google Docs")

        if not docs:
            query_text = f' matching "{query}"' if query else ""
            return f"No Google Docs found{query_text}."

        # Format docs list for template
        docs_list = "\n".join(
            [
                f"• **{doc['title']}** - [Open]({doc['url']})"
                for doc in docs[:5]  # Show first 5 docs
            ]
        )
        if len(docs) > 5:
            docs_list += f"\n... and {len(docs) - 5} more documents"

        query_text = f' matching "{query}"' if query else ""

        # Return formatted response using template
        return GOOGLE_DOCS_LIST_TEMPLATE.format(
            count=len(docs),
            plural="s" if len(docs) != 1 else "",
            query_text=query_text,
            docs_list=docs_list,
        )

    except Exception as e:
        logger.error(f"Error listing Google Docs: {e}")
        return f"Error listing Google Docs: {str(e)}"


@tool
@with_rate_limiting("google_docs_operations")
@with_doc(GET_GOOGLE_DOC)
async def get_google_doc_tool(
    document_id: Annotated[str, "ID of the document to retrieve"],
    config: RunnableConfig,
) -> str:
    """Retrieve the content and metadata of a specific Google Doc."""
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return "Authentication credentials not provided"

        # Send progress update
        writer = get_stream_writer()
        writer({"progress": "Retrieving Google Doc content..."})

        doc = await get_google_doc(
            refresh_token=auth["refresh_token"],
            access_token=auth["access_token"],
            document_id=document_id,
        )

        # Send structured data to frontend
        writer = get_stream_writer()
        writer(
            {
                "google_docs_data": {
                    "document": {
                        "id": document_id,
                        "title": doc["title"],
                        "url": doc["url"],
                        "content": doc["content"],
                        "type": "google_doc",
                    },
                    "action": "get",
                    "message": f"Retrieved document: {doc['title']}",
                    "type": "retrieve",
                }
            }
        )

        logger.info(f"Retrieved Google Doc: {document_id}")

        # Truncate content for preview
        content_preview = (
            doc["content"][:500] + "..."
            if len(doc["content"]) > 500
            else doc["content"]
        )

        # Return formatted response using template
        return GOOGLE_DOCS_GET_TEMPLATE.format(
            title=doc["title"],
            document_id=document_id,
            url=doc["url"],
            content_preview=content_preview,
        )

    except Exception as e:
        logger.error(f"Error retrieving Google Doc {document_id}: {e}")
        return f"Error retrieving Google Doc: {str(e)}"


@tool
@with_rate_limiting("google_docs_operations")
@with_doc(UPDATE_GOOGLE_DOC)
async def update_google_doc_tool(
    config: RunnableConfig,
    document_id: Annotated[str, "ID of the document to update"],
    content: Annotated[str, "Content to add or replace"],
    insert_at_end: Annotated[
        bool, "Whether to append at end or replace all content"
    ] = True,
) -> str:
    """Update the content of an existing Google Doc."""
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return "Authentication credentials not provided"

        # Send progress update
        writer = get_stream_writer()
        action_type = (
            "Appending content to" if insert_at_end else "Replacing content in"
        )
        writer({"progress": f"{action_type} Google Doc..."})

        result = await update_google_doc_content(
            refresh_token=auth["refresh_token"],
            access_token=auth["access_token"],
            document_id=document_id,
            content=content,
            insert_at_end=insert_at_end,
        )

        # Get document info for display
        doc_info = await get_google_doc(
            auth["refresh_token"], auth["access_token"], document_id
        )

        # Send structured data to frontend
        writer = get_stream_writer()
        writer(
            {
                "google_docs_data": {
                    "title": doc_info["title"],
                    "url": result["url"],
                    "document_id": document_id,
                    "action": "update",
                    "content_preview": (
                        content[:200] + "..." if len(content) > 200 else content
                    ),
                }
            }
        )

        logger.info(f"Updated Google Doc: {document_id}")

        action_text = "appended to" if insert_at_end else "replaced in"
        content_preview = content[:200] + "..." if len(content) > 200 else content

        # Return formatted response using template
        return GOOGLE_DOCS_UPDATE_TEMPLATE.format(
            document_id=document_id,
            action=action_text,
            url=result["url"],
            content_preview=content_preview,
        )

    except Exception as e:
        logger.error(f"Error updating Google Doc {document_id}: {e}")
        return f"Error updating Google Doc: {str(e)}"


@tool
@with_rate_limiting("google_docs_operations")
@with_doc(FORMAT_GOOGLE_DOC)
async def format_google_doc_tool(
    document_id: Annotated[str, "ID of the document to format"],
    start_index: Annotated[int, "Start position for formatting"],
    end_index: Annotated[int, "End position for formatting"],
    config: RunnableConfig,
    bold: Annotated[Optional[bool], "Apply bold formatting"] = None,
    italic: Annotated[Optional[bool], "Apply italic formatting"] = None,
    underline: Annotated[Optional[bool], "Apply underline formatting"] = None,
    font_size: Annotated[Optional[int], "Font size in points"] = None,
    foreground_color: Annotated[
        Optional[Dict[str, float]], "Text color as RGB values (0-1)"
    ] = None,
) -> str:
    """Apply formatting to a specific range of text in a Google Doc."""
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return "Authentication credentials not provided"

        # Send progress update
        writer = get_stream_writer()
        writer({"progress": "Applying formatting to Google Doc..."})

        formatting: Dict[str, Union[bool, int, Dict[str, float]]] = {}
        if bold is not None:
            formatting["bold"] = bold
        if italic is not None:
            formatting["italic"] = italic
        if underline is not None:
            formatting["underline"] = underline
        if font_size is not None:
            formatting["fontSize"] = font_size
        if foreground_color is not None:
            formatting["foregroundColor"] = foreground_color

        result = await format_google_doc(
            refresh_token=auth["refresh_token"],
            access_token=auth["access_token"],
            document_id=document_id,
            start_index=start_index,
            end_index=end_index,
            formatting=formatting,
        )

        # Get document info for display
        doc_info = await get_google_doc(
            auth["refresh_token"], auth["access_token"], document_id
        )

        # Send structured data to frontend
        writer = get_stream_writer()
        writer(
            {
                "google_docs_data": {
                    "title": doc_info["title"],
                    "url": result["url"],
                    "document_id": document_id,
                    "action": "format",
                    "formatting": formatting,
                    "range": f"{start_index}-{end_index}",
                }
            }
        )

        logger.info(f"Applied formatting to Google Doc: {document_id}")

        # Build formatting description
        format_parts = []
        if bold:
            format_parts.append("bold")
        if italic:
            format_parts.append("italic")
        if underline:
            format_parts.append("underline")
        if font_size:
            format_parts.append(f"font size {font_size}pt")
        if foreground_color:
            format_parts.append("text color")

        formatting_text = (
            ", ".join(format_parts) if format_parts else "custom formatting"
        )

        # Return formatted response using template
        return GOOGLE_DOCS_FORMAT_TEMPLATE.format(
            document_id=document_id,
            formatting=formatting_text,
            range=f"characters {start_index}-{end_index}",
            url=result["url"],
        )

    except Exception as e:
        logger.error(f"Error formatting Google Doc {document_id}: {e}")
        return f"Error formatting Google Doc: {str(e)}"


@tool
@with_rate_limiting("google_docs_operations")
@with_doc(SHARE_GOOGLE_DOC)
async def share_google_doc_tool(
    document_id: Annotated[str, "ID of the document to share"],
    email: Annotated[str, "Email address to share with"],
    config: RunnableConfig,
    role: Annotated[str, "Permission level (reader, writer, owner)"] = "writer",
    send_notification: Annotated[bool, "Whether to send email notification"] = True,
) -> str:
    """Share a Google Doc with another user."""
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return "Authentication credentials not provided"

        # Send progress update
        writer = get_stream_writer()
        writer({"progress": f"Sharing Google Doc with {email}..."})

        result = await share_google_doc(
            refresh_token=auth["refresh_token"],
            access_token=auth["access_token"],
            document_id=document_id,
            email=email,
            role=role,
            send_notification=send_notification,
        )

        # Get document info for display
        doc_info = await get_google_doc(
            auth["refresh_token"], auth["access_token"], document_id
        )

        # Send structured data to frontend
        writer = get_stream_writer()
        writer(
            {
                "google_docs_data": {
                    "title": doc_info["title"],
                    "url": result["url"],
                    "document_id": document_id,
                    "action": "share",
                    "shared_with": email,
                    "role": role,
                    "notification_sent": send_notification,
                }
            }
        )

        logger.info(f"Shared Google Doc {document_id} with {email}")

        notification_text = "with" if send_notification else "without"

        # Return formatted response using template
        return GOOGLE_DOCS_SHARE_TEMPLATE.format(
            email=email,
            role=role,
            document_id=document_id,
            notification=notification_text,
            url=result["url"],
        )

    except Exception as e:
        logger.error(f"Error sharing Google Doc {document_id}: {e}")
        return f"Error sharing Google Doc: {str(e)}"


@tool
@with_rate_limiting("google_docs_operations")
@with_doc(SEARCH_GOOGLE_DOCS)
async def search_google_docs_tool(
    query: Annotated[str, "Search terms to look for"],
    config: RunnableConfig,
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """Search through the user's Google Docs by title and content."""
    try:
        auth = get_auth_from_config(config)

        if not auth["access_token"] or not auth["refresh_token"]:
            return "Authentication credentials not provided"

        # Send progress update
        writer = get_stream_writer()
        writer({"progress": f"Searching Google Docs for '{query}'..."})

        docs = await search_google_docs(
            refresh_token=auth["refresh_token"],
            access_token=auth["access_token"],
            query=query,
            limit=limit,
        )

        # Send structured data to frontend
        writer = get_stream_writer()

        # Format documents for better frontend display
        formatted_docs = []
        for doc in docs:
            formatted_docs.append(
                {
                    "id": doc["document_id"],
                    "title": doc["title"],
                    "url": doc["url"],
                    "created_time": doc.get("created_time"),
                    "modified_time": doc.get("modified_time"),
                    "type": "google_doc",
                }
            )

        writer(
            {
                "google_docs_data": {
                    "documents": formatted_docs,
                    "query": query,
                    "count": len(docs),
                    "action": "search",
                    "message": f"Found {len(docs)} document{'s' if len(docs) != 1 else ''} matching '{query}'",
                    "type": "search",
                }
            }
        )

        logger.info(f"Found {len(docs)} Google Docs matching query: {query}")

        if not docs:
            return f"No Google Docs found matching '{query}'."

        # Format search results for template
        docs_list = "\n".join(
            [
                f"• **{doc['title']}** - [Open]({doc['url']})"
                for doc in docs[:5]  # Show first 5 results
            ]
        )
        if len(docs) > 5:
            docs_list += f"\n... and {len(docs) - 5} more results"

        # Return formatted response using template
        return GOOGLE_DOCS_SEARCH_TEMPLATE.format(
            query=query,
            count=len(docs),
            plural="s" if len(docs) != 1 else "",
            docs_list=docs_list,
        )

    except Exception as e:
        logger.error(f"Error searching Google Docs: {e}")
        return f"Error searching Google Docs: {str(e)}"


# Export all tools for registry
tools = [
    create_google_doc_tool,
    list_google_docs_tool,
    get_google_doc_tool,
    update_google_doc_tool,
    format_google_doc_tool,
    share_google_doc_tool,
    search_google_docs_tool,
]
