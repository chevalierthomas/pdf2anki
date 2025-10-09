from __future__ import annotations

import base64
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .flashcards import (
    FlashcardGenerationError,
    build_anki_deck,
    build_flashcards_from_text,
    extract_pdf_text,
)


def _cleanup_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:  # pragma: no cover - best effort cleanup
        pass

app = FastAPI(title="PDF vers Anki", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/generate")
async def generate_deck(
    background_tasks: BackgroundTasks, pdf: UploadFile = File(...)
):
    allowed_types = {"application/pdf", "application/x-pdf", "application/acrobat", "application/octet-stream"}
    if pdf.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")

    raw_data = await pdf.read()
    if not raw_data:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")

    try:
        text = extract_pdf_text(raw_data)
        cards = build_flashcards_from_text(text)
        deck_title = Path(pdf.filename or "Deck PDF").stem or "Deck PDF"
        deck_path = build_anki_deck(cards, deck_title)
    except FlashcardGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    filename = f"{deck_title}.apkg"

    deck_bytes = Path(deck_path).read_bytes()
    deck_base64 = base64.b64encode(deck_bytes).decode("ascii")

    background_tasks.add_task(_cleanup_file, Path(deck_path))

    serialized_cards = [{"front": card.front, "back": card.back} for card in cards]

    return {
        "deck_filename": filename,
        "deck_data": deck_base64,
        "cards": serialized_cards,
    }
