from typing import List

from app.schemas import Entity, STTResultMessage


def extract_entities_from_stt(message: STTResultMessage) -> List[Entity]:
    # Quick POC: use entities if provided; otherwise wrap text as a single entity
    if message.entities:
        return message.entities
    if message.text:
        return [Entity(name="transcript", value=message.text, confidence=None)]
    return []


async def enrich_entities_with_llm(message: STTResultMessage) -> List[Entity]:
    # POC mode: no LLM; just echo entities from STT or fallback to transcript
    return extract_entities_from_stt(message)
