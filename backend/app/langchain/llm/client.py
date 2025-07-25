from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-1.5-flash"


def init_llm(streaming: bool = True, model: Optional[str] = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or MODEL,
        temperature=0.1,
        streaming=streaming,
    )


def init_gemini_llm(model: Optional[str] = None) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model or GEMINI_MODEL,
        temperature=0.1,
    )
