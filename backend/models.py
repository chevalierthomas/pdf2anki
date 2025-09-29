from typing import Dict, List, Literal, Optional

from pydantic import BaseModel

CardType = Literal["qa", "cloze"]


class ExtractRequest(BaseModel):
    filename: str
    language: Optional[str] = "en"
    card_types: List[CardType] = ["qa", "cloze"]
    max_cards: int = 100


class Card(BaseModel):
    id: str
    type: CardType
    question: str
    answer: str
    tags: List[str] = []
    source_page: int
    confidence: float
    source_snippet: str


class ExtractResponse(BaseModel):
    cards: List[Card]
    metrics: Dict[str, int]


class ExportRequest(BaseModel):
    deck_name: str
    cards: List[Card]
