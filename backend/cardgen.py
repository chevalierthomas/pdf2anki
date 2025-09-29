import uuid
from typing import Dict, List


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def _confidence(question: str, answer: str) -> float:
    qlen, alen = len(question), len(answer)
    score = 1.0
    if qlen < 12 or qlen > 220:
        score -= 0.2
    if alen > 260:
        score -= 0.2
    return max(0.3, min(1.0, score))


def _make_card(
    card_type: str,
    question: str,
    answer: str,
    page: int,
    source: str,
    tags: List[str],
) -> Dict[str, object]:
    return {
        "id": _new_id(),
        "type": card_type,
        "question": question.strip(),
        "answer": answer.strip(),
        "tags": tags,
        "source_page": page,
        "confidence": _confidence(question, answer),
        "source_snippet": source,
    }


def generate_cards(
    facts: List[Dict[str, object]],
    card_types: List[str],
    max_cards: int,
) -> List[Dict[str, object]]:
    cards: List[Dict[str, object]] = []

    for fact in facts:
        if fact["kind"] == "definition":
            if "qa" in card_types:
                question = f"What is **{fact['term']}**?"
                answer = fact["desc"]
                cards.append(
                    _make_card(
                        "qa",
                        question,
                        answer,
                        fact["page"],
                        fact["source"],
                        ["definition"],
                    )
                )
            if "cloze" in card_types and 10 < len(fact["desc"]) < 200:
                sentence = f"{fact['term']} is {fact['desc']}"
                if fact["term"] in sentence:
                    cloze = sentence.replace(
                        fact["term"], f"{{{{c1::{fact['term']}}}}}"
                    )
                    cards.append(
                        _make_card(
                            "cloze",
                            cloze,
                            "",
                            fact["page"],
                            fact["source"],
                            ["definition", "cloze"],
                        )
                    )
        elif fact["kind"] == "list" and "qa" in card_types:
            question = f"List the key points: {fact['title']}"
            answer = "; ".join(fact["items"])
            cards.append(
                _make_card(
                    "qa",
                    question,
                    answer,
                    fact["page"],
                    fact["source"],
                    ["list"],
                )
            )

        if len(cards) >= max_cards:
            break

    return cards
