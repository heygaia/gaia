from langchain_core.prompts import PromptTemplate

from app.agents.prompts.agent_prompts import AGENT_SYSTEM_PROMPT

AGENT_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["current_datetime", "user_name", "user_preferences"],
    template=AGENT_SYSTEM_PROMPT,
)
