from typing import List, Literal


class Phrase:
    def __init__(self, phrase_id: str, prompt: str):
        self.id = phrase_id
        self.prompt = prompt


def get_phrases() -> List[Phrase]:
    # Placeholder phrases; replace with your predefined set
    return [
        Phrase("phrase_1", "Say the pickup location"),
        Phrase("phrase_2", "Say the dropoff location"),
        Phrase("phrase_3", "Say the requested pickup time"),
    ]


Status = Literal["pending", "awaiting_confirmation", "confirmed"]
