from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuleConfig:
    max_line_length: int = 120
    forbid_print: bool = True
    require_type_hints: bool = True
    forbid_wildcard_import: bool = True


class CodingRuleEngine:
    def __init__(self, config: RuleConfig) -> None:
        self.config = config

    def check(self, code: str) -> list[str]:
        violations: list[str] = []
        lines = code.splitlines()

        for idx, line in enumerate(lines, start=1):
            if len(line) > self.config.max_line_length:
                violations.append(
                    f"Line {idx}: exceeds max line length ({self.config.max_line_length})"
                )
            if "\t" in line:
                violations.append(f"Line {idx}: tab character is not allowed")
            if self.config.forbid_print and "print(" in line:
                violations.append(f"Line {idx}: print() is forbidden by rule")
            if self.config.forbid_wildcard_import and "import *" in line:
                violations.append(f"Line {idx}: wildcard import is forbidden")

        if self.config.require_type_hints:
            for idx, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped.startswith("def "):
                    continue
                if "->" not in stripped:
                    violations.append(f"Line {idx}: function return type hint is required")
                signature = stripped[4 : stripped.find("(")]
                if not signature:
                    violations.append(f"Line {idx}: invalid function declaration")
                params_start = stripped.find("(")
                params_end = stripped.find(")")
                if params_start != -1 and params_end != -1:
                    params = stripped[params_start + 1 : params_end]
                    if params.strip():
                        for part in params.split(","):
                            part = part.strip()
                            if ":" not in part:
                                violations.append(
                                    f"Line {idx}: parameter '{part}' missing type hint"
                                )

        return violations
