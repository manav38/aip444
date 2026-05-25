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