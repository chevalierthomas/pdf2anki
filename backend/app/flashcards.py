"""Utilities for extracting text from PDFs and building flashcards."""
from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from io import BytesIO
from typing import Iterable, List

import genanki
from PyPDF2 import PdfReader

try:  # pragma: no cover - optional dependency during import time
    from openai import OpenAI
except Exception:  # pragma: no cover - allow running without the package installed
    OpenAI = None  # type: ignore


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


def _clean_cards(cards: Iterable[Flashcard]) -> List[Flashcard]:
    seen = set()
    unique_cards: List[Flashcard] = []
    for card in cards:
        key = (card.front.strip(), card.back.strip())
        if not card.front.strip() or not card.back.strip():
            continue
        if key in seen:
            continue
        seen.add(key)
        unique_cards.append(
            Flashcard(front=card.front.strip(), back=card.back.strip())
        )
    return unique_cards


def build_flashcards_with_heuristics(text: str) -> List[Flashcard]:
    """Generate flashcards using local heuristics as a fallback."""

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

    return _clean_cards(cards)


def _call_chatgpt_for_cards(text: str, max_cards: int = 40) -> List[Flashcard]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise FlashcardGenerationError(
            "Aucune clé OpenAI détectée. Définissez OPENAI_API_KEY pour activer la génération."
        )

    if OpenAI is None:  # pragma: no cover - executed only when package missing
        raise FlashcardGenerationError(
            "La dépendance 'openai' n'est pas installée."
        )

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    # Limiter la taille du prompt afin d'éviter les dépassements de contexte
    trimmed_text = text.strip()
    max_chars = int(os.getenv("OPENAI_PROMPT_CHAR_LIMIT", "8000"))
    if len(trimmed_text) > max_chars:
        trimmed_text = trimmed_text[:max_chars]

    system_prompt = (
        "Tu es un expert en pédagogie qui crée des cartes mémoire Anki au format question/réponse. "
        "Respecte le contenu fourni et réponds en JSON pur."
    )
    user_prompt = (
        "Extrait jusqu'à {max_cards} cartes mémoire pertinentes du texte suivant. "
        "Réponds uniquement en JSON avec la forme: {{\"flashcards\": [{{\"front\": \"...\", \"back\": \"...\"}}]}}. "
        "Pas de texte hors JSON.\n\nTexte:\n{texte}"
    ).format(max_cards=max_cards, texte=trimmed_text)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:  # pragma: no cover - network related
        raise FlashcardGenerationError("La génération via OpenAI a échoué.") from exc

    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise FlashcardGenerationError("Réponse vide de l'API OpenAI.")

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise FlashcardGenerationError("Réponse OpenAI invalide (JSON attendu).") from exc

    raw_cards = payload.get("flashcards") if isinstance(payload, dict) else payload
    if not isinstance(raw_cards, list):
        raise FlashcardGenerationError("Structure JSON inattendue pour les cartes générées.")

    cards = [
        Flashcard(front=str(entry.get("front", "")), back=str(entry.get("back", "")))
        for entry in raw_cards
    ]
    cleaned = _clean_cards(cards)
    if not cleaned:
        raise FlashcardGenerationError("Aucune carte valide renvoyée par OpenAI.")
    return cleaned


def build_flashcards_from_text(text: str) -> List[Flashcard]:
    """Generate flashcards from extracted text, using ChatGPT when possible."""

    try:
        cards = _call_chatgpt_for_cards(text)
    except FlashcardGenerationError:
        cards = build_flashcards_with_heuristics(text)

    return cards


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
