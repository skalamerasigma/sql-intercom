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
INTERCOM_API_BASE: str = os.getenv("INTERCOM_API_BASE", "https://api.intercom.io")
REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
PER_PAGE: int = int(os.getenv("PER_PAGE", "150"))

# Dashboard config
REFRESH_INTERVAL_SECONDS: int = int(os.getenv("REFRESH_INTERVAL_SECONDS", "30"))


