import json
import os
from typing import Any, Dict

from fastapi import WebSocket, WebSocketDisconnect

from app.custom_stt import AiolaClient, LiveEvents
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
        self.connection = None
        self._setup_stt()

    def _setup_stt(self) -> None:
        # Authenticate and create client (Mock flow matching real Aiola usage)
        api_key = os.getenv("AIOLA_API_KEY") or "dummy_key"
        token_result = AiolaClient.grant_token(api_key=api_key)
        client = AiolaClient(access_token=token_result.access_token)
        
        # Create streaming connection
        self.connection = client.stt.stream(lang_code='en')

        @self.connection.on(LiveEvents.Structured)
        async def on_structured(data: Dict[str, Any]) -> None:
            entities = [Entity(**e) for e in data.get("entities", [])]
            message = STTResultMessage(
                type="stt_result",
                text=data.get("text", ""),
                entities=entities,
            )
            await self.handle_stt_result(message)

        self.connection.connect()

    async def run(self) -> None:
        await self.websocket.accept()
        try:
            await self.websocket.send_json(ReadyMessage().model_dump())
        except WebSocketDisconnect:
            # Client disconnected immediately after accept
            if self.connection:
                await self.connection.close()
            return

        try:
            while True:
                message = await self.websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break
                
                if "bytes" in message:
                    if self.connection:
                        await self.connection.send(message["bytes"])
                elif "text" in message:
                    await self.handle_client_message(message["text"])
        except WebSocketDisconnect:
            pass
        finally:
            if self.connection:
                await self.connection.close()

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
        interaction_id = message.interaction_id or self.state.next_interaction_id()
        entities = await enrich_entities_with_llm(message)
        result = self.state.set_result(interaction_id=interaction_id, text=message.text, entities=entities)

        await self.send_result(result)
        await self.websocket.send_json(
            {
                "type": "prompt_confirmation",
                "interaction_id": interaction_id,
                "prompt": f"Are you confirming: {result.text}?",
            }
        )

    async def handle_confirm(self, message: ConfirmMessage) -> None:
        result = self.state.confirm(interaction_id=message.interaction_id, confirmed=message.confirmed)
        await self.send_result(result)

        if not message.confirmed:
            await self.websocket.send_json(RetryMessage(interaction_id=message.interaction_id).model_dump())

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
