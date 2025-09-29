from typing import Dict, List, Literal, Optional

from pydantic import BaseModel

CardType = Literal["qa", "cloze"]


class ExtractRequest(BaseModel):
    filename: str
    language: Optional[str] = "en"
    card_types: List[CardType] = ["qa", "cloze"]
    max_cards: int = 100
    use_llm: bool = True


class Card(BaseModel):
    id: str
    type: CardType
    question: str
    answer: str
    tags: List[str] = []
    source_page: int
    confidence: float
    source_snippet: str
    explanation: Optional[str] = None


class LLMReport(BaseModel):
    used: bool
    generated: int = 0
    enriched: int = 0
    model: Optional[str] = None
    duration_ms: int = 0
    chunks: int = 0
    mode: Literal["extraction", "refinement"] = "extraction"
    error: Optional[str] = None


class ExtractResponse(BaseModel):
    cards: List[Card]
    metrics: Dict[str, float]
    llm: Optional[LLMReport] = None


class ExportRequest(BaseModel):
    deck_name: str
    cards: List[Card]
