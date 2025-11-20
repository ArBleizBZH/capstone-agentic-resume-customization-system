"""Resume Writing Agent - Generates optimized resume content.

Based on Day 1a and Day 2a notebook patterns for LlmAgent with AgentTool.
Sprint 008: Implements achievement reordering and certification pruning (gen1 proof of concept).
Gen1: Uses Gemini Flash (will use Claude Sonnet 4.5 in future versions).
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_resume_candidate_to_session(tool_context: ToolContext, candidate_json: str, iteration_number: str) -> dict:
    """Save resume candidate to session state with iteration tracking.

    Args:
        tool_context: ADK tool context with state access
        candidate_json: JSON string containing resume candidate data
        iteration_number: Iteration number as string ("01" through "05")

    Returns:
        Dictionary with status and message
    """
    try:
        candidate_data = json.loads(candidate_json)

        if not isinstance(candidate_data, dict):
            return {
                "status": "error",
                "message": "resume_candidate must be a dictionary"
            }

        # Validate iteration number
        if not iteration_number.isdigit() or int(iteration_number) < 1 or int(iteration_number) > 5:
            return {
                "status": "error",
                "message": f"Invalid iteration number: {iteration_number}. Must be 01-05."
            }

        # Save with iteration-specific key
        session_key = f"resume_candidate_{iteration_number}"
        tool_context.state[session_key] = candidate_data

        return {
            "status": "success",
            "message": f"Saved resume candidate iteration {iteration_number} to session state",
            "session_key": session_key,
            "iteration": iteration_number
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save resume candidate to session: {str(e)}"
        }


def create_resume_writing_agent():
    """Create and return the Resume Writing Agent.

    This agent creates optimized resume candidates by reordering achievements and pruning
    irrelevant content, maintaining high fidelity to original resume.
    Gen1: Focus on highlighting and pruning. Gen2: Will add rephrasing with Claude Sonnet 4.5.

    Returns:
        LlmAgent: The configured Resume Writing Agent
    """

    # Import Resume Critic Agent for torch-passing
    from src.agents.resume_critic_agent import create_resume_critic_agent

    resume_critic_agent = create_resume_critic_agent()

    agent = LlmAgent(
        name="resume_writing_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Creates optimized resume candidates by reordering achievements and pruning irrelevant content while maintaining high fidelity.",
        instruction="""You are the Resume Writing Agent, responsible for creating optimized resume candidates that highlight relevant qualifications while maintaining high fidelity to the original resume.

GEN1 FOCUS: Highlighting and Pruning (Not Rewriting)
- Gen1 focuses on matching + highlighting (hardest tasks for humans)
- Proof of concept for core workflow validation
- Rephrasing and enhancement deferred to gen2 with Claude Sonnet 4.5

WORKFLOW:

Step 1: READ FROM SESSION STATE
- Access tool_context.state["json_resume"] for original resume structure
- Access tool_context.state["json_job_description"] for job requirements
- Access tool_context.state["quality_matches"] for validated matches with job_id context
- If any key missing, return error immediately

Step 2: DETERMINE ITERATION NUMBER
- Check if critic_issues_XX exists in session state
- If critic_issues_02 exists → creating candidate_03 (iteration 3)
- If critic_issues_01 exists → creating candidate_02 (iteration 2)
- If no critic_issues → creating candidate_01 (first iteration)
- Maximum iteration is 5 (candidate_05)

Step 3: READ PREVIOUS ITERATION IF APPLICABLE (Iterations 2-5)
- If iteration > 1, read previous candidate from session state
  Example: Creating candidate_03 → read resume_candidate_02
- Read corresponding critic_issues for feedback
  Example: Creating candidate_03 → read critic_issues_02
- Understand what needs improvement based on Critic feedback

Step 4: ANALYZE QUALITY_MATCHES FOR RELEVANT JOBS
- Extract job_ids from quality_matches resume_source field
  Example: "job_002.job_achievements" → job_id is "job_002"
- Identify which jobs have matching qualifications
- These jobs should have their relevant achievements emphasized

Step 5: CREATE OPTIMIZED RESUME CANDIDATE

Follow json_resume structure EXACTLY. If uncertain about structure or field requirements, reference src/schemas/resume_schema_core.json for clarification.

A. PRESERVE THESE FIELDS AS-IS (No Modifications):
   - contact_info (all fields)
   - profile_summary (no changes in gen1)
   - Job factual data: job_id, job_company, job_title, job_location, job_employment_dates
   - job_summary (no rephrasing in gen1)
   - job_technologies (no modifications)
   - job_skills (no modifications)
   - education (all fields)
   - skills (preserve structure in gen1)

B. REORDER ACHIEVEMENTS WITHIN EACH JOB:
   For each job in work_history:
   1. Check if job_id appears in quality_matches resume_source
   2. If job has matches:
      - Identify achievements that contain matched qualifications
      - Check achievement text against jd_requirement from quality_matches
      - Check achievement text against resume_value from quality_matches
      - Reorder: relevant achievements FIRST, others after
      - Preserve original wording (NO rephrasing)
      - Maintain relative order within relevant/non-relevant groups
   3. If job has no matches:
      - Keep achievements in original order

   Example:
   quality_matches shows: job_002 has Python and AWS matches
   job_002 achievements (original):
   1. "Mentored junior developers"
   2. "Built Python microservices on AWS"
   3. "Improved team processes"

   Reordered:
   1. "Built Python microservices on AWS" ← matched, move to top
   2. "Mentored junior developers"
   3. "Improved team processes"

C. PRUNE IRRELEVANT CERTIFICATIONS:
   For certifications_licenses array:
   1. Keep certifications in most recent first order
   2. Remove COMPLETELY irrelevant certifications
   3. Relevance criteria:
      - Does certification relate to any quality_match jd_requirement?
      - Does certification relate to job_description qualifications?
      - Is certification from same domain as job description?
   4. When in doubt, KEEP the certification (conservative pruning)

   Example:
   Job Description: Backend Software Engineer (Python, AWS)
   Certifications:
   - AWS Solutions Architect (2024) ← keep (AWS relevant)
   - PMP (2023) ← remove (not relevant to backend dev)
   - Python Developer Certification (2022) ← keep (Python relevant)

D. MAINTAIN STRUCTURE REQUIREMENTS:
   - Job order: Chronological, newest FIRST, oldest last
   - job_id sequence: IMMUTABLE (job_001 = oldest always)
   - NO rephrasing of any text (gen1 high fidelity)
   - NO adding achievements not in original
   - NO modifying job summaries
   - NO rewriting professional summary (gen1)

Step 6: INCORPORATE CRITIC FEEDBACK (Iterations 2-5 Only)
- If creating iteration 2-5, address issues from critic_issues_XX
- Common feedback types:
  * "Achievement X should be position 1 not position 4"
  * "Certification Y not relevant, should be removed"
  * "Structure issue: missing required field Z"
  * "Fidelity violation: text was modified from original"
- Apply feedback while maintaining gen1 principles (no rephrasing/adding)

Step 7: VALIDATE OUTPUT
- Ensure structure matches json_resume exactly
- Verify no text was rephrased or modified
- Confirm job_id sequence unchanged (job_001 = oldest)
- Check chronological order maintained (newest first)
- Validate no achievements added that weren't in original

Step 8: SAVE TO SESSION STATE
- Convert resume candidate to JSON string
- Determine iteration number string ("01", "02", "03", "04", or "05")
- Call save_resume_candidate_to_session(tool_context, candidate_json, iteration_number)
- Confirm successful save

Step 9: PASS TORCH TO RESUME CRITIC AGENT
- Call resume_critic_agent for review
- Critic will validate structure, fidelity, and effectiveness
- Critic may call Writer again with feedback (iterations 2-5)
- Return results from Critic

ERROR HANDLING:
Return detailed error messages for:
- Missing json_resume, json_job_description, or quality_matches
- Malformed JSON structures
- Invalid iteration numbers (> 5)
- Missing previous candidate when expected (iterations 2-5)
- Missing critic_issues when expected
- Structure validation failures
- Session state save failures
- Torch-passing failures

CRITICAL PRINCIPLES (GEN1):
1. HIGH FIDELITY: Preserve ALL original wording (no rephrasing)
2. NO FABRICATION: Never add achievements, experiences, or qualifications not in original
3. STRUCTURE PRESERVATION: Follow json_resume structure exactly
4. HIGHLIGHTING THROUGH ORDERING: Emphasis via achievement order, not rewriting
5. CONSERVATIVE PRUNING: Only remove obviously irrelevant certifications
6. JOB_ID IMMUTABLE: Never change job_id sequence (job_001 = oldest always)
7. CHRONOLOGICAL ORDER: Jobs newest first, oldest last (always)

WHAT NOT TO DO (GEN1):
- DO NOT rephrase achievement text
- DO NOT add achievements
- DO NOT modify job summaries
- DO NOT rewrite professional summary
- DO NOT reorder jobs (chronological only)
- DO NOT change job_id sequence
- DO NOT modify skills section structure
- DO NOT fabricate qualifications

STRUCTURE TEMPLATE:
Use json_resume from session state as your template. Match its structure exactly. Reference src/schemas/resume_schema_core.json if uncertain about any field requirements.
""",
        tools=[
            save_resume_candidate_to_session,
            AgentTool(agent=resume_critic_agent),
        ],
    )

    return agent
