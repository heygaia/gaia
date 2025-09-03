"""Workflow generation service for LLM-based step creation."""

from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config.loggers import general_logger as logger
from app.langchain.llm.client import init_llm
from app.langchain.templates.workflow_template import WORKFLOW_GENERATION_TEMPLATE
from app.models.workflow_models import WorkflowStep


class WorkflowPlan(BaseModel):
    """Schema for complete workflow plan."""

    steps: List[WorkflowStep] = Field(description="List of workflow steps")


class WorkflowGenerationService:
    """Service for generating workflow steps using LLM."""

    @staticmethod
    async def generate_steps_with_llm(description: str, title: str) -> list:
        """Generate workflow steps using LLM with structured output."""
        try:
            # Create the parser
            parser = PydanticOutputParser(pydantic_object=WorkflowPlan)

            # Import here to avoid circular dependency at module level
            from app.langchain.tools.core.registry import (
                tool_registry,
            )

            # Create structured tool information with categories
            tools_with_categories = []
            for category in tool_registry.get_all_categories():
                category_tools = tool_registry.get_tools_by_category(category)
                tool_names = [
                    tool.name if hasattr(tool, "name") else str(tool)
                    for tool in category_tools
                ]
                tools_with_categories.append(f"{category}: {', '.join(tool_names)}")

            for tool in tool_registry.get_core_tools():
                tool_name = tool.name if hasattr(tool, "name") else str(tool)
                tools_with_categories.append(f"Always Available: {tool_name}")

            # Initialize LLM
            llm = init_llm(streaming=False)

            # Create chain using the template
            chain = WORKFLOW_GENERATION_TEMPLATE | llm | parser

            # Generate workflow plan
            result = await chain.ainvoke(
                {
                    "description": description,
                    "title": title,
                    "tools": "\n".join(tools_with_categories),
                    "categories": ", ".join(tool_registry.get_all_categories()),
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            # Convert to list of dictionaries for storage
            steps_data = []
            for i, step in enumerate(result.steps, 1):
                steps_data.append(step.model_dump())

            logger.info(f"Generated {len(steps_data)} workflow steps for: {title}")
            return steps_data

        except Exception as e:
            logger.error(f"Error in LLM workflow generation: {str(e)}")
            return []
