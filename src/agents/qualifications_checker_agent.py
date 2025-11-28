"""Qualifications Checker Agent - Verifies and coordinates qualification matches.

Based on Day 1a and Day 2a notebook patterns for LlmAgent with AgentTool.
"""

import json
from typing import List, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_quality_matches_to_session(tool_context: ToolContext, quality_matches: List[Dict[str, Any]]) -> dict:
    """Save quality matches to session state.

    Args:
        tool_context: ADK tool context with state access
        quality_matches: List containing quality match objects

    Returns:
        Dictionary with status and message
    """
    try:
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

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save quality matches to session: {str(e)}"
        }


def save_possible_matches_to_session(tool_context: ToolContext, possible_quality_matches: List[Dict[str, Any]]) -> dict:
    """Save possible quality matches to session state (for internal processing).

    Args:
        tool_context: ADK tool context with state access
        possible_quality_matches: List containing possible match objects

    Returns:
        Dictionary with status and message
    """
    try:
        if not isinstance(possible_quality_matches, list):
            return {
                "status": "error",
                "message": "possible_quality_matches must be a list"
            }

        tool_context.state["possible_quality_matches"] = possible_quality_matches

        return {
            "status": "success",
            "message": f"Saved {len(possible_quality_matches)} possible matches to session state for validation",
            "match_count": len(possible_quality_matches)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save possible matches to session: {str(e)}"
        }


def create_qualifications_checker_agent():
    """Create and return the Qualifications Checker Agent.

    This agent validates preliminary matches from the Qualifications Matching Agent,
    verifies inferred matches with high threshold, and finalizes the quality_matches list
    in session state.

    Returns:
        LlmAgent: The configured Qualifications Checker Agent
    """

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
        description="Validates and finalizes qualification matches by verifying inferred matches with high threshold.",
        instruction="""You are the Qualifications Checker Agent, responsible for validating preliminary matches and finalizing the quality_matches list.

WORKFLOW:

Step 1: READ FROM SESSION STATE
- Read all data from session state:
  * resume_dict = state.get('resume_dict')
  * job_description_dict = state.get('job_description_dict')
  * quality_matches = state.get('quality_matches')
  * possible_quality_matches = state.get('possible_quality_matches')
- These are Python objects (dicts and lists) - access data directly (no parsing needed)
- If any required data is missing or empty:
  * Log the error
  * Return "ERROR: [qualifications_checker_agent] Missing required data in session state"
  * Stop processing

Step 2: VERIFY AND REFINE MATCHES
- You now have quality_matches and possible_quality_matches as Python lists
- CRITICAL: Iterate through every item in possible_quality_matches
- Apply a HIGH THRESHOLD of validation (virtual certainty required)
- If validated, move the match to the quality_matches list
- If not validated, discard the match entirely
- The final quality_matches list should be the union of the original quality matches and the verified possible matches

Step 3: SAVE QUALITY_MATCHES TO SESSION STATE
- Call save_quality_matches_to_session with quality_matches parameter only (pass the Python list directly, not JSON)
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [qualifications_checker_agent] <INSERT ERROR MESSAGE FROM TOOL>" to the parent agent, then STOP.

Step 4: SAVE POSSIBLE_QUALITY_MATCHES TO SESSION STATE
- The final, empty possible_quality_matches list (after verification and discarding) should be an empty Python list []
- Call save_possible_matches_to_session with possible_quality_matches parameter only (pass the empty Python list directly, not JSON)
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [qualifications_checker_agent] <INSERT ERROR MESSAGE FROM TOOL>" to the parent agent, then STOP.
- If the tool response is "success": DO NOT STOP. Immediately proceed to Step 5.

Step 5: RETURN SUCCESS MESSAGE - CRITICAL
After both save tools complete successfully, you MUST generate a final text response.
**DO NOT RETURN None** or empty content.
**DO NOT STOP** after the tool calls without generating this response.

MANDATORY FINAL RESPONSE FORMAT:
"SUCCESS: Validated and finalized qualification matches.

VALIDATION SUMMARY:
- Final quality matches: XX (verified with high confidence)
- Possible matches processed: XX validated, XX discarded
- Validation threshold: Virtual certainty required

Quality matches list finalized and saved to session state."

ERROR HANDLING:
This is a Worker Agent. Follow the ADK three-layer pattern:

Session State Validation:
- If quality_matches, possible_quality_matches, resume_dict, or job_description_dict is missing from session state:
  * Log error
  * Return "ERROR: [qualifications_checker_agent] Missing required data in session state"
  * Stop

When using tools (save functions):
- Check tool response for status: "error"
- If status is "error":
  * Log error
  * Return "ERROR: [qualifications_checker_agent] <INSERT ERROR MESSAGE FROM TOOL>"
  * Stop

For validation errors during processing:
- If malformed data structures: Log error, return "ERROR: [qualifications_checker_agent] Invalid data structure in input" to parent agent, and stop
- If verification logic fails: Log error, return "ERROR: [qualifications_checker_agent] Verification process failed" to parent agent, and stop

Log all errors before returning them to parent agent.

CRITICAL PRINCIPLES:
1. VERIFICATION WORKER: You receive preliminary matches, execute verification logic, save FINAL match lists
2. SEQUENTIAL EXECUTION: Complete all save operations before returning
3. RETURN SUCCESS MESSAGE: Your final output is a success message - DO NOT RETURN None
4. NO PREMATURE STOPPING: Do not return None after tool calls - continue to generate final response
5. YOU ARE A WORKER: You do NOT call other agents - parent orchestrator (Resume Refiner) calls the next agent
""",
        tools=[
            save_quality_matches_to_session,
            save_possible_matches_to_session,
        ],
    )

    return agent
