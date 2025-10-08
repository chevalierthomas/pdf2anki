from pathlib import Path

from backend.app.flashcards import build_flashcards_from_text, build_anki_deck, Flashcard


def test_build_flashcards_from_text_term_definition():
    text = """Python: Un langage de programmation.

JavaScript: Langage pour le web."""
    cards = build_flashcards_from_text(text)
    assert len(cards) == 2
    assert cards[0].front == "Python"
    assert "langage" in cards[0].back


def test_build_flashcards_from_text_paragraph_summary():
    text = (
        "Le cycle de l'eau commence par l'évaporation. L'eau s'élève, se condense"
        " et retombe sous forme de précipitations. Ce cycle maintient l'équilibre hydrique."
    )
    cards = build_flashcards_from_text(text)
    assert len(cards) == 1
    assert "évaporation" in cards[0].front
    assert "précipitations" in cards[0].back


def test_build_anki_deck():
    cards = [Flashcard(front="Question", back="Réponse")]
    deck_path = build_anki_deck(cards, "Test Deck")
    assert deck_path.endswith(".apkg")
    Path(deck_path).unlink()
