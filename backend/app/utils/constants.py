"""Project-wide constants.

Centralizing default values keeps configuration decisions visible and avoids
scattering hardcoded strings across database, logging, and future service code.
"""

from pathlib import Path

# The backend directory is the stable base for local files such as SQLite DBs.
BACKEND_DIR: Path = Path(__file__).resolve().parents[2]

# SQLite database file used for the MVP. Environment overrides are supported in
# database.py, but this default keeps local setup friction low.
DEFAULT_DATABASE_PATH: Path = BACKEND_DIR / "travel.db"

# Local application logs. The directory is ignored by Git.
LOG_DIR: Path = BACKEND_DIR / "logs"
APP_LOG_PATH: Path = LOG_DIR / "app.log"

# Default logging level for development; can be overridden with LOG_LEVEL.
DEFAULT_LOG_LEVEL: str = "DEBUG"
