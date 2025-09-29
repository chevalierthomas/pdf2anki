import re
from typing import Dict, Iterable, List


DEFINITION_PATTERN = re.compile(
    r"(?:Definition[:\-]\s*)?(.{2,60}?)\s+(?:is|are|refers to|means|est|sont|désigne)\s+(.{10,250})",
    flags=re.IGNORECASE,
)
COLON_DEFINITION_PATTERN = re.compile(
    r"^(?:\d+\.\s*)?(.{2,70}?)\s*[:\-–—]\s+(.{10,250})$",
    flags=re.IGNORECASE | re.MULTILINE,
)
ENUMERATION_PATTERNS: Iterable[re.Pattern[str]] = (
    re.compile(r"(.+?)\s+(?:consists of|includes|comprises|contains)\s+(.+)", re.IGNORECASE),
    re.compile(
        r"(.+?)\s+(?:se compose de|comprend|comprennent|inclut|incluent)\s+(.+)",
        re.IGNORECASE,
    ),
)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-ZÉÈÊÀÂÇÎÔÙ0-9])")


def extract_facts(
    sections: List[Dict[str, str]], language: str = "en"
) -> List[Dict[str, object]]:
    """Identify definition, list and summary facts from section text."""

    facts: List[Dict[str, object]] = []
    normalized_language = _normalise_language(language)

    seen_definitions = set()

    for section in sections:
        text = section["text"]
        raw_text = section.get("raw", text)
        page = section["page"]

        for term, description, snippet in _definition_candidates(text, raw_text):
            key = (term.lower(), description.lower())
            if key in seen_definitions:
                continue
            seen_definitions.add(key)
            facts.append(
                {
                    "kind": "definition",
                    "term": term,
                    "desc": description,
                    "page": page,
                    "source": snippet,
                }
            )

        for title, items, snippet in _list_candidates(text, raw_text, normalized_language):
            facts.append(
                {
                    "kind": "list",
                    "title": title,
                    "items": items,
                    "page": page,
                    "source": snippet,
                }
            )

        summary_fact = _summary_candidate(section, normalized_language)
        if summary_fact:
            summary_fact.update({"page": page, "source": raw_text[:400]})
            facts.append(summary_fact)

    return facts


def _definition_candidates(text: str, raw_text: str) -> Iterable[tuple[str, str, str]]:
    snippet = raw_text[:400]

    for match in DEFINITION_PATTERN.finditer(text):
        term = match.group(1).strip()
        description = match.group(2).strip().split("\n")[0]
        if len(term) < 2 or len(description) < 10:
            continue
        yield term, description, snippet

    for match in COLON_DEFINITION_PATTERN.finditer(text):
        term = match.group(1).strip()
        description = match.group(2).strip()
        if len(term) < 2 or len(description) < 10:
            continue
        yield term, description, snippet


def _list_candidates(
    text: str, raw_text: str, language: str
) -> Iterable[tuple[str, List[str], str]]:
    snippet = raw_text[:400]

    bullet_lines = [
        line.strip("•- \t")
        for line in text.splitlines()
        if line.strip().startswith(("•", "-"))
    ]
    if 2 <= len(bullet_lines) <= 8:
        title = _pick_title(text, bullet_lines[0])
        yield title, _clean_items(bullet_lines), snippet

    numbered_lines = [
        re.sub(r"^\s*\d+[\.)]\s*", "", line).strip()
        for line in text.splitlines()
        if re.match(r"^\s*\d+[\.)]\s+", line)
    ]
    if 2 <= len(numbered_lines) <= 8:
        title = _pick_title(text, numbered_lines[0])
        yield title, _clean_items(numbered_lines), snippet

    sentences = _split_sentences(text)
    for sentence in sentences:
        for pattern in ENUMERATION_PATTERNS:
            match = pattern.match(sentence)
            if not match:
                continue
            title = match.group(1).strip()
            raw_items = match.group(2).strip()
            items = _split_enumeration(raw_items, language)
            if 2 <= len(items) <= 8:
                yield title, _clean_items(items), snippet


def _summary_candidate(section: Dict[str, str], language: str) -> Dict[str, object] | None:
    heading = section.get("heading", "").strip()
    text = section["text"]
    if not heading or len(heading) < 4:
        return None

    sentences = [s for s in _split_sentences(text) if len(s) >= 30]
    if not sentences:
        return None

    summary = " ".join(sentences[:2]).strip()
    if len(summary) < 40 or len(summary) > 320:
        return None

    return {
        "kind": "summary",
        "title": heading,
        "summary": summary,
        "language": language,
    }


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = SENTENCE_SPLIT_PATTERN.split(text)
    if not parts:
        return [text.strip()]
    return [part.strip() for part in parts if part.strip()]


def _pick_title(text: str, fallback: str) -> str:
    first_line = text.splitlines()[0].strip()
    if len(first_line) > 6 and len(first_line) <= 120:
        return first_line
    return fallback[:80]


def _split_enumeration(items: str, language: str) -> List[str]:
    delimiters = [",", ";", " • "]
    normalized_language = _normalise_language(language)
    if normalized_language == "fr":
        delimiters.extend([" et ", " ou "])
    else:
        delimiters.extend([" and ", " or "])

    pattern = re.compile("|".join(map(re.escape, delimiters)))
    return [chunk.strip() for chunk in pattern.split(items) if chunk.strip()]


def _clean_items(items: Iterable[str]) -> List[str]:
    cleaned = []
    seen = set()
    for item in items:
        value = re.sub(r"\s+", " ", item).strip()
        if not value or value.lower() in seen:
            continue
        seen.add(value.lower())
        cleaned.append(value)
    return cleaned


def _normalise_language(language: str | None) -> str:
    if not language:
        return "en"
    language = language.lower()
    if language.startswith("fr"):
        return "fr"
    if language.startswith("en"):
        return "en"
    return "en"
