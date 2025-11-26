"""Qualifications Checker Agent - Verifies and coordinates qualification matches.

Based on Day 1a and Day 2a notebook patterns for LlmAgent with AgentTool.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_quality_matches_to_session(tool_context: ToolContext, matches_json: str) -> dict:
    """Save quality matches to session state.

    Args:
        tool_context: ADK tool context with state access
        matches_json: JSON string containing list of quality matches

    Returns:
        Dictionary with status and message
    """
    try:
        quality_matches = json.loads(matches_json)

        if not isinstance(quality_matches, list):
            return {
                "status": "error",
                "message": "quality_matches must be a list"
            }

        tool_context.state["quality_matches"] = quality_matches

        return {
            "status": "success",
            "message": f"Saved {len(quality_matches)} quality matches to session state",
            "match_count": len(quality_matches)
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save quality matches to session: {str(e)}"
        }


def save_possible_matches_to_session(tool_context: ToolContext, matches_json: str) -> dict:
    """Save possible quality matches to session state (for internal processing).

    Args:
        tool_context: ADK tool context with state access
        matches_json: JSON string containing list of possible matches

    Returns:
        Dictionary with status and message
    """
    try:
        possible_matches = json.loads(matches_json)

        if not isinstance(possible_matches, list):
            return {
                "status": "error",
                "message": "possible_quality_matches must be a list"
            }

        tool_context.state["possible_quality_matches"] = possible_matches

        return {
            "status": "success",
            "message": f"Saved {len(possible_matches)} possible matches to session state for validation",
            "match_count": len(possible_matches)
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save possible matches to session: {str(e)}"
        }


def create_qualifications_checker_agent():
    """Create and return the Qualifications Checker Agent.

    This agent coordinates saving matches to session state and delegating to Resume Writing Agent.
    Pure coordinator - receives matches from Qualifications Matching Agent, saves them, passes to Resume Writing Agent.

    Returns:
        LlmAgent: The configured Qualifications Checker Agent
    """

    # Import Resume Writing Agent for delegation
    from src.agents.resume_writing_agent import create_resume_writing_agent
    from src.agents.resume_critic_agent import create_resume_critic_agent

    # Create both agents for write-critique loop
    resume_writing_agent = create_resume_writing_agent()
    resume_critic_agent = create_resume_critic_agent()

    # Wire them together to enable write-critique loop
    resume_writing_agent.tools.append(AgentTool(agent=resume_critic_agent))
    resume_critic_agent.tools.append(AgentTool(agent=resume_writing_agent))

    agent = LlmAgent(
        name="qualifications_checker_agent",
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
        description="Coordinates saving qualification matches and delegating to Resume Writing Agent.",
        instruction="""You are the Qualifications Checker Agent, responsible for coordinating the workflow from matching to resume writing.

WORKFLOW:

Step 1: RECEIVE AND VALIDATE INPUT PARAMETERS
- You will receive five required parameters from the Qualifications Matching Agent:
  * quality_matches_json: Preliminary quality matches list
  * possible_matches_json: Matches requiring verification
  * json_resume: Original resume structure (for context)
  * json_job_description: Job description (for context)
  * resume: Resume text (for verification)
- Check if all five parameters are present and non-empty
- If any parameter is missing or empty:
  * Log the error
  * Return "ERROR: [qualifications_checker_agent] Missing required input parameters"
  * Stop processing

Step 2: VERIFY AND REFINE MATCHES
- Parse possible_matches_json and quality_matches_json into lists
- CRITICAL: Iterate through every item in possible_quality_matches
- Apply a HIGH THRESHOLD of validation (virtual certainty required)
- If validated, move the match to the quality_matches list
- If not validated, discard the match entirely
- The final quality_matches list should be the union of the original quality matches and the verified possible matches

Step 3: SAVE QUALITY_MATCHES TO SESSION STATE
- Convert quality_matches list to JSON string
- Call save_quality_matches_to_session with matches_json parameter only
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [qualifications_checker_agent] <INSERT ERROR MESSAGE FROM TOOL>" to the parent agent, then STOP.

Step 4: SAVE POSSIBLE_QUALITY_MATCHES TO SESSION STATE
- Convert the final, empty possible_matches list (after verification and discarding) to the JSON string "[]"
- Call save_possible_matches_to_session with "[]" parameter only
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [qualifications_checker_agent] <INSERT ERROR MESSAGE FROM TOOL>" to the parent agent, then STOP.
- If the tool response is "success": DO NOT STOP. Immediately proceed to Step 5.

Step 5: CALL RESUME WRITING AGENT AND RETURN ITS RESPONSE
- Call resume_writing_agent with explicit parameters:
  * json_resume: Pass the original parameter received from parent
  * json_job_description: Pass the original parameter received from parent
  * resume: Pass the original 'resume' text received as an input parameter in Step 1
  * quality_matches: Pass the original parameter received from parent

CRITICAL FINAL STEP - MANDATORY TEXT RESPONSE:
After calling resume_writing_agent, you MUST generate a text response.
**DO NOT RETURN None** - this will break the workflow.
**DO NOT STOP** after the tool call without generating this response.

Your final response MUST contain the EXACT, COMPLETE text returned by `resume_writing_agent`.
Simply echo/relay the writing agent's response - do not summarize, modify, or add your own text.

If `resume_writing_agent` returns None or empty content, immediately report:
"ERROR: [qualifications_checker_agent] -> Resume Writing Agent returned no content"

ERROR HANDLING:
This is a Coordinator Agent. Follow the ADK three-layer pattern:

Parameter Validation:
- If quality_matches_json, possible_matches_json, json_resume, json_job_description, or resume parameters are missing or empty:
  * Log error
  * Return "ERROR: [qualifications_checker_agent] Missing required input parameters"
  * Stop

When using tools (save functions):
- Check tool response for status: "error"
- If status is "error":
  * Log error
  * Return "ERROR: [qualifications_checker_agent] <INSERT ERROR MESSAGE FROM TOOL>"
  * Stop

When calling sub-agents (resume_writing_agent):
- Check sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found:
  * Log error
  * Prepend agent name to create error chain
  * Return "ERROR: [qualifications_checker_agent] -> <INSERT ERROR FROM CHILD AGENT>"
  * Stop

For validation errors during processing:
- If malformed JSON structures: Log error, return "ERROR: [qualifications_checker_agent] Invalid JSON structure in input data" to parent agent, and stop
- If verification logic fails: Log error, return "ERROR: [qualifications_checker_agent] Verification process failed" to parent agent, and stop

Log all errors before returning them to parent agent.

CRITICAL PRINCIPLES:
1. VERIFICATION COORDINATION: You receive preliminary matches from Qualifications Matching Agent, execute the verification logic, save the FINAL match lists, and then delegate to the Resume Writing Agent.
2. SEQUENTIAL EXECUTION: Complete all save operations before calling resume_writing_agent
3. RETURN WRITING AGENT OUTPUT: Your final output is the resume_writing_agent's response - DO NOT RETURN None
4. NO PREMATURE STOPPING: Do not return None after tool calls - continue to next step
""",
        tools=[
            save_quality_matches_to_session,
            save_possible_matches_to_session,
            AgentTool(agent=resume_writing_agent),
        ],
        sub_agents=[
            resume_writing_agent,
        ],
    )

    return agent
