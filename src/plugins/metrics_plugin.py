"""Custom metrics plugin for Resume Optimization System observability.

Tracks system-specific metrics and provides detailed observability into agent behavior.
Based on Day 4a notebook plugin patterns with all callback types.

Sprint 002: Full observability with complete context.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse


class ResumeOptimizationMetricsPlugin(BasePlugin):
    """Custom plugin for Resume Optimization System observability.

    Tracks:
    - Agent invocation counts by type (job application, refiner, matching, writing, critic)
    - Total LLM calls across all agents
    - Total tool calls
    - Performance metrics (duration per agent)
    - Errors with full context (type, message, stack trace, agent, query)

    Based on CountInvocationPlugin pattern from Day 4a notebook.
    """

    def __init__(self) -> None:
        """Initialize the metrics plugin with all counters and tracking structures."""
        super().__init__(name="resume_optimization_metrics")

        # Agent-specific invocation counters
        self.job_applications_processed: int = 0
        self.resume_refinements: int = 0
        self.qualifications_matches: int = 0
        self.critic_reviews: int = 0
        self.writing_generations: int = 0

        # System-wide operation counters
        self.total_llm_calls: int = 0
        self.total_tool_calls: int = 0
        self.total_agent_calls: int = 0

        # Performance tracking
        self.agent_start_times: Dict[str, datetime] = {}
        self.agent_durations: List[Dict[str, Any]] = []

        # Error tracking
        self.errors: List[Dict[str, Any]] = []

        logging.info("[Metrics] ResumeOptimizationMetricsPlugin initialized")

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        """Track agent invocations and start timing.

        Called before an agent is invoked. Increments agent-specific counters
        and records start time for performance tracking.

        Args:
            agent: The agent about to be invoked
            callback_context: Context information about the callback
        """
        self.total_agent_calls += 1
        agent_name = agent.name.lower()

        # Generate unique key for timing tracking
        timing_key = f"{agent.name}_{self.total_agent_calls}"
        self.agent_start_times[timing_key] = datetime.now()

        # Store timing key in context for later retrieval
        if hasattr(callback_context, 'custom_data'):
            callback_context.custom_data['timing_key'] = timing_key

        # Count agent-specific invocations
        if "job_application" in agent_name:
            self.job_applications_processed += 1
            logging.info(f"[Metrics] Job Application Agent called (total: {self.job_applications_processed})")
        elif "resume_refiner" in agent_name:
            self.resume_refinements += 1
            logging.info(f"[Metrics] Resume Refiner Agent called (total: {self.resume_refinements})")
        elif "qualifications_matching" in agent_name or "matching" in agent_name:
            self.qualifications_matches += 1
            logging.info(f"[Metrics] Qualifications Matching Agent called (total: {self.qualifications_matches})")
        elif "resume_critic" in agent_name or "critic" in agent_name:
            self.critic_reviews += 1
            logging.info(f"[Metrics] Resume Critic Agent called (total: {self.critic_reviews})")
        elif "resume_writing" in agent_name or "writing" in agent_name:
            self.writing_generations += 1
            logging.info(f"[Metrics] Resume Writing Agent called (total: {self.writing_generations})")

        logging.debug(f"[Metrics] Agent '{agent.name}' starting (total agents called: {self.total_agent_calls})")

    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        """Log agent completion and calculate performance timing.

        Called after an agent completes. Calculates duration and logs performance metrics.

        Args:
            agent: The agent that completed
            callback_context: Context information about the callback
        """
        # Retrieve timing key from context
        timing_key = None
        if hasattr(callback_context, 'custom_data') and 'timing_key' in callback_context.custom_data:
            timing_key = callback_context.custom_data['timing_key']

        # Calculate duration if we have start time
        if timing_key and timing_key in self.agent_start_times:
            start_time = self.agent_start_times[timing_key]
            duration = (datetime.now() - start_time).total_seconds()

            # Store duration for metrics summary
            self.agent_durations.append({
                "agent_name": agent.name,
                "duration_seconds": duration,
                "timestamp": start_time.isoformat()
            })

            logging.info(f"[Metrics] Agent '{agent.name}' completed in {duration:.2f}s")

            # Clean up timing data
            del self.agent_start_times[timing_key]
        else:
            logging.debug(f"[Metrics] Agent '{agent.name}' completed (no timing data)")

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> None:
        """Count LLM calls across all agents.

        Called before the LLM model is invoked. Tracks total API calls.

        Args:
            callback_context: Context information about the callback
            llm_request: The request being sent to the LLM
        """
        self.total_llm_calls += 1
        logging.debug(f"[Metrics] LLM call #{self.total_llm_calls}")

    async def after_tool_callback(self, **kwargs) -> None:
        """Count tool uses across all agents.

        Called after a tool is used. Tracks total tool invocations.

        Args:
            **kwargs: Keyword arguments which may include callback_context, tool, etc.
        """
        self.total_tool_calls += 1
        logging.debug(f"[Metrics] Tool call #{self.total_tool_calls}")

    async def on_model_error_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
        error: Exception,
    ) -> Optional[LlmResponse]:
        """Capture errors with full context for debugging.

        Called when an error occurs in the model. Captures comprehensive error
        information including type, message, stack trace, and context.

        Args:
            callback_context: Context information about the callback
            llm_request: The LLM request that resulted in the error
            error: The exception that occurred

        Returns:
            Optional[LlmResponse]: None to use default error handling
        """
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "agent": getattr(callback_context, 'agent_name', 'unknown'),
            "traceback": traceback.format_exc()
        }

        self.errors.append(error_info)

        # Log comprehensive error details
        logging.error(f"""
[ERROR CAPTURED]
Timestamp: {error_info['timestamp']}
Agent: {error_info['agent']}
Error Type: {error_info['error_type']}
Error Message: {error_info['error_message']}
Traceback:
{error_info['traceback']}
        """.strip())

        return None

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all metrics.

        Returns:
            Dictionary containing all tracked metrics organized by category:
            - agents: Agent-specific invocation counts
            - system: System-wide operation counts
            - performance: Timing statistics
            - errors: Error details
        """
        # Calculate performance statistics
        if self.agent_durations:
            durations = [d['duration_seconds'] for d in self.agent_durations]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
        else:
            avg_duration = max_duration = min_duration = 0.0

        return {
            "agents": {
                "job_applications_processed": self.job_applications_processed,
                "resume_refinements": self.resume_refinements,
                "qualifications_matches": self.qualifications_matches,
                "critic_reviews": self.critic_reviews,
                "writing_generations": self.writing_generations,
            },
            "system": {
                "total_agent_calls": self.total_agent_calls,
                "total_llm_calls": self.total_llm_calls,
                "total_tool_calls": self.total_tool_calls,
                "total_errors": len(self.errors),
            },
            "performance": {
                "average_duration_seconds": round(avg_duration, 2),
                "max_duration_seconds": round(max_duration, 2),
                "min_duration_seconds": round(min_duration, 2),
                "agent_durations": self.agent_durations,
            },
            "errors": self.errors
        }
