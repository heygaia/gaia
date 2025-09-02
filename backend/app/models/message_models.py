from typing import List, Optional, Dict, Any

from pydantic import BaseModel
from typing_extensions import TypedDict


class MessageDict(TypedDict):
    role: str
    content: str


class FileData(BaseModel):
    fileId: str
    url: str
    filename: str
    type: Optional[str] = "file"
    message: Optional[str] = "File uploaded successfully"


class SelectedWorkflowData(BaseModel):
    id: str
    title: str
    description: str
    steps: List[Dict[str, Any]]


class MessageRequestWithHistory(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    messages: List[MessageDict]
    fileIds: Optional[List[str]] = []
    fileData: Optional[List[FileData]] = []
    selectedTool: Optional[str] = None  # Tool selected via slash commands
    toolCategory: Optional[str] = None  # Category of the selected tool
    selectedWorkflow: Optional[SelectedWorkflowData] = (
        None  # Workflow selected for execution
    )


class SaveIncompleteConversationRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    fileIds: Optional[List[str]] = []
    fileData: Optional[List[FileData]] = []
    selectedTool: Optional[str] = None
    toolCategory: Optional[str] = None
    selectedWorkflow: Optional[SelectedWorkflowData] = None
    incomplete_response: str = ""  # The partial response from the bot


class MessageRequest(BaseModel):
    message: str


class MessageRequestPrimary(BaseModel):
    message: str
    conversation_id: str
