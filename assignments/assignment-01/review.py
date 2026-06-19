import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from prompts import (
    JUDGE_SYSTEM_PROMPT,
    MAINTAINABILITY_SYSTEM_PROMPT,
    SECURITY_SYSTEM_PROMPT,
    TOOLS,
)
from tools import execute_tool


REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "google/gemini-2.5-flash")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "google/gemini-2.5-flash")
MAX_TOOL_ITERATIONS = 4


def debug_log(enabled: bool, message: str) -> None:
    if enabled:
        print(message, file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI code review CLI for staged git changes or a specific file."
    )

    parser.add_argument(
        "--file",
        dest="file_path",
        help="Review one specific file instead of staged git changes.",
    )

    parser.add_argument(
        "--output",
        dest="output_path",
        help="Output HTML file path.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print detailed execution logs to stderr.",
    )

    return parser.parse_args()


def load_api_key() -> str:
    load_dotenv(find_dotenv())

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print(
            "Error: OPENROUTER_API_KEY not found in environment or .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    return api_key


def get_client(api_key: str) -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def get_staged_diff() -> str:
    try:
        completed = subprocess.run(
            ["git", "diff", "--staged"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("Error: git was not found. Install git or use --file mode.", file=sys.stderr)
        sys.exit(1)

    if completed.returncode != 0:
        print("Error: Could not read staged git diff.", file=sys.stderr)
        print(completed.stderr, file=sys.stderr)
        sys.exit(1)

    diff = completed.stdout.strip()

    if not diff:
        print("Nothing to review: no staged git changes found.", file=sys.stderr)
        sys.exit(1)

    return diff


def get_file_input(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not path.is_file():
        print(f"Error: Path is not a file: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        print(f"Error: Could not read file {file_path}: {error}", file=sys.stderr)
        sys.exit(1)

    if not content.strip():
        print(f"Nothing to review: file is empty: {file_path}", file=sys.stderr)
        sys.exit(1)

    return content


def build_review_input(args: argparse.Namespace) -> tuple[str, str]:
    if args.file_path:
        content = get_file_input(args.file_path)
        review_input = "\n".join(
            [
                "MODE: File Mode",
                f"FILE: {args.file_path}",
                "",
                "SOURCE CODE:",
                "```",
                content,
                "```",
            ]
        )
        return "File Mode", review_input

    diff = get_staged_diff()
    review_input = "\n".join(
        [
            "MODE: Git Mode",
            "INPUT: staged git diff from `git diff --staged`",
            "",
            "DIFF:",
            "```diff",
            diff,
            "```",
        ]
    )
    return "Git Mode", review_input


def default_output_path() -> str:
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    return f"review-{timestamp}.html"


def parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])

        raise


def normalize_findings(parsed: dict[str, Any]) -> dict[str, Any]:
    if "findings" not in parsed or not isinstance(parsed["findings"], list):
        return {"findings": []}

    normalized = []

    for finding in parsed["findings"]:
        if not isinstance(finding, dict):
            continue

        normalized.append(
            {
                "path": str(finding.get("path", "unknown")),
                "line": int(finding.get("line", 0) or 0),
                "severity": str(finding.get("severity", "warn")),
                "category": str(finding.get("category", "general")),
                "description": str(finding.get("description", "")),
            }
        )

    return {"findings": normalized}


def force_final_json(
    client: OpenAI,
    reviewer_name: str,
    messages: list[dict[str, Any]],
    temperature: float,
    debug: bool,
) -> dict[str, Any]:
    debug_log(
        debug,
        f"[{reviewer_name}] Max tool iterations reached. Forcing final JSON response.",
    )

    messages.append(
        {
            "role": "user",
            "content": (
                "Stop calling tools now. Based only on the original input and the tool "
                "results already provided, return the final JSON review. Return only valid "
                "JSON in this exact shape: "
                '{"findings":[{"path":"file.py","line":1,"severity":"warn",'
                '"category":"category","description":"description"}]}. '
                "Do not call any more tools."
            ),
        }
    )

    try:
        completion = client.chat.completions.create(
            model=REVIEWER_MODEL,
            temperature=temperature,
            messages=messages,
            tool_choice="none",
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content or '{"findings": []}'
        parsed = normalize_findings(parse_json_content(content))

    except Exception as error:
        debug_log(debug, f"[{reviewer_name}] Forced JSON failed: {error}")
        parsed = {
            "findings": [
                {
                    "path": "unknown",
                    "line": 0,
                    "severity": "warn",
                    "category": "tooling",
                    "description": "Reviewer failed to produce valid JSON after tool use.",
                }
            ]
        }

    debug_log(
        debug,
        f"[{reviewer_name}] Raw JSON findings:\n{json.dumps(parsed, indent=2)}",
    )
    debug_log(debug, f"[{reviewer_name}] Reviewer finished.")

    return parsed


def call_reviewer_sync(
    client: OpenAI,
    reviewer_name: str,
    system_prompt: str,
    review_input: str,
    temperature: float,
    debug: bool,
) -> dict[str, Any]:
    debug_log(debug, f"[{reviewer_name}] Reviewer started.")

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": review_input},
    ]

    for iteration in range(1, MAX_TOOL_ITERATIONS + 1):
        debug_log(debug, f"[{reviewer_name}] LLM iteration {iteration}.")

        try:
            completion = client.chat.completions.create(
                model=REVIEWER_MODEL,
                temperature=temperature,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                response_format={"type": "json_object"},
            )
        except Exception as error:
            debug_log(debug, f"[{reviewer_name}] LLM call failed: {error}")
            return {
                "findings": [
                    {
                        "path": "unknown",
                        "line": 0,
                        "severity": "warn",
                        "category": "tooling",
                        "description": f"Reviewer LLM call failed: {error}",
                    }
                ]
            }

        assistant_message = completion.choices[0].message
        tool_calls = assistant_message.tool_calls

        assistant_entry: dict[str, Any] = {
            "role": "assistant",
            "content": assistant_message.content or "",
        }

        if tool_calls:
            assistant_entry["tool_calls"] = [
                tool_call.model_dump(exclude_none=True)
                for tool_call in tool_calls
            ]

        messages.append(assistant_entry)

        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments

                debug_log(
                    debug,
                    f"[{reviewer_name}] Calling tool {tool_name} with {raw_arguments}",
                )

                try:
                    arguments = json.loads(raw_arguments)
                except json.JSONDecodeError as error:
                    tool_output = f"Error: Tool arguments were not valid JSON: {error}"
                else:
                    tool_output = execute_tool(tool_name, arguments)

                debug_log(debug, f"[{reviewer_name}] Tool output:\n{tool_output[:3000]}")

                if len(tool_output) > 3000:
                    debug_log(debug, f"[{reviewer_name}] Tool output truncated in debug log.")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_output,
                    }
                )

            continue

        content = assistant_message.content or '{"findings": []}'

        try:
            parsed = normalize_findings(parse_json_content(content))
        except json.JSONDecodeError as error:
            debug_log(debug, f"[{reviewer_name}] JSON parse failed: {error}")
            parsed = {
                "findings": [
                    {
                        "path": "unknown",
                        "line": 0,
                        "severity": "warn",
                        "category": "tooling",
                        "description": "Reviewer did not return valid JSON.",
                    }
                ]
            }

        debug_log(
            debug,
            f"[{reviewer_name}] Raw JSON findings:\n{json.dumps(parsed, indent=2)}",
        )
        debug_log(debug, f"[{reviewer_name}] Reviewer finished.")

        return parsed

    return force_final_json(
        client=client,
        reviewer_name=reviewer_name,
        messages=messages,
        temperature=temperature,
        debug=debug,
    )


async def run_reviewer(
    client: OpenAI,
    reviewer_name: str,
    system_prompt: str,
    review_input: str,
    temperature: float,
    debug: bool,
) -> dict[str, Any]:
    return await asyncio.to_thread(
        call_reviewer_sync,
        client,
        reviewer_name,
        system_prompt,
        review_input,
        temperature,
        debug,
    )


def call_judge(
    client: OpenAI,
    mode: str,
    review_input: str,
    security_report: dict[str, Any],
    maintainability_report: dict[str, Any],
    debug: bool,
) -> str:
    debug_log(debug, "[Lead Developer] Synthesis started.")

    user_prompt = "\n".join(
        [
            f"Review mode: {mode}",
            "",
            "Original input being reviewed:",
            review_input[:20000],
            "",
            "Security Auditor JSON:",
            json.dumps(security_report, indent=2),
            "",
            "Maintainability Critic JSON:",
            json.dumps(maintainability_report, indent=2),
            "",
            "Create the final single-file HTML report now.",
        ]
    )

    completion = client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    html = completion.choices[0].message.content or ""
    html = html.strip()

    if html.startswith("```html"):
        html = html.removeprefix("```html").strip()

    if html.startswith("```"):
        html = html.removeprefix("```").strip()

    if html.endswith("```"):
        html = html.removesuffix("```").strip()

    debug_log(debug, "[Lead Developer] Synthesis finished.")

    return html


async def main_async() -> None:
    args = parse_args()
    api_key = load_api_key()
    client = get_client(api_key)

    mode, review_input = build_review_input(args)

    debug_log(args.debug, f"[Main] Mode selected: {mode}")
    debug_log(args.debug, f"[Main] Reviewer model: {REVIEWER_MODEL}")
    debug_log(args.debug, f"[Main] Judge model: {JUDGE_MODEL}")

    security_task = run_reviewer(
        client=client,
        reviewer_name="Security",
        system_prompt=SECURITY_SYSTEM_PROMPT,
        review_input=review_input,
        temperature=0.1,
        debug=args.debug,
    )

    maintainability_task = run_reviewer(
        client=client,
        reviewer_name="Maintainability",
        system_prompt=MAINTAINABILITY_SYSTEM_PROMPT,
        review_input=review_input,
        temperature=0.25,
        debug=args.debug,
    )

    security_report, maintainability_report = await asyncio.gather(
        security_task,
        maintainability_task,
    )

    html = call_judge(
        client=client,
        mode=mode,
        review_input=review_input,
        security_report=security_report,
        maintainability_report=maintainability_report,
        debug=args.debug,
    )

    output_path = args.output_path or default_output_path()

    try:
        Path(output_path).write_text(html, encoding="utf-8")
    except OSError as error:
        print(f"Error: Could not write output file {output_path}: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Review complete. HTML report saved to: {output_path}")


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("Review cancelled.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()