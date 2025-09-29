import io
import random
from typing import Dict, List

import genanki


def build_apkg(deck_name: str, cards: List[Dict[str, object]]) -> bytes:
    deck_id = random.randrange(1 << 30, 1 << 31)
    model_id = random.randrange(1 << 30, 1 << 31)

    model = genanki.Model(
        model_id,
        "PDF2Anki Cloze+QA",
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
            {"name": "Tags"},
            {"name": "Source"},
        ],
        templates=[
            {
                "name": "QA Card",
                "qfmt": "<div class='q'>{{Question}}</div><div class='src'>{{Source}}</div>",
                "afmt": "{{FrontSide}}<hr id='answer'><div class='a'>{{Answer}}</div>",
            },
            {
                "name": "Cloze Card",
                "qfmt": "{{cloze:Question}}<div class='src'>{{Source}}</div>",
                "afmt": "{{cloze:Question}}<hr id='answer'><div class='a'>{{Answer}}</div>",
            },
        ],
        css="""
            .card { font-family: Inter, Arial; font-size: 16px; line-height: 1.5; }
            .q { font-weight: 600; }
            .src { color: #888; font-size: 12px; margin-top: 8px; }
            .a { margin-top: 10px; }
        """,
    )

    deck = genanki.Deck(deck_id, deck_name)
    for card in cards:
        note = genanki.Note(
            model=model,
            fields=[
                card["question"],
                card["answer"],
                " ".join(card["tags"]),
                f"p.{card['source_page']}",
            ],
            guid=card["id"],
            tags=card["tags"],
        )
        if card["type"] == "cloze":
            note.model()["type"] = 1
        deck.add_note(note)

    package = genanki.Package(deck)
    buffer = io.BytesIO()
    package.write_to_file(buffer)
    return buffer.getvalue()
