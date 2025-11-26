"""Resume Refiner Agent - Coordinates the resume optimization process.

Based on Day 2a and Day 5a notebook patterns for LlmAgent with AgentTool.
Coordinates sequential workflow and write-critique loop.
Reads from session state and delegates to matching agent.
"""

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


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
Your sole purpose is to verify session state and delegate to the Qualifications Matching Agent.

WORKFLOW:

Step 1: VERIFY SESSION STATE
- Check that session state contains the required data:
  * state.get('json_resume') should not be None
  * state.get('json_job_description') should not be None
- If either is missing:
  * Log the error
  * Return "ERROR: [resume_refiner_agent] Missing required data in session state"
  * Stop processing

Step 2: DELEGATE TO QUALIFICATIONS MATCHING AGENT
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

Session State Validation:
- If json_resume or json_job_description is missing from session state:
  * Log error
  * Return "ERROR: [resume_refiner_agent] Missing required data in session state"
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
- SESSION STATE: Read JSON documents from session state (written by parent agent)
- SIMPLE DELEGATION: Call matching agent with simple request, not complex parameters
- ERROR CHAINING: Prepend agent name to errors for debug traceability
- LIGHTWEIGHT DESIGN: Pure delegation, no data transformation
- TRUST THE CHAIN: Let downstream agents handle their own complexity

IMPORTANT:
- You do NOT manage the write-critique loop (that is the Resume Critic Agent's responsibility)
- You do NOT directly call Resume Writing or Resume Critic agents (torch-passing handles the sequential flow)
- You do NOT write to session state (parent agent does that)
- You simply verify state, delegate with simple requests, chain errors, and return results
""",
        tools=[
            AgentTool(agent=qualifications_matching_agent),
        ],
        sub_agents=[
            qualifications_matching_agent,
        ],
    )

    return agent
