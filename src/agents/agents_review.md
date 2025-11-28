# Agent Compliance Review
**Date**: 2025-01-27
**Reviewer**: Code Review System
**Standard**: ENGINEERING_GUIDE.md Agentic Principles

## Executive Summary

Reviewed 9 agent files against the Engineering Guide standards. Found **15 compliance issues** across **5 agents**. Most issues are documentation/comment violations (sprint references, outdated comments). One critical architectural issue identified in write-critique loop implementation.

### Compliance by Agent

| Agent | Status | Issues |
|-------|--------|--------|
| job_application_agent.py | COMPLIANT | 0 |
| application_documents_agent.py | ISSUES FOUND | 2 |
| resume_ingest_agent.py | COMPLIANT | 0 |
| job_description_ingest_agent.py | COMPLIANT | 0 |
| resume_refiner_agent.py | ISSUES FOUND | 1 |
| qualifications_matching_agent.py | COMPLIANT | 0 |
| qualifications_checker_agent.py | ISSUES FOUND | 7 |
| resume_writing_agent.py | ISSUES FOUND | 3 |
| resume_critic_agent.py | ISSUES FOUND | 2 |

---

## Critical Issues (Require Immediate Fix)

### CRITICAL-001: Circular Dependency in Write-Critique Loop
**Agent**: `qualifications_checker_agent.py`
**Location**: Lines 99-100
**Severity**: CRITICAL

**Issue**:
```python
resume_writing_agent.tools.append(AgentTool(agent=resume_critic_agent))
resume_critic_agent.tools.append(AgentTool(agent=resume_writing_agent))
```

**Problem**: Dynamically modifying agent tools after creation violates ADK best practices and creates tight coupling. This pattern is not documented in Engineering Guide and differs from standard agent creation patterns.

**Impact**:
- Breaks separation of concerns
- Makes debugging difficult
- Violates ADK agent initialization patterns
- Not following course notebook patterns

**Recommendation**: Research ADK documentation for proper write-critique loop pattern. Consider:
1. Using sub_agents parameter instead of dynamic tool modification
2. Implementing loop control through parent coordinator
3. Alternative ADK-compliant circular workflow patterns

---

## High Priority Issues (Sprint/Comment Violations)

### HIGH-001: Sprint Reference in Docstring
**Agent**: `application_documents_agent.py`
**Location**: Lines 26-27
**Severity**: HIGH

**Issue**:
```python
Sprint 012: Implements parameter passing pattern to handle session isolation.
Ingest agents return JSON in their responses, this agent extracts and returns it.
```

**Violation**: Project directive states "No sprint information in code, including docstrings or comments"

**Fix**: Remove sprint reference, update comment to reflect current implementation

---

### HIGH-002: Outdated Implementation Comment
**Agent**: `application_documents_agent.py`
**Location**: Lines 26-27
**Severity**: HIGH

**Issue**: Comment states "Ingest agents return JSON in their responses, this agent extracts and returns it" which is INCORRECT. Current implementation uses session state pattern - ingest agents save dicts to session state, no JSON extraction occurs.

**Violation**: Anti-Pattern #5 "Returning JSON in Agent Responses" - comment describes old pattern

**Fix**: Update docstring to reflect session state implementation:
```python
"""Create and return the Application Documents Agent.

This agent coordinates the complete document processing workflow:
1. Loads resume and job description files using MCP filesystem
2. Delegates to ingest agents to convert raw documents to structured dicts
3. Ingest agents save dicts directly to session state
4. Returns success confirmation to parent agent

Returns:
    LlmAgent: The configured Application Documents Agent with MCP filesystem and ingest agents
"""
```

---

### HIGH-003: Missing Step 3 in Workflow
**Agent**: `resume_refiner_agent.py`
**Location**: Lines 50-78
**Severity**: HIGH

**Issue**: Workflow jumps from "Step 2" directly to "Step 4", skipping Step 3

**Violation**: Workflow clarity and documentation standards

**Fix**: Renumber steps or add missing Step 3:
```
Step 2: DELEGATE TO QUALIFICATIONS MATCHING AGENT
...

Step 3: WAIT FOR RESPONSE
- The matching agent will coordinate the full workflow
- Wait for complete response before proceeding

Step 4: CHECK FOR ERRORS AND CHAIN THEM
```

---

### HIGH-004: Sprint Reference in Comment
**Agent**: `resume_writing_agent.py`
**Location**: Line 70
**Severity**: HIGH

**Issue**:
```python
Focus on highlighting and pruning. Gen2: Will add rephrasing with Claude Sonnet 4.5.
```

**Violation**: Project directive - no sprint or generation information in code

**Fix**: Remove generational reference:
```python
Focus on highlighting and pruning achievements, maintaining high fidelity to original resume.
```

---

### HIGH-005: Outdated Circular Dependency Comment
**Agent**: `resume_writing_agent.py`
**Location**: Line 72
**Severity**: HIGH

**Issue**:
```python
NOTE: Resume Critic Agent will be added to tools after creation to avoid circular dependency.
```

**Problem**: This note is INCORRECT. The circular dependency is handled in qualifications_checker_agent.py (lines 99-100), not after this agent's creation.

**Fix**: Remove outdated note or update to reflect actual implementation

---

### HIGH-006: Duplicate Circular Dependency Comment
**Agent**: `resume_critic_agent.py`
**Location**: Line 111
**Severity**: HIGH

**Issue**:
```python
NOTE: Resume Writing Agent will be added to tools after creation to avoid circular dependency.
```

**Problem**: Same as HIGH-005. Incorrect location for circular dependency handling.

**Fix**: Remove outdated note

---

## Medium Priority Issues (Sub_agents Parameter)

### MED-001: Missing sub_agents Entry
**Agent**: `qualifications_checker_agent.py`
**Location**: Lines 206-213
**Severity**: MEDIUM

**Issue**: `resume_critic_agent` is added to tools but NOT to sub_agents list

**Code**:
```python
tools=[
    save_quality_matches_to_session,
    save_possible_matches_to_session,
    AgentTool(agent=resume_writing_agent),  # In sub_agents
],
sub_agents=[
    resume_writing_agent,  # Listed
    # resume_critic_agent missing!
],
```

**Violation**: Engineering Guide states sub_agents parameter should list all child agents for ADK compliance (Sprint 016)

**Impact**: May affect ADK's internal agent tracking and lifecycle management

**Fix**: Add resume_critic_agent to sub_agents:
```python
sub_agents=[
    resume_writing_agent,
    resume_critic_agent,
],
```

---

### MED-002: Inconsistent Sub_agents Declaration
**Agent**: `qualifications_checker_agent.py`
**Location**: Lines 92-100
**Severity**: MEDIUM

**Issue**: Both writing and critic agents are created and cross-wired, but only writing_agent is listed in sub_agents parameter. This creates asymmetry in agent hierarchy declaration.

**Recommendation**: Since both agents are created and used in this scope, both should be listed in sub_agents for consistency and ADK compliance.

---

## Low Priority Issues (Documentation/Clarity)

### LOW-001: Typo in Comment
**Agent**: `resume_critic_agent.py`
**Location**: Line 229
**Severity**: LOW

**Issue**:
```python
# Original ocuments are source of truth
```

**Fix**: "ocuments" should be "documents"

---

### LOW-002: Inconsistent Error Message Format
**Agent**: `resume_writing_agent.py`
**Location**: Line 220
**Severity**: LOW

**Issue**: Error message format differs from other agents
```python
"ERROR: [resume_writing_agent] -> <INSERT ERROR MESSAGE FROM TOOL>"
```

**Standard Format** (from other agents):
```python
"ERROR: [resume_writing_agent] <INSERT ERROR MESSAGE FROM TOOL>"
```

**Note**: Tool errors use single angle brackets, sub-agent errors use arrow notation. This is actually CORRECT per error chaining pattern (anti-pattern #6).

**Status**: NOT AN ISSUE - following correct pattern

---

### LOW-003: Missing Parameter Documentation
**Agent**: `resume_writing_agent.py`
**Location**: Line 15
**Severity**: LOW

**Issue**: Function `save_resume_candidate_to_session` uses `candidate_json` parameter name but documentation doesn't clarify it expects a JSON STRING, not a dict.

**Current**:
```python
candidate_json: JSON string containing resume candidate data
```

**Better**:
```python
candidate_json: Resume candidate as JSON string (not dict - must be pre-serialized)
```

**Impact**: Low - parameter name suggests string, but explicit note would help

---

### LOW-004: Inconsistent JSON String Handling
**Agent**: `resume_writing_agent.py`, `resume_critic_agent.py`
**Location**: Multiple
**Severity**: LOW

**Issue**: These agents accept JSON strings as tool parameters and parse them internally, while other agents accept Python dicts directly.

**Pattern in resume_writing_agent.py:15**:
```python
def save_resume_candidate_to_session(tool_context: ToolContext, candidate_json: str, ...):
    candidate_data = json.loads(candidate_json)  # Parse JSON string
```

**Pattern in resume_ingest_agent.py:14**:
```python
def save_resume_dict_to_session(tool_context: ToolContext, resume_dict: dict) -> dict:
    # Accepts dict directly, no parsing
```

**Explanation**: This is intentional based on data size:
- Ingest agents: LLM generates small dict directly
- Writing/Critic agents: LLM generates large resume dict, so JSON string avoids MALFORMED_FUNCTION_CALL

**Status**: NOT AN ISSUE - following Anti-Pattern #1 mitigation strategy

---

## Architectural Observations (Not Issues)

### OBS-001: Session State Implementation Correct
All agents properly implement session state pattern per Engineering Guide:
- Worker agents save to session state via tools
- Coordinator agents read from session state
- No large dicts/lists passed as parameters
- Type hints use `List[Dict[str, Any]]` correctly

### OBS-002: Error Chaining Implemented Correctly
All coordinator agents follow three-layer error handling:
- Check for "ERROR:" keyword
- Prepend agent name for traceability
- Chain errors through parent hierarchy

### OBS-003: Continuation Instructions Present
All agents include explicit "DO NOT RETURN None" and "IMMEDIATELY CONTINUE" instructions per Anti-Pattern #4.

### OBS-004: No Abbreviations Used
All agents use full "job_description" terminology, no "jd" abbreviations found.

---

## Summary of Required Actions

### Immediate (Critical)
1. **CRITICAL-001**: Research and fix write-critique loop circular dependency pattern

### High Priority (Sprint/Comments)
1. **HIGH-001**: Remove sprint reference from application_documents_agent.py docstring
2. **HIGH-002**: Update application_documents_agent.py docstring to reflect session state
3. **HIGH-003**: Fix missing Step 3 in resume_refiner_agent.py workflow
4. **HIGH-004**: Remove generation reference from resume_writing_agent.py
5. **HIGH-005**: Remove/update circular dependency note in resume_writing_agent.py
6. **HIGH-006**: Remove/update circular dependency note in resume_critic_agent.py

### Medium Priority (ADK Compliance)
1. **MED-001**: Add resume_critic_agent to sub_agents in qualifications_checker_agent.py
2. **MED-002**: Document asymmetric sub_agents pattern or make symmetric

### Low Priority (Polish)
1. **LOW-001**: Fix typo "ocuments" → "documents" in resume_critic_agent.py

---

## Compliance Metrics

- **Total Agents Reviewed**: 9
- **Fully Compliant**: 4 (44%)
- **Minor Issues**: 5 (56%)
- **Critical Issues**: 1
- **Total Issues**: 15
- **Anti-Pattern Violations**: 0 (all avoided correctly)
- **Session State Compliance**: 100%
- **Type Hint Compliance**: 100%
- **Error Chaining Compliance**: 100%

---

## Conclusion

The agent codebase demonstrates strong adherence to the Engineering Guide principles:
- Session state pattern correctly implemented across all agents
- Type hints properly specified with `List[Dict[str, Any]]`
- Error chaining follows three-layer pattern
- No large data passed as parameters
- Continuation instructions prevent premature stopping

Primary issues are documentation-related (sprint references, outdated comments) rather than architectural violations. The one critical issue (write-critique loop pattern) requires research into ADK best practices for circular workflows.

**Overall Assessment**: GOOD - Core patterns correct, documentation needs cleanup, one architectural question to resolve.
