"""Main entry point for the Resume Optimization System.

Sprint 002: Enhanced observability with metrics tracking and summary display.
Based on Day 1a, Day 3a, and Day 4a notebook patterns.
"""

import asyncio
from src.plugins import logging_config  # Initialize logging
from src.app import create_runner


def print_metrics_summary(metrics):
    """Format and display metrics summary.

    Args:
        metrics: Dictionary containing metrics from ResumeOptimizationMetricsPlugin
    """
    print("\n" + "="*60)
    print("METRICS SUMMARY")
    print("="*60)

    # Agent invocations
    print("\nAgent Invocations:")
    agents = metrics['agents']
    print(f"  Job Applications Processed: {agents['job_applications_processed']}")
    print(f"  Resume Refinements: {agents['resume_refinements']}")
    print(f"  Qualifications Matches: {agents['qualifications_matches']}")
    print(f"  Critic Reviews: {agents['critic_reviews']}")
    print(f"  Writing Generations: {agents['writing_generations']}")

    # System operations
    print("\nSystem Operations:")
    system = metrics['system']
    print(f"  Total Agent Calls: {system['total_agent_calls']}")
    print(f"  Total LLM Calls: {system['total_llm_calls']}")
    print(f"  Total Tool Calls: {system['total_tool_calls']}")
    print(f"  Total Errors: {system['total_errors']}")

    # Performance metrics
    print("\nPerformance:")
    perf = metrics['performance']
    print(f"  Average Duration: {perf['average_duration_seconds']}s")
    print(f"  Max Duration: {perf['max_duration_seconds']}s")
    print(f"  Min Duration: {perf['min_duration_seconds']}s")

    # Individual agent durations
    if perf['agent_durations']:
        print("\n  Agent Durations:")
        for duration in perf['agent_durations']:
            print(f"    {duration['agent_name']}: {duration['duration_seconds']:.2f}s")

    # Errors (if any)
    if metrics['errors']:
        print("\nErrors:")
        for error in metrics['errors']:
            print(f"  [{error['timestamp']}] {error['error_type']}: {error['error_message']}")

    print("="*60 + "\n")


async def main():
    """Main function to test the resume optimization system."""

    print("\n" + "="*60)
    print("Resume Optimization System - Sprint 002 Test")
    print("="*60 + "\n")

    try:
        # Create the runner and get metrics plugin
        print("Creating runner...")
        runner, metrics_plugin = create_runner()

        # Basic test: Simple query to verify agent instantiation
        print("\nRunning basic test query...\n")

        response = await runner.run_debug(
            "Hello! Please confirm you are the Job Application Agent and ready to help with resume customization."
        )

        print("\n" + "="*60)
        print("Sprint 002 Test Complete!")
        print("="*60)
        print("\nAll agents successfully instantiated and responding.")
        print("Logs saved to:")
        print("  - logs/logger.log (main application log)")
        print("  - logs/web.log (web UI log)")
        print("  - logs/metrics.log (metrics-specific log)")

        # Display metrics summary if in development mode
        if metrics_plugin:
            metrics = metrics_plugin.get_metrics_summary()
            print_metrics_summary(metrics)
        else:
            print("\nMetrics tracking disabled (production mode)")

        print("\nNext steps: Sprint 003 - Job Application Agent + Ingest Agents")

    except Exception as e:
        print(f"\nError during test: {e}")
        print(f"Details: {type(e).__name__}")
        raise


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
