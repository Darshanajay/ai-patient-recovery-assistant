# Patient Recovery AI Service

FastAPI + LangGraph AI service for extracting discharge-summary information.

## Setup

Activate your existing virtual environment, then install dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Ollama is optional for the deterministic labelled-field fallback. If enabled, set
`OLLAMA_MODEL` to a model already installed locally (default: `qwen2.5:7b`).

## Run

```bash
uvicorn main:app --reload --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs

## Tests

```bash
python -m pytest -q
```

The test suite includes template rejection, existing structured fixtures, API validation,
and a realistic-layout synthetic PDF. Ollama is mocked/offline in parser tests so the
tests are deterministic. Medication reminders and calendar actions remain disabled
until the extracted information is verified. Warning-sign entries remain for clinician
review.

## PDF extraction notes

The document parser handles labelled fields, common text-extracted medication tables,
and numbered paragraph sections for activity, diet, warning signs, and appointments.
PDF layouts vary by hospital and scanner; scanned/image-only PDFs need OCR and are
reported as unreadable by the current upload endpoint.

All sample PDF content is fictional and for software testing only.
