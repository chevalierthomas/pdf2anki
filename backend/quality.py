import hashlib
from typing import Dict, List


def apply_checks(cards: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Deduplicate and enforce length constraints on generated cards."""
    seen_hashes = set()
    filtered: List[Dict[str, object]] = []

    for card in cards:
        fingerprint = hashlib.sha1(
            (card["type"] + card["question"] + card["answer"]).encode()
        ).hexdigest()
        if fingerprint in seen_hashes:
            continue
        seen_hashes.add(fingerprint)

        if len(card["question"]) > 240:
            card["question"] = card["question"][:240] + "…"
        if len(card["answer"]) > 280:
            card["answer"] = card["answer"][:280] + "…"

        filtered.append(card)

    return filtered
