from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.calendar_models import EventCreateRequest
from app.models.mail_models import EmailComposeRequest
from app.models.message_models import FileData
from app.models.search_models import DeepResearchResults, SearchResults
from app.models.weather_models import WeatherData


class ImageData(BaseModel):
    url: str
    prompt: str
    improved_prompt: Optional[str] = None


class EmailFetchData(BaseModel):
    from_: str
    subject: str
    time: str


class CalendarFetchData(BaseModel):
    summary: str
    start_time: str
    calendar_name: str


class CalendarListFetchData(BaseModel):
    name: str
    id: str
    description: str
    backgroundColor: Optional[str] = None


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
    calendar_options: Optional[List[EventCreateRequest]] = None
    search_results: Optional[SearchResults] = None
    deep_research_results: Optional[DeepResearchResults] = None
    weather_data: Optional[WeatherData] = None
    email_compose_data: Optional[List[EmailComposeRequest]] = None
    email_fetch_data: Optional[List[EmailFetchData]] = None
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
