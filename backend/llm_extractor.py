"""LLM-driven card extraction with chunked prompts."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from llm_utils import EXTRACTION_MODEL, OpenAIError, estimate_tokens, get_async_client


MAX_CHUNK_TOKENS = int(os.getenv("LLM_MAX_CHUNK_TOKENS", "3200"))
CHUNK_OVERLAP = int(os.getenv("LLM_CHUNK_OVERLAP_TOKENS", "200"))


@dataclass
class Section:
    page: int
    text: str


@dataclass
class Chunk:
    text: str
    start_page: int
    end_page: int


async def generate_cards(
    sections: Sequence[Dict[str, object]],
    language: str,
    card_types: Sequence[str],
    max_cards: int,
) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    """Generate flashcards with an LLM using chunked prompts."""

    client = get_async_client()
    if client is None:
        return [], {
            "used": False,
            "generated": 0,
            "chunks": 0,
            "model": None,
            "duration_ms": 0,
            "error": "OpenAI API key not configured on server",
        }

    normalized = _normalise_sections(sections)
    if not normalized:
        return [], {
            "used": False,
            "generated": 0,
            "chunks": 0,
            "model": EXTRACTION_MODEL,
            "duration_ms": 0,
            "error": None,
        }

    chunks = list(_build_chunks(normalized))
    cards: List[Dict[str, object]] = []
    total_duration = 0

    for idx, chunk in enumerate(chunks, start=1):
        remaining = max_cards - len(cards)
        if remaining <= 0:
            break

        prompt = _build_prompt(chunk, language, card_types, remaining)
        chunk_start = time.perf_counter()
        try:
            response = await client.chat.completions.create(  # type: ignore[union-attr]
                model=EXTRACTION_MODEL,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You analyse textbook excerpts and produce factual Anki flashcards"
                            " in the requested language. Only quote information explicitly"
                            " present in the text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except OpenAIError as exc:  # pragma: no cover - depends on network
            return cards, {
                "used": True,
                "generated": len(cards),
                "chunks": idx,
                "model": EXTRACTION_MODEL,
                "duration_ms": int(total_duration * 1000),
                "error": str(exc),
            }

        chunk_duration = time.perf_counter() - chunk_start
        total_duration += chunk_duration
        message = response.choices[0].message.content if response.choices else ""
        cards.extend(_parse_cards(message, chunk, card_types, remaining))

    cards = cards[:max_cards]
    return cards, {
        "used": True,
        "generated": len(cards),
        "chunks": len(chunks),
        "model": EXTRACTION_MODEL,
        "duration_ms": int(total_duration * 1000),
        "error": None,
    }


def _normalise_sections(sections: Sequence[Dict[str, object]]) -> List[Section]:
    normalised: List[Section] = []
    for entry in sections:
        text = str(entry.get("text", "")).strip()
        if not text:
            continue
        page_raw = entry.get("page", 1)
        try:
            page = int(page_raw)
        except (TypeError, ValueError):
            page = 1
        normalised.append(Section(page=page, text=text))
    return normalised


def _build_chunks(sections: Sequence[Section]) -> Iterable[Chunk]:
    if not sections:
        return []

    buffer: List[Section] = []
    current_tokens = 0

    for section in sections:
        tokens = estimate_tokens(section.text)
        if buffer and current_tokens + tokens > MAX_CHUNK_TOKENS:
            yield Chunk(
                text="\n\n".join(item.text for item in buffer),
                start_page=buffer[0].page,
                end_page=buffer[-1].page,
            )
            if CHUNK_OVERLAP > 0 and buffer:
                overlap: List[Section] = []
                overlap_tokens = 0
                for previous in reversed(buffer):
                    overlap.insert(0, previous)
                    overlap_tokens += estimate_tokens(previous.text)
                    if overlap_tokens >= CHUNK_OVERLAP:
                        break
                buffer = overlap + [section]
            else:
                buffer = [section]
            current_tokens = sum(estimate_tokens(item.text) for item in buffer)
        else:
            buffer.append(section)
            current_tokens += tokens

    if buffer:
        yield Chunk(
            text="\n\n".join(item.text for item in buffer),
            start_page=buffer[0].page,
            end_page=buffer[-1].page,
        )


def _build_prompt(
    chunk: Chunk, language: str, card_types: Sequence[str], remaining: int
) -> str:
    card_list = ", ".join(card_types) if card_types else "qa"
    instructions = (
        "Analyse the following PDF excerpt spanning pages "
        f"{chunk.start_page} to {chunk.end_page}. "
        f"Create up to {remaining} concise Anki cards in JSON format. "
        f"Only produce the supported card types: {card_list}. "
        "Each card must be grounded in the excerpt and include the page number "
        "and a short source snippet to justify the answer."
    )
    schema = (
        "Return JSON like:\n"
        "{\n  \"cards\": [\n    {\n      \"type\": \"qa|cloze\",\n"
        "      \"question\": str,\n      \"answer\": str,\n      \"tags\": [str],\n"
        "      \"explanation\": Optional[str],\n      \"source_page\": int,\n"
        "      \"source_snippet\": str,\n      \"confidence\": Optional[float]\n"
        "    }\n  ]\n}\n"
        "If the excerpt lacks enough information, return an empty list."
    )
    prompt = (
        f"Language: {language}\n"
        f"Supported card types: {card_list}\n"
        f"Maximum cards for this chunk: {remaining}\n"
        f"Excerpt:\n{chunk.text}"
    )
    return instructions + "\n\n" + schema + "\n\n" + prompt


def _parse_cards(
    message: Optional[str],
    chunk: Chunk,
    allowed_types: Sequence[str],
    remaining: int,
) -> List[Dict[str, object]]:
    if not message:
        return []
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return []

    results: List[Dict[str, object]] = []
    for entry in payload.get("cards", []):
        if len(results) >= remaining:
            break
        card_type = entry.get("type", "qa")
        if card_type not in allowed_types:
            continue
        question = entry.get("question")
        answer = entry.get("answer", "")
        if not isinstance(question, str) or not question.strip():
            continue
        if not isinstance(answer, str):
            answer = ""
        tags = entry.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        source_page = entry.get("source_page", chunk.start_page)
        try:
            page = int(source_page)
        except (TypeError, ValueError):
            page = chunk.start_page
        snippet = entry.get("source_snippet")
        if not isinstance(snippet, str) or not snippet.strip():
            snippet = chunk.text[:400]
        confidence = entry.get("confidence")
        try:
            confidence_value = float(confidence) if confidence is not None else 0.7
        except (TypeError, ValueError):
            confidence_value = 0.7
        explanation = entry.get("explanation")
        if explanation is not None and not isinstance(explanation, str):
            explanation = None
        results.append(
            {
                "id": uuid.uuid4().hex[:12],
                "type": card_type,
                "question": question.strip(),
                "answer": answer.strip(),
                "tags": [t for t in tags if isinstance(t, str) and t],
                "source_page": page,
                "source_snippet": snippet.strip(),
                "confidence": max(0.3, min(1.0, confidence_value)),
                "explanation": explanation.strip() if isinstance(explanation, str) else None,
            }
        )
    return results

