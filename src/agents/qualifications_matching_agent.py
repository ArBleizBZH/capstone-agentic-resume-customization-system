"""Qualifications Matching Agent - Finds matches between resume and job description.

Based on Day 1a and Day 2a notebook patterns for LlmAgent with AgentTool.
Sprint 007: Implements categorized matching with high-threshold validation.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
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


def create_qualifications_matching_agent():
    """Create and return the Qualifications Matching Agent.

    This agent compares resume against job description using categorized qualifications,
    validates inferred matches with high threshold, and passes torch to Resume Writing Agent.

    Returns:
        LlmAgent: The configured Qualifications Matching Agent
    """

    # Import Resume Writing Agent for torch-passing
    from src.agents.resume_writing_agent import create_resume_writing_agent

    resume_writing_agent = create_resume_writing_agent()

    agent = LlmAgent(
        name="qualifications_matching_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Finds and validates matches between resume qualifications and job requirements using categorized comparison.",
        instruction="""You are the Qualifications Matching Agent, responsible for comparing the candidate's resume against the job description to identify quality matches.

WORKFLOW:

Step 1: READ STRUCTURED DATA FROM SESSION STATE
- Access tool_context.state["json_resume"] for structured resume data
- Access tool_context.state["json_job_description"] for structured job description data
- If either key is missing or empty, return error immediately:
  "Error: Missing required data in session state. Both json_resume and json_job_description must be present."

Step 2: COMPARE CATEGORIZED QUALIFICATIONS
Compare using the categorized structure from Option B schema:

A. TECHNICAL SKILLS MATCHING
   - Compare JD required.technical_skills vs resume skills categories and job_technologies
   - Compare JD preferred.technical_skills vs resume skills and job_technologies
   - Examples of matches:
     * Exact: "Python" in JD, "Python" in resume → quality_match (exact)
     * Direct: "AWS" in JD, "AWS" in job_001.job_technologies → quality_match (exact)

B. DOMAIN KNOWLEDGE MATCHING
   - Compare JD required.domain_knowledge vs resume job_summary, job_achievements
   - Compare JD preferred.domain_knowledge vs resume experience descriptions
   - Examples of matches:
     * Direct: "Microservices architecture" in JD, "Designed microservices platform" in resume → quality_match (direct)
     * Direct: "RESTful API design" in JD, "Built RESTful APIs" in job_achievements → quality_match (direct)

C. SOFT SKILLS MATCHING
   - Compare JD required.soft_skills vs resume job_operated_as, job_achievements
   - Compare JD preferred.soft_skills vs resume experience
   - Examples of matches:
     * Direct: "Team leadership" in JD, "Tech Lead managing 5 developers" in job_operated_as → quality_match (direct)
     * Direct: "Communication" in JD, "Collaborated across teams" in achievements → quality_match (direct)

D. EDUCATION MATCHING
   - Compare JD required.education vs resume education section
   - Examples of matches:
     * Direct: "Bachelor's degree in Computer Science" in both → quality_match (exact)

E. EXPERIENCE YEARS MATCHING
   - Compare JD required.experience_years vs resume work history duration
   - Calculate total relevant experience from job_employment_dates
   - Examples of matches:
     * Direct: "5+ years" in JD, candidate has 7 years → quality_match (direct)

Step 3: CREATE QUALITY_MATCHES (HIGH CONFIDENCE)
For each certain match, create match object with this structure:
{
  "jd_requirement": "Python",
  "jd_category": "required.technical_skills",
  "resume_source": "job_001.job_technologies",
  "resume_value": "Python",
  "match_type": "exact"
}

Match types for quality_matches:
- "exact": Identical match (e.g., "Python" == "Python")
- "direct": Clear evidence (e.g., "Led team of 5" for "Team leadership")

Preserve job_id context in resume_source:
- Format: "{job_id}.{field_name}" or "{section}.{category}"
- Examples: "job_001.job_technologies", "job_003.job_operated_as", "skills.Programming & Scripting"

Step 4: CREATE POSSIBLE_QUALITY_MATCHES (INFERRED - NEEDS VALIDATION)
For matches requiring inference, create match object with:
{
  "jd_requirement": "HTML",
  "jd_category": "required.technical_skills",
  "resume_source": "job_002.job_title",
  "resume_value": "Full-stack Web Developer",
  "match_type": "inferred",
  "reasoning": "Full-stack web developers inherently work with HTML/CSS"
}

Examples of valid inferences:
- "Full-stack Web Developer" → HTML, CSS, JavaScript
- "DevOps Engineer" → CI/CD, Linux, Scripting
- "Data Scientist" → Python, Statistics, ML
- "Responsive web applications" → CSS knowledge

Examples that should NOT be inferred:
- "Software Engineer" → Python (could be any language)
- "Team member" → Leadership (participation ≠ leadership)
- "Worked with databases" → PostgreSQL (could be any DB)

Step 5: VALIDATE POSSIBLE_QUALITY_MATCHES WITH HIGH THRESHOLD
For each possible_quality_match, apply HIGH threshold validation:

VALIDATION CRITERIA:
- Inference must be virtually certain
- Industry-standard associations only
- No room for reasonable doubt
- When uncertain, DISCARD (false negative acceptable, false positive NOT acceptable)

For each possible match:
- If HIGH confidence (virtually certain) → Move to quality_matches with match_type="validated_inference"
- If uncertain → DISCARD (do not include anywhere)

After validation, possible_quality_matches should be EMPTY.

Step 6: SAVE QUALITY_MATCHES TO SESSION STATE
- Convert final quality_matches list to JSON string
- Call save_quality_matches_to_session(tool_context, quality_matches_json)
- Confirm successful save

Step 7: SAVE POSSIBLE_QUALITY_MATCHES TO SESSION STATE (SHOULD BE EMPTY)
- After validation, this should be an empty list []
- Call save_possible_matches_to_session(tool_context, "[]")
- This documents that validation completed

Step 8: PASS TORCH TO RESUME WRITING AGENT
- Call resume_writing_agent to begin resume optimization
- Writing Agent will use quality_matches to create optimized resume
- Return results from Writing Agent

ERROR HANDLING:
Return detailed error messages for:
- Missing json_resume or json_job_description in session state
- Malformed JSON structures
- Missing required sections (qualifications in JD, work_history in resume)
- Empty qualifications (no requirements to match against)
- Session state save failures
- Torch-passing failures

CRITICAL PRINCIPLES:
1. HIGH FIDELITY: Only match qualifications actually present in resume
2. NO FABRICATION: Never infer qualifications without HIGH confidence
3. PRESERVE CONTEXT: Include job_id in resume_source for all matches
4. CATEGORIZED MATCHING: Use field-to-field comparison to prevent false positives
5. HIGH THRESHOLD: Better to miss a match than fabricate a qualification
6. EMPTY POSSIBLE MATCHES: Validate everything before passing torch

MATCH STRUCTURE REQUIREMENTS:
Every match must include:
- jd_requirement: The requirement from job description
- jd_category: Which category in JD (e.g., "required.technical_skills")
- resume_source: Where in resume (with job_id context)
- resume_value: The actual text/value from resume
- match_type: "exact", "direct", or "validated_inference"
- reasoning: (only for validated_inference matches)
""",
        tools=[
            save_quality_matches_to_session,
            save_possible_matches_to_session,
            AgentTool(agent=resume_writing_agent),
        ],
    )

    return agent
