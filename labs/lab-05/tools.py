from typing import Any
from urllib.parse import quote

import requests


MAX_FILE_LINES = 1000
REQUEST_TIMEOUT = 30


def read_github_files(
    files: list[dict[str, Any]],
    max_lines: int = MAX_FILE_LINES,
) -> str:
    """
    Read one or more raw text files from public GitHub repositories.

    Each file object should contain:
    - owner: GitHub username or organization
    - repo: repository name
    - path: path to the file inside the repository
    - ref: branch, tag, or commit SHA; defaults to main

    Files longer than max_lines are truncated to protect the LLM context window.
    Errors are returned as readable text so the model can adjust its next action.
    """

    if not files:
        return "Error: No GitHub files were provided."

    if max_lines < 1:
        return "Error: max_lines must be at least 1."

    results: list[str] = []

    for index, file_info in enumerate(files, start=1):
        owner = str(file_info.get("owner", "")).strip()
        repo = str(file_info.get("repo", "")).strip()
        path = str(file_info.get("path", "")).strip()
        ref = str(file_info.get("ref", "main")).strip() or "main"

        if not owner or not repo or not path:
            results.append(
                _format_error(
                    index=index,
                    owner=owner or "missing-owner",
                    repo=repo or "missing-repo",
                    path=path or "missing-path",
                    ref=ref,
                    message=(
                        "Missing required information. Each file needs owner, "
                        "repo, and path."
                    ),
                )
            )
            continue

        encoded_owner = quote(owner, safe="")
        encoded_repo = quote(repo, safe="")
        encoded_ref = quote(ref, safe="")
        encoded_path = quote(path.lstrip("/"), safe="/")

        raw_url = (
            f"https://raw.githubusercontent.com/"
            f"{encoded_owner}/{encoded_repo}/{encoded_ref}/{encoded_path}"
        )

        try:
            response = requests.get(
                raw_url,
                headers={"User-Agent": "AIP444-Lab-05"},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.Timeout:
            results.append(
                _format_error(
                    index,
                    owner,
                    repo,
                    path,
                    ref,
                    "The GitHub request timed out. Try again later.",
                )
            )
            continue
        except requests.RequestException as error:
            results.append(
                _format_error(
                    index,
                    owner,
                    repo,
                    path,
                    ref,
                    f"Network request failed: {error}",
                )
            )
            continue

        if response.status_code == 404:
            results.append(
                _format_error(
                    index,
                    owner,
                    repo,
                    path,
                    ref,
                    (
                        "File not found. Verify the repository, file path, and "
                        "ref. New PR files may require the PR head commit SHA."
                    ),
                )
            )
            continue

        if response.status_code in (401, 403):
            results.append(
                _format_error(
                    index,
                    owner,
                    repo,
                    path,
                    ref,
                    (
                        f"GitHub denied the request with HTTP "
                        f"{response.status_code}. The repository may be private "
                        f"or a rate limit may have been reached."
                    ),
                )
            )
            continue

        if response.status_code == 429:
            results.append(
                _format_error(
                    index,
                    owner,
                    repo,
                    path,
                    ref,
                    "GitHub rate limit exceeded. Wait before trying again.",
                )
            )
            continue

        if response.status_code != 200:
            results.append(
                _format_error(
                    index,
                    owner,
                    repo,
                    path,
                    ref,
                    f"GitHub returned HTTP {response.status_code}.",
                )
            )
            continue

        content = response.text
        lines = content.splitlines()
        total_lines = len(lines)
        was_truncated = total_lines > max_lines

        if was_truncated:
            displayed_content = "\n".join(lines[:max_lines])
            displayed_content += (
                f"\n\n[File truncated: showing first {max_lines:,} "
                f"of {total_lines:,} lines]"
            )
        else:
            displayed_content = content

        language = _guess_markdown_language(path)

        results.append(
            "\n".join(
                [
                    f"## File {index}: `{owner}/{repo}/{path}`",
                    "",
                    f"- Ref: `{ref}`",
                    f"- Raw URL: {raw_url}",
                    f"- Total lines: {total_lines}",
                    f"- Truncated: {'yes' if was_truncated else 'no'}",
                    "",
                    f"```{language}",
                    displayed_content,
                    "```",
                ]
            )
        )

    return "\n\n---\n\n".join(results)


def _format_error(
    index: int,
    owner: str,
    repo: str,
    path: str,
    ref: str,
    message: str,
) -> str:
    return "\n".join(
        [
            f"## File {index}: `{owner}/{repo}/{path}`",
            "",
            f"- Ref: `{ref}`",
            f"- Error: {message}",
        ]
    )


def _guess_markdown_language(path: str) -> str:
    extension = path.rsplit(".", 1)[-1].lower() if "." in path else ""

    languages = {
        "py": "python",
        "js": "javascript",
        "jsx": "jsx",
        "ts": "typescript",
        "tsx": "tsx",
        "json": "json",
        "md": "markdown",
        "html": "html",
        "css": "css",
        "scss": "scss",
        "java": "java",
        "cpp": "cpp",
        "cc": "cpp",
        "c": "c",
        "h": "c",
        "cs": "csharp",
        "go": "go",
        "rs": "rust",
        "sh": "bash",
        "yml": "yaml",
        "yaml": "yaml",
        "xml": "xml",
        "sql": "sql",
    }

    return languages.get(extension, "text")