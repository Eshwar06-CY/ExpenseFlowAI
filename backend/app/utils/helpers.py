import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

def get_utc_now() -> datetime:
    """Returns the current datetime in UTC timezone."""
    return datetime.now(timezone.utc)

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    """Formats a datetime object to a string format."""
    return dt.strftime(format_str)

def generate_uuid() -> str:
    """Generates a secure UUID string."""
    return str(uuid.uuid4())

def standard_response(
    success: bool,
    data: Optional[Any] = None,
    message: Optional[str] = None,
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns a unified response dictionary format for all endpoints.
    """
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    if error_code is not None:
        response["error_code"] = error_code
    return response
