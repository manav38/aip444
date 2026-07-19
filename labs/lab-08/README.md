# Lab 8 - A Visual Debugger

This lab builds a CLI tool called `img-debug`.

The tool accepts a screenshot of a developer error, optimizes the image, sends it to a vision-capable LLM through OpenRouter, allows the model to call a Tavily web search tool, and prints a debugging explanation with possible fixes.

## Files

- `img_debug.py`: Main CLI tool.
- `image_utils.py`: Resizes and compresses screenshots, then converts them to Base64.
- `web_search.py`: Tavily search tool implementation.
- `prompts.py`: System prompt for the visual debugging assistant.
- `test-images/`: Folder for test screenshots.

## Models and APIs

- Vision model: `google/gemini-3-flash-preview`
- Search tool: Tavily Search API

## Setup

Install dependencies:

```bash
pip install openai python-dotenv tavily-python pillow