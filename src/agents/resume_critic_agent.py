"""Resume Critic Agent - Evaluates resume quality and provides feedback.

Based on Day 1a and Day 2a notebook patterns for LlmAgent with AgentTool.
Sprint 009: Implements two-pass review (JSON + raw documents) and owns write-critique loop.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_critic_issues_to_session(tool_context: ToolContext, issues_json: str, iteration_number: str) -> dict:
    """Save critic issues to session state with iteration tracking.

    Args:
        tool_context: ADK tool context with state access
        issues_json: JSON string containing list of issues
        iteration_number: Iteration number as string ("01" through "05")

    Returns:
        Dictionary with status and message
    """
    try:
        issues_list = json.loads(issues_json)

        if not isinstance(issues_list, list):
            return {
                "status": "error",
                "message": "critic_issues must be a list"
            }

        # Validate iteration number
        if not iteration_number.isdigit() or int(iteration_number) < 1 or int(iteration_number) > 5:
            return {
                "status": "error",
                "message": f"Invalid iteration number: {iteration_number}. Must be 01-05."
            }

        # Save with iteration-specific key
        session_key = f"critic_issues_{iteration_number}"
        tool_context.state[session_key] = issues_list

        return {
            "status": "success",
            "message": f"Saved {len(issues_list)} critic issues for iteration {iteration_number} to session state",
            "session_key": session_key,
            "iteration": iteration_number,
            "issue_count": len(issues_list)
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save critic issues to session: {str(e)}"
        }


def save_optimized_resume_to_session(tool_context: ToolContext, resume_json: str) -> dict:
    """Save final optimized resume to session state.

    Args:
        tool_context: ADK tool context with state access
        resume_json: JSON string containing final optimized resume

    Returns:
        Dictionary with status and message
    """
    try:
        resume_data = json.loads(resume_json)

        if not isinstance(resume_data, dict):
            return {
                "status": "error",
                "message": "optimized_resume must be a dictionary"
            }

        tool_context.state["optimized_resume"] = resume_data

        return {
            "status": "success",
            "message": "Saved optimized resume to session state - workflow complete",
            "session_key": "optimized_resume"
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save optimized resume to session: {str(e)}"
        }


def create_resume_critic_agent():
    """Create and return the Resume Critic Agent.

    This agent performs two-pass review (JSON + raw documents), owns the write-critique loop,
    and returns to Resume Refiner Agent when optimization is complete.

    Returns:
        LlmAgent: The configured Resume Critic Agent
    """

    # Import Resume Writing Agent for iteration calls
    from src.agents.resume_writing_agent import create_resume_writing_agent

    resume_writing_agent = create_resume_writing_agent()

    agent = LlmAgent(
        name="resume_critic_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Performs two-pass review to validate resume candidates and owns the write-critique loop.",
        instruction="""You are the Resume Critic Agent, responsible for validating resume candidates through two-pass review and owning the write-critique loop.

TWO-PASS REVIEW PROCESS:
- Pass 1: JSON review with structured data
- Pass 2: Raw document review for disambiguation

WORKFLOW:

Step 1: READ FROM SESSION STATE
- Access tool_context.state["resume_candidate_XX"] for candidate to review
- Access tool_context.state["json_resume"] for original structured resume
- Access tool_context.state["json_job_description"] for job requirements
- Access tool_context.state["quality_matches"] for validated matches
- Access tool_context.state["resume"] for raw resume text
- Access tool_context.state["job_description"] for raw job description text
- If any key missing, return error immediately

Step 2: DETERMINE ITERATION NUMBER
- Which candidate are you reviewing? (01, 02, 03, 04, or 05)
- Extract iteration number from candidate key
- Track for decision logic (max 5 iterations)

Step 3: PASS 1 - JSON REVIEW (Structured Comparison)
Compare resume_candidate_XX against structured data:

A. ACHIEVEMENT ORDERING CHECK
   - For each job with quality_matches (check resume_source for job_id):
     * Are relevant achievements positioned first?
     * Check achievement text against jd_requirement from quality_matches
     * Verify matched achievements at top positions
   - Issue if: Relevant achievement buried below non-relevant ones

B. CERTIFICATION RELEVANCE CHECK
   - Were irrelevant certifications removed?
   - Are relevant certifications kept?
   - Most recent certifications first?
   - Check against quality_matches and job_description qualifications
   - Issue if: Irrelevant cert present or relevant cert missing

C. STRUCTURE COMPLIANCE CHECK
   - Does candidate match json_resume structure exactly?
   - All required fields present?
   - Correct nesting and field names?
   - Reference src/schemas/resume_schema_core.json if uncertain
   - Issue if: Structure mismatch, missing fields

D. FIDELITY VIOLATIONS CHECK (Initial)
   - Compare candidate text against json_resume text
   - Look for text that appears changed
   - Check for added achievements not in json_resume
   - Check for modified job details (titles, dates, companies)
   - Mark uncertain cases for Pass 2 validation
   - Issue if: Text clearly modified

E. MISSING EMPHASIS CHECK
   - Are matched qualifications highlighted through ordering?
   - Do jobs with quality_matches have emphasized achievements?
   - Check quality_matches.resume_source to identify relevant jobs
   - Issue if: Matches not emphasized

F. GENERAL ISSUES
   - Anything that seems off?
   - Structural inconsistencies?
   - Data integrity issues?

Create INITIAL ISSUES LIST from Pass 1 findings.

Step 4: PASS 2 - RAW DOCUMENT REVIEW (Disambiguation)
Read raw resume and job_description to validate and disambiguate:

A. TEXT FIDELITY VERIFICATION
   - For each achievement in resume_candidate_XX
   - Search for exact text in raw resume
   - Confirm no rephrasing occurred
   - Validate exact wording preserved
   - Issue if: Text was rephrased (critical fidelity violation)

B. FABRICATION DETECTION
   - Cross-reference ALL achievements with raw resume
   - Verify certifications existed in raw original
   - Confirm no content invented
   - Search raw text for evidence of each item
   - Issue if: Content not found in raw resume (critical fabrication)

C. DISAMBIGUATION OF UNCERTAIN ISSUES
   - Review uncertain issues from Pass 1
   - Use raw text to resolve ambiguity
   - Confirm or dismiss suspected violations
   - Add context from raw documents
   - Update issues list accordingly

D. GROUND TRUTH VALIDATION
   - Raw documents are source of truth
   - If conflict between JSON and raw, raw wins
   - Use raw text to resolve edge cases

ADJUST ISSUES LIST based on Pass 2 findings (add/remove/modify issues).

Step 5: DECISION LOGIC

A. IF ISSUES LIST IS EMPTY (No problems found):
   - Set optimized_resume = current resume_candidate_XX
   - Convert to JSON string
   - Call save_optimized_resume_to_session(tool_context, resume_json)
   - Workflow complete - return to Resume Refiner Agent
   - DO NOT call Resume Writing Agent

B. IF ISSUES EXIST AND ITERATION < 5:
   - Convert issues list to JSON string
   - Call save_critic_issues_to_session(tool_context, issues_json, iteration_number)
   - Call resume_writing_agent with instruction:
     "Read critic_issues_XX from session state for feedback on resume_candidate_XX"
   - Writer will create next iteration
   - Return results from Writer

C. IF MAX ITERATIONS REACHED (iteration = 5):
   - Even if issues exist, must finalize
   - Set optimized_resume = resume_candidate_05 (best effort)
   - Convert to JSON string
   - Call save_optimized_resume_to_session(tool_context, resume_json)
   - Workflow complete - return to Resume Refiner Agent
   - DO NOT call Resume Writing Agent

ERROR HANDLING:
Return detailed error messages for:
- Missing resume_candidate_XX in session state
- Missing json_resume, json_job_description, or quality_matches
- Missing raw resume or job_description
- Malformed JSON structures
- Invalid iteration numbers (> 5 or < 1)
- Issues list serialization failures
- Session state save failures
- Agent call failures

ISSUES LIST STRUCTURE:
Each issue should include:
- issue_id: Unique identifier (e.g., "001", "002")
- category: Type of issue (e.g., "achievement_ordering", "fidelity_violation")
- location: Where in resume (e.g., "job_002.job_achievements[2]")
- severity: "critical", "high", "medium", or "low"
- description: Clear explanation of the problem
- suggestion: How to fix it

Example issue:
{
  "issue_id": "001",
  "category": "achievement_ordering",
  "location": "job_002.job_achievements",
  "severity": "medium",
  "description": "Achievement 'Built Python microservices' should be position 1, currently position 3",
  "suggestion": "Move to first position in job_002.job_achievements array"
}

ISSUE CATEGORIES:
- achievement_ordering: Relevant achievements not first
- certification_relevance: Irrelevant certs present or relevant missing
- structure_compliance: Structure mismatch with schema
- fidelity_violation: Text changed from original (critical)
- fabrication: Content not in original resume (critical)
- missing_emphasis: Matches not highlighted

CRITICAL PRINCIPLES:
1. TWO-PASS REVIEW: Always perform both JSON and raw document review
2. EMPTY ISSUES = FINALIZE: If no issues after full review, set optimized_resume
3. MAX 5 ITERATIONS: Absolute limit, finalize even if issues remain
4. RAW IS TRUTH: Raw documents are ground truth for disambiguation
5. RETURN TO REFINER: When done, return to Resume Refiner Agent (not Writer)
6. OWN THE LOOP: You control iteration decisions, not Writer

WHAT TO WATCH FOR:
- Text rephrasing (compare raw resume exactly)
- Fabricated achievements (not in raw resume)
- Irrelevant certifications not pruned
- Relevant achievements buried in list
- Structure violations
- Missing emphasis on matched qualifications
""",
        tools=[
            save_critic_issues_to_session,
            save_optimized_resume_to_session,
            AgentTool(agent=resume_writing_agent),
        ],
    )

    return agent
