"""Resume Refiner Agent - Coordinates the resume optimization process.

Uses SequentialAgent pattern to coordinate matching and publish workflow.
"""

from google.adk.agents import SequentialAgent


def create_resume_refiner_agent():
    """Create and return the Resume Refiner Agent.

    This agent coordinates the resume optimization process using SequentialAgent:
    1. Qualifications Matching Agent finds preliminary matches
    2. Qualifications Checker Agent validates the matches
    3. Resume Publisher Agent (LoopAgent) runs write-critique loop

    SequentialAgent automatically:
    - Passes the same InvocationContext to all sub-agents
    - Shares session state across matching, checking, and publishing phases
    - Executes sub-agents in order: Matching → Checker → Publisher
    - Propagates errors from sub-agents up the chain

    Returns:
        SequentialAgent: The configured Resume Refiner Agent
    """

    # Import agents needed for sequential workflow
    from src.agents.qualifications_matching_agent import create_qualifications_matching_agent
    from src.agents.qualifications_checker_agent import create_qualifications_checker_agent
    from src.agents.resume_publisher_agent import create_resume_publisher_agent

    qualifications_matching_agent = create_qualifications_matching_agent()
    qualifications_checker_agent = create_qualifications_checker_agent()
    resume_publisher_agent = create_resume_publisher_agent()

    agent = SequentialAgent(
        name="resume_refiner_agent",
        sub_agents=[
            qualifications_matching_agent,
            qualifications_checker_agent,
            resume_publisher_agent,
        ],
    )

    return agent
