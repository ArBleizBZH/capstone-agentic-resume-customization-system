# Sprint 002: Full Observability with Complete Context

**Status**: 🔄 In Progress
**Date Started**: 2025-01-19
**Estimated Duration**: 60-90 minutes

---

## Objective

Implement production-ready observability with enhanced logging, custom metrics plugin, performance tracking, and ADK Web UI integration.

---

## Scope: Option C - Complete Observability Setup

### What Will Be Built

1. **Enhanced Logging Configuration**
   - Timestamps and logger names in format
   - Multiple log files (logger.log, web.log, metrics.log)
   - Log cleanup at startup
   - Environment-based configuration (dev/production)

2. **Custom Metrics Plugin**
   - ResumeOptimizationMetricsPlugin class
   - All callback types (before/after agent, model, tool, error)
   - Agent-specific counters
   - Performance timing
   - Error tracking with full context
   - Metrics summary method

3. **Debug Utilities**
   - Log inspection functions
   - Metrics display helpers
   - Pretty-print formatters

4. **ADK Web UI Integration**
   - Setup documentation
   - Usage guide
   - Debugging workflow

5. **Sprint Documentation**
   - Sprint 001 summary
   - Sprint 002 plan (this document)

---

## Files to Create

### New Files (3 files)

1. **`src/plugins/metrics_plugin.py`**
   - ResumeOptimizationMetricsPlugin class
   - All callback implementations:
     - `before_agent_callback` - Track starts, timing
     - `after_agent_callback` - Track completions, duration
     - `before_model_callback` - Count LLM calls
     - `after_tool_callback` - Count tool uses
     - `on_model_error_callback` - Capture errors with context
   - Agent-specific counters:
     - `job_applications_processed`
     - `resume_refinements`
     - `qualifications_matches`
     - `critic_reviews`
     - `writing_generations`
   - System counters:
     - `total_llm_calls`
     - `total_tool_calls`
   - Performance tracking (start times, durations)
   - Error tracking (list with full context)
   - `get_metrics_summary()` method

2. **`src/utils/__init__.py`** - Utils package init

3. **`src/utils/debug_utils.py`**
   - `print_recent_logs(filename, lines)` - Display recent log entries
   - `print_metrics_summary(metrics)` - Format and display metrics
   - Log file inspection utilities

### Documentation Files (2 files - already created)

4. **`docs/sprints/sprint_001_summary.md`** - Sprint 001 complete summary
5. **`docs/sprints/sprint_002_plan.md`** - This plan

---

## Files to Modify

### Configuration Updates (5 files)

1. **`src/plugins/logging_config.py`**
   - Add enhanced format:
     ```python
     format="%(asctime)s - %(name)s - %(filename)s:%(lineno)s - %(levelname)s: %(message)s"
     ```
   - Implement multiple file handlers:
     - `logs/logger.log` - Main application log
     - `logs/web.log` - ADK web UI log (for future use)
     - `logs/metrics.log` - Metrics-specific log
   - Add log cleanup function:
     ```python
     for log_file in ["logger.log", "web.log", "metrics.log"]:
         if os.path.exists(f"logs/{log_file}"):
             os.remove(f"logs/{log_file}")
     ```
   - Environment-based log levels:
     - `development`: DEBUG
     - `production`: INFO
   - Keep console output with appropriate level

2. **`src/app.py`**
   - Import `ResumeOptimizationMetricsPlugin`
   - Import environment variable
   - Conditional plugin loading:
     ```python
     plugins = [LoggingPlugin()]
     if ENV == "development":
         plugins.append(ResumeOptimizationMetricsPlugin())
     ```
   - Store metrics plugin reference for access in main.py
   - Return both runner and metrics_plugin (if loaded)

3. **`main.py`**
   - Update to receive metrics_plugin from create_runner()
   - Display metrics summary at end of test:
     ```python
     if metrics_plugin:
         metrics = metrics_plugin.get_metrics_summary()
         print_metrics_summary(metrics)
     ```
   - Enhanced output formatting
   - Import debug utilities

4. **`.env.template`**
   - Add `ENVIRONMENT` variable:
     ```
     # Environment (development or production)
     ENVIRONMENT=development
     ```

5. **`README.md`**
   - Add "Observability & Debugging" section
   - Document ADK Web UI setup and usage:
     - How to create ADK agent folder
     - How to run `adk web --log_level DEBUG`
     - How to access the web interface
     - What the Events tab shows
     - How to inspect traces
   - Add "Debugging Workflow" guide
   - Update Quick Reference Card with web UI commands

---

## Implementation Steps

### Step 1: Create Documentation Structure ✅
- [x] Create `docs/sprints/` directory
- [x] Write Sprint 001 summary
- [x] Write Sprint 002 plan

### Step 2: Enhanced Logging Configuration
- [ ] Update `logging_config.py`:
  - Enhanced format with timestamps and logger names
  - Multiple file handlers (logger, web, metrics)
  - Log cleanup function at startup
  - Environment-based log levels
  - Test multi-file logging

### Step 3: Custom Metrics Plugin
- [ ] Create `src/utils/` directory
- [ ] Create `metrics_plugin.py`:
  - Plugin class structure
  - All callback methods
  - Agent-specific counters
  - Performance timing logic
  - Error tracking with full context
  - Metrics summary method
  - Test plugin callbacks

### Step 4: Debug Utilities
- [ ] Create `debug_utils.py`:
  - Log file reader function
  - Metrics formatter function
  - Pretty-print helpers
  - Test utilities

### Step 5: Integration
- [ ] Update `app.py`:
  - Import metrics plugin
  - Environment-based plugin loading
  - Return metrics plugin reference
  - Test plugin loading
- [ ] Update `main.py`:
  - Receive metrics plugin
  - Display metrics summary
  - Enhanced output formatting
  - Test end-to-end
- [ ] Update `.env.template`:
  - Add ENVIRONMENT variable

### Step 6: Documentation
- [ ] Update `README.md`:
  - Add Observability section
  - Add ADK Web UI setup guide
  - Add Debugging Workflow
  - Update Quick Reference
  - Test documentation clarity

### Step 7: Testing & Validation
- [ ] Verify multiple log files created
- [ ] Confirm metrics tracking works
- [ ] Test environment switching (dev/production)
- [ ] Validate all callbacks fire correctly
- [ ] Test error capture
- [ ] Test performance timing
- [ ] Verify metrics summary displays correctly

---

## Code Patterns Source

All patterns from Day 4a Agent Observability notebook:

- **Enhanced logging format**: Section 1.3
- **Custom plugin structure**: Section 3.2
- **All callback types**: Section 3.4
- **Error callbacks**: Best practices from notebook
- **LoggingPlugin usage**: Section 3.4
- **ADK web UI**: Section 2

---

## Expected Deliverables

### Code Deliverables
✅ Enhanced logging with timestamps, logger names, 3 log files
✅ Custom ResumeOptimizationMetricsPlugin with all callbacks
✅ Performance timing for each agent
✅ Error tracking with full context (stack trace, agent, query)
✅ Environment-based configuration (dev/production)
✅ Debug utilities for log inspection
✅ Metrics summary display

### Documentation Deliverables
✅ Sprint 001 summary (complete history)
✅ Sprint 002 plan (this document)
✅ ADK Web UI setup and usage guide
✅ Debugging workflow documentation
✅ Updated README with observability features

---

## Success Criteria

### Functional
- [ ] Multiple log files created in `logs/` directory
- [ ] Custom metrics appear in logs with `[Metrics]` prefix
- [ ] Performance timing logged for each agent (duration in seconds)
- [ ] Errors captured with full context (type, message, stack trace)
- [ ] Metrics summary displays at end of test run
- [ ] Environment variable switches logging levels correctly

### Quality
- [ ] All code follows Day 4a notebook patterns
- [ ] Logging is informative but not overwhelming
- [ ] Metrics provide actionable insights
- [ ] Documentation is clear for non-technical users
- [ ] ADK Web UI integration is well-documented

### Testing
- [ ] Run main.py successfully
- [ ] Verify 3 log files created
- [ ] Check metrics summary shows correct counts
- [ ] Introduce an error and verify it's captured
- [ ] Switch to production mode and verify INFO logging

---

## Metrics to Track

### Agent Invocations
- Job applications processed
- Resume refinements
- Qualifications matches
- Critic reviews
- Writing generations

### System Operations
- Total LLM calls
- Total tool calls
- Total errors
- Average agent duration

### Development Insights
- Which agents are called most frequently?
- Where are errors occurring?
- Which operations are slowest?
- What's the typical execution path?

---

## ADK Web UI Integration

### Setup (to be documented in README)

```bash
# Create agent folder for web UI
adk create resume-agent --model gemini-2.5-flash-lite --api_key $GOOGLE_API_KEY

# Run web UI with debug logging
adk web --log_level DEBUG
```

### Usage (to be documented)

1. **Start web UI** - Opens local server with chat interface
2. **Events Tab** - View chronological agent actions
3. **Trace View** - See timing for each step
4. **Function Calls** - Inspect tool invocations
5. **LLM Requests** - View full prompts sent to model
6. **Debugging** - Identify issues in agent flow

---

## Estimated Timeline

- **Step 1**: Documentation structure - 10 min ✅ COMPLETE
- **Step 2**: Enhanced logging - 15 min
- **Step 3**: Custom metrics plugin - 25 min
- **Step 4**: Debug utilities - 10 min
- **Step 5**: Integration - 15 min
- **Step 6**: Documentation - 15 min
- **Step 7**: Testing - 10 min

**Total**: 60-90 minutes

---

## Risk Mitigation

### Potential Issues

1. **Multiple file handlers conflict**
   - Mitigation: Test logging configuration in isolation first
   - Use proper handler management in logging.basicConfig()

2. **Metrics plugin callbacks not firing**
   - Mitigation: Add debug logging within callbacks
   - Verify plugin is loaded in runner

3. **Environment variable not loading**
   - Mitigation: Test with python-dotenv explicitly
   - Add fallback to "development" if not set

4. **Log files grow too large**
   - Mitigation: Log cleanup at startup
   - Document log rotation for future sprints

---

## Future Enhancements (Post-Sprint 002)

### Gen2 Additions
- Log rotation (prevent files from growing indefinitely)
- Structured logging (JSON format for parsing)
- Cloud Trace integration (if deploying to cloud)
- Metrics export to monitoring systems (Prometheus, Datadog)
- Alert thresholds (error rate, performance degradation)

### Gen3+ Additions
- Real-time metrics dashboard
- Performance benchmarking
- A/B testing framework
- Cost tracking per resume processed

---

## References

- **Day 4a Notebook**: Agent Observability patterns
- **ADK Docs**: https://google.github.io/adk-docs/observability/logging/
- **Plugin Docs**: https://google.github.io/adk-docs/plugins/
- **Sprint 001 Summary**: `docs/sprints/sprint_001_summary.md`

---

## Notes

- This sprint focuses on **developer observability** for debugging gen1
- Production-grade monitoring will be added in gen2
- ADK Web UI is essential for understanding agent flow
- Custom metrics help identify bottlenecks early
- Environment-based config prepares for deployment

---

**Sprint 002 Status**: 🔄 **IN PROGRESS**
**Next Sprint**: 003 - Job Application Agent + Ingest Agents
