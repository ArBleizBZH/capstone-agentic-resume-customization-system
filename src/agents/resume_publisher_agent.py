"""Resume Publisher Agent - Controls write-critique loop.

Uses LoopAgent pattern to manage iterative refinement via resume_writing_agent
and resume_critic_agent. Exits when critic approves (escalate=True) or after
max 5 iterations.
"""

from google.adk.agents import LoopAgent


def create_resume_publisher_agent():
    """Create and return the Resume Publisher Agent.

    This LoopAgent orchestrates the write-critique loop:
    - Max 5 iterations
    - Each iteration: Writer creates draft, Critic reviews
    - Exit when Critic sets escalate=True (approved)

    LoopAgent automatically:
    - Passes the same InvocationContext in each iteration
    - Allows state changes to persist across loops
    - Exits early when escalate=True is detected
    - Shares session state with writer and critic agents

    Returns:
        LoopAgent: The configured Resume Publisher Agent
    """
    from src.agents.resume_writing_agent import create_resume_writing_agent
    from src.agents.resume_critic_agent import create_resume_critic_agent

    resume_writing_agent = create_resume_writing_agent()
    resume_critic_agent = create_resume_critic_agent()

    agent = LoopAgent(
        name="resume_publisher_agent",
        max_iterations=5,
        sub_agents=[
            resume_writing_agent,
            resume_critic_agent
        ]
    )

    return agent
