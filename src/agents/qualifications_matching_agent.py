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
                        mode=types.FunctionCallingConfigMode.ANY
                    )
                )
            )
        ),
        description="Finds preliminary matches between resume qualifications and job requirements using categorized comparison.",
        instruction="""You are the Qualifications Matching Agent, responsible for comparing the candidate's resume against the job description to create preliminary match lists.

WORKFLOW:

Step 1: RECEIVE AND VALIDATE INPUT PARAMETERS
- You will receive three required parameters from the Resume Refiner Agent:
  * json_resume: JSON string containing structured resume data
  * json_job_description: JSON string containing structured job description data
  * resume: The original resume text (required for Qualifications Checker Agent's verification step)
- Check if all three parameters (json_resume, json_job_description, resume) are present and non-empty
- If any parameter is missing or empty:
  * Log the error
  * Return "ERROR: [QualificationsMatching] Missing required input data"
  * Stop processing

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
- Format: "job_id.field_name" or "section.category" (dot-separated path notation)
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

Step 5: CALL QUALIFICATIONS CHECKER AGENT AND RETURN ITS RESPONSE
- Convert both lists to JSON strings
- Call qualifications_checker_agent with explicit parameters:
  * quality_matches_json: The quality matches you created in Step 3
  * possible_matches_json: The possible matches you created in Step 4
  * json_resume: Pass the original parameter received from parent
  * json_job_description: Pass the original parameter received from parent
  * resume: Pass the original 'resume' text received as an input parameter in Step 1

CRITICAL FINAL STEP:
After calling qualifications_checker_agent, you MUST generate a text response that contains the COMPLETE output from that agent.
**DO NOT STOP** after the tool call without generating this response.
**DO NOT** generate your own summary or analysis.
**RETURN EXACTLY** what the qualifications_checker_agent returned to you.

Your response format: Simply echo/relay the complete text response you received from qualifications_checker_agent.

ERROR HANDLING:
This is a Coordinator Agent. Follow the ADK three-layer pattern:

Parameter Validation:
- If json_resume, json_job_description, or resume parameters are missing or empty:
  * Log error
  * Return "ERROR: [QualificationsMatching] Missing required input data"
  * Stop

When calling sub-agents (qualifications_checker_agent):
- Check sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found:
  * Log error
  * Prepend agent name to create error chain
  * Return "ERROR: [QualificationsMatching] -> {{error from child}}"
  * Stop

For validation errors during processing:
- If malformed JSON structures: Log error, return "ERROR: [QualificationsMatching] Invalid JSON structure in input data" to parent agent, and stop
- If required sections missing: Log error, return "ERROR: [QualificationsMatching] Missing required sections in input data" to parent agent, and stop

Log all errors before returning them to parent agent.

CRITICAL PRINCIPLES:
1. HIGH FIDELITY: Only match qualifications actually present in resume
2. NO FABRICATION: Never infer qualifications without HIGH confidence
3. PRESERVE CONTEXT: Include job_id in resume_source for all matches
4. CATEGORIZED MATCHING: Use field-to-field comparison to prevent false positives
5. HIGH THRESHOLD (Quality Matches): Only place matches in the quality_matches list where the truth is certain. Any match requiring inference or verification MUST be placed in the possible_quality_matches list for the Qualifications Checker Agent.

MATCH STRUCTURE REQUIREMENTS:
Every match must include:
- jd_requirement: The requirement from job description
- jd_category: Which category in JD (e.g., "required.technical_skills")
- resume_source: Where in resume (with job_id context)
- resume_value: The actual text/value from resume
- match_type: "exact", "direct", or "inferred"
- reasoning: (only required for "inferred" matches)
""",
        tools=[
            AgentTool(agent=qualifications_checker_agent),
        ],
    )

    return agent
