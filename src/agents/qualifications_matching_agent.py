"""Qualifications Matching Agent - Finds matches between resume and job description."""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def create_qualifications_matching_agent():
    """Create and return the Qualifications Matching Agent.

    This agent compares resume against job description using categorized qualifications
    and creates preliminary match lists. Delegates to Qualifications Checker Agent for verification and coordination.

    Returns:
        LlmAgent: The configured Qualifications Matching Agent
    """

    # Import Qualifications Checker Agent for delegation
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
        description="Finds preliminary matches between resume qualifications and job requirements using categorized comparison.",
        instruction="""You are the Qualifications Matching Agent.
Your Goal: Compare the candidate's resume against the job description to create preliminary match lists, then call the checker agent.

WORKFLOW:

1.  **ANALYZE & COMPARE**: Compare resume qualifications against job requirements.
    - Technical Skills: Match Job Description technical_skills with resume skills, job_technologies
    - Domain Knowledge: Match Job Description domain_knowledge with resume job_summary, job_achievements
    - Soft Skills: Match Job Description soft_skills with resume job_operated_as, job_achievements
    - Education: Match Job Description education with resume education
    - Experience: Compare Job Description experience_years with resume work history duration

2.  **CREATE MATCH OBJECTS** in two lists:
    
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

3.  **CALL CHECKER AGENT**:
    Call `qualifications_checker_agent` with:
    - `quality_matches_json`: JSON string of quality matches list
    - `possible_matches_json`: JSON string of possible matches list
    - `json_resume`: Original resume JSON
    - `json_job_description`: Original Job Description JSON
    - `resume`: Original resume text

4.  **RETURN RESPONSE** - CRITICAL:
    After calling the checker, you MUST generate a final text response.
    **DO NOT RETURN None** or empty content.
    **DO NOT STOP** after the tool call without generating this response.
    
    Your response MUST contain the EXACT, COMPLETE text returned by `qualifications_checker_agent`.
    Simply echo/relay the checker's response - do not summarize or modify it.

CRITICAL RULES:
- You MUST call the `qualifications_checker_agent` after creating lists
- You MUST return the checker's complete response - DO NOT RETURN None
- If checker returns None or error, immediately report it to parent
- Preserve job_id context in all match objects
""",
        tools=[
            AgentTool(agent=qualifications_checker_agent),
        ],
        sub_agents=[
            qualifications_checker_agent,
        ],
    )

    return agent
