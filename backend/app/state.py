import uuid
from typing import Dict, List

from app.schemas import Entity, ResultModel


class SessionState:
    def __init__(self) -> None:
        self.results: Dict[str, ResultModel] = {}

    def next_interaction_id(self) -> str:
        return str(uuid.uuid4())

    def set_result(self, interaction_id: str, text: str, entities: List[Entity]) -> ResultModel:
        result = self.results.get(
            interaction_id,
            ResultModel(interaction_id=interaction_id, text="", entities=[], status="pending"),
        )
        result.text = text
        result.entities = entities
        result.status = "awaiting_confirmation"
        self.results[interaction_id] = result
        return result

    def confirm(self, interaction_id: str, confirmed: bool) -> ResultModel:
        result = self.results[interaction_id]
        result.status = "confirmed" if confirmed else "pending"
        self.results[interaction_id] = result
        return result

    def summary(self) -> List[ResultModel]:
        return list(self.results.values())
