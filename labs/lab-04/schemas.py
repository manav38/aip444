from pydantic import BaseModel, Field


class Flashcard(BaseModel):
    application: str = Field(
        description="1-2 sentence real-world workplace task where this concept is needed."
    )
    challenge: str = Field(
        description="A specific problem to solve in the scenario. All acronyms must be expanded."
    )
    answer: str = Field(
        description="Correct solution with a brief explanation."
    )
    evidence: str = Field(
        description="Direct quote from the source notes supporting this card."
    )
    misconception: str = Field(
        description="Quote of what a junior developer or student might incorrectly believe."
    )
    correction: str = Field(
        description="Why the misconception is wrong, citing the notes."
    )


class FlashcardResponse(BaseModel):
    flashcards: list[Flashcard] = Field(
        description="A list of structured ACE flashcards generated from the provided notes."
    )