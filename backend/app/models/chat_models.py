from enum import Enum
from typing import List, Optional

from app.models.calendar_models import EventCreateRequest
from app.models.mail_models import EmailComposeRequest
from app.models.message_models import FileData, SelectedWorkflowData
from app.models.search_models import DeepResearchResults, SearchResults
from app.models.weather_models import WeatherData
from pydantic import BaseModel, Field


class ImageData(BaseModel):
    url: str
    prompt: str
    improved_prompt: Optional[str] = None


class EmailFetchData(BaseModel):
    from_: str = Field(alias="from")
    subject: str
    time: str
    thread_id: Optional[str] = None


class CalendarFetchData(BaseModel):
    summary: str
    start_time: str
    calendar_name: str


class CalendarListFetchData(BaseModel):
    name: str
    id: str
    description: str
    backgroundColor: Optional[str] = None


class EmailThreadMessage(BaseModel):
    id: str
    from_: str = Field(alias="from")
    sender_name: str
    sender_email: str
    sender_avatar_url: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    time: str
    snippet: Optional[str] = None


class EmailThreadData(BaseModel):
    thread_id: str
    messages: List[EmailThreadMessage]
    messages_count: int


class IntegrationConnectionData(BaseModel):
    """Data structure for integration connection prompts."""

    integration_id: str
    integration_name: str
    integration_icon: str
    integration_description: str
    integration_category: str
    message: str
    connect_url: str
    settings_url: Optional[str] = None


class SupportTicketData(BaseModel):
    """Data structure for support ticket creation."""

    type: str = Field(
        ..., description="Type of support request: 'support' or 'feature'"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Brief title of the issue or request",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed description of the issue or request",
    )
    user_name: Optional[str] = Field(None, description="Name of the user")
    user_email: Optional[str] = Field(None, description="Email of the user")


class MessageModel(BaseModel):
    type: str
    response: str
    date: Optional[str] = None
    image_data: Optional[ImageData] = None
    disclaimer: Optional[str] = None
    subtype: Optional[str] = None
    file: Optional[bytes] = None
    filename: Optional[str] = None
    filetype: Optional[str] = None
    message_id: Optional[str] = None
    fileIds: Optional[List[str]] = []
    fileData: Optional[List[FileData]] = []
    selectedTool: Optional[str] = None
    toolCategory: Optional[str] = None
    selectedWorkflow: Optional[SelectedWorkflowData] = None
    calendar_options: Optional[List[EventCreateRequest]] = None
    search_results: Optional[SearchResults] = None
    deep_research_results: Optional[DeepResearchResults] = None
    weather_data: Optional[WeatherData] = None
    email_compose_data: Optional[List[EmailComposeRequest]] = None
    email_fetch_data: Optional[List[EmailFetchData]] = None
    email_thread_data: Optional[EmailThreadData] = None
    support_ticket_data: Optional[List[SupportTicketData]] = None
    calendar_fetch_data: Optional[List[CalendarFetchData]] = None
    calendar_list_fetch_data: Optional[List[CalendarListFetchData]] = None
    memory_data: Optional[dict] = None
    todo_data: Optional[dict] = None
    document_data: Optional[dict] = None
    goal_data: Optional[dict] = None
    code_data: Optional[dict] = None
    google_docs_data: Optional[dict] = None
    follow_up_actions: Optional[List[str]] = []
    integration_connection_required: Optional[IntegrationConnectionData] = None


class SystemPurpose(str, Enum):
    EMAIL_PROCESSING = "email_processing"
    REMINDER_PROCESSING = "reminder_processing"
    WORKFLOW_EXECUTION = "workflow_execution"
    OTHER = "other"


class ConversationModel(BaseModel):
    conversation_id: str
    description: str = "New Chat"
    is_system_generated: Optional[bool] = False
    system_purpose: Optional[SystemPurpose] = None


class UpdateMessagesRequest(BaseModel):
    conversation_id: str
    messages: List[MessageModel]


class StarredUpdate(BaseModel):
    starred: bool


class PinnedUpdate(BaseModel):
    pinned: bool
