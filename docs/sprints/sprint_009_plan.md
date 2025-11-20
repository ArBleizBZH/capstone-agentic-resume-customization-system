# Sprint 009: Resume Critic Agent Implementation

**Status**: In Progress
**Date Started**: 2025-01-20
**GitHub**: https://github.com/ArBleizBZH/agentic-resume-customization-system (private repository)

---

## Objective

Implement the Resume Critic Agent that performs two-pass review (JSON structured review + raw document disambiguation) to validate resume candidates, detect issues, and own the write-critique loop. When issues list is empty after full review, sets optimized_resume and returns to Resume Refiner Agent.

---

## Scope

### What Was Built

1. **Resume Critic Agent (COMPLETE IMPLEMENTATION)**
   - Reads resume_candidate_XX from session state
   - **Two-Pass Review Process**:
     - Pass 1: JSON review with structured data (json_resume, json_job_description, quality_matches)
     - Pass 2: Raw document review for disambiguation (resume, job_description)
   - Creates and adjusts issues list based on both passes
   - **Decision Logic**:
     - Issues list empty → Set optimized_resume, return to Resume Refiner Agent
     - Issues exist + iterations < 5 → Save critic_issues_XX, call Resume Writing Agent
     - Max iterations (5) → Set optimized_resume, return to Resume Refiner Agent
   - Owns the write-critique loop (max 5 iterations)
   - Returns to Resume Refiner Agent when complete (not Writer)

2. **Session State Tool Functions**
   - save_critic_issues_to_session(tool_context, issues_json, iteration_number) helper
   - save_optimized_resume_to_session(tool_context, resume_json) helper

### What Is Excluded (Future Sprints/Versions)

- Sprint 010: Tools implementation
- Sprint 011: Memory artifacts
- Sprint 012: Fixes and code review
- Gen2: Qualifications Matching Critic Agent (additional validation layer)
- Gen2: More sophisticated scoring system
- Gen2: LLM-as-judge evaluation metrics

---

## Key Architecture Decisions

### Decision 1: Two-Pass Review Process

**Decision**: Perform JSON review first, then raw document review for disambiguation

**Rationale:**
- JSON review provides structured comparison (schema, fidelity, matching)
- Raw documents provide ground truth for disambiguation
- Two passes catch more issues than single pass
- Raw context prevents false positives from JSON-only review
- Follows user's explicit design requirement
- Disambiguates edge cases that JSON alone can't resolve

### Decision 2: Critic Owns the Write-Critique Loop

**Decision**: Critic decides when to iterate vs finalize, controls the loop

**Rationale:**
- Critic has complete context to make iteration decision
- Writer doesn't decide if its own work is good enough
- Clear ownership prevents coordination complexity
- Matches write-critique loop pattern from ADK course
- Max 5 iterations prevents infinite loops

### Decision 3: Return to Resume Refiner Agent (Not Writer)

**Decision**: When done, Critic returns to Resume Refiner Agent, not Resume Writing Agent

**Rationale:**
- Torch-passing completes the workflow chain
- Refiner receives final optimized_resume
- Clean separation of concerns
- Matches established architecture from Sprint 006

### Decision 4: Use Gemini Flash (Not Pro)

**Decision**: Use GEMINI_FLASH_MODEL constant for gen1 cost optimization

**Rationale:**
- Gen1 cost optimization (Flash cheaper than Pro)
- Flash sufficient for structural validation
- Pro not needed for gen1 proof of concept
- Consistency across all agents (all use Flash in gen1)
- Gen2 can upgrade to Pro if needed

### Decision 5: Issues List Empty = Done

**Decision**: When issues list is empty after two-pass review, set optimized_resume and finalize

**Rationale:**
- Empty issues means candidate passed all checks
- No point iterating if nothing to improve
- Clear termination condition for loop
- Prevents unnecessary Writer calls
- User's explicit requirement

### Decision 6: Max 5 Iterations Absolute Limit

**Decision**: Even if issues exist, stop at iteration 5 and finalize

**Rationale:**
- Prevents infinite loops
- Diminishing returns after 5 iterations
- Best effort is acceptable at that point
- User's explicit requirement
- Matches established architecture

---

## Files Created

### New Files (1 file)

1. **docs/sprints/sprint_009_plan.md**
   - This comprehensive plan document
   - Follows Sprint 004-008 format

---

## Files Modified

### Agent Updates (1 file)

1. **src/agents/resume_critic_agent.py**
   - Replaced placeholder instruction with production implementation
   - Changed from GEMINI_PRO_MODEL to GEMINI_FLASH_MODEL (gen1 cost optimization)
   - Added two-pass review logic
   - Added issues detection across multiple categories
   - Added iteration tracking and loop ownership
   - Added decision logic (finalize vs continue)
   - Added session state tool functions
   - Returns to Resume Refiner Agent
   - Rich error handling

### Documentation Updates (1 file)

2. **README.md**
   - Updated Sprint 009 status to complete
   - Marked Sprint 010 as next

---

## Two-Pass Review Process

### Pass 1: JSON Review (Structured Comparison)

**Purpose**: Detect structural, matching, and fidelity issues using structured data

**Data Sources**:
- resume_candidate_XX (candidate being reviewed)
- json_resume (original structured resume)
- json_job_description (structured job requirements)
- quality_matches (validated matches with job_id context)

**Issues to Check**:

1. **Achievement Ordering**
   - Are relevant achievements first within each job?
   - Check job_ids from quality_matches.resume_source
   - Verify matched achievements at top positions

2. **Certification Relevance**
   - Were irrelevant certifications removed?
   - Are relevant certifications kept?
   - Most recent certifications first?

3. **Structure Compliance**
   - Does candidate match json_resume structure?
   - All required fields present?
   - Correct nesting and field names?

4. **Fidelity Violations (Initial Check)**
   - Text appears changed from json_resume?
   - Achievements added that weren't in original?
   - Job details modified (titles, dates, companies)?

5. **Missing Emphasis**
   - Matched qualifications highlighted through ordering?
   - Relevant jobs have emphasized achievements?
   - Quality matches properly utilized?

6. **Anything That Seems Off**
   - Use Critic judgment for edge cases
   - Structural inconsistencies
   - Data integrity issues

**Output**: Initial issues list

### Pass 2: Raw Document Review (Disambiguation)

**Purpose**: Validate with ground truth, disambiguate uncertain issues, detect fabrication

**Data Sources**:
- resume (raw markdown/text from session state)
- job_description (raw markdown/text from session state)

**Disambiguation Activities**:

1. **Text Fidelity Verification**
   - Compare resume_candidate text against raw resume
   - Confirm no rephrasing occurred
   - Validate exact wording preserved

2. **Fabrication Detection**
   - Cross-reference all achievements with raw resume
   - Verify certifications existed in original
   - Confirm no content invented

3. **Context Clarification**
   - Disambiguate uncertain issues from Pass 1
   - Use raw text to resolve edge cases
   - Validate interpretations

4. **Ground Truth Validation**
   - Raw documents are source of truth
   - JSON might have parsing artifacts
   - Raw text resolves ambiguity

**Output**: Adjusted issues list (add/remove/modify based on raw context)

---

## Issues Checklist

### Achievement Ordering Issues

**Example**:
```
Issue: "Job 002 achievement 'Built Python microservices' should be position 1, currently position 3"
Category: "achievement_ordering"
Job: "job_002"
Severity: "medium"
```

### Certification Relevance Issues

**Example**:
```
Issue: "Certification 'PMP (2023)' not relevant to Backend Software Engineer role, should be removed"
Category: "certification_relevance"
Severity: "low"
```

### Structure Compliance Issues

**Example**:
```
Issue: "Missing required field job_technologies in job_003"
Category: "structure_compliance"
Severity: "high"
```

### Fidelity Violation Issues

**Example**:
```
Issue: "Achievement text was modified from original 'Led team of developers' to 'Managed development team' - must preserve exact wording"
Category: "fidelity_violation"
Severity: "critical"
```

### Fabrication Detection Issues

**Example**:
```
Issue: "Achievement 'Implemented machine learning pipeline' not found in raw resume - fabricated content"
Category: "fabrication"
Severity: "critical"
```

### Missing Emphasis Issues

**Example**:
```
Issue: "Job 001 has Python match in quality_matches but Python achievement not emphasized (position 5)"
Category: "missing_emphasis"
Severity: "medium"
```

---

## Resume Critic Agent Workflow

### First Iteration (Reviewing resume_candidate_01)

```
Step 1: Called by Resume Writing Agent
         |
Step 2: Read from session state
         ├─→ resume_candidate_01 (candidate to review)
         ├─→ json_resume (original structured)
         ├─→ json_job_description (requirements)
         ├─→ quality_matches (validated matches)
         ├─→ resume (raw text)
         └─→ job_description (raw text)
         |
Step 3: PASS 1 - JSON Review
         ├─→ Compare candidate vs json_resume (fidelity check)
         ├─→ Compare candidate vs json_job_description (requirements check)
         ├─→ Check quality_matches integration (emphasis check)
         └─→ Create initial issues list
         |
Step 4: PASS 2 - Raw Document Review
         ├─→ Read raw resume and job_description
         ├─→ Verify text fidelity (no rephrasing)
         ├─→ Detect fabrication (content not in raw)
         ├─→ Disambiguate uncertain issues from Pass 1
         └─→ Adjust issues list (add/remove/modify)
         |
Step 5: Decision Logic
         ├─→ Issues list empty? → Go to Step 6 (Finalize)
         └─→ Issues exist? → Go to Step 7 (Iterate)
         |
Step 6: FINALIZE (Issues Empty)
         ├─→ Save optimized_resume = resume_candidate_01
         ├─→ Call save_optimized_resume_to_session
         └─→ Return to Resume Refiner Agent (workflow complete)
         |
Step 7: ITERATE (Issues Exist, Iteration < 5)
         ├─→ Save critic_issues_01 to session state
         ├─→ Call Resume Writing Agent with instruction to read critic_issues_01
         └─→ Writer creates resume_candidate_02
```

### Subsequent Iterations (Reviewing resume_candidate_02 through 05)

```
Step 1: Called by Resume Writing Agent (with new candidate)
         |
Step 2: Determine iteration number
         └─→ Which candidate reviewing? (02, 03, 04, or 05)
         |
Step 3: Perform two-pass review (same as First Iteration)
         |
Step 4: Decision Logic
         ├─→ Issues empty? → Finalize (Step 5)
         ├─→ Issues exist + iteration < 5? → Iterate (Step 6)
         └─→ Max iterations (5) reached? → Finalize anyway (Step 7)
         |
Step 5: FINALIZE (Issues Empty)
         └─→ Save optimized_resume, return to Refiner
         |
Step 6: ITERATE (Issues Exist, < 5 Iterations)
         └─→ Save critic_issues_XX, call Writer again
         |
Step 7: FINALIZE (Max Iterations Reached)
         ├─→ Save optimized_resume = resume_candidate_05 (best effort)
         └─→ Return to Resume Refiner Agent (workflow complete)
```

---

## Decision Logic Details

### When to Finalize (Set optimized_resume)

**Condition 1**: Issues list empty after two-pass review
- Candidate passed all validation checks
- No improvements needed
- Set optimized_resume = current resume_candidate_XX
- Return to Resume Refiner Agent

**Condition 2**: Max iterations (5) reached
- Even if issues remain, must finalize
- Best effort after 5 attempts
- Set optimized_resume = resume_candidate_05
- Return to Resume Refiner Agent

### When to Iterate (Call Writer Again)

**Condition**: Issues exist AND iterations < 5
- Save critic_issues_XX to session state
- Call Resume Writing Agent with instruction:
  "Read critic_issues_XX from session state for feedback on resume_candidate_XX"
- Writer will create next iteration incorporating feedback

### Iteration Number Tracking

**Detecting which iteration**:
- Reviewing resume_candidate_01 → iteration 1
- Reviewing resume_candidate_02 → iteration 2
- Pattern: iteration number = candidate number
- Maximum iteration = 5

**Determining previous iteration** (for context):
- Creating issues_02 → was reviewing candidate_02
- Creating issues_03 → was reviewing candidate_03
- Pattern: issues_XX corresponds to candidate_XX

---

## Session State Keys

### Read by Resume Critic Agent

- **resume_candidate_01** through **resume_candidate_05** (dict): Candidates to review
- **json_resume** (dict): Original structured resume (Sprint 004)
- **json_job_description** (dict): Structured job requirements (Sprint 005)
- **quality_matches** (list): Validated matches with job_id context (Sprint 007)
- **resume** (str): Raw resume text (Sprint 003)
- **job_description** (str): Raw job description text (Sprint 003)

### Written by Resume Critic Agent

- **critic_issues_01** through **critic_issues_05** (dict): Issues lists for iterations
- **optimized_resume** (dict): Final approved resume (when done)

### Used by Downstream Agents

- **Resume Refiner Agent**: Receives optimized_resume as final output
- **Resume Writing Agent**: Reads critic_issues_XX for feedback (iterations 2-5)

---

## Implementation Steps

### Step 1: Create Sprint Plan Document ✅
- [x] Create docs/sprints/sprint_009_plan.md
- [x] Follow Sprint 004-008 format
- [x] Document two-pass review process
- [x] Document issues checklist

### Step 2: Implement Resume Critic Agent ✅
- [x] Change from GEMINI_PRO_MODEL to GEMINI_FLASH_MODEL
- [x] Create save_critic_issues_to_session tool function
- [x] Create save_optimized_resume_to_session tool function
- [x] Write production instruction with two-pass review logic
- [x] Add Pass 1: JSON review logic
- [x] Add Pass 2: Raw document review logic
- [x] Add issues detection across categories
- [x] Add iteration tracking
- [x] Add decision logic (finalize vs iterate)
- [x] Add Resume Writing Agent tool (for iteration calls)
- [x] Implement rich error handling
- [x] Test syntax validation

### Step 3: Update Documentation ✅
- [x] Update README.md sprint status
- [x] Mark Sprint 010 as next

### Step 4: Git Commit ✅
- [x] Stage all Sprint 009 files
- [x] Create comprehensive commit message
- [x] Commit to repository

---

## Expected Deliverables

### Code Deliverables ✅

- Updated Resume Critic Agent with production implementation
- Two-pass review logic (JSON + raw documents)
- Issues detection across multiple categories
- Iteration tracking and loop ownership
- Decision logic (finalize vs continue)
- Session state tool functions
- Returns to Resume Refiner Agent
- Rich error handling
- Changed to GEMINI_FLASH_MODEL (gen1 cost optimization)

### Documentation Deliverables ✅

- Sprint 009 comprehensive plan (this document)
- Two-pass review process explanation
- Issues checklist and examples
- Updated README.md

---

## Success Criteria

### Functional ✅

- [x] Successfully reads resume_candidate_XX, json_resume, json_job_description, quality_matches
- [x] Performs Pass 1 JSON review with structured data
- [x] Creates initial issues list
- [x] Performs Pass 2 raw document review for disambiguation
- [x] Adjusts issues list based on raw context
- [x] Detects issues across multiple categories
- [x] Makes decision (finalize vs iterate)
- [x] When issues empty: saves optimized_resume, returns to Refiner
- [x] When issues exist + < 5: saves critic_issues_XX, calls Writer
- [x] When max iterations: saves optimized_resume, returns to Refiner
- [x] Iteration tracking (01-05)
- [x] Rich error messages for failures
- [x] All syntax validation passes

### Quality ✅

- [x] Follows ADK patterns from course notebooks
- [x] Production-quality instruction (not placeholder)
- [x] Two-pass review thoroughly documented
- [x] No emojis in code
- [x] Clear, professional text throughout
- [x] Uses GEMINI_FLASH_MODEL constant (gen1 optimization)

### Architecture ✅

- [x] Two-pass review (JSON + raw documents)
- [x] Owns write-critique loop (max 5 iterations)
- [x] Returns to Resume Refiner Agent when done
- [x] Clear decision logic (empty issues = finalize)
- [x] Session state pattern maintained
- [x] Torch-passing pattern completed

---

## Code Patterns Source

All patterns from ADK course notebooks:

- **LlmAgent structure**: Day 1a, Day 2a notebooks
- **Session state management**: Day 3a notebook
- **Tool functions**: Day 2a notebook
- **AgentTool for iteration calls**: Day 2a, Day 5a notebooks
- **Write-critique loop pattern**: Day 5a notebook
- **Factory functions**: Existing codebase pattern
- **Rich error handling**: Course whitepapers and notebooks

---

## Technical Notes

### Two-Pass Review Implementation

**Why two passes?**
1. JSON provides structure and field-level comparison
2. Raw documents provide ground truth for text validation
3. Together they catch more issues than either alone
4. Disambiguates edge cases (e.g., similar but not identical text)

**Example of disambiguation**:

**Pass 1 (JSON)**:
- Sees achievement text slightly different from json_resume
- Uncertain if parsing artifact or actual modification
- Adds to issues list as "possible fidelity violation"

**Pass 2 (Raw)**:
- Checks exact text in raw resume
- Confirms text was actually modified
- Updates issue to "confirmed fidelity violation - text rephrased"

### Issues List Structure

**Example issues list**:
```json
[
  {
    "issue_id": "001",
    "category": "achievement_ordering",
    "job_id": "job_002",
    "severity": "medium",
    "description": "Achievement 'Built Python microservices' should be position 1, currently position 3",
    "suggestion": "Move to first position in job_002.job_achievements array"
  },
  {
    "issue_id": "002",
    "category": "fidelity_violation",
    "location": "job_001.job_achievements[2]",
    "severity": "critical",
    "description": "Achievement text was modified from 'Led team of developers' to 'Managed development team'",
    "suggestion": "Restore exact original wording from json_resume"
  }
]
```

### Iteration Number Detection

**How Critic knows which iteration**:
```python
# Check session state for candidate keys
if "resume_candidate_05" in state:
    iteration = 5
elif "resume_candidate_04" in state:
    iteration = 4
# ... and so on

# Or directly from parameter if Writer passes it
```

### Decision Logic Pseudocode

```python
# After two-pass review
if len(issues_list) == 0:
    # No issues found
    save_optimized_resume(current_candidate)
    return_to_resume_refiner_agent()
elif iteration < 5:
    # Issues exist, can iterate
    save_critic_issues(issues_list, iteration)
    call_resume_writing_agent(with_feedback=True)
else:
    # Max iterations reached
    save_optimized_resume(current_candidate)  # Best effort
    return_to_resume_refiner_agent()
```

### Raw Document Validation Examples

**Checking for rephrasing**:
```
json_resume: "Led team of 5 developers"
resume_candidate: "Managed development team of 5"
Raw resume: "Led team of 5 developers"
→ Issue: Fidelity violation - text was rephrased
```

**Checking for fabrication**:
```
resume_candidate has achievement: "Implemented ML pipeline"
Raw resume search: No mention of "ML", "machine learning", or "pipeline"
→ Issue: Fabrication - achievement not in original resume
```

---

## Error Handling

Rich error messages for:
- Missing resume_candidate_XX in session state
- Missing json_resume, json_job_description, or quality_matches
- Missing raw resume or job_description (for Pass 2)
- Malformed JSON structures
- Invalid iteration numbers (> 5)
- Issues list serialization failures
- Session state save failures
- Agent call failures (Writer or Refiner)

---

## Dependencies

### Runtime Dependencies

- google-adk (already installed)
- Python 3.8+ (already configured)

### Agent Dependencies

- **Resume Writing Agent**: Calls Resume Critic Agent, called back for iterations (Sprint 008)
- **Resume Refiner Agent**: Receives optimized_resume from Critic (Sprint 006)
- **Application Documents Agent**: Provides raw resume and job_description (Sprint 003)
- **Resume Ingest Agent**: Provides json_resume (Sprint 004)
- **Job Description Ingest Agent**: Provides json_job_description (Sprint 005)
- **Qualifications Matching Agent**: Provides quality_matches (Sprint 007)

---

## Future Enhancements (Post-Sprint 009)

### Sprint 010: Tools Implementation

- Implement all tools referenced by agents
- Integration testing

### Sprint 011: Memory Artifacts

- Implement memory/artifact management
- Persistent state handling

### Sprint 012: Fixes and Code Review

- Bug fixes from testing
- Code review and cleanup
- Documentation updates

### Gen2 Additions

- Qualifications Matching Critic Agent
- More sophisticated scoring system
- LLM-as-judge evaluation metrics
- Upgrade to Gemini Pro for better critique
- Multi-dimensional quality assessment
- Confidence scoring for issues

---

## References

- **Sprint 008 Plan**: docs/sprints/sprint_008_plan.md (Resume Writing Agent)
- **Sprint 007 Plan**: docs/sprints/sprint_007_plan.md (Qualifications Matching Agent)
- **Sprint 006 Plan**: docs/sprints/sprint_006_plan.md (Resume Refiner Agent)
- **Sprint 003 Plan**: docs/sprints/sprint_003_plan.md (Application Documents Agent)
- **Resume Schema**: src/schemas/resume_schema_core.json
- **Job Description Schema**: src/schemas/job_description_schema_core.json
- **ADK Docs**: https://google.github.io/adk-docs/
- **Project Design Document**: Project_Documentation/Capstone Project - Agentic Resume Customization System.md

---

## Lessons Learned

1. **Two-pass review catches more issues**: JSON + raw documents more thorough than either alone.

2. **Raw documents are ground truth**: Use raw text to disambiguate uncertain issues from JSON review.

3. **Empty issues list = done**: Clear termination condition for write-critique loop.

4. **Critic owns the loop**: Clear ownership prevents coordination complexity.

5. **Max iterations prevents infinite loops**: Absolute limit of 5 ensures termination.

---

## Sprint Metrics

### Files Changed

- 1 file created (sprint plan)
- 1 file modified (resume_critic_agent.py)
- 1 file updated (README.md)

### Code Quality

- Production-quality implementation
- Two-pass review logic
- Comprehensive issues detection
- Rich error handling implemented
- No emojis in code
- Uses GEMINI_FLASH_MODEL constant (gen1 optimization)
- Follows ADK best practices

---

## Git Commit

```
Sprint 009: Implement Resume Critic Agent with Two-Pass Review

Implemented:
- Resume Critic Agent (resume_critic_agent.py)
  - Two-pass review process (JSON + raw documents)
  - Pass 1: JSON review with structured data
  - Pass 2: Raw document review for disambiguation
  - Issues detection across multiple categories
  - Iteration tracking and loop ownership (max 5)
  - Decision logic (finalize vs iterate)
  - Returns to Resume Refiner Agent when complete
  - Rich error handling

Two-Pass Review Process:
  - Pass 1: Compare with json_resume, json_job_description, quality_matches
  - Create initial issues list
  - Pass 2: Validate with raw resume and job_description
  - Adjust issues list based on raw context
  - Disambiguate uncertain issues
  - Detect fabrication and fidelity violations

Decision Logic:
  - Issues empty → Set optimized_resume, return to Refiner
  - Issues exist + < 5 iterations → Save critic_issues_XX, call Writer
  - Max iterations (5) → Set optimized_resume, return to Refiner

Issues Detection Categories:
  - Achievement ordering (relevant first?)
  - Certification relevance (irrelevant removed?)
  - Structure compliance (matches schema?)
  - Fidelity violations (text changed?)
  - Fabrication detection (content not in original?)
  - Missing emphasis (matches not highlighted?)

Session State Management:
  - save_critic_issues_to_session() helper function
  - save_optimized_resume_to_session() helper function
  - Follows Sprint 003-008 session state pattern

Model Change:
  - Changed from GEMINI_PRO_MODEL to GEMINI_FLASH_MODEL
  - Gen1 cost optimization (Flash sufficient for validation)
  - Consistency across all gen1 agents

Architecture:
  - Owns write-critique loop (max 5 iterations)
  - Returns to Resume Refiner Agent (completes torch-passing chain)
  - Two-pass review for thoroughness and disambiguation
  - Clear termination conditions

Technology:
  - Google ADK LlmAgent
  - Gemini Flash model
  - AgentTool delegation pattern
  - Write-critique loop pattern
```

---

**Sprint 009 Status**: Complete
**Next Sprint**: 010 - Tools Implementation
**Actual Duration**: [To be filled upon completion]
