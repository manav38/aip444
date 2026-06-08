# Lab 4 - Structured Outputs and Code Reading

This lab refactors the Lab 2 flashcard generator into an HTTP API server using FastAPI, Pydantic, and OpenRouter structured outputs.

## Features

- FastAPI server
- POST endpoint at `/api/generate`
- Pydantic request validation
- Pydantic schema for flashcard response structure
- OpenAI SDK structured output parsing
- Test client that sends notes to the server
- JSON response containing structured flashcards

## Setup

Install dependencies:

```bash
pip install fastapi uvicorn python-dotenv openai pydantic requests
```

The OpenRouter API key must be stored in the root `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
```

## Run Server

From this folder:

```bash
python server.py
```

Server runs at:

```text
http://localhost:3000
```

## Test Client

In a second terminal, from this folder:

```bash
python test_client.py
```

The client reads `notes.md`, sends a POST request to `/api/generate`, and prints the structured JSON response.

## Files

- `server.py`: FastAPI server.
- `schemas.py`: Pydantic schema for structured flashcard output.
- `flashcard_generator.py`: OpenRouter structured output generation logic.
- `SYSTEM_PROMPT.md`: Prompt used by the model.
- `test_client.py`: Client script for testing the API.
- `notes.md`: Sample notes used for testing.