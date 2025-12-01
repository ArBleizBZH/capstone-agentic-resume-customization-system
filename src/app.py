"""App and Runner setup for the Resume Optimization System.

Based on Day 3a and Day 4a notebook patterns with enhanced observability.
Sprint 002: Environment-based plugin loading with custom metrics.
"""

import os
from dotenv import load_dotenv

from google.adk.apps.app import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.plugins.logging_plugin import LoggingPlugin

from src.agents.job_application_agent import create_job_application_agent
from src.plugins.metrics_plugin import ResumeOptimizationMetricsPlugin

# Load environment variables
load_dotenv()

# Environment configuration
ENV = os.getenv("ENVIRONMENT", "development")


def create_app():
    """Create and configure the ADK App.

    Returns:
        tuple: (App, metrics_plugin or None)
            - App: Configured application with root agent and plugins
            - metrics_plugin: ResumeOptimizationMetricsPlugin instance if in development, None otherwise
    """

    # Create the root agent
    root_agent = create_job_application_agent()

    # Configure plugins based on environment
    plugins = [LoggingPlugin()]  # Always include base logging
    metrics_plugin = None

    if ENV != "production":
        # Add custom metrics plugin for development observability
        metrics_plugin = ResumeOptimizationMetricsPlugin()
        plugins.append(metrics_plugin)
        print(f"Development plugins loaded: LoggingPlugin, ResumeOptimizationMetricsPlugin")
    else:
        print(f"Production plugins loaded: LoggingPlugin")

    # Create the App with plugins
    app = App(
        name="resume_optimizer_app",
        root_agent=root_agent,
        plugins=plugins,
    )

    return app, metrics_plugin


async def create_runner(initial_state: dict):
    """Create and configure the Runner with session service.

    Plugins are configured in the app.

    Returns:
        tuple: (Runner, metrics_plugin or None, session_id)
            - Runner: Configured runner with InMemorySessionService
            - metrics_plugin: ResumeOptimizationMetricsPlugin instance if in development, None otherwise
            - session_id: ID of the session with initial state
    """

    # Create the app with plugins
    app, metrics_plugin = create_app()

    # Create session service (InMemorySessionService for gen1)
    session_service = InMemorySessionService()

    # Create a session with initial state (async operation)
    session = await session_service.create_session(
        app_name="resume_optimizer_app",
        user_id="default_user",
        state=initial_state
    )

    # Create runner
    runner = Runner(
        app=app,
        session_service=session_service,
    )

    print(f"Runner configured ({ENV} mode) with InMemorySessionService")

    return runner, metrics_plugin, session.id
