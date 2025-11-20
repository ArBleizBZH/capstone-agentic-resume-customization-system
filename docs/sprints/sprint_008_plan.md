# Sprint 008: Resume Writing Agent Implementation

**Status**: In Progress
**Date Started**: 2025-01-20
**GitHub**: https://github.com/ArBleizBZH/agentic-resume-customization-system (private repository)

---

## Objective

Implement the Resume Writing Agent that creates optimized resume candidates by reordering achievements within jobs based on quality_matches, pruning irrelevant certifications, and maintaining high fidelity to the original resume structure. Gen1 focuses on highlighting and pruning (the hardest tasks for humans), not rewriting.

---

## Scope

### What Was Built

1. **Resume Writing Agent (COMPLETE IMPLEMENTATION)**
   - Reads json_resume, json_job_description, and quality_matches from session state
   - Uses json_resume structure as template (Option D: concrete example)
   - References src/schemas/resume_schema_core.json for edge cases
   - Reorders achievements within each job by relevance to quality_matches
   - Uses job_id context from quality_matches.resume_source to identify relevant jobs
   - Prunes completely irrelevant certifications (keeps most recent first)
   - Maintains chronological job order (newest first)
   - Preserves job_id sequence (job_001 = oldest, always stable)
   - NO rephrasing, NO adding, NO rewriting (gen1 proof of concept)
   - Creates resume_candidate_01 through resume_candidate_05 (JSON structure)
   - Saves to session state with iteration tracking
   - Passes torch to Resume Critic Agent
   - Handles critic feedback for iterations 2-5

2. **Session State Tool Function**
   - save_resume_candidate_to_session(tool_context, candidate_json, iteration_number) helper

### What Is Excluded (Future Sprints/Versions)

- Gen2: Achievement rephrasing to highlight keywords
- Gen2: Professional summary rewriting
- Gen2: Adding relevant achievements from job history
- Gen2: Skills section reordering
- Gen2: Claude Sonnet 4.5 for superior writing quality
- Sprint 009: Resume Critic Agent implementation
- Sprint 010: Final resume formatting/rendering tools

---

## Key Architecture Decisions

### Decision 1: Gen1 Proof of Concept Focus

**Decision**: Gen1 focuses on highlighting and pruning, NOT rewriting or rephrasing

**Rationale:**
- Finding qualification matches is hardest for humans (gets crosseyed)
- Highlighting relevant achievements is second hardest
- Proving the matching + highlighting workflow validates core system
- Rephrasing can come in gen2 with better models (Claude Sonnet 4.5)
- Simplicity enables faster implementation and validation
- High fidelity maintained through minimal modification

### Decision 2: Use json_resume as Structure Template (Option D)

**Decision**: Use json_resume from session state as primary template, schema file as backup reference

**Rationale:**
- Agent already has json_resume in session state (concrete example)
- Most accurate - uses actual resume structure
- Flexible - handles any resume schema variations
- No file loading complexity or code duplication
- Schema file available for edge cases or uncertainty
- Simplest approach that works

### Decision 3: Reorder Achievements Within Jobs Only

**Decision**: Reorder achievements within each job by relevance, do NOT reorder jobs themselves

**Rationale:**
- Jobs must stay chronological (newest first) - industry standard
- job_id sequence must remain stable (job_001 = oldest always)
- Emphasis happens through achievement ordering, not job ordering
- Maintains resume credibility and readability
- ATS systems expect chronological order

### Decision 4: Prune Irrelevant Certifications Only

**Decision**: Remove completely irrelevant certifications, keep most recent first

**Rationale:**
- Irrelevant certifications dilute focus
- Recent certifications show current expertise
- Pruning creates space for relevant content
- Gen1 keeps it simple - just remove obvious mismatches
- Professional summary stays as-is (gen1 simplicity)

### Decision 5: No Rephrasing in Gen1

**Decision**: Preserve all original wording, no rephrasing or rewriting

**Rationale:**
- High fidelity requirement (no fabrication)
- Original wording represents candidate's actual experience
- Rephrasing risks changing meaning or introducing errors
- Gen2 with Claude Sonnet 4.5 better suited for nuanced rewriting
- Emphasis through ordering sufficient for gen1 proof of concept

### Decision 6: Iteration Tracking

**Decision**: Track iteration number (01-05) and handle critic feedback for subsequent iterations

**Rationale:**
- Critic owns the write-critique loop (max 5 iterations)
- Writer creates candidate_01, then Critic reviews
- Critic calls Writer again with feedback (creates candidate_02, 03, 04, 05)
- Iteration tracking enables improvement cycle
- Max 5 prevents infinite loops

---

## Files Created

### New Files (1 file)

1. **docs/sprints/sprint_008_plan.md**
   - This comprehensive plan document
   - Follows Sprint 004-007 format

---

## Files Modified

### Agent Updates (1 file)

1. **src/agents/resume_writing_agent.py**
   - Replaced placeholder instruction with production implementation
   - Added achievement reordering logic
   - Added certification pruning logic
   - Added iteration tracking and critic feedback handling
   - Added session state tool function
   - Added torch-passing to Resume Critic Agent
   - Rich error handling

### Documentation Updates (1 file)

2. **README.md**
   - Updated Sprint 008 status to complete
   - Marked Sprint 009 as next

---

## Resume Writing Agent Workflow

### First Iteration (resume_candidate_01)

```
Step 1: Called by Qualifications Matching Agent
         |
Step 2: Read from session state
         ├─→ json_resume (original resume structure)
         ├─→ json_job_description (job requirements)
         └─→ quality_matches (validated matches with job_id context)
         |
Step 3: Analyze quality_matches
         └─→ Identify which jobs (job_ids) have matching qualifications
         |
Step 4: Reorder achievements within each job
         ├─→ For jobs with matches: relevant achievements first
         └─→ For jobs without matches: keep original order
         |
Step 5: Prune certifications
         ├─→ Keep most recent first
         └─→ Remove completely irrelevant certifications
         |
Step 6: Preserve structure
         ├─→ Maintain chronological job order (newest first)
         ├─→ Preserve job_id sequence (job_001 = oldest)
         ├─→ Keep all original wording (no rephrasing)
         └─→ Follow json_resume structure exactly
         |
Step 7: Save to session state
         └─→ Call save_resume_candidate_to_session(candidate_json, "01")
         |
Step 8: Pass torch to Resume Critic Agent
         └─→ Call resume_critic_agent for review
```

### Subsequent Iterations (resume_candidate_02 through 05)

```
Step 1: Called by Resume Critic Agent with feedback
         |
Step 2: Read from session state
         ├─→ json_resume (original)
         ├─→ json_job_description (requirements)
         ├─→ quality_matches (validated matches)
         ├─→ resume_candidate_XX (previous iteration)
         └─→ critic_issues_XX (feedback from Critic)
         |
Step 3: Incorporate critic feedback
         └─→ Address issues identified in critic_issues_XX
         |
Step 4: Create improved candidate
         ├─→ Apply same reordering and pruning logic
         └─→ Incorporate feedback adjustments
         |
Step 5: Save next iteration
         └─→ Call save_resume_candidate_to_session(candidate_json, "02/03/04/05")
         |
Step 6: Pass torch back to Resume Critic Agent
         └─→ Return for next review (or final if iteration 5)
```

---

## What Writer DOES Do (Gen1)

### Achievement Reordering Within Jobs

**Logic:**
1. For each job in work_history
2. Check if job_id appears in quality_matches resume_source field
3. If job has matches:
   - Reorder achievements to put matched ones first
   - Matched achievement = achievement text contains qualification from quality_matches
   - Use resume_value from quality_matches to identify relevant achievements
4. If job has no matches:
   - Keep achievements in original order

**Example:**
```json
quality_matches: [
  {"resume_source": "job_002.job_achievements", "jd_requirement": "Python"},
  {"resume_source": "job_002.job_technologies", "jd_requirement": "AWS"}
]

job_002 achievements (original order):
1. "Mentored junior developers"
2. "Built Python microservices on AWS"
3. "Improved team processes"

job_002 achievements (reordered):
1. "Built Python microservices on AWS" ← matched
2. "Mentored junior developers"
3. "Improved team processes"
```

### Certification Pruning

**Logic:**
1. Keep certifications in most recent first order
2. Remove completely irrelevant certifications
3. Relevance determined by:
   - Does certification relate to any quality_match?
   - Does certification relate to job description qualifications?
   - Is certification from same domain as job description?

**Example:**
```
Job Description: Backend Software Engineer (Python, AWS)

Certifications (original):
1. AWS Solutions Architect (2024) ← relevant, keep
2. PMP (2023) ← not relevant to backend dev, remove
3. Python Developer Certification (2022) ← relevant, keep
4. CompTIA A+ (2015) ← not relevant, remove

Certifications (pruned):
1. AWS Solutions Architect (2024)
2. Python Developer Certification (2022)
```

### Structure Preservation

**What stays exactly the same:**
- Contact information (all fields)
- Professional summary (no changes in gen1)
- Job titles, companies, dates (factual data)
- Job summaries (no rephrasing in gen1)
- Achievement wording (no rephrasing in gen1)
- Education (preserve all)
- Skills section (preserve structure in gen1)
- Job order (chronological, newest first)
- job_id sequence (job_001 = oldest, always)

---

## What Writer DOES NOT Do (Gen1)

### NO Rephrasing
- Do NOT rewrite achievement text
- Do NOT change wording to add keywords
- Do NOT modify job summaries
- Preserve original candidate's voice

### NO Adding Content
- Do NOT add achievements not in original resume
- Do NOT fabricate experience
- Do NOT infer unstated qualifications
- High fidelity requirement

### NO Job Reordering
- Do NOT change chronological order
- Do NOT move most relevant job to top
- Newest job always first, oldest last
- job_id sequence immutable

### NO Summary Modification (Gen1)
- Do NOT rewrite professional summary
- Do NOT create new summary
- Gen2 will handle summary optimization
- Keep original for gen1

### NO Skills Reordering (Gen1)
- Do NOT reorder skills by relevance
- Keep original skills structure
- Gen2 will handle skills optimization
- Simplicity for gen1

---

## Schema Reference Strategy (Option D)

### Primary Template: json_resume

The agent uses json_resume from session state as the structure template:
- Concrete example of actual resume
- Shows exact field names and nesting
- Demonstrates which fields are present/absent
- Most accurate representation

### Backup Reference: resume_schema_core.json

For edge cases or uncertainty:
- Authoritative source for field requirements
- Documents optional vs required fields
- Provides structure clarification
- Located at src/schemas/resume_schema_core.json

### Instruction Language

"Create resume_candidate following the EXACT structure of json_resume from session state. Preserve all fields and nesting. If you encounter any uncertainty about structure or field requirements, reference the schema definition at src/schemas/resume_schema_core.json for clarification."

---

## Iteration and Critic Feedback Handling

### How Iteration Numbering Works

**First call (from Matching Agent):**
- Creates resume_candidate_01
- Passes to Resume Critic Agent

**Subsequent calls (from Critic Agent):**
- Critic includes iteration number in feedback
- Writer reads previous candidate (resume_candidate_XX)
- Writer reads critic issues (critic_issues_XX)
- Writer creates next candidate (resume_candidate_XX+1)
- Maximum 5 iterations total (candidate_01 through candidate_05)

### Reading Critic Feedback

**Critic instruction to Writer:**
"Read critic_issues_02 from session state for feedback on resume_candidate_02"

**Writer response:**
1. Access tool_context.state["critic_issues_02"]
2. Review issues identified by Critic
3. Access tool_context.state["resume_candidate_02"]
4. Understand what needs improvement
5. Create resume_candidate_03 incorporating feedback

### Types of Critic Feedback (Examples)

**Achievement ordering issues:**
"Job 002: Most relevant achievement for Python requirement is buried at position 4, should be position 1"

**Irrelevant content:**
"Certification 'Project Management Professional' not relevant to backend engineering role, should be removed"

**Structure issues:**
"Missing required field job_technologies in job_003"

**Fidelity violations:**
"Achievement text was modified from original, must preserve exact wording"

---

## Session State Keys

### Read by Resume Writing Agent

- **json_resume** (dict): Original structured resume (Sprint 004)
- **json_job_description** (dict): Structured job description (Sprint 005)
- **quality_matches** (list): Validated matches with job_id context (Sprint 007)
- **resume_candidate_XX** (dict): Previous iteration (for iterations 2-5)
- **critic_issues_XX** (dict): Critic feedback (for iterations 2-5)

### Written by Resume Writing Agent

- **resume_candidate_01** through **resume_candidate_05** (dict): Resume iterations in JSON format
- Final iteration becomes **optimized_resume** (set by Critic Agent in Sprint 009)

---

## Implementation Steps

### Step 1: Create Sprint Plan Document ✅
- [x] Create docs/sprints/sprint_008_plan.md
- [x] Follow Sprint 004-007 format
- [x] Document gen1 simplicity focus
- [x] Document fidelity rules and boundaries

### Step 2: Implement Resume Writing Agent ✅
- [x] Create save_resume_candidate_to_session tool function
- [x] Write production instruction with reordering logic
- [x] Add certification pruning logic
- [x] Add iteration tracking logic
- [x] Add critic feedback handling logic
- [x] Add torch-passing to Resume Critic Agent
- [x] Implement rich error handling
- [x] Test syntax validation

### Step 3: Update Documentation ✅
- [x] Update README.md sprint status
- [x] Mark Sprint 009 as next

### Step 4: Git Commit ✅
- [x] Stage all Sprint 008 files
- [x] Create comprehensive commit message
- [x] Commit to repository

---

## Expected Deliverables

### Code Deliverables ✅

- Updated Resume Writing Agent with production implementation
- Achievement reordering logic (within jobs, by relevance)
- Certification pruning logic (remove irrelevant, keep recent first)
- Iteration tracking and critic feedback handling
- Session state tool function
- Structure preservation (json_resume template)
- Torch-passing to Resume Critic Agent
- Rich error handling

### Documentation Deliverables ✅

- Sprint 008 comprehensive plan (this document)
- Gen1 simplicity rationale
- Fidelity rules and boundaries
- Updated README.md

---

## Success Criteria

### Functional ✅

- [x] Successfully reads json_resume, json_job_description, quality_matches from session
- [x] Uses json_resume structure as template
- [x] Reorders achievements within jobs by relevance to quality_matches
- [x] Uses job_id context from resume_source to identify relevant jobs
- [x] Prunes completely irrelevant certifications
- [x] Maintains chronological job order (newest first)
- [x] Preserves job_id sequence (job_001 = oldest)
- [x] NO rephrasing, adding, or rewriting (gen1 fidelity)
- [x] Saves resume_candidate_01 to session state
- [x] Handles critic feedback for iterations 2-5
- [x] Passes torch to Resume Critic Agent
- [x] Rich error messages for failures
- [x] All syntax validation passes

### Quality ✅

- [x] Follows ADK patterns from course notebooks
- [x] Production-quality instruction (not placeholder)
- [x] Gen1 simplicity maintained (no scope creep)
- [x] No emojis in code
- [x] Clear, professional text throughout
- [x] Uses GEMINI_FLASH_MODEL constant

### Architecture ✅

- [x] High fidelity maintained (no fabrication)
- [x] Structure template approach (Option D)
- [x] Iteration tracking for write-critique loop
- [x] Torch-passing to Resume Critic Agent
- [x] Session state pattern maintained
- [x] Gen1 proof of concept validated (matching + highlighting)

---

## Code Patterns Source

All patterns from ADK course notebooks:

- **LlmAgent structure**: Day 1a, Day 2a notebooks
- **Session state management**: Day 3a notebook
- **Tool functions**: Day 2a notebook
- **AgentTool torch-passing**: Day 2a, Day 5a notebooks
- **Iteration handling**: Day 5a notebook (write-critique loop pattern)
- **Factory functions**: Existing codebase pattern
- **Rich error handling**: Course whitepapers and notebooks

---

## Technical Notes

### Achievement Relevance Detection

**How to determine if achievement is relevant:**

1. Extract job_id from quality_matches resume_source
   - Example: "job_002.job_achievements" → job_id is "job_002"

2. For each achievement in that job:
   - Check if achievement text contains any jd_requirement from matching quality_matches
   - Check if achievement text contains resume_value from quality_matches
   - If yes → achievement is relevant, move to top

3. Sort achievements:
   - Relevant achievements first (in original relative order)
   - Non-relevant achievements after (in original relative order)

**Example:**
```json
quality_matches: [
  {
    "jd_requirement": "Python",
    "resume_source": "job_002.job_technologies",
    "resume_value": "Python"
  },
  {
    "jd_requirement": "Microservices",
    "resume_source": "job_002.job_achievements",
    "resume_value": "Built microservices platform"
  }
]

job_002 achievements:
[
  "Mentored 3 junior developers",
  "Built microservices platform using Python", ← relevant (contains Python + microservices)
  "Improved deployment processes",
  "Designed RESTful APIs" ← possibly relevant (architecture)
]

Reordered:
[
  "Built microservices platform using Python", ← relevant to top
  "Mentored 3 junior developers",
  "Improved deployment processes",
  "Designed RESTful APIs"
]
```

### Certification Relevance Detection

**How to determine if certification is irrelevant:**

1. Check if certification relates to any quality_match jd_requirement
2. Check if certification domain aligns with job_description qualifications
3. If no relationship found → completely irrelevant, prune

**Examples:**

Job: Backend Software Engineer (Python, AWS)
- AWS Solutions Architect → relevant (AWS requirement)
- Python Developer Certification → relevant (Python requirement)
- PMP (Project Management) → irrelevant (no management requirement)
- CompTIA A+ (Hardware) → irrelevant (backend software role)

### Iteration Number Tracking

**Detecting iteration number:**

1. Check if critic_issues_XX exists in session state
2. If critic_issues_02 exists → creating candidate_03 (iteration 3)
3. If no critic_issues → creating candidate_01 (first iteration)
4. Maximum iteration is 5 (candidate_05)

**Determining which candidate to read:**

- Creating candidate_02 → read resume_candidate_01 and critic_issues_01
- Creating candidate_03 → read resume_candidate_02 and critic_issues_02
- Pattern: read candidate_XX and critic_issues_XX where XX = current_iteration - 1

### Structure Preservation Implementation

**Approach:**
1. Deep copy json_resume structure
2. Modify only specified fields:
   - work_history[*].job_achievements (reorder)
   - certifications_licenses (prune)
3. All other fields copied as-is
4. Validate output matches resume_schema_core.json structure

**What NOT to copy:**
- Nothing - copy everything, modify minimally

---

## Error Handling

Rich error messages for:
- Missing json_resume, json_job_description, or quality_matches in session state
- Malformed JSON structures
- Invalid iteration numbers (> 5)
- Missing previous candidate when handling critic feedback
- Missing critic_issues when expected
- Structure validation failures
- Session state save failures
- Torch-passing failures

---

## Dependencies

### Runtime Dependencies

- google-adk (already installed)
- Python 3.8+ (already configured)

### Agent Dependencies

- **Qualifications Matching Agent**: Calls Resume Writing Agent (Sprint 007)
- **Resume Critic Agent**: Called by Resume Writing Agent, calls back for iterations (Sprint 009 - next)
- **Resume Ingest Agent**: Provides json_resume (Sprint 004)
- **Job Description Ingest Agent**: Provides json_job_description (Sprint 005)

---

## Future Enhancements (Post-Sprint 008)

### Sprint 009: Resume Critic Agent

- Reviews resume_candidate_XX for issues
- Validates no fabrication occurred
- Checks achievement ordering
- Validates structure compliance
- Creates critic_issues_XX with feedback
- Owns write-critique loop (max 5 iterations)
- Calls Writer again if issues found
- Sets final optimized_resume when done

### Gen2 Additions

- Achievement rephrasing to emphasize keywords
- Professional summary rewriting aligned to job
- Skills section reordering (matched skills first)
- Adding relevant achievements from other jobs
- Claude Sonnet 4.5 for superior writing quality
- Contextual enhancement while maintaining fidelity
- Advanced ATS optimization

---

## References

- **Sprint 007 Plan**: docs/sprints/sprint_007_plan.md (Qualifications Matching Agent)
- **Sprint 006 Plan**: docs/sprints/sprint_006_plan.md (Resume Refiner Agent)
- **Sprint 004 Plan**: docs/sprints/sprint_004_plan.md (resume schema with job_id)
- **Resume Schema**: src/schemas/resume_schema_core.json
- **Job Description Schema**: src/schemas/job_description_schema_core.json
- **ADK Docs**: https://google.github.io/adk-docs/
- **Project Design Document**: Project_Documentation/Capstone Project - Agentic Resume Customization System.md

---

## Lessons Learned

1. **Gen1 simplicity is powerful**: Focus on matching + highlighting validates core workflow without complexity.

2. **Option D template approach works**: Using json_resume as template is simpler than loading schema files.

3. **Iteration tracking enables improvement**: Write-critique loop needs clear iteration numbering (01-05).

4. **Highlighting > Rewriting for gen1**: Reordering achievements and pruning irrelevant content creates emphasis without fabrication risk.

5. **High fidelity through minimal modification**: Preserving original wording maintains candidate's voice and prevents errors.

---

## Sprint Metrics

### Files Changed

- 1 file created (sprint plan)
- 1 file modified (resume_writing_agent.py)
- 1 file updated (README.md)

### Code Quality

- Production-quality implementation
- Gen1 simplicity maintained
- High fidelity preservation
- Rich error handling implemented
- No emojis in code
- Uses GEMINI_FLASH_MODEL constant
- Follows ADK best practices

---

## Git Commit

```
Sprint 008: Implement Resume Writing Agent with Achievement Reordering

Implemented:
- Resume Writing Agent (resume_writing_agent.py)
  - Creates optimized resume candidates (JSON structure)
  - Reorders achievements within jobs by relevance to quality_matches
  - Uses job_id context from resume_source to identify relevant jobs
  - Prunes completely irrelevant certifications
  - Maintains chronological job order and job_id sequence
  - NO rephrasing/adding/rewriting (gen1 high fidelity)
  - Handles critic feedback for iterations 2-5
  - Passes torch to Resume Critic Agent
  - Rich error handling

Gen1 Proof of Concept Focus:
  - Highlighting and pruning (hardest tasks for humans)
  - Validates matching + highlighting workflow
  - High fidelity through minimal modification
  - Rephrasing deferred to gen2 with Claude Sonnet 4.5

Structure Template Approach (Option D):
  - Uses json_resume from session state as template
  - References resume_schema_core.json for edge cases
  - Simplest approach with no file loading complexity

Achievement Reordering:
  - Within each job, relevant achievements first
  - Relevance determined by quality_matches job_id context
  - Preserves original wording (no rephrasing)
  - Maintains relative order within relevant/non-relevant groups

Certification Pruning:
  - Keeps most recent first
  - Removes completely irrelevant certifications
  - Relevance based on quality_matches and job requirements

Iteration Handling:
  - Tracks iteration number (01-05)
  - Reads previous candidate and critic_issues for iterations 2-5
  - Incorporates feedback while maintaining fidelity
  - Maximum 5 iterations (write-critique loop)

Session State Management:
  - save_resume_candidate_to_session() helper function
  - Follows Sprint 003-007 session state pattern

Architecture:
  - High fidelity maintained (no fabrication)
  - Structure preservation with minimal modification
  - Torch-passing to Resume Critic Agent
  - Iteration tracking for write-critique loop

Technology:
  - Google ADK LlmAgent
  - Gemini Flash model
  - AgentTool delegation pattern
```

---

**Sprint 008 Status**: Complete
**Next Sprint**: 009 - Resume Critic Agent
**Actual Duration**: [To be filled upon completion]
