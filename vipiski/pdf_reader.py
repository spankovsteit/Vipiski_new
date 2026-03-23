"""
PDF → Unicode text using PyPDF2.

Limitations
-----------
``extract_text()`` quality depends on how the bank embeds fonts. If a statement
starts failing to match regex rules, consider pdfplumber or OCR — but keep the
public function signature ``extract_pdf_text(path) -> str`` so ``engine.py`` stays
unchanged.
"""

from __future__ import annotations

from pathlib import Path

from PyPDF2 import PdfReader


def extract_pdf_text(pdf_path: Path) -> str:
    """Concatenate non-empty page texts in order."""
    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "".join(parts)
