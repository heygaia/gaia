from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.calendar_models import EventCreateRequest
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


class MessageModel(BaseModel):
    type: str
    response: str
    date: Optional[str] = None
    image_data: Optional[ImageData] = None
    searchWeb: Optional[bool] = False
    deepSearchWeb: Optional[bool] = False
    pageFetchURLs: Optional[List] = []
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
    email_compose_data: Optional[dict] = None
    memory_data: Optional[dict] = None
    todo_data: Optional[dict] = None
    document_data: Optional[dict] = None
    goal_data: Optional[dict] = None
    code_data: Optional[dict] = None
    google_docs_data: Optional[dict] = None


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
