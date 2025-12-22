from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.schemas import (
    ConfirmMessage,
    RequestStateMessage,
    ResultModel,
    ResultPayload,
    RetryMessage,
    ReadyMessage,
    STTResultMessage,
)
from app.service import enrich_entities_with_llm
from app.state import SessionState

load_dotenv()

app = FastAPI(title="Voice Agent Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def result_to_payload(result: ResultModel) -> ResultPayload:
    return ResultPayload(result=result)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    session = SessionState()
    await websocket.send_json(ReadyMessage().model_dump())

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "stt_result":
                message = STTResultMessage(**data)
                await handle_stt_message(websocket, session, message)
            elif msg_type == "confirm":
                message = ConfirmMessage(**data)
                await handle_confirm_message(websocket, session, message)
            elif msg_type == "request_state":
                _ = RequestStateMessage(**data)
                await websocket.send_json(
                    {
                        "type": "state",
                        "results": [r.model_dump() for r in session.summary()],
                    }
                )
                
            else:
                await websocket.send_json({"type": "error", "message": "Unknown message type"})
    except WebSocketDisconnect:
        return


async def handle_stt_message(websocket: WebSocket, session: SessionState, message: STTResultMessage) -> None:
    phrase_id = message.phrase_id or session.next_phrase_id()
    entities = await enrich_entities_with_llm(message)
    result = session.set_result(phrase_id=phrase_id, text=message.text, entities=entities)

    await websocket.send_json(result_to_payload(result).model_dump())
    await websocket.send_json(
        {
            "type": "prompt_confirmation",
            "phrase_id": phrase_id,
            "prompt": f"Are you confirming: {result.text}?",
        }
    )


async def handle_confirm_message(websocket: WebSocket, session: SessionState, message: ConfirmMessage) -> None:
    result = session.confirm(phrase_id=message.phrase_id, confirmed=message.confirmed)
    await websocket.send_json(result_to_payload(result).model_dump())

    if not message.confirmed:
        await websocket.send_json(RetryMessage(phrase_id=message.phrase_id).model_dump())
