"""Qualifications Matching Agent - Finds matches between resume and job description.

Implements session state pattern for data sharing between agents.
"""

from typing import List, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY
from src.tools.session_tools import read_from_session


def save_quality_matches_to_session(tool_context: ToolContext, quality_matches: List[Dict[str, Any]]) -> dict:
    """Save quality matches list to session state.

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
        tool_context.state['quality_matches'] = quality_matches
        return {
            "status": "success",
            "message": f"Saved {len(quality_matches)} quality matches to session state"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save quality matches to session: {str(e)}"
        }


def save_possible_matches_to_session(tool_context: ToolContext, possible_quality_matches: List[Dict[str, Any]]) -> dict:
    """Save possible quality matches list to session state.

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
        tool_context.state['possible_quality_matches'] = possible_quality_matches
        return {
            "status": "success",
            "message": f"Saved {len(possible_quality_matches)} possible matches to session state"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save possible matches to session: {str(e)}"
        }


def create_qualifications_matching_agent():
    """Create and return the Qualifications Matching Agent.

    This agent compares resume against job description using categorized qualifications
    and creates preliminary match lists, saving them to session state.

    Returns:
        LlmAgent: The configured Qualifications Matching Agent
    """    
    
    from src.agents.qualifications_checker_agent import create_qualifications_checker_agent
        
    qualifications_checker_agent = create_qualifications_checker_agent()

    agent = LlmAgent(
        name="qualifications_matching_agent",
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
        description="Finds preliminary matches between resume qualifications and job requirements using categorized comparison. Then have qualifications_checker_agent validate those lists.",
        instruction="""You are the Qualifications Matching Agent.
Your Goal: Read resume and job description from session state, create preliminary match lists, save them to session state, and have qualifications_checker_agent validate them.

WORKFLOW:

Step 1: READ FROM SESSION STATE
- Call read_from_session with key="resume_dict" to retrieve the structured resume
- Check the response: if "found" is false, return "ERROR: [qualifications_matching_agent] resume_dict not found in session state" and stop
- Extract resume_dict from the "value" field
- Call read_from_session with key="job_description_dict" to retrieve the structured job description
- Check the response: if "found" is false, return "ERROR: [qualifications_matching_agent] job_description_dict not found in session state" and stop
- Extract job_description_dict from the "value" field
- These are Python dictionaries - access data directly (no parsing needed)

Step 2: ANALYZE & CREATE MATCH LISTS
Compare resume qualifications against job requirements:
- Technical Skills: Match Job Description technical_skills with resume skills, job_technologies
- Domain Knowledge: Match Job Description domain_knowledge with resume job_summary, job_achievements
- Soft Skills: Match Job Description soft_skills with resume job_operated_as, job_achievements
- Education: Match Job Description education with resume education
- Experience: Compare Job Description experience_years with resume work history duration

Create two lists:

**quality_matches** (High confidence - exact or direct evidence):
- "exact": Identical match (e.g., "Python" in both Job Description and resume)
- "direct": Clear evidence (e.g., "Led team of 5" for "Team leadership")

**possible_matches** (Inferred - needs validation):
- "inferred": Reasonable inference (e.g., "Full-stack Web Developer" → HTML/CSS)
- Include reasoning field explaining the inference

Each match object MUST have:
```
{
  "jd_requirement": "Python",
  "jd_category": "required.technical_skills",
  "resume_source": "job_001.job_technologies",
  "resume_value": "Python",
  "match_type": "exact|direct|inferred",
  "reasoning": "Only for inferred matches"
}
```

**IMPORTANT**: Preserve job_id context in resume_source (e.g., "job_001.job_technologies")

Step 3: SAVE QUALITY MATCHES TO SESSION STATE
- Call save_quality_matches_to_session with quality_matches parameter only (pass the Python list directly)
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [qualifications_matching_agent] <INSERT ERROR MESSAGE FROM TOOL>" to parent agent, then STOP

Step 4: SAVE POSSIBLE MATCHES TO SESSION STATE
- Call save_possible_matches_to_session with possible_quality_matches parameter only (pass the Python list directly)
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [qualifications_matching_agent] <INSERT ERROR MESSAGE FROM TOOL>" to parent agent, then STOP
- If tool response indicates "success": Continue to Step 5


STEP 5: CALL QUALIFICATIONS CHECKER
- Call qualifications_checker_agent.
- WAIT for its response.
- The Checker agent will save the final 'quality_matches' to session state.
- Only proceed to Step 6 after you receive a SUCCESS response from the Checker.
- If the tool response indicates "error": Log the error and return "ERROR: [qualifications_checker_agent] <INSERT ERROR MESSAGE FROM TOOL>" to parent agent, then STOP
- If tool response indicates "success": Continue to Step 6

Step 6: RETURN SUCCESS MESSAGE - CRITICAL
After the qualifications_checker_agent complete successfully, you MUST generate a final text response.
**DO NOT RETURN None** or empty content.
**DO NOT STOP** after the tool calls without generating this response.

MANDATORY FINAL RESPONSE FORMAT:
"SUCCESS: Identified and saved qualification matches to session state.

MATCH SUMMARY:
- Quality matches: XX (Final list of validated matches)
- Possible matches: XX (Count of possible matches before validation)

The final quality match list has been saved to session state and is ready for the next step."

ERROR HANDLING:

When reading from session state:
- If resume_dict or job_description_dict is missing:
  * Log error
  * Return "ERROR: [qualifications_matching_agent] Missing resume or job description in session state"
  * Stop

When using tools (save functions):
- Check tool response for status: "error"
- If status is "error":
  * Log error
  * Return "ERROR: [qualifications_matching_agent] <INSERT ERROR MESSAGE FROM TOOL>"
  * Stop

Log all errors before returning them to parent agent.

CRITICAL RULES:
- Read resume/JD from session state - NOT from parameters
- Save match lists to session state - NOT pass as parameters
- Return success message after saving - DO NOT RETURN None
- Preserve job_id context in all match objects
""",
        tools=[
            read_from_session,
            AgentTool(agent=qualifications_checker_agent),
            save_quality_matches_to_session,
            save_possible_matches_to_session,
        ],
        sub_agents=[
            qualifications_checker_agent
        ],
    )

    return agent
