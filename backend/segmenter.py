import re
from typing import Dict, List


HEADING_PATTERN = re.compile(
    r"\n(?=[A-Z][A-Z \-]{3,}$|\w[^.\n]{0,40}:\s?$)",
    flags=re.MULTILINE,
)


def split_into_sections(text_by_page: List[str]) -> List[Dict[str, str]]:
    """Split raw page texts into moderately-sized sections with optional headings."""
    sections: List[Dict[str, str]] = []
    for index, page_text in enumerate(text_by_page, start=1):
        parts = re.split(HEADING_PATTERN, page_text)
        for chunk in parts:
            chunk = chunk.strip()
            if len(chunk) <= 40:
                continue

            lines = [line.strip() for line in chunk.splitlines() if line.strip()]
            if not lines:
                continue

            heading = lines[0]
            body_lines = lines[1:]
            body = "\n".join(body_lines).strip()

            if not body:
                body = chunk

            sections.append(
                {
                    "page": index,
                    "text": body,
                    "heading": heading,
                    "raw": chunk,
                }
            )
    return sections
