# Email processing graph using the generalized plan-execute framework
from contextlib import asynccontextmanager
from typing import List

from app.langchain.core.graph_builder.build_plan_execute_graph import (
    PlanExecuteConfig,
    PlanExecuteProcessor,
    PlanExecuteTemplateProvider,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate


class EmailTemplateProvider(PlanExecuteTemplateProvider):
    """Email-specific template provider"""

    def __init__(self):
        # Import email-specific models
        from app.models.mail_models import (
            EmailProcessingPlan,
            EmailProcessingReplanResult,
        )

        self.plan_model = EmailProcessingPlan
        self.replan_model = EmailProcessingReplanResult

    def get_plan_template(self) -> ChatPromptTemplate:
        from app.langchain.prompts.mail_prompts import EMAIL_PROCESSING_PLANNER

        return ChatPromptTemplate.from_messages(
            [
                ("system", EMAIL_PROCESSING_PLANNER),
                ("placeholder", "{messages}"),
            ]
        )

    def get_replan_template(self) -> ChatPromptTemplate:
        from app.langchain.prompts.mail_prompts import EMAIL_PROCESSING_REPLANNER

        return ChatPromptTemplate.from_template(EMAIL_PROCESSING_REPLANNER)

    def get_plan_parser(self) -> PydanticOutputParser:
        return PydanticOutputParser(pydantic_object=self.plan_model)

    def get_replan_parser(self) -> PydanticOutputParser:
        return PydanticOutputParser(pydantic_object=self.replan_model)

    def format_execution_task(
        self, task: str, plan: List[str], original_input: str
    ) -> str:
        plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
        return f"""For the following email processing plan:
{plan_str}

You are tasked with executing step 1: {task}

Original email content: {original_input}"""


# Factory function for email processing (maintains backward compatibility)
@asynccontextmanager
async def build_mail_processing_graph():
    """
    Factory function to build email processing graph.
    Maintains backward compatibility with existing code.
    """
    # Create configuration
    config = PlanExecuteConfig(
        processing_name="Email Processing",
        plan_template="",  # Will be set by template provider
        replan_template="",  # Will be set by template provider
    )

    # Create template provider
    template_provider = EmailTemplateProvider()

    # Create processor
    processor = PlanExecuteProcessor(config=config, template_provider=template_provider)

    async with processor.build_graph() as graph:
        # Set the plan and replan templates
        yield graph
