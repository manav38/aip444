# Lab 2 - ACE Flashcard Generator

This lab creates a command line tool called `flashcards`.

The tool accepts a notes file and generates ACE flashcards using OpenRouter and the OpenAI SDK.

## ACE Format

Each card follows this structure:

```text
=== CARD [number] ===
APPLICATION: ...
CHALLENGE: ...
ANSWER: ...
EVIDENCE: "..."
MISCONCEPTION: "..."
CORRECTION: ...
===
```

## Setup

Install dependencies:

```bash
pip install openai python-dotenv
```

The OpenRouter API key must be stored in the root `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Make sure `.env` is included in `.gitignore`.

## Run

From this folder:

```bash
python flashcards.py week-03-notes.md --cards 3
```

Generate one card:

```bash
python flashcards.py week-03-notes.md --cards 1
```

Generate five cards:

```bash
python flashcards.py week-03-notes.md --cards 5
```

Test empty notes:

```bash
python flashcards.py test-empty.md --cards 2
```

Test minimal notes:

```bash
python flashcards.py test-minimal.md --cards 3
```

## Files

- `flashcards.py`: Python command line tool.
- `SYSTEM_PROMPT.md`: Final production system prompt.
- `INITIAL_SYSTEM_PROMPT.md`: Initial zero-shot system prompt.
- `week-03-notes.md`: Week 3 prompt engineering notes used for main testing.
- `test-empty.md`: Empty notes edge case.
- `test-minimal.md`: Minimal notes edge case.