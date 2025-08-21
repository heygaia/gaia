from langchain_cerebras import ChatCerebras
from langchain_core.runnables.utils import ConfigurableField
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-1.5-flash"
CEREBRAS_MODEL = "gpt-oss-120b"


def init_llm(streaming: bool = True):
    return (
        ChatOpenAI(
            model=MODEL,
            temperature=0.1,
            streaming=streaming,
        )
        .configurable_fields(
            model_name=ConfigurableField(id="model_name", name="LLM Model Name")
        )
        .configurable_alternatives(
            ConfigurableField(id="provider"),
            default_key="openai",
            gemini=ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                temperature=0.1,
            ),
            cerebras=ChatCerebras(
                model=CEREBRAS_MODEL,
                temperature=0.1,
                streaming=streaming,
                reasoning_effort="medium",
            ),
        )
    )


def init_gemini_llm():
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0.1,
    )


# def init_llm(streaming: bool = True):
#     return ChatCerebras(
#         model=CEREBRAS_MODEL,
#         temperature=0.1,
#         streaming=streaming,
#         reasoning_effort="medium",
#     )
