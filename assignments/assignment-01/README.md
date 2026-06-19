# Assignment 1 - AI Code Review

This project implements an AI code review CLI named `review.py`.

The tool reviews either staged git changes or a specific file. It runs two specialized AI reviewers in parallel, then sends their structured JSON findings to a Lead Developer judge that creates a final HTML report.

## Reviewers Used

1. Security Auditor
   - Looks for hardcoded secrets, dangerous patterns, missing validation, and unsafe logic.

2. Maintainability Critic
   - Looks for unclear names, unused imports, incorrect types, missing imports, and readability problems.

## Features

- Git Mode: reviews staged git changes using `git diff --staged`.
- File Mode: reviews a specific file with `--file`.
- Debug Mode: prints detailed logs to stderr with `--debug`.
- Tool calling:
  - `read_file(file_path, start_line, end_line)`
  - `ripgrep(search_pattern)`
- Parallel reviewer execution using `asyncio.gather`.
- Structured JSON reviewer findings.
- Lead Developer synthesis into a single HTML report.
- Custom output path with `--output`.

## Setup

Install dependencies:

    pip install openai python-dotenv

Install ripgrep:

    winget install BurntSushi.ripgrep.MSVC

Store your OpenRouter key in the root `.env` file:

    OPENROUTER_API_KEY=your_key_here

Optional model overrides:

    REVIEWER_MODEL=google/gemini-2.5-flash
    JUDGE_MODEL=google/gemini-2.5-flash

## File Mode Test

    python review.py --debug --file bad_code.py

Expected findings include:

- Hardcoded API key.
- Unused `sys` import.
- Missing `math` import.
- Unclear variable name `x`.
- Incorrect return type annotation.

## Git Mode Test

Stage a small change:

    git status
    git add README.md
    python review.py --debug

The tool reviews the staged diff and saves an HTML report.

## Output

If no output file is provided, the tool creates a file like:

    review-14-06-2026-23-50-10.html

You can specify a file:

    python review.py --file bad_code.py --output report.html

## AI Usage

AI assistance was used to help design the program structure, prompts, tool-calling loop, and debugging strategy. The final code was reviewed and tested before submission.
Dogfooding test change.
