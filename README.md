# Voice Agent (Python + Next.js)

Web-based AI chat agent with a Python FastAPI WebSocket backend and Next.js frontend. The agent captures entities per interaction, asks for confirmation, and handles dynamic conversation flow. STT is provided by your custom endpoint; Azure Speech handles TTS; Azure OpenAI can enrich entities.

## Structure
- backend: FastAPI WebSocket server
- frontend: Next.js App Router client
- .github/copilot-instructions.md: workspace checklist

## Quick start
1. Backend
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   cp .env.example .env  # fill in placeholders
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
2. Frontend
   ```bash
   cd frontend
   npm install
   cp .env.local.example .env.local
   npm run dev
   ```
3. Open http://localhost:3000 and speak/paste text. The app sends STT payloads over WebSocket, shows extracted entities, and asks for confirmation.

## Environment variables
- Backend: see backend/.env.example (Azure OpenAI, Azure Speech, custom STT endpoint)
- Frontend: NEXT_PUBLIC_WS_URL (WebSocket endpoint)

## Tests
```bash
cd backend
pytest
```
