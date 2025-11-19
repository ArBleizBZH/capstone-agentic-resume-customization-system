"""Model configuration for all agents.

Based on Day 1a notebook patterns for retry configuration and model setup.
"""

import os
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retry configuration for API calls
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Model configurations (from Day 1a notebook)
GEMINI_FLASH_MODEL = "gemini-2.5-flash-lite"
GEMINI_PRO_MODEL = "gemini-2.5-flash-lite"  # Using same model for now

# API Key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not found in environment. "
        "Please add it to your .env file or set it as an environment variable."
    )
