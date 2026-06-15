# Lab 5 - Tool Calling with GitHub Context

This lab extends the Lab 3 GitHub Pull Request explainer by giving the LLM access to a GitHub file-reading tool.

The model receives a Pull Request diff and comments. If the diff does not provide enough surrounding context, the model can request complete files from the GitHub repository.

## Features

* Parses public GitHub Pull Request URLs.
* Fetches Pull Request metadata, diff, and issue comments.
* Provides a `read_github_files` tool to the LLM.
* Reads files through `raw.githubusercontent.com`.
* Supports multiple files in one tool call.
* Uses the Pull Request head commit SHA for accurate file versions.
* Truncates files longer than 1,000 lines.
* Adds a truncation notice when a large file is shortened.
* Handles missing files, invalid paths, network errors, and rate limits.
* Limits tool-calling iterations to prevent infinite loops.
* Prints tool names, arguments, and result sizes for debugging.
* Produces a final Markdown explanation of the Pull Request.

## Setup

Install dependencies:

```bash
pip install requests openai python-dotenv
```

Store the OpenRouter API key in the repository root `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Make sure `.env` is included in `.gitignore`.

## Files

* `pr-advice.py`: Pull Request analysis and tool-calling loop.
* `tools.py`: GitHub raw-file reading tool.
* `test_tool.py`: Direct tests for the GitHub tool.
* `SYSTEM_PROMPT.md`: Instructions for Pull Request analysis and responsible tool use.
* `README.md`: Lab setup and usage documentation.

## Test the GitHub Tool

From the `labs/lab-05` folder, run:

```bash
python test_tool.py
```

The test script checks:

* An existing GitHub file.
* A missing GitHub file.
* Multiple GitHub files in one request.

## Run the Pull Request Explainer

```bash
python pr-advice.py https://github.com/microsoft/vscode/pull/289801
```

The terminal displays:

* The parsed Pull Request information.
* The Pull Request head commit SHA.
* The diff and comments fetched.
* Each LLM iteration.
* Whether the model requested a tool call.
* The tool name and arguments.
* The tool result size.
* The final Pull Request analysis.

Example tool-calling logs:

```text
LLM iteration: 1
Tool calls requested: 1
Calling tool: read_github_files
Arguments: {"files": [...]}
Tool result length: 25000 characters
LLM iteration: 2
```

## Lab Testing Requirements

Test the application with two different Pull Requests:

1. A Pull Request where the model needs additional file context and calls `read_github_files`.
2. A Pull Request where the diff and comments are sufficient and the model does not call the tool.

For each test, keep the Pull Request URL, console output, and final analysis for the submission document.
