import py_compile
from pathlib import Path


def check_python(project_path: Path) -> tuple[bool, str]:
    """Compile project Python files without adding another linter dependency."""
    errors: list[str] = []
    for path in sorted(project_path.rglob("*.py")):
        if any(part in {".venv", "__pycache__"} for part in path.parts):
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as error:
            errors.append(str(error))
    return (not errors, "\n".join(errors) if errors else "Python syntax check passed")
