# Structured Outputs Notes

Structured outputs force the model to return valid JSON that follows a schema.

Schemas act like contracts for data exchange between an application and an AI model.

Pydantic is a Python library used to define data models and validate data.

FastAPI uses Pydantic models to validate incoming request bodies.

A middleware function can run before and after a request is handled.

CORS allows a browser frontend from another origin to call an API server.

Structured outputs solve formatting problems, but they do not guarantee that the content is factually correct.

Direct evidence from source notes helps reduce hallucination because the model must ground the answer in provided text.