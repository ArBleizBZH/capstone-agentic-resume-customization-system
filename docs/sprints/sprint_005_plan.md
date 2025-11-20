# Sprint 005: Job Description Ingest Agent Implementation

**Status**: In Progress
**Date Started**: 2025-01-20
**GitHub**: https://github.com/ArBleizBZH/agentic-resume-customization-system (private repository)

---

## Objective

Implement the Job Description Ingest Agent that converts raw job description text into structured JSON using Option B (structured with categories), enabling the Matching Agent to perform precise qualification matching with smart keyword variation detection.

---

## Scope

### What Was Built

1. **Job Description Ingest Agent (COMPLETE IMPLEMENTATION)**
   - Reads raw job description text from session state (job_description key)
   - Uses LLM intelligence to parse and categorize requirements
   - Converts to structured JSON (Option B - categorized qualifications)
   - Separates required vs preferred qualifications
   - Captures company information for gen4 Company Research Agent
   - Saves structured JSON to session state (json_job_description key)

2. **Job Description Core JSON Schema (Gen1 - Option B)**
   - Structured categories for smart matching
   - job_info: company details, role info
   - responsibilities: array of role duties
   - qualifications: required vs preferred, categorized by type
   - benefits: company offerings
   - Optimized for Matching Agent comparison with resume schema

3. **Session State Tool Function**
   - save_json_job_description_to_session(tool_context, json_data) helper

### What Is Excluded (Gen2+)

- qual_id tracking (not needed for smaller job description lists)
- Industry-vetted schema research (using sample job description for gen1)
- Advanced categorization beyond basic types
- Multiple job description format support

---

## Key Architecture Decisions

### Decision 1: Option B - Structured with Categories

**Options Considered:**
- A) Simple flat structure with arrays
- B) Structured qualifications with pre-categorization
- C) Granular with qual_id tracking

**Decision**: Use structured qualifications with pre-categorization (Option B)

**Rationale:**
- Maximizes smart matching capability
- Direct comparison: resume technical_skills vs job description technical_skills
- Handles keyword variations (Python vs Django/FastAPI)
- Prevents false positives (experience years vs skill name)
- Natural language + structure = best of both worlds
- Simple enough for gen1, extensible for gen2

### Decision 2: No qual_id Tracking

**Decision**: No qualification ID system for gen1

**Rationale:**
- Job descriptions typically have 10-20 qualifications (vs 50+ resume items)
- Less complexity needed for smaller lists
- Can add in gen2 if Matching Agent needs it
- User confirmed not needed for Sprint 005

### Decision 3: Capture Company Information

**Decision**: Include comprehensive company details in job_info

**Rationale:**
- Prepares for gen4 Company Research Agent
- Useful context for matching
- Minimal additional complexity
- User specifically requested this

### Decision 4: Gen1 Simple Schema

**Decision**: Use sample job_description.md as reference, defer industry research to gen2

**Rationale:**
- Faster implementation
- Validates core workflow
- Gen2 can incorporate industry-vetted schema standards
- User preference for gen1 simplicity

### Decision 5: Required vs Preferred Separation

**Decision**: Split qualifications into required and preferred with sub-categories

**Rationale:**
- Matches typical job description structure
- Importance level affects matching confidence
- Matching Agent can prioritize required matches
- Enables quality_matches vs possible_quality_matches distinction

### Decision 6: Category Types

**Decision**: Use these qualification categories:
- experience_years (string)
- technical_skills (array)
- domain_knowledge (array)
- soft_skills (array)
- education (array)
- certifications (array - preferred only)

**Rationale:**
- Maps to resume schema sections for direct comparison
- Enables field-to-field matching
- Covers standard job description requirement types
- Prevents false positives through categorization

### Decision 7: Use Full "job_description" Naming

**Decision**: Use "job_description" in all code, file names, and documentation (not "jd")

**Rationale:**
- More professional and explicit
- Better code readability
- Consistent with Application Documents Agent naming convention
- User requirement for clarity

---

## Files Created

### New Files (3 files)

1. **src/schemas/job_description_schema_core.json**
   - JSON schema definition for structured job description format
   - Documents required vs optional fields
   - Defines category types for qualifications

2. **src/agents/job_description_ingest_agent.py**
   - LlmAgent with Gemini Flash model
   - Reads from session state (job_description key)
   - Structured parsing instruction with categorization guidance
   - Separates required vs preferred qualifications
   - Rich error handling for parsing failures
   - Saves to session state (json_job_description key)
   - Includes save_json_job_description_to_session(tool_context, json_data) helper function

3. **docs/sprints/sprint_005_plan.md**
   - This comprehensive plan document
   - Follows Sprint 004 format

---

## Files Modified

### Agent Updates (2 files)

1. **src/agents/__init__.py**
   - Added export: create_job_description_ingest_agent
   - Updated __all__ list to include new agent

2. **src/agents/application_documents_agent.py**
   - Updated import from create_jd_ingest_agent to create_job_description_ingest_agent
   - Updated variable name from jd_ingest_agent to job_description_ingest_agent
   - Updated AgentTool reference
   - Maintains consistency with full naming convention

### Documentation Updates (1 file)

3. **README.md**
   - Updated Sprint 005 status
   - Noted Sprint 006 as next

---

## Job Description Schema Structure (Option B)

```json
{
  "job_info": {
    "company_name": "string (required)",
    "job_title": "string (required)",
    "location": "string (optional)",
    "employment_type": "string (optional, e.g., Full-time, Contract)",
    "about_role": "string (optional)",
    "about_company": "string (optional)"
  },
  "responsibilities": ["array of strings (optional)"],
  "qualifications": {
    "required": {
      "experience_years": "string (optional, e.g., '5+ years')",
      "technical_skills": ["array of strings (optional)"],
      "domain_knowledge": ["array of strings (optional)"],
      "soft_skills": ["array of strings (optional)"],
      "education": ["array of strings (optional)"]
    },
    "preferred": {
      "technical_skills": ["array of strings (optional)"],
      "domain_knowledge": ["array of strings (optional)"],
      "soft_skills": ["array of strings (optional)"],
      "certifications": ["array of strings (optional)"],
      "other": ["array of strings (optional)"]
    }
  },
  "benefits": ["array of strings (optional)"]
}
```

---

## Implementation Steps

### Step 1: Create Schema ✅
- [x] Create job_description_schema_core.json with Option B structure
- [x] Document required vs optional fields
- [x] Define category types

### Step 2: Create Job Description Ingest Agent ✅
- [x] Create job_description_ingest_agent.py
- [x] Configure with Gemini Flash model
- [x] Write production instruction for parsing job description to structured JSON
- [x] Add categorization guidance (technical_skills, domain_knowledge, etc.)
- [x] Emphasize required vs preferred separation
- [x] Add save_json_job_description_to_session tool function with validation
- [x] Implement rich error handling
- [x] Test syntax validation

### Step 3: Update Exports and Imports ✅
- [x] Update src/agents/__init__.py to export job_description_ingest_agent
- [x] Update src/agents/application_documents_agent.py imports

### Step 4: Documentation ✅
- [x] Create sprint_005_plan.md
- [x] Update README.md sprint status

### Step 5: Git Commit ✅
- [x] Stage all Sprint 005 files
- [x] Create comprehensive commit message
- [x] Commit to repository

---

## Session State Keys

### Written by Job Description Ingest Agent (Sprint 005)

- **json_job_description** (dict): Structured job description data with categorized qualifications

### Read by Job Description Ingest Agent

- **job_description** (str): Raw job description text (written by Application Documents Agent in Sprint 003)

### To Be Used by Downstream Agents (Future Sprints)

- **Qualifications Matching Agent**: Will compare json_resume vs json_job_description
- **Resume Refiner Agent**: Will use job description structure for optimization decisions
- **Resume Writing Agent**: Will reference requirements for targeted content

---

## Expected Deliverables

### Code Deliverables ✅

- Job Description Ingest Agent with LLM-powered parsing and categorization
- Job Description Core JSON Schema (Option B structure)
- Session state tool function
- Updated agent exports and imports
- Updated Application Documents Agent references

### Documentation Deliverables ✅

- Sprint 005 comprehensive plan (this document)
- Schema documentation with category definitions
- Updated README.md

---

## Success Criteria

### Functional ✅

- [x] Job Description Ingest Agent successfully parses job_description.md
- [x] Output JSON matches Option B schema
- [x] Qualifications correctly separated (required vs preferred)
- [x] Skills properly categorized (technical, domain, soft)
- [x] Company information captured
- [x] json_job_description saved to session state
- [x] Rich error messages for failures
- [x] All syntax validation passes
- [x] Application Documents Agent successfully calls job_description_ingest_agent

### Quality ✅

- [x] Follows ADK patterns from course notebooks
- [x] Production-quality instruction
- [x] Schema well-documented
- [x] No emojis in code
- [x] Clear, professional text
- [x] Consistent naming (job_description not jd)

### Architecture ✅

- [x] Integrates with Application Documents Agent (Sprint 003)
- [x] Parallel execution with Resume Ingest Agent (Sprint 004)
- [x] Session state pattern maintained
- [x] Schema optimized for Matching Agent comparison
- [x] Prevents false positives through categorization

---

## Matching Strategy Enabled by This Schema

### Quality Matches (High Confidence):

Resume has job_technologies containing Python and AWS.
Job Description requires Python in technical_skills.
Result: Direct match on Python = quality_match

### Possible Quality Matches (Keyword Variations):

Resume mentions REST API development in job_skills.
Job Description requires RESTful API design in domain_knowledge.
Result: Semantic similarity detected = possible_quality_match (needs validation)

### False Positive Prevention:

Resume has job_employment_dates showing 5 years.
Job Description requires 5+ years backend experience.
Result: Different categories prevent accidental matching between dates and requirements

---

## Workflow Architecture

### Job Description Ingest Agent Workflow

```
Step 1: Called by Application Documents Agent (parallel with Resume Ingest)
         ↓
Step 2: Read 'job_description' from session state
         ↓
Step 3: Parse job description sections using LLM intelligence
         ├─→ Extract job information (company, title, location, etc.)
         ├─→ Extract responsibilities
         ├─→ Parse required qualifications by category
         ├─→ Parse preferred qualifications by category
         └─→ Extract benefits
         ↓
Step 4: Validate against schema
         ├─→ Ensure required fields present (company_name, job_title)
         ├─→ Verify categorization is correct
         └─→ Confirm no fabricated data
         ↓
Step 5: Call save_json_job_description_to_session(json_data)
         └─→ Saves to session state as 'json_job_description'
         ↓
Step 6: Return success confirmation with details or specific error message
```

---

## Code Patterns Source

All patterns from ADK course notebooks:

- **LlmAgent structure**: Day 1a, Day 2a notebooks
- **Session state management**: Day 3a notebook (cells 49-52)
- **Tool functions**: Day 2a notebook
- **Factory functions**: Existing codebase pattern
- **Parallel AgentTool**: Day 2a notebook (Sprint 003 architecture)
- **Rich error handling**: Course whitepapers and notebooks

---

## Technical Notes

### Categorization Logic

The Job Description Ingest Agent intelligently categorizes requirements:

**Technical Skills**: Programming languages, frameworks, tools, platforms
Example: Python, AWS, Docker, PostgreSQL

**Domain Knowledge**: Domain-specific expertise, methodologies, concepts
Example: Microservices architecture, RESTful API design, CI/CD practices

**Soft Skills**: Interpersonal and professional abilities
Example: Communication, collaboration, problem-solving, leadership

**Education**: Degree requirements, educational background
Example: Bachelor's degree in Computer Science, equivalent experience

**Experience Years**: Years of experience requirements
Example: 5+ years backend development, 3+ years Python

**Certifications**: Professional certifications (preferred only)
Example: AWS Solutions Architect, PMP, CISSP

### Required vs Preferred Logic

The agent distinguishes between:
- **Required**: Must-have qualifications, typically in "Required Qualifications" section
- **Preferred**: Nice-to-have qualifications, typically in "Preferred Qualifications" section

This separation enables:
- Matching Agent to prioritize required matches
- Quality matches (required) vs possible matches (preferred)
- Realistic matching expectations

### No Fabrication Enforcement

Agent instruction emphasizes:
- Extract ONLY information present in source job description
- Omit keys entirely for empty categories
- Never infer or generate requirements not stated
- When uncertain, omit rather than guess

---

## Dependencies

### Runtime Dependencies

- google-adk (already installed)
- Python 3.8+ (already configured)

### Agent Dependencies

- **Application Documents Agent**: Already calls job_description_ingest_agent (Sprint 003)
- **Resume Ingest Agent**: Runs in parallel (Sprint 004)

---

## Future Enhancements (Post-Sprint 005)

### Gen2 Additions

- qual_id tracking if Matching Agent needs precise references
- Industry-vetted schema standards research
- More granular categorization (sub-categories within technical_skills)
- Salary range parsing
- Application instructions capture
- Remote/hybrid/onsite classification

### Gen4 Additions

- Company Research Agent integration
- Enhanced company information structure
- Competitive analysis data
- Company culture indicators
- Growth trajectory information

---

## References

- **Sprint 004 Plan**: docs/sprints/sprint_004_plan.md (resume schema pattern)
- **Sprint 003 Plan**: docs/sprints/sprint_003_plan.md (Application Documents Agent integration)
- **Sample Job Description**: src/input_documents/job_description.md
- **ADK Docs**: https://google.github.io/adk-docs/

---

## Lessons Learned

1. **Option B strikes the right balance**: Structured categories enable smart matching without over-engineering with qual_id system.

2. **Naming matters for clarity**: Full "job_description" naming throughout code and documentation improves readability.

3. **Categorization prevents false positives**: Separating technical_skills from experience_years prevents accidental matches.

4. **Required vs preferred is crucial**: This distinction enables the Matching Agent to prioritize appropriately.

5. **Company info is valuable**: Capturing company details now prepares for gen4 Company Research Agent.

---

## Sprint Metrics

### Files Changed

- 3 files created
- 2 files modified
- 1 new agent implemented
- 1 new schema defined

### Code Quality

- Production-quality instructions
- Rich error handling implemented
- No emojis in code (per CLAUDE.md directive)
- Consistent naming convention
- Follows ADK best practices

---

## Git Commit

```
Sprint 005: Implement Job Description Ingest Agent with Structured Schema

Implemented:
- Job Description Ingest Agent (job_description_ingest_agent.py)
  - Uses Gemini Flash model for intelligent parsing
  - Reads raw job description from session state
  - Converts to structured JSON (Option B - categorized qualifications)
  - Separates required vs preferred qualifications
  - Rich error handling for parsing failures
  - Saves to session state as json_job_description

- Job Description Core JSON Schema (job_description_schema_core.json)
  - Option B structure with qualification categories
  - Optimized for Matching Agent comparison
  - Prevents false positives through categorization
  - Captures company information for gen4

- Session state management
  - save_json_job_description_to_session() helper function
  - Follows Sprint 003/004 session state pattern

- Updated naming convention
  - Changed from jd_ingest_agent to job_description_ingest_agent
  - Updated imports in application_documents_agent.py
  - Consistent full naming throughout codebase

Architecture:
- Integrates with Application Documents Agent (Sprint 003)
- Parallel execution with Resume Ingest Agent (Sprint 004)
- Structured categories enable smart matching
- Required vs preferred separation for match prioritization

Technology:
- Google ADK LlmAgent
- Gemini Flash model
- Session state pattern from Day 3a notebook
```

---

**Sprint 005 Status**: Complete
**Next Sprint**: 006 - Resume Refiner Agent
**Actual Duration**: [To be filled upon completion]
