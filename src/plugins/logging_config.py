"""Enhanced logging configuration for full observability.

Based on Day 4a notebook best practices for production-ready observability.
Sprint 002: Multiple log files, timestamps, environment-based configuration.
"""

import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment configuration
ENV = os.getenv("ENVIRONMENT", "development")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Clean up old logs at startup
log_files = ["logger.log", "web.log", "metrics.log"]
for log_file in log_files:
    log_path = os.path.join("logs", log_file)
    if os.path.exists(log_path):
        os.remove(log_path)
        print(f"Cleaned up {log_path}")

# Configure logging based on environment
if ENV == "development":
    log_level = logging.DEBUG
    file_log_level = logging.DEBUG
    console_level = logging.DEBUG
    print("Development mode: DEBUG logging enabled")
elif ENV == "production":
    log_level = logging.INFO
    file_log_level = logging.INFO
    console_level = logging.INFO
    print("Production mode: INFO logging enabled")
else:
    # Default to development
    log_level = logging.DEBUG
    file_log_level = logging.DEBUG
    console_level = logging.INFO
    print(f"Unknown environment '{ENV}', defaulting to development mode")

# Enhanced format with timestamps and logger names
log_format = "%(asctime)s - %(name)s - %(filename)s:%(lineno)s - %(levelname)s: %(message)s"

# Configure root logger
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[]  # We'll add handlers manually
)

# Main application log file handler
main_file_handler = logging.FileHandler(os.path.join("logs", "logger.log"))
main_file_handler.setLevel(file_log_level)
main_file_handler.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(main_file_handler)

# Web UI log file handler (for future adk web usage)
web_file_handler = logging.FileHandler(os.path.join("logs", "web.log"))
web_file_handler.setLevel(file_log_level)
web_file_handler.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(web_file_handler)

# Metrics log file handler (for metrics-specific logging)
metrics_file_handler = logging.FileHandler(os.path.join("logs", "metrics.log"))
metrics_file_handler.setLevel(logging.INFO)  # Always INFO for metrics
metrics_file_handler.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(metrics_file_handler)

# Console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setLevel(console_level)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

print(f"Logging configured ({ENV} mode)")
print(f"  Main log: logs/logger.log ({logging.getLevelName(file_log_level)})")
print(f"  Web log: logs/web.log ({logging.getLevelName(file_log_level)})")
print(f"  Metrics log: logs/metrics.log (INFO)")
print(f"  Console: {logging.getLevelName(console_level)}")
