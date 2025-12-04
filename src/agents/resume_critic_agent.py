"""Resume Critic Agent - Evaluates resume quality and provides feedback.

Based on Day 1a and Day 2a notebook patterns for LlmAgent with AgentTool.
"""

from typing import List, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY

from src.tools.session_tools import read_from_session


def save_critic_issues_to_session(tool_context: ToolContext, critic_issues: List[Dict[str, Any]], iteration_number: str) -> dict:
    """Save critic issues to session state with iteration tracking.

    Args:
        tool_context: ADK tool context with state access
        critic_issues: Python list containing issue dictionaries
        iteration_number: Iteration number as string ("01" through "05")

    Returns:
        Dictionary with status and message
    """
    try:
        if not isinstance(critic_issues, list):
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
        tool_context.state[session_key] = critic_issues

        return {
            "status": "success",
            "message": f"Saved {len(critic_issues)} critic issues for iteration {iteration_number} to session state",
            "session_key": session_key,
            "iteration": iteration_number,
            "issue_count": len(critic_issues)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save critic issues to session: {str(e)}"
        }


def save_optimized_resume_to_session(tool_context: ToolContext, optimized_resume: dict) -> dict:
    """Save final optimized resume to session state.

    Args:
        tool_context: ADK tool context with state access
        optimized_resume: Python dict containing final optimized resume

    Returns:
        Dictionary with status and message
    """
    try:
        if not isinstance(optimized_resume, dict):
            return {
                "status": "error",
                "message": "optimized_resume must be a dictionary"
            }

        tool_context.state["optimized_resume"] = optimized_resume

        return {
            "status": "success",
            "message": "Saved optimized resume to session state - workflow complete",
            "session_key": "optimized_resume"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save optimized resume to session: {str(e)}"
        }


def create_resume_critic_agent():
    """Create and return the Resume Critic Agent.

    This agent performs two-pass review (JSON + original documents) and reports
    findings to the Resume Refiner Agent which orchestrates the write-critique loop.

    Returns:
        LlmAgent: The configured Resume Critic Agent
    """

    agent = LlmAgent(
        name="resume_critic_agent",
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
        description="Performs two-pass review to validate resume candidates and owns the write-critique loop.",
        instruction="""You are the Resume Critic Agent, responsible for validating resume candidates through two-pass review and owning the write-critique loop.

TWO-PASS REVIEW PROCESS:
- Pass 1: JSON review with structured data
- Pass 2: document review for disambiguation

WORKFLOW:

Step 1: READ FROM SESSION STATE
- Call read_from_session with key="resume_dict" and extract from "value" field (Python dict containing original resume structure)
- Call read_from_session with key="job_description_dict" and extract from "value" field (Python dict containing job requirements)
- Call read_from_session with key="quality_matches" and extract from "value" field (Python list containing validated matches with job_id context)
- Check each response: if "found" is false for any required key, return "ERROR: [resume_writing_agent] Missing required data in session state" and stop
- These are Python objects - access data directly (no parsing needed)
- Determine current iteration by checking which critic_issues_XX keys exist (if critic_issues_02 exists, we're reviewing candidate_03)
- Read the current resume_candidate_XX from session state based on iteration
- Check if all data is present and non-empty
- If any is missing or empty:
  * Log the error
  * Return "ERROR: [resume_critic_agent] Missing required data in session state"
  * Stop processing

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
   - Does candidate match resume_dict structure exactly?
   - All required fields present?
   - Correct nesting and field names?
   - Reference src/schemas/resume_schema_core.json if uncertain
   - Issue if: Structure mismatch, missing fields

D. FIDELITY VIOLATIONS CHECK (Initial)
   - Compare candidate text against resume_dict text
   - Look for text that appears changed
   - Check for added achievements not in resume_dict
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

Step 4: PASS 2 - ORIGINAL DOCUMENT REVIEW (Disambiguation)
Read resume and job_description to validate and disambiguate:

A. TEXT FIDELITY VERIFICATION
   - For each achievement in resume_candidate_XX
   - Search for exact text in resume
   - Confirm no rephrasing occurred
   - Validate exact wording preserved
   - Issue if: Text was rephrased (critical fidelity violation)

B. FABRICATION DETECTION
   - Cross-reference ALL achievements with resume
   - Verify certifications existed in original
   - Confirm no content invented
   - Search text for evidence of each item
   - Issue if: Content not found in resume (critical fabrication)

C. DISAMBIGUATION OF UNCERTAIN ISSUES
   - Review uncertain issues from Pass 1
   - Use text to resolve ambiguity
   - Confirm or dismiss suspected violations
   - Add context from documents
   - Update issues list accordingly

D. GROUND TRUTH VALIDATION
   - Original documents are source of truth
   - If conflict between JSON and raw text, text wins
   - Use text to resolve edge cases

ADJUST ISSUES LIST based on Pass 2 findings (add/remove/modify issues).

Step 5: SAVE RESULTS AND RETURN - DECISION LOGIC

A. IF ISSUES LIST IS EMPTY (No problems found):
   - Set optimized_resume = current resume_candidate_XX (Python dict)
   - Call save_optimized_resume_to_session with optimized_resume parameter only
   - Note: ADK framework automatically provides tool_context - do not pass it explicitly
   - Check tool response for status: "error"
   - If status is "error": Log error, return "ERROR: [resume_critic_agent] <INSERT ERROR MESSAGE FROM TOOL>", and stop
   - If status is "success": Continue to generate final response
   - CRITICAL: Include "ESCALATE" keyword in your final response to signal loop completion

B. IF ISSUES EXIST (iteration < 5):
   - Call save_critic_issues_to_session with critic_issues (Python list) and iteration_number parameters only
   - Note: ADK framework automatically provides tool_context - do not pass it explicitly
   - Check the tool response for status: "error"
   - If status is "error": Log error, return "ERROR: [resume_critic_agent] <INSERT ERROR MESSAGE FROM TOOL>", and stop
   - If status is "success": Continue to generate final response

C. IF MAX ITERATIONS REACHED (iteration = 5):
   - Even if issues exist, must finalize
   - Set optimized_resume = resume_candidate_05 (Python dict, best effort)
   - Call save_optimized_resume_to_session with optimized_resume parameter only
   - Note: ADK framework automatically provides tool_context - do not pass it explicitly
   - Check tool response for status: "error"
   - If status is "error": Log error, return "ERROR: [resume_critic_agent] <INSERT ERROR MESSAGE FROM TOOL>", and stop
   - If status is "success": Continue to generate final response
   - CRITICAL: Include "ESCALATE" keyword in your final response to signal loop completion

Step 6: RETURN APPROPRIATE MESSAGE - CRITICAL
After save tools complete successfully, you MUST generate a final text response.
**DO NOT RETURN None** or empty content.
**DO NOT STOP** after the tool calls without generating this response.

MANDATORY FINAL RESPONSE FORMATS:

If NO ISSUES (saved optimized_resume):
"ESCALATE: Resume candidate iteration XX approved with no issues.

REVIEW SUMMARY:
- Two-pass review completed (JSON + documents)
- Issues found: 0
- Optimized resume finalized and saved to session state

Resume optimization complete."

If ISSUES FOUND (saved critic_issues_XX):
"SUCCESS: Resume candidate iteration XX reviewed - issues identified.

REVIEW SUMMARY:
- Two-pass review completed (JSON + documents)
- Issues found: XX
- Issue categories: [list categories]
- Critic issues saved to session state as critic_issues_XX

Resume candidate needs revision - iteration [XX+1] required."

If MAX ITERATIONS (saved optimized_resume despite issues):
"ESCALATE: Maximum iterations reached - finalizing resume candidate 05.

REVIEW SUMMARY:
- Two-pass review completed (JSON + documents)
- Issues found: XX (below threshold for rejection)
- Maximum 5 iterations reached - accepting best effort
- Optimized resume finalized and saved to session state

Resume optimization complete (max iterations)."

ERROR HANDLING:
This is a Worker Agent. Follow the ADK three-layer pattern:

Session State Validation:
If resume_dict, job_description_dict, quality_matches, or current resume_candidate_XX is missing from session state:
  * Log error
  * Return "ERROR: [resume_critic_agent] Missing required data in session state"
  * Stop

When using tools (save functions):
- Check tool response for status: "error"
- If status is "error":
  * Log error
  * Return "ERROR: [resume_critic_agent] <INSERT ERROR MESSAGE FROM TOOL>"
  * Stop

For validation errors during processing:
- If malformed data structures: Log error, return "ERROR: [resume_critic_agent] Invalid data structure in input" to parent agent, and stop
- If invalid iteration numbers (> 5 or < 1): Log error, return "ERROR: [resume_critic_agent] Invalid iteration number (must be 1-5)" to parent agent, and stop
- If issues list serialization fails: Log error, return "ERROR: [resume_critic_agent] Failed to serialize critic issues" to parent agent, and stop

Log all errors before returning them to parent agent.

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
1. TWO-PASS REVIEW: Always perform both JSON and document review
2. EMPTY ISSUES = FINALIZE: If no issues after full review, set optimized_resume
3. MAX 5 ITERATIONS: Absolute limit, finalize even if issues remain at iteration 5
4. ORIGINAL DOCUMENTS ARE TRUTH: The original documents are ground truth for disambiguation
5. YOU ARE A WORKER: You do NOT call other agents - the parent LoopAgent controls the loop
6. SAVE AND REPORT: Save your findings to session state and return appropriate message
7. ESCALATE TO EXIT LOOP: When you approve a resume (save optimized_resume), include "ESCALATE" keyword in your response to signal the LoopAgent to exit early

WHAT TO WATCH FOR:
- Text rephrasing (compare resume exactly)
- Fabricated achievements (not in resume)
- Irrelevant certifications not pruned
- Relevant achievements buried in list
- Structure violations
- Missing emphasis on matched qualifications
""",
        tools=[
            save_critic_issues_to_session,
            save_optimized_resume_to_session,
        ],
    )

    return agent
