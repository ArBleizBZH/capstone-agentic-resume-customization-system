"""Main entry point for the Resume Optimization System.

Sprint 012: End-to-end integration test with full workflow execution.
Based on Day 1a, Day 3a, and Day 4a notebook patterns.
"""
from pathlib import Path
import os
import asyncio
from src.plugins import logging_config  # Initialize logging
from src.app import create_runner
from pathlib import Path
#from google.adk.sessions import SessionState
#from google.adk.sessions.session_state import SessionState

# CONFIG
# Use home directory path (no /mnt/) for WSL compatibility
BASE_DIR = Path(os.getcwd())

# Query for the filenames
#TODO: Add input for file names
RESUME = "resume.md"
JOB_DESCRIPTION = "job_description.md"

files_info= {
    "resume": str(BASE_DIR / RESUME),
    "job_description": str(BASE_DIR / JOB_DESCRIPTION)
}


def read_file(file_path):
    """Reads the entire content of a file."""
    try:
        # 'r' mode for reading, 'utf-8' is a common and robust encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            # .read() returns the file's entire content as a single string
            content = file.read()
            return content
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' was not found.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while reading '{file_path}': {e}")

def read_files(files_info):
    """Reads the entire content of the files."""
    
    # Initialize an empty dictionary to store all results
    results = {}

    # Extracting the paths using the dictionary keys
    resume_path = files_info["resume"]
    job_description_path = files_info["job_description"]
    
    # loop through files
    for key, file_path in files_info.items():
        # ... process the key and file_path here ...
        print(f"Processing key: {key}, file_path: {file_path}")
        
        try:        
            # Call read_file and store the content in the results dictionary
            file_content = read_file(file_path)
            results[key] = file_content
        except FileNotFoundError as e:
            # Handle the specific error and do NOT save the key to Session State.
            print(f"*** ERROR: File '{file_path}' not loaded for '{key}'. Details: {e}")
        except Exception as e:
            # Handle other, unexpected errors.
            print(f"*** UNEXPECTED ERROR during file load for '{key}': {e}")        
        
    # Return the dictionary containing all file contents
    return results

def load_data():
    """ Load resume and job description data into session state. """

    # Retrieve the files contents
    files_contents = read_files(files_info)
    
    return files_contents

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
    """Main function to run the complete resume optimization workflow."""

    print("\n" + "="*60)
    print("Resume Optimization System - Sprint 012 E2E Test")
    print("="*60 + "\n")

    try:
        # Create a base SessionState object
        #initial_state = SessionState()
        
        # 2. Call load_data() to load the files contents
        pre_loaded_state = load_data()
        
        # Create the runner and get metrics plugin
        print("Creating runner...")
        runner, metrics_plugin, session_id = await create_runner(initial_state=pre_loaded_state)

        # Full workflow test with actual input files
        print("\nRunning full workflow with input files...")

        response = await runner.run_debug(
            "Please optimize my resume for this job application. "
            "Resume file: resume.md. "
            "Job description file: job_description.md.",
            session_id=session_id
        )

        print("\n" + "="*60)
        print("Sprint 012 E2E Test Complete!")
        print("="*60)
        print("\nWorkflow executed.")
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

    except Exception as e:
        print(f"\nError during workflow execution: {e}")
        print(f"Details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
