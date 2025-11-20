# Agentic Resume Customization System

An AI-powered multi-agent system built with Google's Agent Development Kit (ADK) that customizes resumes to match specific job descriptions while maintaining high fidelity to the original resume.

## Project Overview

This system uses a multi-agent architecture with sequential agents, parallel agents, and write-critique loops to optimize resumes for job applications.

### Competition Track
**Concierge Agents** (for Good)

### Key Features
- Multi-agent orchestration (sequential + loop patterns)
- Write-critique iterative improvement loop
- High-fidelity output (no fabricated qualifications)
- Built-in observability with LoggingPlugin
- MCP integration for tools

## System Architecture (Gen1)

```
Job Application Agent (Root Orchestrator)
    ↓
Resume Refiner Agent (Coordinator)
    ↓
Qualifications Matching Agent (Sequential)
    ↓
Resume Writing Agent ←→ Resume Critic Agent (Write-Critique Loop)
    ↓
Optimized Resume Output
```

## Project Structure

```
CAPSTONE/
├── src/
│   ├── agents/
│   │   ├── job_application_agent.py       # Root orchestrator
│   │   ├── resume_refiner_agent.py        # Workflow coordinator
│   │   ├── qualifications_matching_agent.py # Match finder
│   │   ├── resume_writing_agent.py        # Content generator
│   │   └── resume_critic_agent.py         # Quality evaluator
│   ├── config/
│   │   └── model_config.py                # Model & retry configs
│   ├── plugins/
│   │   └── logging_config.py              # Observability setup
│   └── app.py                              # App + Runner setup
├── main.py                                  # Entry point
├── requirements.txt                         # Dependencies
├── .env.template                           # Environment variables template
└── logs/                                    # Log output directory
```

## Setup Instructions for Non-Technical Users

This guide will walk you through setting up the Resume Optimization System step-by-step, even if you're not familiar with programming.

### Step 1: Check Python Installation

First, check if Python is installed on your computer.

**On Windows:**
1. Press `Windows + R`, type `cmd`, and press Enter
2. Type: `python --version` and press Enter
3. You should see something like `Python 3.8.10` or higher

**On Mac/Linux:**
1. Open Terminal
2. Type: `python3 --version` and press Enter
3. You should see something like `Python 3.8.10` or higher

**If Python is not installed:**
- Download from: https://www.python.org/downloads/
- Install with default options
- Make sure to check "Add Python to PATH" during installation

---

### Step 2: Get Your Google API Key

You'll need a free API key to use Google's AI models.

1. Go to: https://aistudio.google.com/app/api-keys
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (it looks like: `AIzaSyD...`)
5. **Keep this key private** - don't share it with anyone!

---

### Step 3: Navigate to the Project Folder

**On Windows (using Command Prompt or PowerShell):**
```cmd
cd E:\_Data\_Education\DataScience\Google_AI_Agents_Intensive\CAPSTONE
```

**On Windows (using WSL) or Mac/Linux:**
```bash
cd /mnt/e/_Data/_Education/DataScience/Google_AI_Agents_Intensive/CAPSTONE
```

*Note: Adjust the path if you saved the project elsewhere.*

---

### Step 4: Create a Virtual Environment

A virtual environment keeps this project's files separate from other Python projects on your computer.

**On Windows (Command Prompt):**
```cmd
python -m venv venv
```

**On Mac/Linux/WSL:**
```bash
python3 -m venv venv
```

This creates a folder called `venv` in your project directory.

---

### Step 5: Activate the Virtual Environment

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**On Mac/Linux/WSL:**
```bash
source venv/bin/activate
```

**✅ Success Check:** Your command prompt should now show `(venv)` at the beginning:
```
(venv) C:\...\CAPSTONE>
```

---

### Step 6: Install Required Software Packages

With the virtual environment activated, install the necessary packages:

```bash
pip install -r requirements.txt
```

This will download and install:
- Google Agent Development Kit (ADK)
- Python-dotenv (for managing your API key)

*This may take a few minutes.*

---

### Step 7: Configure Your API Key

**On Windows (Command Prompt):**
```cmd
copy .env.template .env
notepad .env
```

**On Mac/Linux/WSL:**
```bash
cp .env.template .env
nano .env
```

1. This opens the `.env` file in a text editor
2. Replace `your_api_key_here` with your actual Google API key from Step 2
3. It should look like:
   ```
   GOOGLE_API_KEY=AIzaSyD...your_actual_key...
   ```
4. Save and close the file
   - In Notepad: File → Save, then close
   - In nano: Press `Ctrl+X`, then `Y`, then Enter

**⚠️ Important:** Never commit the `.env` file to Git or share it publicly!

---

### Step 8: Run the Test

Now let's verify everything is working:

```bash
python main.py
```

**What you should see:**
```
🚀 Resume Optimization System - Sprint 001 Test
📦 Creating runner...
✅ Runner configured with InMemorySessionService and LoggingPlugin
🧪 Running basic test query...

[Agent responses will appear here]

✅ Sprint 001 Test Complete!
```

**If you see errors:**
- Make sure your virtual environment is activated (you should see `(venv)`)
- Check that your API key is correctly set in `.env`
- Verify you're in the CAPSTONE folder

---

### Step 9: When You're Done

To exit the virtual environment:

```bash
deactivate
```

**Next time you want to use the system:**
1. Navigate to the CAPSTONE folder (Step 3)
2. Activate the virtual environment (Step 5)
3. Run the program (Step 8)

---

## Quick Reference Card

### Every Time You Use This System:

```bash
# 1. Navigate to project folder
cd /path/to/CAPSTONE

# 2. Activate virtual environment
source venv/bin/activate      # Mac/Linux/WSL
# OR
venv\Scripts\activate.bat     # Windows CMD

# 3. Run the program
python main.py

# 4. When done, deactivate
deactivate
```

---

## Troubleshooting

### "Python is not recognized..."
- Python is not installed or not in your PATH
- Reinstall Python and check "Add to PATH" option

### "pip is not recognized..."
- Try using `python -m pip` instead of just `pip`

### "ModuleNotFoundError: No module named 'google.adk'"
- Your virtual environment is not activated
- Run the activation command from Step 5

### "ValueError: GOOGLE_API_KEY not found..."
- Your `.env` file is missing or incorrect
- Make sure you completed Step 7 correctly
- Check that the `.env` file is in the CAPSTONE folder

### "429 Error" or "Rate limit exceeded"
- You've made too many API requests
- Wait a few minutes and try again
- Check Google AI Studio free tier limits

---

## Need Help?

- Check the [ADK Documentation](https://google.github.io/adk-docs/)
- Ask on the [Kaggle Discord](https://discord.com/invite/kaggle)
- Review troubleshooting in the course FAQs

---

## Observability & Debugging

### Logging

The system uses enhanced logging with multiple log files for different purposes:

- **logs/logger.log** - Main application log (all agent activity)
- **logs/web.log** - ADK web UI log (for future web interface usage)
- **logs/metrics.log** - Metrics-specific log (performance tracking)

Log levels are controlled by the `ENVIRONMENT` variable in `.env`:
- `development`: DEBUG level (detailed logging)
- `production`: INFO level (essential logging only)

### Metrics Tracking (Development Mode Only)

When running in development mode, the system automatically tracks:

**Agent Invocations:**
- Job applications processed
- Resume refinements
- Qualifications matches
- Critic reviews
- Writing generations

**System Operations:**
- Total LLM calls
- Total tool calls
- Total errors

**Performance:**
- Average agent duration
- Individual agent timing
- Slowest/fastest operations

View metrics at the end of each run in the METRICS SUMMARY section.

### Using ADK Web UI for Debugging

The ADK Web UI provides a visual interface for debugging your agents in real-time.

**Setup:**

1. Create an agent folder for the web UI:
```bash
cd /path/to/CAPSTONE
adk create debug-agent --model gemini-2.5-flash-lite --api_key $GOOGLE_API_KEY
```

2. Start the web UI with debug logging:
```bash
adk web --log_level DEBUG
```

3. Open your browser to the URL shown (usually http://localhost:8000)

**Features:**

- **Chat Interface** - Interact with your agent in real-time
- **Events Tab** - See chronological list of all agent actions
- **Trace View** - Visual timeline showing timing for each step
- **Function Calls** - Inspect tool invocations and parameters
- **LLM Requests** - View full prompts sent to the model
- **LLM Responses** - See complete model responses

**Debugging Workflow:**

1. Run your agent through the web UI
2. If something goes wrong, click the **Events** tab
3. Find the problematic step in the timeline
4. Click to expand and see:
   - Input parameters
   - Function calls made
   - LLM requests/responses
   - Error messages
5. Use this information to identify and fix issues

**Tip:** The web UI is especially useful for debugging:
- Agent orchestration flow (which agent calls which)
- Write-critique loop iterations
- Tool parameter passing
- Prompt engineering issues

### Viewing Logs

**Command line:**
```bash
# View main log
cat logs/logger.log

# View last 50 lines
tail -50 logs/logger.log

# Follow log in real-time
tail -f logs/logger.log

# View metrics log
cat logs/metrics.log
```

**In Python:**
```python
# Logs are automatically created when you run main.py
# Metrics summary is displayed at the end of execution
```

---

## Sprint Status

### ✅ Sprint 001: All Agents Basics Defined with Observability Enabled
- [x] Project structure created
- [x] All 5 gen1 agents defined
- [x] LoggingPlugin observability configured
- [x] App + Runner with InMemorySessionService
- [x] Basic test harness working

### ✅ Sprint 002: Full Observability with Context
- [x] Enhanced logging with multiple log files
- [x] Metrics tracking plugin
- [x] Development vs production modes
- [x] Complete observability setup

### ✅ Sprint 003: Job Application Agent + Application Documents Agent
- [x] Job Application Agent fully implemented
- [x] Application Documents Agent with MCP filesystem
- [x] Session state management
- [x] AgentTool delegation pattern
- [x] Sample input documents

### ✅ Sprint 004: Resume Ingest Agent
- [x] Resume Ingest Agent implemented
- [x] Tier 1 core JSON schema
- [x] job_id tracking system (oldest = job_001)
- [x] High-fidelity parsing with no fabrication
- [x] Rich error handling
- [x] Session state integration

### ✅ Sprint 005: Job Description Ingest Agent
- [x] Job Description Ingest Agent implemented
- [x] Structured schema with categorized qualifications (Option B)
- [x] Required vs preferred separation
- [x] Smart categorization for matching optimization
- [x] Company information capture
- [x] Parallel execution with Resume Ingest Agent

### ✅ Sprint 006: Resume Refiner Agent
- [x] Resume Refiner Agent implemented
- [x] Simple orchestrator pattern
- [x] Torch-passing workflow initiation
- [x] Rich error handling with context
- [x] Production-quality instruction

### ✅ Sprint 007: Qualifications Matching Agent
- [x] Qualifications Matching Agent implemented
- [x] Categorized qualification comparison (Option B structure)
- [x] Quality matches with job_id context preservation
- [x] High-threshold validation for inferred matches
- [x] Empties possible_quality_matches after validation
- [x] Torch-passing to Resume Writing Agent

### 🔄 Upcoming Sprints
- Sprint 008: Resume Writing Agent
- Sprint 007: Qualifications Matching Agent
- Sprint 008: Resume Writing Agent
- Sprint 009: Resume Critic Agent
- Sprint 010: Tools implementation
- Sprint 011: Memory artefacts
- Sprint 012: Fixes and Code Review

## Technology Stack

- **Framework**: Google Agent Development Kit (ADK)
- **Models**: Gemini 2.5 Flash Lite, Gemini 1.5 Pro
- **Session Management**: InMemorySessionService (gen1)
- **Observability**: LoggingPlugin (DEBUG level)
- **Tools**: MCP (to be implemented in later sprints)

## Development

### Logging
Logs are saved to `logs/logger.log` with DEBUG level enabled for development.

### Code Style
- Follow patterns from ADK course notebooks
- Use type hints
- Include docstrings for all functions and classes
- Keep prompts in agent instruction fields

## References

- [ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Python GitHub](https://github.com/google/adk-python)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Project Design Document](Project_Documentation/Capstone%20Project%20-%20Agentic%20Resume%20Customization%20System.md)

## License

[To be determined]

## Authors

[Your name]

---

**Sprint 001 Status**: ✅ Complete
**Next Sprint**: 002 - Full observability with context
