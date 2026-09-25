import json
import re
from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yaml", ".yml"}
IGNORED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}


@dataclass(frozen=True)
class FileChange:
    path: str
    content: str


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


def parse_file_changes(response: str) -> list[FileChange]:
    """Parse a structured multi-file response from an agent."""
    match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    payload = (match.group(1) if match else response).strip()
    if not payload:
        raise ValueError("LLM returned an empty file change set")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError(f"LLM returned invalid file-change JSON: {error}") from error

    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, list) or not files:
        raise ValueError("File-change JSON must contain a non-empty 'files' list")

    changes: list[FileChange] = []
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("content"), str):
            raise ValueError("Each file change must contain string 'path' and 'content' fields")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or item["path"] in seen:
            raise ValueError(f"Unsafe or duplicate file path: {item['path']}")
        seen.add(item["path"])
        changes.append(FileChange(item["path"], item["content"]))
    return changes


def apply_file_changes(project_path: Path, changes: list[FileChange]) -> list[Path]:
    """Apply validated file changes within a project."""
    return [write_project_file(project_path, change.path, change.content) for change in changes]


def format_file_changes(changes: list[FileChange]) -> str:
    """Render changes as compact, path-delimited context for the next agent."""
    return "".join(f"\n--- {change.path} ---\n{change.content}\n" for change in changes)


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
