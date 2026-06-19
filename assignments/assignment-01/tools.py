import os
import subprocess
from pathlib import Path
from typing import Any


MAX_FILE_LINES = 400
MAX_TOOL_CHARS = 20000


def _safe_path(file_path: str) -> Path:
    """
    Convert a user/model-supplied path into a safe local path.

    The tool only reads files inside the current repository folder.
    This prevents accidental access to unrelated system files.
    """
    base_dir = Path.cwd().resolve()
    target_path = (base_dir / file_path).resolve()

    if base_dir not in target_path.parents and target_path != base_dir:
        raise ValueError("Path is outside the current project folder.")

    return target_path


def read_file(
    file_path: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    """
    Read a local source file.

    Optional start_line and end_line are 1-based and inclusive.
    Long results are truncated to protect the LLM context window.
    """
    try:
        path = _safe_path(file_path)
    except ValueError as error:
        return f"Error: {error}"

    if not path.exists():
        return f"Error: File not found: {file_path}"

    if not path.is_file():
        return f"Error: Path is not a file: {file_path}"

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        return f"Error: Could not read file {file_path}: {error}"

    lines = content.splitlines()

    if start_line is not None and start_line < 1:
        return "Error: start_line must be 1 or greater."

    if end_line is not None and end_line < 1:
        return "Error: end_line must be 1 or greater."

    start_index = (start_line - 1) if start_line else 0
    end_index = end_line if end_line else len(lines)

    selected_lines = lines[start_index:end_index]
    was_line_truncated = len(selected_lines) > MAX_FILE_LINES

    if was_line_truncated:
        selected_lines = selected_lines[:MAX_FILE_LINES]

    numbered_lines = [
        f"{start_index + offset + 1}: {line}"
        for offset, line in enumerate(selected_lines)
    ]

    result = "\n".join(
        [
            f"File: {file_path}",
            f"Total lines: {len(lines)}",
            f"Returned lines: {start_index + 1}-{start_index + len(selected_lines)}",
            f"Line truncated: {'yes' if was_line_truncated else 'no'}",
            "",
            *numbered_lines,
        ]
    )

    if len(result) > MAX_TOOL_CHARS:
        result = result[:MAX_TOOL_CHARS] + "\n\n[Tool output truncated by character limit]"

    return result


def ripgrep(search_pattern: str) -> str:
    """
    Search the current repository using ripgrep.

    Returns matching file paths, line numbers, and snippets.
    """
    if not search_pattern.strip():
        return "Error: search_pattern cannot be empty."

    command = [
        "rg",
        "--line-number",
        "--column",
        "--hidden",
        "--glob",
        "!.git",
        "--glob",
        "!.env",
        "--glob",
        "!__pycache__",
        "--glob",
        "!*.pyc",
        search_pattern,
        ".",
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except FileNotFoundError:
        return (
            "Error: ripgrep command 'rg' was not found. "
            "Install ripgrep or add it to PATH."
        )
    except subprocess.TimeoutExpired:
        return "Error: ripgrep search timed out."

    if completed.returncode == 1:
        return f"No matches found for pattern: {search_pattern}"

    if completed.returncode not in (0, 1):
        return (
            f"Error: ripgrep failed with exit code {completed.returncode}\n"
            f"{completed.stderr}"
        )

    output = completed.stdout.strip()

    if len(output) > MAX_TOOL_CHARS:
        output = output[:MAX_TOOL_CHARS] + "\n\n[ripgrep output truncated]"

    return output


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """
    Dispatch model-requested tool calls to local Python functions.
    """
    if tool_name == "read_file":
        return read_file(
            file_path=str(arguments.get("file_path", "")),
            start_line=arguments.get("start_line"),
            end_line=arguments.get("end_line"),
        )

    if tool_name == "ripgrep":
        return ripgrep(
            search_pattern=str(arguments.get("search_pattern", ""))
        )

    return f"Error: Unknown tool requested: {tool_name}"