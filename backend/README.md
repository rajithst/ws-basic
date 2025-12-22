# Voice Agent Backend

FastAPI + WebSocket backend for the voice-driven entity capture flow. Uses placeholders for STT, Azure OpenAI, and Azure Speech; swap in real endpoints via environment variables.

## Running locally

```bash
# From repository root
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment

Copy `.env.example` to `.env` and update values.
