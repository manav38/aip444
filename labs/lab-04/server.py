"""
Lab 4 FastAPI Server

This file defines a small HTTP API server for the structured flashcard generator.

The server accepts a POST request at /api/generate with JSON data containing:
- notes: the course notes or source text
- cards: the number of flashcards to generate

FastAPI validates the request body using the GenerateRequest Pydantic model.
The route then sends the notes and card count to generate_flashcards(), which calls
the LLM and returns structured JSON that matches the flashcard schema.

This server also includes:
- CORS middleware so a browser frontend could call the API
- a custom middleware that records request processing time
- error handling so server problems return a clear HTTP 500 response
"""

import time

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from flashcard_generator import generate_flashcards


app = FastAPI()

# CORS allows clients from other origins, such as a separate frontend app,
# to send requests to this API server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# This middleware runs on every HTTP request.
# It measures how long the server takes to process the request and adds that
# timing value to the response headers.
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# This Pydantic model defines the expected JSON request body.
# FastAPI uses it to validate that "notes" is a string and "cards" is an integer.
class GenerateRequest(BaseModel):
    notes: str
    cards: int = 3


# This endpoint receives notes from a client and returns structured flashcards.
# The client sends JSON to /api/generate, and FastAPI converts it into
# a GenerateRequest object before this function runs.
@app.post("/api/generate")
async def generate_cards(request: GenerateRequest):
    try:
        result = await generate_flashcards(request.notes, request.cards)
        return result
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Server running on http://localhost:3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)