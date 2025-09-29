import re
from typing import Dict, List


DEFINITION_PATTERN = re.compile(
    r"(?:Definition[:\-]\s*)?(.{2,60}?)\s+(?:is|are|est|sont)\s+(.{10,250})",
    flags=re.IGNORECASE,
)


def extract_facts(sections: List[Dict[str, str]]) -> List[Dict[str, object]]:
    """Identify definition and list facts from section text."""
    facts: List[Dict[str, object]] = []
    for section in sections:
        text = section["text"]
        page = section["page"]

        for match in DEFINITION_PATTERN.finditer(text):
            term = match.group(1).strip()
            description = match.group(2).strip().split("\n")[0]
            facts.append(
                {
                    "kind": "definition",
                    "term": term,
                    "desc": description,
                    "page": page,
                    "source": text[:400],
                }
            )

        bullet_lines = [
            line.strip("•- \t")
            for line in text.splitlines()
            if line.strip().startswith(("•", "-"))
        ]
        if 2 <= len(bullet_lines) <= 8:
            title = text.splitlines()[0][:80]
            facts.append(
                {
                    "kind": "list",
                    "title": title,
                    "items": bullet_lines,
                    "page": page,
                    "source": text[:400],
                }
            )

    return facts
