"""Resume Refiner Agent - Coordinates the resume optimization process.

Based on Day 2a and Day 5a notebook patterns for LlmAgent with AgentTool.
Coordinates sequential workflow and write-critique loop.
Implements session state pattern for data sharing between agents.
"""

import json
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_resume_to_session(tool_context: ToolContext, json_resume: str) -> dict:
    """Save resume JSON to session state.

    Args:
        tool_context: ADK tool context with state access
        json_resume: JSON string containing structured resume data

    Returns:
        Dictionary with status and message
    """
    try:
        resume_data = json.loads(json_resume)
        tool_context.state['json_resume'] = json_resume
        return {
            "status": "success",
            "message": "Resume JSON saved to session state"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid resume JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save resume to session: {str(e)}"
        }


def save_job_description_to_session(tool_context: ToolContext, json_job_description: str) -> dict:
    """Save job description JSON to session state.

    Args:
        tool_context: ADK tool context with state access
        json_job_description: JSON string containing structured job description data

    Returns:
        Dictionary with status and message
    """
    try:
        jd_data = json.loads(json_job_description)
        tool_context.state['json_job_description'] = json_job_description
        return {
            "status": "success",
            "message": "Job Description JSON saved to session state"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid job description JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save job description to session: {str(e)}"
        }


def create_resume_refiner_agent():
    """Create and return the Resume Refiner Agent.

    This agent coordinates the resume optimization process through
    sequential workflow: Matching -> Resume Writing -> Resume Critic loop.

    Returns:
        LlmAgent: The configured Resume Refiner Agent
    """

    # Import Matching Agent (only agent this orchestrator directly calls)
    from src.agents.qualifications_matching_agent import create_qualifications_matching_agent

    qualifications_matching_agent = create_qualifications_matching_agent()

    agent = LlmAgent(
        name="resume_refiner_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY,
            generate_content_config=types.GenerateContentConfig(
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.AUTO
                    )
                )
            )
        ),
        description="Lightweight orchestrator that initiates the resume optimization workflow by delegating to the qualifications matching process.",
        instruction="""You are the Resume Refiner Agent, a lightweight second-tier orchestrator responsible for initiating the resume optimization workflow.

ROLE:
Your sole purpose is to save documents to session state and start the resume optimization process by delegating to the Qualifications Matching Agent.

WORKFLOW:

Step 0: RECEIVE AND VALIDATE INPUT PARAMETERS
- You will receive four required parameters from the Job Application Agent:
  * json_resume: JSON string containing structured resume data
  * json_job_description: JSON string containing structured job description data
  * resume: The original resume text (raw document)
  * job_description: The original job description text (raw document)
- Check if all four parameters are present and non-empty
- If any parameter is missing or empty:
  * Log the error
  * Return "ERROR: [resume_refiner_agent] Missing required input JSON data"
  * Stop processing

Step 1: SAVE RESUME JSON TO SESSION STATE
- Call save_resume_to_session with json_resume parameter only
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [resume_refiner_agent] <INSERT ERROR MESSAGE FROM TOOL>" to parent agent, then STOP

Step 2: SAVE JOB DESCRIPTION JSON TO SESSION STATE
- Call save_job_description_to_session with json_job_description parameter only
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [resume_refiner_agent] <INSERT ERROR MESSAGE FROM TOOL>" to parent agent, then STOP

Step 3: DELEGATE TO QUALIFICATIONS MATCHING AGENT
- Call qualifications_matching_agent with a SIMPLE request parameter:
  "Please compare the resume against the job description and identify qualification matches"
- DO NOT pass JSON data as parameters - it is already in session state
- The Qualifications Matching Agent will read from session state
- The Qualifications Matching Agent will then pass the torch to the Resume Writing Agent
- The Resume Writing Agent will notify the Resume Critic Agent
- The Resume Critic Agent owns the write-critique loop and will iterate until quality is achieved

Step 4: CHECK FOR ERRORS AND CHAIN THEM
- Check the response from qualifications_matching_agent for the keyword "ERROR:"
- If "ERROR:" is present:
  * Log the error
  * Prepend agent name to create error chain
  * Return "ERROR: [resume_refiner_agent] -> <INSERT ERROR MESSAGE FROM CHILD>"
  * Stop

Step 5: RETURN FINAL OPTIMIZED RESUME

CRITICAL FINAL RESPONSE:
After qualifications_matching_agent completes, you MUST generate a final text response.
**DO NOT RETURN None** or empty content - this will break the workflow.
**DO NOT STOP** after the matching agent call without generating this response.

Your final response MUST contain the EXACT, COMPLETE text returned by `qualifications_matching_agent`.
Simply echo/relay the matching agent's response - do not summarize or modify it.

If `qualifications_matching_agent` returns None or empty content, immediately report:
"ERROR: [resume_refiner_agent] -> Qualifications Matching Agent returned no content"

After the workflow completes successfully, return the final optimized resume (markdown string) to the Job Application Agent.
The optimized resume will have been created through the write-critique loop managed by the qualifications checker, writing, and critic agents.

ERROR HANDLING:
This is a Coordinator Agent. Follow the ADK three-layer pattern:

Parameter Validation:
- If json_resume, or json_job_description, or resume, or job_description parameters are missing or empty:
  * Log error
  * Return "ERROR: [resume_refiner_agent] Missing required input JSON data"
  * Stop

When using tools (save functions):
- Check tool response for status: "error"
- If status is "error":
  * Log error
  * Return "ERROR: [resume_refiner_agent] <INSERT ERROR MESSAGE FROM TOOL>"
  * Stop

When calling sub-agents (qualifications_matching_agent):
- Check sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found:
  * Log error
  * Prepend agent name to create error chain
  * Return "ERROR: [resume_refiner_agent] -> <INSERT ERROR MESSAGE FROM CHILD>"
  * Stop

Log all errors before returning them to parent agent.

CRITICAL PRINCIPLES:
- SESSION STATE: Save JSON documents to session state for downstream agents to access
- SIMPLE DELEGATION: Call matching agent with simple request, not complex parameters
- ERROR CHAINING: Prepend agent name to errors for debug traceability
- LIGHTWEIGHT DESIGN: Use tools for state management, delegation for workflow
- TRUST THE CHAIN: Let downstream agents handle their own complexity

IMPORTANT:
- You do NOT manage the write-critique loop (that is the Resume Critic Agent's responsibility)
- You do NOT directly call Resume Writing or Resume Critic agents (torch-passing handles the sequential flow)
- You save JSON to session state, then delegate with simple requests
- You simply validate inputs, save to state, delegate, chain errors, and return results
""",
        tools=[
            save_resume_to_session,
            save_job_description_to_session,
            AgentTool(agent=qualifications_matching_agent),
        ],
        sub_agents=[
            qualifications_matching_agent,
        ],
    )

    return agent
