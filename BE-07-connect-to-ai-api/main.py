"""BE-07 — Connect to an AI API: ticket classification endpoint.

One endpoint asks an LLM for a JUDGEMENT and returns a trustworthy,
structured answer — never free-form chatbot text.

    POST /classify   { "message": "..." }  ->  Classification (strict schema)
"""

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()

from llm import ClassificationError, create_classifier
from schemas import Classification, ClassificationRequest

app = FastAPI(
    title="AI Classifier API",
    description="Classify support tickets with a real LLM, returning strict "
    "structured output (category, sentiment, confidence, tidy subject).",
    version="1.0.0",
)

classifier = create_classifier()


@app.get("/")
def root():
    return {"name": "AI Classifier API", "endpoint": "/classify", "schema": "Classification"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify", response_model=Classification)
def classify(payload: ClassificationRequest):
    try:
        result = classifier.classify(payload)
    except ClassificationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return result
