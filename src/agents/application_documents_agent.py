"""Application Documents Agent - Coordinates document ingestion.

Uses SequentialAgent pattern for automatic session state sharing across ingest agents.
"""

from google.adk.agents import SequentialAgent


def create_application_documents_agent():
    """Create and return the Application Documents Agent.

    This agent coordinates the complete document processing workflow using SequentialAgent:
    1. Resume Ingest Agent converts raw resume from session state to structured resume_dict
    2. Job Description Ingest Agent converts raw job description to structured job_description_dict
    3. Both agents save their results to session state automatically

    SequentialAgent automatically:
    - Passes the same InvocationContext to all sub-agents
    - Shares session state across ingest agents
    - Executes sub-agents in order: Resume Ingest → Job Description Ingest
    - Propagates errors from sub-agents up the chain

    Returns:
        SequentialAgent: The configured Application Documents Agent
    """
    # Import ingest agents
    from src.agents.resume_ingest_agent import create_resume_ingest_agent
    from src.agents.job_description_ingest_agent import create_job_description_ingest_agent

    resume_ingest_agent = create_resume_ingest_agent()
    job_description_ingest_agent = create_job_description_ingest_agent()

    agent = SequentialAgent(
        name="application_documents_agent",
        sub_agents=[
            resume_ingest_agent,
            job_description_ingest_agent,
        ],
    )

    return agent
