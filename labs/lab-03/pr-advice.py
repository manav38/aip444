import argparse
import os
import sys
from datetime import datetime
from typing import Dict, List
from urllib.parse import urlparse

import requests
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI


STUDENT_NAME = "Manav"
STUDENT_ID = "174134239"
MODEL = "google/gemini-2.5-pro"
MAX_DIFF_CHARS = 95000


def print_header() -> None:
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"pr-advice: Developed by {STUDENT_NAME} - {STUDENT_ID}")
    print(f"Run Date: {run_date}")
    print("--------------------------------------------------------------")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explain a GitHub Pull Request using its diff and discussion comments."
    )

    parser.add_argument(
        "pr_url",
        help="Public GitHub Pull Request URL, for example https://github.com/microsoft/vscode/pull/289801",
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

    if parsed.scheme != "https" or parsed.netloc != "github.com":
        print("Error: URL must be a valid https://github.com Pull Request URL")
        sys.exit(1)

    parts = [part for part in parsed.path.split("/") if part]

    if len(parts) != 4 or parts[2] != "pull":
        print("Error: URL must follow this format: https://github.com/OWNER/REPO/pull/NUMBER")
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


def fetch_diff(pr_url: str) -> str:
    diff_url = f"{pr_url}.diff"

    try:
        response = requests.get(diff_url, timeout=30)
    except requests.RequestException as error:
        print("Error fetching PR diff")
        print(error)
        sys.exit(1)

    if response.status_code != 200:
        print(f"Error fetching PR diff: HTTP {response.status_code}")
        sys.exit(1)

    diff_text = response.text

    if len(diff_text) > MAX_DIFF_CHARS:
        print(f"Warning: Diff is {len(diff_text)} characters and will be truncated.")
        diff_text = diff_text[:MAX_DIFF_CHARS] + "\n...[Diff Truncated]..."

    return diff_text


def fetch_comments(owner: str, repo: str, issue_num: str) -> List[Dict[str, str]]:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}/comments"

    headers = {
        "User-Agent": "AIP444-Lab-03",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=30)
    except requests.RequestException as error:
        print("Error fetching GitHub comments")
        print(error)
        sys.exit(1)

    if response.status_code != 200:
        print(f"GitHub API Error: {response.status_code}")
        print("If this is a 403 error, you may have hit GitHub's unauthenticated rate limit.")
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


def format_comments_as_xml(comments: List[Dict[str, str]]) -> str:
    if not comments:
        return "<thread>\n  <no_comments>No issue comments were found for this Pull Request.</no_comments>\n</thread>"

    thread_parts = ["<thread>"]

    for comment in comments:
        username = escape_xml(comment["username"])
        date = escape_xml(comment["date"])
        body = escape_xml(comment["body"])

        thread_parts.append(f'  <comment username="{username}" date="{date}">')
        thread_parts.append(body)
        thread_parts.append("  </comment>")

    thread_parts.append("</thread>")

    return "\n".join(thread_parts)


def build_user_prompt(pr_info: Dict[str, str], diff_text: str, comments_xml: str) -> str:
    diff_block = f"```diff\n{diff_text}\n```"

    return f"""
Analyze this GitHub Pull Request.

PR URL: {pr_info["url"]}
Owner: {pr_info["owner"]}
Repository: {pr_info["repo"]}
Pull Request Number: {pr_info["number"]}

The code changes are provided in a fenced diff block.
The discussion comments are provided inside XML tags.

<diff_section>
{diff_block}
</diff_section>

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
    except Exception as error:
        print(f"Error reading {description}: {path}")
        print(error)
        sys.exit(1)


def call_openrouter(api_key: str, system_prompt: str, user_prompt: str) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0.2,
            max_tokens=8000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return completion.choices[0].message.content.strip()

    except Exception as error:
        print("Error while calling OpenRouter API")
        print(error)
        sys.exit(1)


def main() -> None:
    print_header()

    args = parse_arguments()
    api_key = load_api_key()

    pr_info = parse_github_pr_url(args.pr_url)

    print(f"PR parsed: {pr_info['owner']}/{pr_info['repo']} #{pr_info['number']}")

    diff_text = fetch_diff(pr_info["url"])
    print(f"Diff fetched: {len(diff_text)} characters")

    comments = fetch_comments(pr_info["owner"], pr_info["repo"], pr_info["number"])
    print(f"Comments fetched: {len(comments)}")

    system_prompt = get_file_contents("SYSTEM_PROMPT.md", "System prompt file")
    comments_xml = format_comments_as_xml(comments)
    user_prompt = build_user_prompt(pr_info, diff_text, comments_xml)

    print()
    print("Generating PR advice...")
    print()

    output = call_openrouter(api_key, system_prompt, user_prompt)

    print(output)


if __name__ == "__main__":
    main()