from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"
DEFAULT_MAX_FIX_ROUNDS = 2


def validate_max_fix_rounds(value: Any, source: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{source} must be a non-negative integer")
    return value


def load_max_fix_rounds(config_path: Path) -> int:
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {config_path}")

    tdd = data.get("tdd", {})
    if not isinstance(tdd, dict):
        raise ValueError(f"tdd must be a mapping: {config_path}")

    value = tdd.get("max_fix_rounds", DEFAULT_MAX_FIX_ROUNDS)
    return validate_max_fix_rounds(value, "tdd.max_fix_rounds")
