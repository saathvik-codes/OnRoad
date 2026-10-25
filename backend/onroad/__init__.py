"""OnRoad backend package."""
import os as _os
from pathlib import Path as _Path

# Local runs: read backend/.env (secrets live there, git-ignored). Variables already set (Render, Docker) win.
_env = _Path(__file__).resolve().parent.parent / ".env"
if _env.is_file():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            _k, _v = _k.strip(), _v.strip()
            if _k in ("DB_PATH", "IMG_CACHE") and _v and not _Path(_v).is_absolute():
                _v = str((_env.parent / _v).resolve())     # relative to backend/, wherever the process starts
            _os.environ.setdefault(_k, _v)
