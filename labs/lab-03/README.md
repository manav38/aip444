# Lab 3 - GitHub PR Explainer

This lab creates a command line tool called `pr-advice`.

The tool accepts a public GitHub Pull Request URL, fetches the PR diff and issue comments, and sends both to an LLM through OpenRouter. The LLM responds as a senior engineer explaining the PR to a junior developer.

## Features

- Validates GitHub Pull Request URLs.
- Extracts owner, repository name, and Pull Request number.
- Fetches the PR `.diff` text.
- Truncates very large diffs over 95,000 characters.
- Fetches PR issue comments using the GitHub API.
- Uses required GitHub API headers.
- Uses fenced `diff` blocks for code changes.
- Uses XML tags for PR comments.
- Generates a Markdown report with:
  - tl;dr
  - Stakeholders
  - Changes
  - Risks
  - Learning

## Setup

Install dependencies:

```bash
pip install requests openai python-dotenv