"""Session state tools for reading from shared session state.

These tools allow agents to read data from session state without needing
to pass large data structures as function parameters.
"""

from google.adk.tools.tool_context import ToolContext


def read_from_session(tool_context: ToolContext, key: str) -> dict:
    """Read a value from session state by key.

    Args:
        tool_context: ADK tool context with state access
        key: The session state key to read

    Returns:
        Dictionary with key, value, and found status
    """
    value = tool_context.state.get(key)

    return {
        "key": key,
        "value": value,
        "found": value is not None
    }
