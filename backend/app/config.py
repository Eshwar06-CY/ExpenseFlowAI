# Redirect config to core settings to preserve clean architecture
from app.core.config import settings, Settings

__all__ = ["settings", "Settings"]
