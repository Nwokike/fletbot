"""Path utilities for cross-platform persistence.

Ensures data is stored in the correct system directories:
- Windows: %APPDATA%/fletbot
- Android: /data/user/0/.../files/fletbot
"""

import os
from pathlib import Path

def get_app_data_dir() -> Path:
    """Return the absolute path to the persistent app data directory."""
    # Flet sets these environment variables automatically in production/mobile
    base = os.environ.get("FLET_APP_STORAGE_DATA")
    
    if base:
        app_dir = Path(base) / "fletbot"
    else:
        # Fallback for development (current directory)
        app_dir = Path.home() / ".fletbot"
    
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_memory_dir() -> Path:
    """Return path for agent memory files."""
    path = get_app_data_dir() / "memory"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_sessions_dir() -> Path:
    """Return path for session JSON files."""
    path = get_app_data_dir() / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path
