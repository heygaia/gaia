from composio import Composio
from app.config.settings import settings
from composio_langchain import LangchainProvider

import logging

logger = logging.getLogger(__name__)

class ComposioService:
    def __init__(self):
        self.composio = Composio(provider=LangchainProvider(),api_key="ak_WdZt4cbr16csoSZJ2IiH")
    def get_notion_tools(self,user_id: str):
        """
        Returns Composio-managed Notion tools for a specific user.
        """
        return self.composio.tools.get(user_id=user_id, toolkits=["NOTION"])

    def get_google_sheet_tools(self,user_id: str):
        """
        Returns Composio-managed Notion tools for a specific user.
        """
        return self.composio.tools.get(user_id=user_id, toolkits=["GOOGLESHEET"])

composio_service = ComposioService()