from fastapi import APIRouter, Depends, HTTPException
from composio import Composio
from app.api.v1.dependencies.oauth_dependencies import get_current_user

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


router = APIRouter()

@router.post("/connect/{provider}")
async def connect_account(provider: str, user: dict = Depends(get_current_user)):
    if provider not in SOCIAL_CONFIGS:
        raise HTTPException(status_code=404, detail="Provider not supported")
    
    config = SOCIAL_CONFIGS[provider]

    try:
        composio_client = Composio(api_key="ak_WdZt4cbr16csoSZJ2IiH")
        connection_request = composio_client.connected_accounts.initiate(
            user_id=user["user_id"],
            auth_config_id=config["auth_config_id"]
        )

        return {
            "status": "pending",
            "redirect_url": connection_request.redirect_url,
            "connection_id": connection_request.id
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
