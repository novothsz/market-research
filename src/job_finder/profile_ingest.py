from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def _read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Profile file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _read_pdf_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Profile file not found: {path}")
    
    reader = PdfReader(path)
    text_parts: list[str] = []
    
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            text_parts.append(text)
    
    return "\n\n".join(text_parts).strip()


def load_profile(profile_file: Path | None = None, profile_text: str | None = None) -> str:
    chunks: list[str] = []
    if profile_file is not None:
        if profile_file.suffix.lower() == ".pdf":
            chunks.append(_read_pdf_file(profile_file))
        else:
            chunks.append(_read_text_file(profile_file))
    if profile_text:
        chunks.append(profile_text.strip())
    return "\n\n".join(c for c in chunks if c)
