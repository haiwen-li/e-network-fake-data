"""PDF fetching and text extraction.

Strategy: stream PDF bytes from URL → extract text with pdfplumber in-memory
          → save only the .txt file (no PDF stored on disk).
"""
from __future__ import annotations
from typing import List

import io
from pathlib import Path

import httpx
import pdfplumber

TEXT_DIR = Path(__file__).parent.parent.parent / "data" / "text"
TEXT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_pdf_as_text(url: str, doc_id: str, timeout: int = 60) -> str:
    """Download a PDF from url, extract text in-memory, save as data/text/<doc_id>.txt.

    Returns the extracted text string.
    Raises httpx.HTTPError on network failure, ValueError if no text extracted.
    """
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        pdf_bytes = response.content

    text = _extract_text_from_bytes(pdf_bytes)
    if not text.strip():
        raise ValueError(f"No text extracted from PDF at {url}")

    save_path = TEXT_DIR / f"{doc_id}.txt"
    save_path.write_text(text, encoding="utf-8")
    return text


def _extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """Extract text from raw PDF bytes using pdfplumber."""
    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
    return "\n\n".join(pages)


def read_text_file(doc_id: str) -> str:
    """Read extracted text from data/text/<doc_id>.txt.

    Also tries an uppercase+underscore variant (e.g. HOUSE_OVERSIGHT_010477.txt)
    to handle documents registered with a lowercase-hyphen slug.
    """
    path = TEXT_DIR / f"{doc_id}.txt"
    if not path.exists():
        alt = TEXT_DIR / f"{doc_id.upper().replace('-', '_')}.txt"
        if alt.exists():
            path = alt
        else:
            raise FileNotFoundError(f"No text file found for doc_id={doc_id!r}. Run fetch first.")
    return path.read_text(encoding="utf-8", errors="ignore")


def register_local_txt(src_path: Path, doc_id: str) -> str:
    """Copy or symlink a local .txt file into data/text/ under doc_id."""
    dest = TEXT_DIR / f"{doc_id}.txt"
    dest.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
    return str(dest)


def text_file_exists(doc_id: str) -> bool:
    return (TEXT_DIR / f"{doc_id}.txt").exists()


def chunk_text(text: str, chunk_size: int = 8000, overlap: int = 500) -> List[str]:
    """Split text into overlapping chunks for Claude extraction.

    chunk_size and overlap are in characters.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks
