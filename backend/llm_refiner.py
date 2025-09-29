"""Optional LLM-powered refinement of generated cards."""
from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Optional, Tuple

from llm_utils import OpenAIError, REFINEMENT_MODEL, get_async_client


MAX_CARDS = int(os.getenv("LLM_REFINEMENT_LIMIT", "15"))


async def refine_cards(
    cards: List[Dict[str, object]], language: str | None
) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    """Use an LLM to polish questions/answers when credentials are configured."""

    client = get_async_client()
    if client is None or not cards:
        return cards, {
            "used": False,
            "enriched": 0,
            "model": None,
            "duration_ms": 0,
            "error": None,
        }

    subset = cards[:MAX_CARDS]
    prompt = _build_prompt(subset, language or "en")

    start = time.perf_counter()
    try:
        response = await client.chat.completions.create(  # type: ignore[union-attr]
            model=REFINEMENT_MODEL,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You rewrite flashcards so that they stay factual, concise, and"
                        " faithful to the provided PDF excerpts. Return polished cards"
                        " in JSON and never invent facts beyond the supplied source."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
    except OpenAIError as exc:  # pragma: no cover - depends on network
        return cards, {
            "used": True,
            "enriched": 0,
            "model": REFINEMENT_MODEL,
            "duration_ms": int((time.perf_counter() - start) * 1000),
            "error": str(exc),
        }

    duration_ms = int((time.perf_counter() - start) * 1000)
    message = response.choices[0].message.content if response.choices else ""
    updates = _parse_updates(message)

    enriched = 0
    for card in subset:
        update = updates.get(card["id"], {})
        if not update:
            continue
        enriched += 1
        if "question" in update and isinstance(update["question"], str):
            card["question"] = update["question"].strip()
        if "answer" in update and isinstance(update["answer"], str):
            card["answer"] = update["answer"].strip()
        if "explanation" in update and isinstance(update["explanation"], str):
            card["explanation"] = update["explanation"].strip()
        if "tags" in update and isinstance(update["tags"], list):
            merged_tags = list({*card.get("tags", []), *update["tags"]})
            card["tags"] = sorted(filter(None, merged_tags))
        if "confidence" in update:
            try:
                value = float(update["confidence"])
            except (TypeError, ValueError):
                value = card.get("confidence", 0.7)
            card["confidence"] = max(0.3, min(1.0, value))

    return cards, {
        "used": True,
        "enriched": enriched,
        "model": getattr(response, "model", REFINEMENT_MODEL),
        "duration_ms": duration_ms,
        "error": None,
    }


def _build_prompt(cards: List[Dict[str, object]], language: str) -> str:
    payload = {
        "language": language,
        "cards": [
            {
                "id": card["id"],
                "type": card["type"],
                "question": card["question"],
                "answer": card["answer"],
                "tags": card.get("tags", []),
                "source_snippet": card.get("source_snippet", ""),
            }
            for card in cards
        ],
    }
    instructions = (
        "Polish each card so that it reads naturally in the requested language,"
        " keeps one atomic fact, and cites only details from the source snippet."
        " Provide an optional short explanation summarising why the answer matters."
        " Output JSON with this shape: {\n"
        "  \"cards\": [\n"
        "    {\n"
        "      \"id\": str,\n"
        "      \"question\": str,\n"
        "      \"answer\": str,\n"
        "      \"tags\": [str],\n"
        "      \"explanation\": Optional[str],\n"
        "      \"confidence\": Optional[float]\n"
        "    }\n"
        "  ]\n"
        "}."
    )
    return instructions + "\n\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def _parse_updates(message: Optional[str]) -> Dict[str, Dict[str, object]]:
    if not message:
        return {}
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return {}
    updates: Dict[str, Dict[str, object]] = {}
    for entry in data.get("cards", []):
        card_id = entry.get("id")
        if not isinstance(card_id, str):
            continue
        updates[card_id] = entry
    return updates
