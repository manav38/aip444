import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from tools import read_github_files


STUDENT_NAME = "Manav"
STUDENT_ID = "174134239"
MODEL = "google/gemini-2.5-pro"
MAX_DIFF_CHARS = 95000
MAX_TOOL_ITERATIONS = 5
REQUEST_TIMEOUT = 30


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_github_files",
            "description": (
                "Read one or more complete files from a public GitHub repository. "
                "Use this tool only when the pull request diff does not provide "
                "enough surrounding code to understand an important change. "
                "Prefer exact file paths shown in the diff and use the pull "
                "request head commit SHA as the ref."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "description": (
                            "The GitHub files needed to resolve a specific "
                            "uncertainty in the pull request."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "owner": {
                                    "type": "string",
                                    "description": (
                                        "GitHub repository owner or organization, "
                                        "for example microsoft."
                                    ),
                                },
                                "repo": {
                                    "type": "string",
                                    "description": (
                                        "GitHub repository name, for example vscode."
                                    ),
                                },
                                "path": {
                                    "type": "string",
                                    "description": (
                                        "Exact repository-relative path to the file."
                                    ),
                                },
                                "ref": {
                                    "type": "string",
                                    "description": (
                                        "Branch, tag, or commit SHA. Use the PR "
                                        "head commit SHA for the PR version."
                                    ),
                                },
                            },
                            "required": ["owner", "repo", "path", "ref"],
                            "additionalProperties": False,
                        },
                        "minItems": 1,
                        "maxItems": 4,
                    }
                },
                "required": ["files"],
                "additionalProperties": False,
            },
        },
    }
]


def print_header() -> None:
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"pr-advice: Developed by {STUDENT_NAME} - {STUDENT_ID}")
    print(f"Run Date: {run_date}")
    print("--------------------------------------------------------------")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Explain a GitHub Pull Request using its diff, comments, "
            "and optional GitHub file context."
        )
    )

    parser.add_argument(
        "pr_url",
        help=(
            "Public GitHub Pull Request URL, for example "
            "https://github.com/microsoft/vscode/pull/289801"
        ),
    )

    return parser.parse_args()


def load_api_key() -> str:
    load_dotenv(find_dotenv())

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("Error: OPENROUTER_API_KEY not found")
        sys.exit(1)

    return api_key


def parse_github_pr_url(pr_url: str) -> Dict[str, str]:
    parsed = urlparse(pr_url)

    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        print("Error: URL must be a valid HTTPS GitHub Pull Request URL")
        sys.exit(1)

    parts = [part for part in parsed.path.split("/") if part]

    if len(parts) != 4 or parts[2] != "pull":
        print(
            "Error: URL must follow this format: "
            "https://github.com/OWNER/REPO/pull/NUMBER"
        )
        sys.exit(1)

    owner = parts[0]
    repo = parts[1]
    pr_number = parts[3]

    if not pr_number.isdigit():
        print("Error: Pull Request number must be numeric")
        sys.exit(1)

    return {
        "owner": owner,
        "repo": repo,
        "number": pr_number,
        "url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
    }


def github_headers() -> Dict[str, str]:
    return {
        "User-Agent": "AIP444-Lab-05",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_pr_metadata(
    owner: str,
    repo: str,
    pr_number: str,
) -> Dict[str, str]:
    api_url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/pulls/{pr_number}"
    )

    try:
        response = requests.get(
            api_url,
            headers=github_headers(),
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as error:
        print("Error fetching Pull Request metadata")
        print(error)
        sys.exit(1)

    if response.status_code != 200:
        print(
            f"Error fetching Pull Request metadata: "
            f"HTTP {response.status_code}"
        )
        sys.exit(1)

    data = response.json()

    return {
        "title": data.get("title", ""),
        "state": data.get("state", ""),
        "author": data.get("user", {}).get("login", "unknown"),
        "base_ref": data.get("base", {}).get("ref", "main"),
        "base_sha": data.get("base", {}).get("sha", ""),
        "head_ref": data.get("head", {}).get("ref", ""),
        "head_sha": data.get("head", {}).get("sha", ""),
    }


def fetch_diff(pr_url: str) -> str:
    diff_url = f"{pr_url}.diff"

    try:
        response = requests.get(
            diff_url,
            headers={"User-Agent": "AIP444-Lab-05"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as error:
        print("Error fetching PR diff")
        print(error)
        sys.exit(1)

    if response.status_code != 200:
        print(f"Error fetching PR diff: HTTP {response.status_code}")
        sys.exit(1)

    diff_text = response.text

    if len(diff_text) > MAX_DIFF_CHARS:
        original_length = len(diff_text)

        print(
            f"Warning: Diff is {original_length} characters and "
            f"will be truncated to {MAX_DIFF_CHARS}."
        )

        diff_text = (
            diff_text[:MAX_DIFF_CHARS]
            + "\n\n[Diff truncated by the application]"
        )

    return diff_text


def fetch_comments(
    owner: str,
    repo: str,
    issue_num: str,
) -> List[Dict[str, str]]:
    api_url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/issues/{issue_num}/comments"
    )

    try:
        response = requests.get(
            api_url,
            headers=github_headers(),
            params={"per_page": 100},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as error:
        print("Error fetching GitHub comments")
        print(error)
        sys.exit(1)

    if response.status_code != 200:
        print(f"GitHub API Error: HTTP {response.status_code}")
        sys.exit(1)

    comments_json = response.json()

    return [
        {
            "username": item.get("user", {}).get("login", "unknown"),
            "body": item.get("body", ""),
            "date": item.get("updated_at", ""),
        }
        for item in comments_json
    ]


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_comments_as_xml(
    comments: List[Dict[str, str]],
) -> str:
    if not comments:
        return (
            "<thread>\n"
            "  <no_comments>"
            "No issue comments were found for this Pull Request."
            "</no_comments>\n"
            "</thread>"
        )

    thread_parts = ["<thread>"]

    for comment in comments:
        username = escape_xml(comment["username"])
        date = escape_xml(comment["date"])
        body = escape_xml(comment["body"])

        thread_parts.append(
            f'  <comment username="{username}" date="{date}">'
        )
        thread_parts.append(body)
        thread_parts.append("  </comment>")

    thread_parts.append("</thread>")

    return "\n".join(thread_parts)


def build_user_prompt(
    pr_info: Dict[str, str],
    metadata: Dict[str, str],
    diff_text: str,
    comments_xml: str,
) -> str:
    pr_url = pr_info["url"]
    owner = pr_info["owner"]
    repo = pr_info["repo"]
    pr_number = pr_info["number"]

    title = metadata["title"]
    state = metadata["state"]
    author = metadata["author"]
    base_ref = metadata["base_ref"]
    base_sha = metadata["base_sha"]
    head_ref = metadata["head_ref"]
    head_sha = metadata["head_sha"]

    diff_block = f"```diff\n{diff_text}\n```"

    return f"""
Analyze the following GitHub Pull Request.

# Pull Request Information

PR URL: {pr_url}
Repository owner: {owner}
Repository: {repo}
Pull Request number: {pr_number}
Title: {title}
State: {state}
Author: {author}
Base branch: {base_ref}
Base commit SHA: {base_sha}
Head branch: {head_ref}
Head commit SHA: {head_sha}

When reading files as they exist in this Pull Request, use the
following head commit SHA as the ref:

{head_sha}

# Code Changes

<diff_section>
{diff_block}
</diff_section>

# Pull Request Discussion

<comments_section>
{comments_xml}
</comments_section>
""".strip()


def get_file_contents(path: str, description: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: {description} not found: {path}")
        sys.exit(1)
    except OSError as error:
        print(f"Error reading {description}: {path}")
        print(error)
        sys.exit(1)


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
) -> str:
    if tool_name != "read_github_files":
        return (
            f"Error: Unknown tool '{tool_name}'. "
            "The only available tool is read_github_files."
        )

    files = arguments.get("files")

    if not isinstance(files, list):
        return (
            "Error: read_github_files requires a files array. "
            "Each item must contain owner, repo, path, and ref."
        )

    return read_github_files(files)


def call_openrouter_with_tools(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    for iteration in range(1, MAX_TOOL_ITERATIONS + 1):
        print(f"LLM iteration: {iteration}")

        try:
            completion = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
                max_tokens=8000,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as error:
            print("Error while calling OpenRouter API")
            print(error)
            sys.exit(1)

        assistant_message = completion.choices[0].message
        tool_calls = assistant_message.tool_calls

        assistant_entry: Dict[str, Any] = {
            "role": "assistant",
            "content": assistant_message.content or "",
        }

        if tool_calls:
            assistant_entry["tool_calls"] = [
                tool_call.model_dump(exclude_none=True)
                for tool_call in tool_calls
            ]

        messages.append(assistant_entry)

        if not tool_calls:
            if not assistant_message.content:
                return "Error: The model returned no final analysis."

            return assistant_message.content.strip()

        print(f"Tool calls requested: {len(tool_calls)}")

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            raw_arguments = tool_call.function.arguments

            print(f"Calling tool: {tool_name}")
            print(f"Arguments: {raw_arguments}")

            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError as error:
                tool_result = (
                    "Error: Tool arguments were not valid JSON. "
                    f"Details: {error}"
                )
            else:
                try:
                    tool_result = execute_tool(
                        tool_name,
                        arguments,
                    )
                except Exception as error:
                    tool_result = (
                        "Error: Tool execution failed unexpectedly. "
                        f"Details: {error}"
                    )

            print(
                f"Tool result length: "
                f"{len(tool_result)} characters"
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

    return (
        "Error: Maximum tool-calling iterations reached before "
        "the model produced a final analysis."
    )


def main() -> None:
    print_header()

    args = parse_arguments()
    api_key = load_api_key()

    pr_info = parse_github_pr_url(args.pr_url)

    print(
        f"PR parsed: {pr_info['owner']}/"
        f"{pr_info['repo']} #{pr_info['number']}"
    )

    metadata = fetch_pr_metadata(
        pr_info["owner"],
        pr_info["repo"],
        pr_info["number"],
    )

    print(f"PR head commit: {metadata['head_sha']}")

    diff_text = fetch_diff(pr_info["url"])
    print(f"Diff fetched: {len(diff_text)} characters")

    comments = fetch_comments(
        pr_info["owner"],
        pr_info["repo"],
        pr_info["number"],
    )
    print(f"Comments fetched: {len(comments)}")

    system_prompt = get_file_contents(
        "SYSTEM_PROMPT.md",
        "System prompt file",
    )

    comments_xml = format_comments_as_xml(comments)

    user_prompt = build_user_prompt(
        pr_info,
        metadata,
        diff_text,
        comments_xml,
    )

    print()
    print("Generating PR advice with tool access...")
    print()

    output = call_openrouter_with_tools(
        api_key,
        system_prompt,
        user_prompt,
    )

    print()
    print(output)


if __name__ == "__main__":
    main()