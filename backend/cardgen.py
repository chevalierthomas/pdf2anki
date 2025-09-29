import re
import uuid
from typing import Dict, List


LANGUAGE_CONFIG = {
    "en": {
        "definition_question": "What is **{term}**?",
        "definition_alt": "Explain **{term}**.",
        "list_question": "List the key points about **{title}**.",
        "summary_question": "Summarize **{title}**.",
        "list_intro": "The main elements of {title} are {items}.",
        "enum_separator": ", ",
        "enum_last_separator": " and ",
    },
    "fr": {
        "definition_question": "Qu'est-ce que **{term}** ?",
        "definition_alt": "Expliquez **{term}**.",
        "list_question": "Citez les points clés concernant **{title}**.",
        "summary_question": "Résumez **{title}**.",
        "list_intro": "Les éléments principaux de {title} sont {items}.",
        "enum_separator": ", ",
        "enum_last_separator": " et ",
    },
}


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
    language: str = "en",
) -> List[Dict[str, object]]:
    cards: List[Dict[str, object]] = []
    normalised_language = _normalise_language(language)
    config = LANGUAGE_CONFIG.get(normalised_language, LANGUAGE_CONFIG["en"])

    for fact in facts:
        kind = fact["kind"]
        if kind == "definition":
            cards.extend(
                _definition_cards(
                    fact,
                    card_types,
                    config,
                    normalised_language,
                )
            )
        elif kind == "list":
            cards.extend(_list_cards(fact, card_types, config))
        elif kind == "summary":
            cards.extend(_summary_cards(fact, card_types, config))

        if len(cards) >= max_cards:
            break

    return cards[:max_cards]


def _definition_cards(
    fact: Dict[str, object],
    card_types: List[str],
    config: Dict[str, str],
    language: str,
) -> List[Dict[str, object]]:
    cards: List[Dict[str, object]] = []
    term = fact["term"]
    description = fact["desc"]

    if "qa" in card_types:
        question = config["definition_question"].format(term=term)
        cards.append(
            _make_card(
                "qa",
                question,
                description,
                fact["page"],
                fact["source"],
                ["definition", _slugify(term)],
            )
        )

    if "qa" in card_types and len(description.split()) > 25:
        concise = _first_sentences(description, 2)
        if concise and concise != description:
            question = config["definition_alt"].format(term=term)
            cards.append(
                _make_card(
                    "qa",
                    question,
                    concise,
                    fact["page"],
                    fact["source"],
                    ["definition", "focus", _slugify(term)],
                )
            )

    if "cloze" in card_types and 10 < len(description) < 220:
        if description.lower().startswith(("is", "est")):
            base_sentence = f"{term} {description}"
        else:
            linking = _linking_verb(description, language)
            base_sentence = f"{term} {linking} {description}" if linking else f"{term} {description}"
        sentence = re.sub(r"\s+", " ", base_sentence).strip()
        if term in sentence:
            cloze_sentence = sentence.replace(term, f"{{{{c1::{term}}}}}", 1)
            cards.append(
                _make_card(
                    "cloze",
                    cloze_sentence,
                    "",
                    fact["page"],
                    fact["source"],
                    ["definition", "cloze", _slugify(term)],
                )
            )

    return cards


def _list_cards(
    fact: Dict[str, object], card_types: List[str], config: Dict[str, str]
) -> List[Dict[str, object]]:
    cards: List[Dict[str, object]] = []
    items = fact["items"]

    if "qa" in card_types:
        question = config["list_question"].format(title=fact["title"])
        answer = "; ".join(items)
        cards.append(
            _make_card(
                "qa",
                question,
                answer,
                fact["page"],
                fact["source"],
                ["list", _slugify(fact["title"])],
            )
        )

    if "cloze" in card_types and 2 <= len(items) <= 6:
        formatted_items = _format_enumeration(
            [f"{{{{c{index}::{item}}}}}" for index, item in enumerate(items, start=1)],
            config,
        )
        sentence = config["list_intro"].format(
            title=fact["title"],
            items=formatted_items,
        )
        cards.append(
            _make_card(
                "cloze",
                sentence,
                "",
                fact["page"],
                fact["source"],
                ["list", "cloze", _slugify(fact["title"])],
            )
        )

    return cards


def _summary_cards(
    fact: Dict[str, object],
    card_types: List[str],
    config: Dict[str, str],
) -> List[Dict[str, object]]:
    if "qa" not in card_types:
        return []
    question = config["summary_question"].format(title=fact["title"])
    answer = fact["summary"]
    return [
        _make_card(
            "qa",
            question,
            answer,
            fact["page"],
            fact["source"],
            ["summary", _slugify(fact["title"])],
        )
    ]


def _format_enumeration(items: List[str], config: Dict[str, str]) -> str:
    if len(items) == 1:
        return items[0]
    return config["enum_separator"].join(items[:-1]) + config["enum_last_separator"] + items[-1]


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "note"


def _first_sentences(text: str, limit: int) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    selected = []
    for sentence in sentences:
        clean = sentence.strip()
        if not clean:
            continue
        selected.append(clean)
        if len(selected) >= limit:
            break
    return " ".join(selected)


def _normalise_language(language: str | None) -> str:
    if not language:
        return "en"
    language = language.lower()
    if language.startswith("fr"):
        return "fr"
    if language.startswith("en"):
        return "en"
    return "en"


def _linking_verb(description: str, language: str) -> str:
    if description.lower().startswith(("is", "est")):
        return ""
    if language == "fr":
        return "est"
    return "is"
