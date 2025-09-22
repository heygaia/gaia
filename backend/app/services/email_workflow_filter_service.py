"""
Email workflow filtering using LLM to decide whether emails should trigger workflows.
Simple function-based approach for intelligent email filtering.
"""

from typing import Dict, List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from app.config.loggers import general_logger as logger
from app.langchain.llm.client import init_llm
from app.langchain.prompts.email_filter_prompts import EMAIL_WORKFLOW_FILTER_PROMPT
from app.models.mail_models import EmailWorkflowFilterDecision
from app.models.workflow_models import Workflow


async def should_process_email_for_workflow(
    email_data: dict, workflow: Workflow, user_id: str
) -> EmailWorkflowFilterDecision:
    """
    Use LLM to decide if an email should trigger a specific workflow.

    Args:
        email_data: Email data from webhook
        workflow: Workflow to potentially trigger
        user_id: User ID for context

    Returns:
        EmailWorkflowFilterDecision with boolean decision and reasoning
    """
    try:
        # Extract email information
        email_subject = email_data.get("subject", "No Subject")
        email_sender = email_data.get("sender", "Unknown Sender")
        email_text = email_data.get("message_text", "")

        # Format workflow steps for LLM context
        workflow_steps_text = ""
        for i, step in enumerate(workflow.steps, 1):
            workflow_steps_text += f"{i}. {step.title}\n"
            workflow_steps_text += f"   Description: {step.description}\n"
            workflow_steps_text += f"   Tool: {step.tool_name}\n"
            if hasattr(step, "tool_inputs") and step.tool_inputs:
                workflow_steps_text += f"   Inputs: {step.tool_inputs}\n"
            workflow_steps_text += "\n"

        print(f"{workflow_steps_text=}")
        # Initialize LLM and parser
        llm = init_llm(streaming=False)
        parser = PydanticOutputParser(pydantic_object=EmailWorkflowFilterDecision)

        # Create prompt template
        prompt = PromptTemplate(
            template=EMAIL_WORKFLOW_FILTER_PROMPT,
            input_variables=[
                "email_sender",
                "email_subject",
                "email_preview",
                "workflow_title",
                "workflow_description",
                "workflow_steps_count",
                "workflow_steps",
            ],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # Create chain
        chain = prompt | llm | parser

        # Get LLM decision
        decision = await chain.ainvoke(
            {
                "email_sender": email_sender,
                "email_subject": email_subject,
                "email_preview": email_text,
                "workflow_title": workflow.title,
                "workflow_description": workflow.description,
                "workflow_steps_count": len(workflow.steps),
                "workflow_steps": workflow_steps_text.strip(),
            }
        )

        logger.info(
            f"Email filter decision for workflow {workflow.id} ({workflow.title}): "
            f"should_process={decision.should_process}, "
            f"confidence={decision.confidence}, "
            f"reason={decision.reasoning[:150]}..."
        )

        # Log workflow steps for debugging
        logger.debug(
            f"Workflow {workflow.id} steps considered: {len(workflow.steps)} steps - "
            f"{[step.title for step in workflow.steps]}"
        )

        return decision

    except Exception as e:
        logger.error(f"Error in email workflow filtering: {str(e)}")
        # Default to processing on error to avoid missing important emails
        return EmailWorkflowFilterDecision(
            should_process=True,
            reasoning=f"Error occurred during filtering, defaulting to process: {str(e)}",
            confidence=0.5,
        )


async def filter_workflows_for_email(
    email_data: dict, workflows: List[Workflow], user_id: str
) -> List[Dict]:
    """
    Filter multiple workflows for a single email.

    Args:
        email_data: Email data from webhook
        workflows: List of potential workflows to trigger
        user_id: User ID for context

    Returns:
        List of dicts with workflow and filter decision
    """
    filtered_results = []

    for workflow in workflows:
        try:
            decision = await should_process_email_for_workflow(
                email_data, workflow, user_id
            )

            filtered_results.append(
                {
                    "workflow": workflow,
                    "decision": decision,
                    "should_execute": decision.should_process,
                }
            )

        except Exception as e:
            logger.error(f"Error filtering workflow {workflow.id}: {str(e)}")
            # Default to include workflow on error
            filtered_results.append(
                {
                    "workflow": workflow,
                    "decision": EmailWorkflowFilterDecision(
                        should_process=True,
                        reasoning=f"Filtering error, defaulting to execute: {str(e)}",
                        confidence=0.5,
                    ),
                    "should_execute": True,
                }
            )

    # Log filtering summary
    total_workflows = len(workflows)
    workflows_to_execute = len([r for r in filtered_results if r["should_execute"]])

    logger.info(
        f"Email filtering complete: {workflows_to_execute}/{total_workflows} workflows will execute"
    )

    return filtered_results
