"""Version info.

VERSION/BUILD_DATE/BUILD_TIME come from the BUILD_VERSION/BUILD_DATE build-args
the Dockerfile bakes in as env vars (see .github/workflows/build.yml). Outside
Docker (e.g. local runs), VERSION falls back to the repo's VERSION file and
BUILD_DATE/BUILD_TIME fall back to "dev".
"""

import os
from datetime import datetime
from pathlib import Path


def _read_version_file() -> str:
    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    try:
        return version_file.read_text().strip()
    except OSError:
        return "unknown"


VERSION = os.environ.get("BUILD_VERSION") or _read_version_file()

_raw_build_date = os.environ.get("BUILD_DATE", "")
BUILD_DATE = "dev"
BUILD_TIME = ""
if _raw_build_date:
    try:
        _dt = datetime.fromisoformat(_raw_build_date.replace("Z", "+00:00"))
        BUILD_DATE = _dt.strftime("%Y-%m-%d")
        BUILD_TIME = _dt.strftime("%H:%M")
    except ValueError:
        pass
