"""Resume Critic Agent - Evaluates resume quality and provides feedback.

Based on Day 1a and Day 2a notebook patterns for LlmAgent with AgentTool.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
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

    This agent performs two-pass review (JSON + original documents), owns the write-critique loop,
    and returns to Resume Refiner Agent when optimization is complete.

    NOTE: Resume Writing Agent will be added to tools after creation to avoid circular dependency.

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
- Read all required data from session state:
  * resume_dict = state.get('resume_dict')  - Original structured resume (for fidelity check)
  * job_description_dict = state.get('job_description_dict')  - Job description (for context)
  * quality_matches = state.get('quality_matches')  - Validated matches (for validation)
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
   - Original ocuments are source of truth
   - If conflict between JSON and raw, wins
   - Use text to resolve edge cases

ADJUST ISSUES LIST based on Pass 2 findings (add/remove/modify issues).

Step 5: DECISION LOGIC

A. IF ISSUES LIST IS EMPTY (No problems found):
   - Set optimized_resume = current resume_candidate_XX
   - Convert to JSON string
   - Call save_optimized_resume_to_session with resume_json parameter only
   - Note: ADK framework automatically provides tool_context - do not pass it explicitly
   - **CRITICAL**: After successful save, you MUST generate a final text response
   - **DO NOT RETURN None** - return the optimized resume markdown to parent
   - DO NOT call Resume Writing Agent

B. IF ISSUES EXIST AND ITERATION < 5:
   - Convert issues list to JSON string
   - Call save_critic_issues_to_session with issues_json and iteration_number parameters only
   - Note: ADK framework automatically provides tool_context - do not pass it explicitly
   - Check the tool response for status: "error"
   - If status is "error": Log error, return "ERROR: [resume_critic_agent] <INSERT ERROR MESSAGE FROM TOOL>", and stop
   - Call resume_writing_agent with a SIMPLE request parameter:
     "Please create the next resume candidate iteration based on the critic issues"
   - DO NOT pass data as parameters - it is already in session state
   - Resume Writing Agent will read from session state and create next iteration
   - Check the response for the keyword "ERROR:"
   - If "ERROR:" is present:
     * Log the error
     * Prepend agent name to create error chain
     - Return "ERROR: [resume_critic_agent] -> <INSERT ERROR MESSAGE FROM RESUME WRITING AGENT>"
     * Stop processing
   - **CRITICAL**: After writing agent completes, you MUST generate a final text response
   - **DO NOT RETURN None** - return the complete response from Resume Writing Agent
   - If Resume Writing Agent returns None, report: "ERROR: [resume_critic_agent] -> Resume Writing Agent returned no content"

C. IF MAX ITERATIONS REACHED (iteration = 5):
   - Even if issues exist, must finalize
   - Set optimized_resume = resume_candidate_05 (best effort)
   - Convert to JSON string
   - Call save_optimized_resume_to_session with resume_json parameter only
   - Note: ADK framework automatically provides tool_context - do not pass it explicitly
    - **CRITICAL**: After successful save, you MUST generate a final text response
   - **DO NOT RETURN None** - return the optimized resume markdown to parent
   - DO NOT call Resume Writing Agent

ERROR HANDLING:
This is a Coordinator Agent (has tools AND calls sub-agent). Follow the ADK three-layer pattern:

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

When calling sub-agents (resume_writing_agent):
- Check sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found:
  * Log error
  * Prepend agent name to create error chain
  * Return "ERROR: [resume_critic_agent] -> <INSERT ERROR MESSAGE FROM CHILD>"
  * Stop

For validation errors during processing:
- If malformed JSON structures: Log error, return "ERROR: [resume_critic_agent] Invalid JSON structure in input data" to parent agent, and stop
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
3. MAX 5 ITERATIONS: Absolute limit, finalize even if issues remain
4. ORIGINAL DOCUMENTS ARE TRUTH: The original documents are ground truth for disambiguation
5. RETURN TO REFINER: When done, return to Resume Refiner Agent (not Resume Writing Agent)
6. OWN THE LOOP: You control iteration decisions, not Resume Writing Agent

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
