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
        App: Configured application with root agent
    """

    # Create the root agent
    root_agent = create_job_application_agent()

    # Create the App
    app = App(
        name="resume_optimizer_app",
        root_agent=root_agent,
        # Future: Add EventsCompactionConfig in Sprint 002 if needed
    )

    return app


def create_runner():
    """Create and configure the Runner with session service and plugins.

    Loads plugins based on environment:
    - development: LoggingPlugin + ResumeOptimizationMetricsPlugin
    - production: LoggingPlugin only

    Returns:
        tuple: (Runner, metrics_plugin or None)
            - Runner: Configured runner with InMemorySessionService
            - metrics_plugin: ResumeOptimizationMetricsPlugin instance if in development, None otherwise
    """

    # Create the app
    app = create_app()

    # Create session service (InMemorySessionService for gen1)
    session_service = InMemorySessionService()

    # Configure plugins based on environment
    plugins = [LoggingPlugin()]  # Always include base logging
    metrics_plugin = None

    if ENV == "development":
        # Add custom metrics plugin for development observability
        metrics_plugin = ResumeOptimizationMetricsPlugin()
        plugins.append(metrics_plugin)
        print(f"Development plugins loaded: LoggingPlugin, ResumeOptimizationMetricsPlugin")
    else:
        print(f"Production plugins loaded: LoggingPlugin")

    # Create runner with plugins
    runner = Runner(
        app=app,
        session_service=session_service,
        plugins=plugins,
    )

    print(f"Runner configured ({ENV} mode) with InMemorySessionService")

    return runner, metrics_plugin
