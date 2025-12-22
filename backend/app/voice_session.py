import json
from typing import Any, Dict

from fastapi import WebSocket, WebSocketDisconnect

from app.custom_stt import CustomSTT, LiveEvents
from app.schemas import (
    ConfirmMessage,
    Entity,
    ReadyMessage,
    RequestStateMessage,
    ResultModel,
    ResultPayload,
    RetryMessage,
    STTResultMessage,
)
from app.service import enrich_entities_with_llm
from app.state import SessionState


class VoiceSession:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.state = SessionState()
        self.stt = CustomSTT()
        self._setup_stt()

    def _setup_stt(self) -> None:
        @self.stt.on(LiveEvents.Structured)
        async def on_structured(data: Dict[str, Any]) -> None:
            entities = [Entity(**e) for e in data.get("entities", [])]
            message = STTResultMessage(
                type="stt_result",
                text=data.get("text", ""),
                entities=entities,
            )
            await self.handle_stt_result(message)

        self.stt.connect()

    async def run(self) -> None:
        await self.websocket.accept()
        await self.websocket.send_json(ReadyMessage().model_dump())

        try:
            while True:
                message = await self.websocket.receive()
                if "bytes" in message:
                    await self.stt.send(message["bytes"])
                elif "text" in message:
                    await self.handle_client_message(message["text"])
        except WebSocketDisconnect:
            await self.stt.close()

    async def handle_client_message(self, text_data: str) -> None:
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "stt_result":
            await self.handle_stt_result(STTResultMessage(**data))
        elif msg_type == "confirm":
            await self.handle_confirm(ConfirmMessage(**data))
        elif msg_type == "request_state":
            await self.handle_request_state(RequestStateMessage(**data))
        else:
            await self.websocket.send_json({"type": "error", "message": "Unknown message type"})

    async def handle_stt_result(self, message: STTResultMessage) -> None:
        phrase_id = message.phrase_id or self.state.next_phrase_id()
        entities = await enrich_entities_with_llm(message)
        result = self.state.set_result(phrase_id=phrase_id, text=message.text, entities=entities)

        await self.send_result(result)
        await self.websocket.send_json(
            {
                "type": "prompt_confirmation",
                "phrase_id": phrase_id,
                "prompt": f"Are you confirming: {result.text}?",
            }
        )

    async def handle_confirm(self, message: ConfirmMessage) -> None:
        result = self.state.confirm(phrase_id=message.phrase_id, confirmed=message.confirmed)
        await self.send_result(result)

        if not message.confirmed:
            await self.websocket.send_json(RetryMessage(phrase_id=message.phrase_id).model_dump())

    async def handle_request_state(self, message: RequestStateMessage) -> None:
        await self.websocket.send_json(
            {
                "type": "state",
                "results": [r.model_dump() for r in self.state.summary()],
            }
        )

    async def send_result(self, result: ResultModel) -> None:
        payload = ResultPayload(result=result)
        await self.websocket.send_json(payload.model_dump())
