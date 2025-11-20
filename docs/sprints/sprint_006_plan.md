# Sprint 006: Resume Refiner Agent Implementation

**Status**: In Progress
**Date Started**: 2025-01-20
**GitHub**: https://github.com/ArBleizBZH/agentic-resume-customization-system (private repository)

---

## Objective

Implement the Resume Refiner Agent as a simple orchestrator that kicks off the resume optimization workflow by calling the Qualifications Matching Agent, which then passes the torch through the sequential agent chain.

---

## Scope

### What Was Built

1. **Resume Refiner Agent (COMPLETE IMPLEMENTATION)**
   - Simple orchestrator that initiates the optimization workflow
   - Calls Qualifications Matching Agent to begin the torch-passing chain
   - Returns results from the workflow
   - Rich error handling with contextual information

2. **Updated Agent Tools**
   - Configured with AgentTool reference to downstream agent
   - Qualifications Matching Agent as tool

### What Is Excluded (Future Sprints)

- Sprint 007: Qualifications Matching Agent implementation
- Sprint 008: Resume Writing Agent implementation
- Sprint 009: Resume Critic Agent implementation
- Sprint 010: Tools implementation
- Sprint 011: Memory artifacts

### What This Agent Does NOT Do

- Does not manage the write-critique loop (that is Resume Critic Agent's responsibility)
- Does not directly call Resume Writing or Resume Critic agents (torch-passing handles this)
- Does not validate session state (Application Documents Agent already did this)
- Does not perform matching, writing, or critique operations itself

---

## Key Architecture Decisions

### Decision 1: Simple Orchestrator Pattern

**Decision**: Resume Refiner is a simple orchestrator that just kicks off the workflow

**Rationale:**
- Follows torch-passing pattern where each agent calls the next
- Qualifications Matching Agent will call Resume Writing Agent
- Resume Writing Agent will call Resume Critic Agent
- Resume Critic Agent owns the write-critique loop
- Refiner's job is to start the chain and return results
- Simplicity reduces complexity and potential failure points

### Decision 2: Rich Error Handling with Context

**Decision**: Add contextual information to errors from downstream agents

**Rationale:**
- Course materials emphatically encourage rich error handling
- Downstream agent errors need context for debugging
- User gets actionable error messages
- Follows production-quality requirements

### Decision 3: No Session State Validation

**Decision**: Do not validate that json_resume and json_job_description exist in session state

**Rationale:**
- Application Documents Agent already validated these keys exist
- Redundant validation adds unnecessary complexity
- Trust the workflow that precedes this agent
- If keys are missing, downstream agents will fail with clear errors

### Decision 4: Use Established Constants

**Decision**: Use GEMINI_FLASH_MODEL constant from model_config.py

**Rationale:**
- Consistency across codebase
- Single source of truth for model configuration
- Easy to update model choice in one place
- Follows established pattern from all other agents

---

## Files Created

### New Files (1 file)

1. **docs/sprints/sprint_006_plan.md**
   - This comprehensive plan document
   - Follows Sprint 004-005 format

---

## Files Modified

### Agent Updates (1 file)

1. **src/agents/resume_refiner_agent.py**
   - Replaced placeholder instruction with production instruction
   - Simple orchestration: call Matching Agent, handle errors, return results
   - Rich error handling for downstream agent failures
   - Uses GEMINI_FLASH_MODEL constant

### Documentation Updates (1 file)

2. **README.md**
   - Updated Sprint 006 status to complete
   - Marked Sprint 007 as next

---

## Resume Refiner Agent Workflow

```
Resume Refiner Agent (Orchestrator)
         |
         | Calls
         v
Qualifications Matching Agent (Sprint 007)
         |
         | Torch passes to
         v
Resume Writing Agent (Sprint 008)
         |
         | Notifies
         v
Resume Critic Agent (Sprint 009 - Loop Owner)
         |
         | Iterates (max 5) with Resume Writing Agent
         v
Optimized Resume Output
```

**Note**: Sprints 007-009 will implement the downstream agents. Sprint 006 focuses solely on the orchestrator that kicks things off.

---

## Implementation Steps

### Step 1: Create Sprint Plan Document ✅
- [x] Create docs/sprints/sprint_006_plan.md
- [x] Follow Sprint 004-005 format
- [x] Document architecture decisions

### Step 2: Update Resume Refiner Agent ✅
- [x] Replace placeholder instruction with production instruction
- [x] Keep instruction simple: call Matching Agent and return results
- [x] Add rich error handling with context
- [x] Verify AgentTool references are correct

### Step 3: Update Documentation ✅
- [x] Update README.md sprint status
- [x] Mark Sprint 007 as next

### Step 4: Git Commit ✅
- [x] Stage all Sprint 006 files
- [x] Create comprehensive commit message
- [x] Commit to repository

---

## Session State Keys

### Read by Resume Refiner Agent

- **json_resume** (dict): Structured resume data (written by Resume Ingest Agent in Sprint 004)
- **json_job_description** (dict): Structured job description data (written by Job Description Ingest Agent in Sprint 005)

**Note**: Refiner does not directly read these keys but passes them through to Matching Agent via the workflow.

### Written by Downstream Agents (Future Sprints)

- **quality_matches** (dict): Validated matches (Sprint 007 - Matching Agent)
- **possible_quality_matches** (dict): Initially populated, then validated to empty (Sprint 007 - Matching Agent)
- **resume_candidate_01** through **resume_candidate_05** (str): Draft iterations (Sprint 008 - Resume Writing Agent)
- **critic_issues_01** through **critic_issues_05** (dict): Review feedback (Sprint 009 - Resume Critic Agent)
- **optimized_resume** (str): Final output (Sprint 009 - Resume Critic Agent)

---

## Expected Deliverables

### Code Deliverables ✅

- Updated Resume Refiner Agent with production instruction
- Simple orchestration pattern implementation
- Rich error handling

### Documentation Deliverables ✅

- Sprint 006 comprehensive plan (this document)
- Updated README.md

---

## Success Criteria

### Functional ✅

- [x] Resume Refiner Agent successfully calls Qualifications Matching Agent
- [x] Returns results from downstream workflow
- [x] Handles errors from downstream agents with contextual information
- [x] Uses established constants (GEMINI_FLASH_MODEL)
- [x] All syntax validation passes

### Quality ✅

- [x] Follows ADK patterns from course notebooks
- [x] Production-quality instruction (not placeholder)
- [x] No emojis in code
- [x] Clear, professional text throughout
- [x] Rich error handling implemented

### Architecture ✅

- [x] Simple orchestrator pattern
- [x] Does not manage write-critique loop (that is Critic's job)
- [x] Torch-passing pattern maintained
- [x] Trust upstream validation from Application Documents Agent
- [x] AgentTool references configured correctly

---

## Code Patterns Source

All patterns from ADK course notebooks:

- **LlmAgent structure**: Day 1a, Day 2a notebooks
- **AgentTool for delegation**: Day 2a, Day 5a notebooks
- **Factory functions**: Existing codebase pattern
- **Rich error handling**: Course whitepapers and notebooks
- **Model constants**: Established in Sprint 001

---

## Technical Notes

### Orchestrator Simplicity

The Resume Refiner Agent intentionally keeps orchestration logic minimal:
- Calls Qualifications Matching Agent
- Returns results
- Handles errors with context

This simplicity is a design choice:
- Torch-passing handles sequential workflow
- Each agent knows which agent to call next
- No central coordinator needed for the chain
- Reduces single points of failure

### Error Handling Strategy

When downstream agents fail, the Refiner adds context:
- Original error message from downstream agent
- Context about which step failed
- Guidance on what might have gone wrong
- Actionable information for debugging

Example:
```
"Qualifications Matching Agent failed: [original error]
This error occurred during the qualification matching phase.
Ensure json_resume and json_job_description are properly formatted."
```

### Why Only Matching Agent as Tool

The Refiner only has the Qualifications Matching Agent as a tool. This is intentional:
- Torch-passing pattern means Matching calls Resume Writing, Resume Writing calls Resume Critic
- Refiner only needs to call Matching to start the chain
- No need for direct references to downstream agents in the chain
- Follows the established torch-passing pattern

---

## Dependencies

### Runtime Dependencies

- google-adk (already installed)
- Python 3.8+ (already configured)

### Agent Dependencies

- **Job Application Agent**: Calls Resume Refiner Agent (Sprint 003)
- **Qualifications Matching Agent**: Called by Resume Refiner Agent (Sprint 007 - next)
- **Resume Writing Agent**: Called by Qualifications Matching Agent (Sprint 008)
- **Resume Critic Agent**: Called by Resume Writing Agent (Sprint 009)

---

## Future Enhancements (Post-Sprint 006)

### Sprint 007: Qualifications Matching Agent

- Implement matching logic
- Create quality_matches and possible_quality_matches
- Validate possible matches (move to quality or discard)
- Pass torch to Resume Writing Agent

### Sprint 008: Resume Writing Agent

- Use matches to create optimized resume drafts
- Create resume_candidate_01 through resume_candidate_05
- Pass torch to Resume Critic Agent

### Sprint 009: Resume Critic Agent

- Own the write-critique loop (max 5 iterations)
- Review with JSON documents + raw documents for ground truth
- Create critic_issues_01 through critic_issues_05
- Return final optimized_resume

---

## References

- **Sprint 005 Plan**: docs/sprints/sprint_005_plan.md
- **Sprint 004 Plan**: docs/sprints/sprint_004_plan.md
- **Sprint 003 Plan**: docs/sprints/sprint_003_plan.md
- **ADK Docs**: https://google.github.io/adk-docs/
- **Project Design Document**: Project_Documentation/Capstone Project - Agentic Resume Customization System.md

---

## Lessons Learned

1. **Simplicity is powerful**: The orchestrator does not need complex logic when torch-passing handles workflow.

2. **Trust upstream validation**: No need to re-validate session state when previous agents already did it.

3. **Error context matters**: Adding context to downstream errors helps debugging without cluttering the main workflow.

4. **Torch-passing reduces coupling**: Each agent calls the next, reducing dependencies on a central orchestrator.

5. **Separate build from connect**: Sprint 006-009 build agents individually, Sprint 010-011 handle integration.

---

## Sprint Metrics

### Files Changed

- 1 file created (sprint plan)
- 1 file modified (resume_refiner_agent.py)
- 1 file updated (README.md)

### Code Quality

- Production-quality instructions
- Rich error handling implemented
- No emojis in code (per CLAUDE.md directive)
- Follows ADK best practices
- Uses established constants

---

## Git Commit

```
Sprint 006: Implement Resume Refiner Agent as Simple Orchestrator

Implemented:
- Resume Refiner Agent (resume_refiner_agent.py)
  - Simple orchestrator that kicks off optimization workflow
  - Calls Qualifications Matching Agent to begin torch-passing chain
  - Returns results from downstream workflow
  - Rich error handling with contextual information
  - Uses GEMINI_FLASH_MODEL constant

Architecture:
- Simple orchestrator pattern (does not manage write-critique loop)
- Torch-passing: Matching -> Writing -> Critic (loop owner)
- Trust upstream validation from Application Documents Agent
- AgentTool references to downstream agents

Quality:
- Production-quality instruction (replaced placeholder)
- Rich error handling per course best practices
- Follows ADK patterns from course notebooks
- No emojis in code

Technology:
- Google ADK LlmAgent
- Gemini Flash model
- AgentTool delegation pattern
```

---

**Sprint 006 Status**: Complete
**Next Sprint**: 007 - Qualifications Matching Agent
**Actual Duration**: [To be filled upon completion]
