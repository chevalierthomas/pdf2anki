import base64
from pathlib import Path

from backend.app.flashcards import (
    Flashcard,
    build_anki_deck,
    build_flashcards_from_text,
    build_flashcards_with_heuristics,
)
from backend.app import main as main_module
from fastapi.testclient import TestClient


def test_build_flashcards_with_heuristics_term_definition():
    text = """Python: Un langage de programmation.

JavaScript: Langage pour le web."""
    cards = build_flashcards_with_heuristics(text)
    assert len(cards) == 2
    assert cards[0].front == "Python"
    assert "langage" in cards[0].back


def test_build_flashcards_with_heuristics_paragraph_summary():
    text = (
        "Le cycle de l'eau commence par l'évaporation. L'eau s'élève, se condense"
        " et retombe sous forme de précipitations. Ce cycle maintient l'équilibre hydrique."
    )
    cards = build_flashcards_with_heuristics(text)
    assert len(cards) == 1
    assert "évaporation" in cards[0].front
    assert "précipitations" in cards[0].back


def test_build_flashcards_from_text_without_openai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cards = build_flashcards_from_text("Python: Langage")
    assert len(cards) == 1
    assert cards[0].front == "Python"


def test_build_anki_deck():
    cards = [Flashcard(front="Question", back="Réponse")]
    deck_path = build_anki_deck(cards, "Test Deck")
    assert deck_path.endswith(".apkg")
    Path(deck_path).unlink()


def test_generate_endpoint_returns_preview(monkeypatch, tmp_path):
    monkeypatch.setattr(main_module, "extract_pdf_text", lambda data: "Term: Definition")
    monkeypatch.setattr(
        main_module,
        "build_flashcards_from_text",
        lambda text: [Flashcard(front="Q", back="A")],
    )

    deck_path = tmp_path / "deck.apkg"

    def fake_build_anki_deck(cards, title):
        deck_path.write_bytes(b"dummy")
        return str(deck_path)

    monkeypatch.setattr(main_module, "build_anki_deck", fake_build_anki_deck)

    client = TestClient(main_module.app)
    response = client.post(
        "/api/generate",
        files={"pdf": ("test.pdf", b"data", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["deck_filename"] == "test.apkg"
    assert payload["cards"] == [{"front": "Q", "back": "A"}]
    assert base64.b64decode(payload["deck_data"]) == b"dummy"
