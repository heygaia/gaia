from composio import Composio, schema_modifier
from app.config.settings import settings
from composio_langchain import LangchainProvider
from composio.types import Tool
import logging

logger = logging.getLogger(__name__)

SOCIAL_CONFIGS = {
    "notion": {
        "auth_config_id": "ac_9Yho1TxOcxHh",
        "toolkit": "NOTION"
    },
    "twitter": {
        "auth_config_id": "ac_o66V1UO0-GI2",
        "toolkit": "TWITTER"
    },
    "google_sheets": {
        "auth_config_id": "ac_r5-Q6qJ4U8Qk",
        "toolkit": "GOOGLE_SHEETS"
    },
    "linkedin": {
        "auth_config_id": "ac_X0iHigf4UZ2c",
        "toolkit": "LINKEDIN"
    }
}


@schema_modifier(toolkits=["NOTION"])
def inject_user_id(tool, toolkit, schema: Tool):
    """
    Dynamically inject user_id from RunnableConfig into Composio tools at runtime.
    """
    # runnable_config = context.get("config")  
    
    # if runnable_config:
    #     metadata = runnable_config.get("metadata", {})
    #     user_id = metadata.get("user_id")
        # if user_id:
    # schema["args"]["user_id"] = 
    schema.description += f"if user_id is not provided use this 688bc1c38769a8edbc71954a"
    return schema


class ComposioService:
    def __init__(self):
        self.composio = Composio(provider=LangchainProvider(), api_key=settings.COMPOSIO_KEY)

    def connect_account(self, provider: str, user_id: str):
        """
        Initiates connection flow for a given provider and user.
        """
        if provider not in SOCIAL_CONFIGS:
            raise ValueError(f"Provider '{provider}' not supported")

        config = SOCIAL_CONFIGS[provider]

        try:
            connection_request = self.composio.connected_accounts.initiate(
                user_id=user_id,
                auth_config_id=config["auth_config_id"]
            )

            return {
                "status": "pending",
                "redirect_url": connection_request.redirect_url,
                "connection_id": connection_request.id
            }
        except Exception as e:
            logger.error(f"Error connecting {provider} for {user_id}: {e}")
            raise

    def get_notion_tools(self, user_id: str):
        # self.composio.tools._get()
        # self.composio.tools.get_raw_composio_tools()
        return self.composio.tools.get(user_id=user_id, toolkits=["NOTION"],modifiers=[inject_user_id])

    def get_google_sheet_tools(self, user_id: str):
        return self.composio.tools.get(user_id=user_id, toolkits=["GOOGLESHEETS"])

    def get_x_tools(self, user_id: str):
        return self.composio.tools.get(user_id=user_id, toolkits=["TWITTER"])

    def get_linkedin_tools(self, user_id: str):
        return self.composio.tools.get(user_id=user_id, toolkits=["LINKEDIN"])


composio_service = ComposioService()
