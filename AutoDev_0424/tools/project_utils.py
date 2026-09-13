import re
from pathlib import Path


TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yaml", ".yml"}
IGNORED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}


def project_name(project_path: Path) -> str:
    """Return the final component of a project path."""
    return project_path.resolve().name


def scan_project(project_path: Path, max_chars: int = 24_000) -> str:
    """Return a compact source snapshot suitable for an LLM prompt."""
    chunks: list[str] = []
    size = 0
    for path in sorted(project_path.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in IGNORED_PARTS for part in path.relative_to(project_path).parts):
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        chunk = f"\n--- {path.relative_to(project_path)} ---\n{content}"
        if size + len(chunk) > max_chars:
            chunks.append("\n--- snapshot truncated ---\n")
            break
        chunks.append(chunk)
        size += len(chunk)
    return "".join(chunks) or "(empty project)"


def write_project_file(project_path: Path, relative_path: str, content: str) -> Path:
    """Write inside project_path and reject path traversal."""
    root = project_path.resolve()
    destination = (root / relative_path).resolve()
    if root != destination and root not in destination.parents:
        raise ValueError(f"Refusing to write outside project: {relative_path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content.rstrip() + "\n", encoding="utf-8")
    return destination


def extract_python(response: str) -> str:
    """Extract the first fenced Python block, accepting plain code as fallback."""
    match = re.search(r"```(?:python)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    code = match.group(1) if match else response
    code = code.strip()
    if not code:
        raise ValueError("LLM returned empty Python code")
    return code


def clean_markdown(response: str) -> str:
    """Remove an optional outer markdown fence."""
    match = re.fullmatch(r"\s*```(?:markdown|md)?\s*(.*?)```\s*", response, re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else response).strip()
