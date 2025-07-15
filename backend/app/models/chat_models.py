from enum import Enum
from typing import List, Optional

from app.models.calendar_models import EventCreateRequest
from app.models.message_models import FileData
from app.models.search_models import DeepResearchResults, SearchResults
from app.models.weather_models import WeatherData
from pydantic import BaseModel


class ImageData(BaseModel):
    url: str
    prompt: str
    improved_prompt: Optional[str] = None


class MessageModel(BaseModel):
    type: str  # "user" or "bot"
    response: str  # Content of the message
    date: Optional[str] = None  # Date of the message or empty
    # Legacy fields - kept for backward compatibility
    # imagePrompt: Optional[str] = None  # The user prompt for the image
    # improvedImagePrompt: Optional[str] = None  # Improved user prompt for the image
    # imageUrl: Optional[str] = None  # URL for the image
    # New structured field for image data
    image_data: Optional[ImageData] = None
    searchWeb: Optional[bool] = False  # Whether it's a web search request
    deepSearchWeb: Optional[bool] = False  # Whether it's a deep research request
    pageFetchURLs: Optional[List] = []
    # Any disclaimer associated with the message
    disclaimer: Optional[str] = None
    # Type of file if it contains a file (image, pdf, etc.)
    subtype: Optional[str] = None
    file: Optional[bytes] = None  # Binary data for the file
    filename: Optional[str] = None  # Name of the file, if any
    filetype: Optional[str] = None  # Name of the file, if any
    message_id: Optional[str] = None  # Message ID
    fileIds: Optional[List[str]] = []  # List of file IDs associated with the message
    fileData: Optional[List[FileData]] = []  # Complete file metadata
    selectedTool: Optional[str] = None  # Tool selected via slash commands
    toolCategory: Optional[str] = None  # Category of the selected tool
    calendar_options: Optional[List[EventCreateRequest]] = None
    search_results: Optional[SearchResults] = None
    deep_research_results: Optional[DeepResearchResults] = (
        None  # Results from deep research
    )
    weather_data: Optional[WeatherData] = None  # Weather data from OpenWeatherMap API
    email_compose_data: Optional[dict] = None  # Email compose data from mail_tool
    memory_data: Optional[dict] = None  # Complete memory operation data
    todo_data: Optional[dict] = None  # Data related to todo operations
    document_data: Optional[dict] = None  # Data related to todo operations
    goal_data: Optional[dict] = None  # Data related to goal operations
    code_data: Optional[dict] = (
        None  # Code execution data with language, code, and output
    )
    google_docs_data: Optional[dict] = None  # Google Docs data from google_docs_tool


class SystemConversationPurpose(str, Enum):
    EMAIL_PROCESSING = "email_processing"
    WORKFLOW_PROCESSING = "workflow_processing"
    OTHER = "other"  # Default or other purposes


class ConversationModel(BaseModel):
    conversation_id: str
    description: str = "New Chat"
    is_system_generated: Optional[bool] = False
    system_purpose: Optional[SystemConversationPurpose] = None


class UpdateMessagesRequest(BaseModel):
    conversation_id: str
    messages: List[MessageModel]
    # new_messages: List[MessageModel]


class StarredUpdate(BaseModel):
    starred: bool


class PinnedUpdate(BaseModel):
    pinned: bool
