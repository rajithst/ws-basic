from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str
    value: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class STTResultMessage(BaseModel):
    type: Literal["stt_result"]
    phrase_id: Optional[str] = None
    text: str
    entities: List[Entity] = Field(default_factory=list)
    raw: Optional[dict] = None  # placeholder for original STT payload


class ConfirmMessage(BaseModel):
    type: Literal["confirm"]
    phrase_id: str
    confirmed: bool


class RequestStateMessage(BaseModel):
    type: Literal["request_state"]


ClientMessage = Union[STTResultMessage, ConfirmMessage, RequestStateMessage]


class ResultModel(BaseModel):
    phrase_id: str
    text: str
    entities: List[Entity]
    status: Literal["pending", "awaiting_confirmation", "confirmed"]


class ReadyMessage(BaseModel):
    type: Literal["ready"] = "ready"


class ResultPayload(BaseModel):
    type: Literal["result"] = "result"
    result: ResultModel


class RetryMessage(BaseModel):
    type: Literal["retry"] = "retry"
    phrase_id: str


ServerMessage = Union[
    ReadyMessage,
    ResultPayload,
    RetryMessage,
]
