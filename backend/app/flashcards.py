"""Utilities for extracting text from PDFs and building flashcards."""
from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from io import BytesIO
from typing import Iterable, List

import genanki
from PyPDF2 import PdfReader


@dataclass
class Flashcard:
    """Represents a single flashcard entry."""

    front: str
    back: str


class FlashcardGenerationError(RuntimeError):
    """Raised when the flashcard generation fails."""


def extract_pdf_text(data: bytes) -> str:
    """Extract all text from a PDF document.

    Args:
        data: Raw bytes of the PDF file.

    Returns:
        A single string containing the extracted text.

    Raises:
        FlashcardGenerationError: If the PDF cannot be read.
    """

    try:
        reader = PdfReader(BytesIO(data))
    except Exception as exc:  # pragma: no cover - defensive programming
        raise FlashcardGenerationError("Le fichier PDF ne peut pas être lu.") from exc

    pieces: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text:
            pieces.append(text)
    return "\n".join(pieces)


def _extract_colon_cards(lines: Iterable[str]) -> List[Flashcard]:
    cards: List[Flashcard] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        if line.count(":") > 3:
            # Heuristique grossière pour éviter les faux positifs avec les horaires, etc.
            continue
        left, right = [part.strip() for part in line.split(":", 1)]
        if len(left) >= 3 and len(right) >= 3:
            cards.append(Flashcard(front=left, back=right))
    return cards


def _summarize_paragraph(paragraph: str) -> Flashcard | None:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip()]
    if len(sentences) < 2:
        return None
    front = sentences[0]
    back = "<br>".join(sentences[1:])
    if len(front) < 10 or len(back) < 10:
        return None
    return Flashcard(front=front, back=back)


def build_flashcards_from_text(text: str) -> List[Flashcard]:
    """Generate flashcards from extracted text.

    The heuristic is intentionally simple: we prioritise "term: definition"
    patterns and fall back to splitting longer paragraphs into a lead
    sentence (front) and supporting sentences (back).
    """

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    cards: List[Flashcard] = []

    for paragraph in paragraphs:
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        colon_cards = _extract_colon_cards(lines)
        if colon_cards:
            cards.extend(colon_cards)
            continue
        summarized = _summarize_paragraph(paragraph)
        if summarized:
            cards.append(summarized)

    # Déduplication basique en gardant l'ordre d'apparition.
    seen = set()
    unique_cards: List[Flashcard] = []
    for card in cards:
        key = (card.front, card.back)
        if key in seen:
            continue
        seen.add(key)
        unique_cards.append(card)
    return unique_cards


def build_anki_deck(cards: List[Flashcard], title: str) -> str:
    """Build an Anki deck file (.apkg) from flashcards.

    Args:
        cards: Flashcards to include in the deck.
        title: Deck title, typically derived from the input file name.

    Returns:
        The path to the generated temporary .apkg file.
    """

    if not cards:
        raise FlashcardGenerationError(
            "Aucune carte n'a pu être générée. Vérifiez la structure du PDF."
        )

    model = genanki.Model(
        model_id=1607392319,
        name="PDF2Anki Basic",
        fields=[{"name": "Question"}, {"name": "Answer"}],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Answer}}",
            }
        ],
    )

    deck = genanki.Deck(deck_id=2059400110, name=title)
    for index, card in enumerate(cards, start=1):
        note = genanki.Note(model=model, fields=[card.front, card.back], guid=str(index))
        deck.add_note(note)

    package = genanki.Package(deck)
    temp_file = tempfile.NamedTemporaryFile(suffix=".apkg", delete=False)
    package.write_to_file(temp_file.name)
    return temp_file.name
