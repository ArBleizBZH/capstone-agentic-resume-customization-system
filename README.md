
## `README.md` Template: Agentic Resume Customization System

### Agentic Resume Customization System

**Competition Track:** Concierge Agents  (for Good)

This project implements a multi-agent AI system designed to automate and optimize the process of tailoring a job applicant's resume to a specific job description. By employing a self-correction loop, the system enforces high-fidelity, highly relevant output, significantly reducing the time required to optimize resumes for job applications.

### 1. Problem & Solution

#### Problem

Job applicants face a time-intensive and laborious process of manually customizing a generic resume for every specific job description (JD). This friction limits the volume and quality of applications, hindering re-employment efforts.

#### Solution

The **Agentic Resume Customization System** automates this process using a coordination of specialized AI agents. The system ingests a candidate's resume and a target JD, processes the information into a standardized format, and runs an optimization cycle to produce a final, high-fidelity resume with maximized relevance to the JD.

**Value Proposition:**

  * **Time Savings:** Estimated savings of **4+ hours** per application customization.
  * **Accuracy Guarantee:** The system is designed to produce a **high-accuracy output** (no made-up qualifications), enforced by the final Critic Agent.

###  2. System Architecture

The system is built as a sequential, multi-agent pipeline using the **Google Agent Development Kit (ADK)**.

#### Architecture Diagram

*(Embed the diagram here. In a GitHub README, you would link to or embed the image file:* `![Agentic Resume Optimizer Diagram](Agentic Resume Optimizer.drawio.png)`*)*

*(Insert your **Agentic Resume Optimizer.drawio.png** here)*

#### Key Agents and Workflow

1.  **Job Application Agent:** Orchestrator that initiates and manages the entire process.
2.  **Ingestion Agents (Resume/JD):** Convert raw documents (PDF/Markdown) into standardized JSON structures (`JSON Resume`, `JSON JD`).
3.  **Qualifications Matching Agent:** Compares JSON structures to identify definite and possible matches between candidate skills/achievements and JD requirements.
4.  **Resume Writing Agent (Creator):** Generates the optimized resume based on the identified matches.
5.  **Resume Critic Agent (Validator):** **The core of the system.** Uses a powerful model (**Gemini 2.5 Pro**) to critically review the optimized resume for:
      * **Fidelity:** Verifying all data is truthful to the original resume.
      * **Optimization:** Ensuring maximal relevance to the JD.
      * *This agent implements the **Write-Critique Self-Correction Loop**, requesting a re-write if any issues are detected.*

#### Technical Principles

  * **Development Kit:** Built using the **Agent Development Kit (ADK)**.
  * **Data Management:** All intermediate data artifacts (JSON, match lists, candidate resume) are managed via **Session Memory**, simplifying state and data passing between agents.
  * **Tooling:** Utilizes custom tools for document I/O (e.g., `read_pdf`, `write_md`).
  * **Observability:** Logging, tracing, and metrics are implemented from the start for debugging and performance monitoring.

###  3. Getting Started (Setup & Installation)

These instructions are for setting up the environment and running the agent.

#### Prerequisites

  * Python 3.10+
  * A Google API Key with access to the Gemini family models.

#### Installation

1.  Clone the repository:
    ```bash
    git clone [Your Repository URL Here]
    cd agentic-resume-customization-system
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set your API key as an environment variable:
    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY"
    ```

#### How to Run

To start the Agentic Resume Customization System:

```bash
python main.py --resume_path="./data/my_generic_resume.pdf" --jd_path="./data/target_job_description.txt"
```

The final optimized resume will be saved to `./output/optimized_resume_[TIMESTAMP].md`.

###  4. Submission & References

| Artifact | Location |
| :--- | :--- |
| **Code Repository** | [This GitHub URL] |
| **Project Write-up** | [Kaggle Write-up URL] |
| **Video Demonstration** | [YouTube/Drive URL] |

**Technical References:**

  * ADK Documentation: `https://google.github.io/adk-docs/`
  * ADK Python Library: `https://github.com/google/adk-python`
