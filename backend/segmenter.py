import re
from typing import Dict, List


HEADING_PATTERN = re.compile(
    r"\n(?=[A-Z][A-Z \-]{3,}$|\w[^.\n]{0,40}:\s?$)",
    flags=re.MULTILINE,
)


def split_into_sections(text_by_page: List[str]) -> List[Dict[str, str]]:
    """Split raw page texts into moderately-sized sections."""
    sections: List[Dict[str, str]] = []
    for index, page_text in enumerate(text_by_page, start=1):
        parts = re.split(HEADING_PATTERN, page_text)
        for chunk in parts:
            chunk = chunk.strip()
            if len(chunk) <= 40:
                continue
            sections.append({"page": index, "text": chunk})
    return sections
