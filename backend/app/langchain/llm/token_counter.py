from typing import Optional

from app.langchain.llm.client import GEMINI_MODEL, OPENAI_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


def get_token_counter(provider: Optional[str] = None, model_name: Optional[str] = None):
    """Get the token counter based on provider and model name."""
    if provider == "openai":
        return ChatOpenAI(
            model=model_name or OPENAI_MODEL,
            temperature=0.1,
        )
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=model_name or GEMINI_MODEL,
            temperature=0.1,
        )
    elif provider == "cerebras":
        return ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0.1,
        )

    return ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.1,
    )
