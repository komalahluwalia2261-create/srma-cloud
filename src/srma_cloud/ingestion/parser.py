"""
Turns raw bytes fetched from a StorageAdapter into text the prompt engine
can screen, plus a dedup key so re-runs don't re-screen unchanged files.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from typing import Optional

from pypdf import PdfReader


@dataclass
class ParsedDocument:
    text: str
    content_hash: str
    page_count: Optional[int] = None
    likely_scanned: bool = False


def parse(raw_bytes: bytes, mime_type: str) -> ParsedDocument:
    if mime_type == "application/pdf":
        return _parse_pdf(raw_bytes)
    if mime_type in ("text/plain", "text/csv", "application/x-research-info-systems"):
        text = raw_bytes.decode("utf-8", errors="replace")
        return ParsedDocument(text=text, content_hash=_hash(raw_bytes))
    raise ValueError(f"Unsupported mime type for parsing: {mime_type}")


def _parse_pdf(raw_bytes: bytes) -> ParsedDocument:
    reader = PdfReader(io.BytesIO(raw_bytes))
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    text = "\n".join(pages_text)

    # Heuristic: a PDF with pages but near-zero extracted characters is
    # almost certainly a scan. Flag it rather than silently screening on
    # an empty string — the caller should route these to OCR or to a
    # human-review queue instead of the LLM.
    avg_chars_per_page = len(text) / max(len(reader.pages), 1)
    likely_scanned = avg_chars_per_page < 20

    return ParsedDocument(
        text=text,
        content_hash=_hash(raw_bytes),
        page_count=len(reader.pages),
        likely_scanned=likely_scanned,
    )


def _hash(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()
