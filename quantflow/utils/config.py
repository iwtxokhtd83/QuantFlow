"""Configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str = "config/default.yaml") -> dict[str, Any]:
    """Load YAML configuration file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
