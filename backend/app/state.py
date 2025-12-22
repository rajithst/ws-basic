from typing import Dict, List

from app.schemas import Entity, ResultModel


class SessionState:
    def __init__(self) -> None:
        self.results: Dict[str, ResultModel] = {}
        self.phrase_counter: int = 0

    def next_phrase_id(self) -> str:
        self.phrase_counter += 1
        return f"phrase_{self.phrase_counter}"

    def set_result(self, phrase_id: str, text: str, entities: List[Entity]) -> ResultModel:
        result = self.results.get(
            phrase_id,
            ResultModel(phrase_id=phrase_id, text="", entities=[], status="pending"),
        )
        result.text = text
        result.entities = entities
        result.status = "awaiting_confirmation"
        self.results[phrase_id] = result
        return result

    def confirm(self, phrase_id: str, confirmed: bool) -> ResultModel:
        result = self.results[phrase_id]
        result.status = "confirmed" if confirmed else "pending"
        self.results[phrase_id] = result
        return result

    def summary(self) -> List[ResultModel]:
        return list(self.results.values())
