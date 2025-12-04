"""Job Application Agent - Root orchestrator for the resume customization system.

Uses SequentialAgent pattern for automatic session state sharing across all sub-agents.
"""

from google.adk.agents import SequentialAgent


def create_job_application_agent():
    """Create and return the Job Application Agent.

    This is the root orchestrator that coordinates the entire
    resume customization workflow using SequentialAgent.

    SequentialAgent automatically:
    - Passes the same InvocationContext to all sub-agents
    - Shares session state across the entire agent hierarchy
    - Executes sub-agents in order: Application Documents → Resume Refiner

    Returns:
        SequentialAgent: The configured Job Application Agent
    """

    # Import agents here to avoid circular imports
    from src.agents.application_documents_agent import create_application_documents_agent
    from src.agents.resume_refiner_agent import create_resume_refiner_agent

    application_documents_agent = create_application_documents_agent()
    resume_refiner_agent = create_resume_refiner_agent()

    agent = SequentialAgent(
        name="job_application_agent",
        sub_agents=[
            application_documents_agent,
            resume_refiner_agent,
        ],
    )

    return agent
