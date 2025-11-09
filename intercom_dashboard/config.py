import os
from dotenv import load_dotenv

# Load environment variables from a local .env file if present
load_dotenv()

INTERCOM_BEARER_TOKEN: str = os.getenv("INTERCOM_BEARER_TOKEN", "")

# Team configuration
TEAM_ID: int = int(os.getenv("INTERCOM_TEAM_ID", "5480079"))

# SLA thresholds (in minutes)
SLA_FIRST_RESPONSE_MINUTES: int = int(os.getenv("SLA_FIRST_RESPONSE_MINUTES", "15"))

# HTTP/API config
INTERCOM_API_BASE: str = os.getenv("INTERCOM_API_BASE", "https://api.intercom.io").strip()
# Validate API base URL
if not INTERCOM_API_BASE or not INTERCOM_API_BASE.startswith(("http://", "https://")):
	raise ValueError(f"Invalid INTERCOM_API_BASE: {INTERCOM_API_BASE}. Must be a valid HTTP/HTTPS URL.")
REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
PER_PAGE: int = int(os.getenv("PER_PAGE", "150"))

# Dashboard config
REFRESH_INTERVAL_SECONDS: int = int(os.getenv("REFRESH_INTERVAL_SECONDS", "30"))

# Business hours config (local time in America/Los_Angeles by default)
BUSINESS_TZ: str = os.getenv("BUSINESS_TZ", "America/Los_Angeles")
BUSINESS_HOURS_START: int = int(os.getenv("BUSINESS_HOURS_START", "6"))   # inclusive, 6 AM
BUSINESS_HOURS_END: int = int(os.getenv("BUSINESS_HOURS_END", "18"))      # exclusive, 6 PM
BUSINESS_EXCLUDE_WEEKENDS: bool = os.getenv("BUSINESS_EXCLUDE_WEEKENDS", "true").lower() in ("1", "true", "yes", "y")

# Demo mode config
DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes", "y", "on")

# Capacity management config
MAX_CHATS_PER_TSE: int = int(os.getenv("MAX_CHATS_PER_TSE", "5"))
CAPACITY_WARNING_THRESHOLD: float = float(os.getenv("CAPACITY_WARNING_THRESHOLD", "0.8"))  # 80%
CAPACITY_CAUTION_THRESHOLD: float = float(os.getenv("CAPACITY_CAUTION_THRESHOLD", "0.9"))  # 90%
CAPACITY_CRITICAL_THRESHOLD: float = float(os.getenv("CAPACITY_CRITICAL_THRESHOLD", "0.95"))  # 95%
SNOOZED_PROJECTION_HOURS: int = int(os.getenv("SNOOZED_PROJECTION_HOURS", "2"))  # Project 2 hours ahead


