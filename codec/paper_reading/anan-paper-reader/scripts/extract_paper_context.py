#!/usr/bin/env python3
"""Extract paper text, metadata, section snippets, and model-figure candidates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FIGURE_KEYWORDS = {
    "overview": 10,
    "framework": 9,
    "architecture": 9,
    "pipeline": 8,
    "model": 7,
    "proposed method": 8,
    "method": 5,
    "approach": 4,
    "system": 3,
}

SECTION_PATTERNS = {
    "title_author_block": r"(?s)\A(.{0,2500})",
    "abstract": r"(?im)^\s*(abstract)\s*$|^\s*abstract[\s.:\u2014-]+",
    "introduction": r"(?im)^\s*(\d+\.?\s*)?introduction\s*$",
    "related_work": r"(?im)^\s*(\d+\.?\s*)?(related work|background|preliminaries)\s*$",
    "method": r"(?im)^\s*(\d+\.?\s*)?(method|methodology|approach|proposed method|model|framework)\s*$",
    "experiments": r"(?im)^\s*(\d+\.?\s*)?(experiments|experimental setup|evaluation|results)\s*$",
    "conclusion": r"(?im)^\s*(\d+\.?\s*)?(conclusion|conclusions)\s*$",
    "limitations": r"(?im)^\s*(\d+\.?\s*)?(limitations|limitation|discussion)\s*$",
    "appendix": r"(?im)^\s*(appendix|appendices|supplementary material)\b",
}


@dataclass
class FigureCandidate:
    page: int
    score: int
    caption_or_context: str


def load_reader(pdf_path: Path):
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError(
            "Missing pypdf. Use the Codex bundled Python runtime or install pypdf."
        ) from exc
    return PdfReader(str(pdf_path))


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_by_page(reader: Any) -> list[str]:
    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            text = f"[TEXT_EXTRACTION_ERROR: {exc}]"
        pages.append(clean_text(text))
    return pages


def write_page_text(pages: list[str], out_path: Path) -> None:
    chunks = []
    for index, text in enumerate(pages, start=1):
        chunks.append(f"\n\n## Page {index}\n\n{text if text else '[NO_TEXT_EXTRACTED]'}")
    out_path.write_text("# Extracted Paper Text\n" + "".join(chunks).strip() + "\n", encoding="utf-8")


def metadata_to_jsonable(reader: Any, pdf_path: Path, pages: list[str]) -> dict[str, Any]:
    try:
        raw_meta = reader.metadata or {}
        raw = {str(key): str(value) for key, value in raw_meta.items()}
    except Exception as exc:
        raw = {"metadata_error": str(exc)}
    nonempty_pages = sum(1 for page in pages if len(page.strip()) > 80)
    return {
        "pdf_file": str(pdf_path),
        "page_count": len(pages),
        "nonempty_text_pages": nonempty_pages,
        "text_extraction_quality": "ok" if nonempty_pages else "empty_or_failed",
        "raw_pdf_metadata": raw,
    }


def snippet_around(text: str, start: int, width: int = 5000) -> str:
    return clean_text(text[start : start + width])


def extract_section_snippets(full_text: str) -> dict[str, str]:
    snippets: dict[str, str] = {}
    for name, pattern in SECTION_PATTERNS.items():
        match = re.search(pattern, full_text)
        snippets[name] = snippet_around(full_text, match.start()) if match else ""
    return snippets


def write_section_snippets(snippets: dict[str, str], out_path: Path) -> None:
    parts = ["# Likely Section Snippets\n"]
    for name, snippet in snippets.items():
        parts.append(f"\n## {name}\n\n{snippet if snippet else '[NOT_FOUND]'}\n")
    out_path.write_text("".join(parts), encoding="utf-8")


def candidate_score(text: str, page_number: int) -> int:
    lower = text.lower()
    if not re.search(r"\b(fig\.?|figure)\s*\d+", lower):
        return 0
    score = 1
    for keyword, value in FIGURE_KEYWORDS.items():
        if keyword in lower:
            score += value
    if re.search(r"\b(fig\.?|figure)\s*1\b", lower):
        score += 4
    if page_number <= 4:
        score += 3
    elif page_number <= 8:
        score += 1
    if any(term in lower for term in ("result", "qualitative", "confusion matrix", "roc", "precision-recall")):
        score -= 2
    return score


def find_figure_candidates(pages: list[str]) -> list[FigureCandidate]:
    candidates: list[FigureCandidate] = []
    caption_re = re.compile(
        r"(?is)\b(?:fig\.?|figure)\s*\d+[:.\-\s].{0,900}?(?=(?:\n\s*(?:fig\.?|figure)\s*\d+[:.\-\s])|\n\s*\d+\.?\s+[A-Z][A-Za-z ]{2,80}\n|$)"
    )
    for page_index, page_text in enumerate(pages, start=1):
        matches = list(caption_re.finditer(page_text))
        if matches:
            for match in matches:
                caption = clean_text(match.group(0))
                score = candidate_score(caption, page_index)
                if score > 0:
                    candidates.append(FigureCandidate(page_index, score, caption))
            continue
        lines = page_text.splitlines()
        for line_index, line in enumerate(lines):
            if re.search(r"\b(fig\.?|figure)\s*\d+", line, re.I):
                context = " ".join(lines[max(0, line_index - 2) : min(len(lines), line_index + 4)])
                score = candidate_score(context, page_index)
                if score > 0:
                    candidates.append(FigureCandidate(page_index, score, clean_text(context)))
    candidates.sort(key=lambda item: (-item.score, item.page))
    return candidates


def write_candidates(candidates: list[FigureCandidate], out_path: Path) -> None:
    data = [
        {"page": item.page, "score": item.score, "caption_or_context": item.caption_or_context}
        for item in candidates
    ]
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Input academic paper PDF")
    parser.add_argument("--out", type=Path, default=Path("anan-paper-reader-output"), help="Output directory")
    args = parser.parse_args()

    pdf_path = args.pdf.expanduser().resolve()
    out_dir = args.out.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    try:
        reader = load_reader(pdf_path)
    except RuntimeError as exc:
        (out_dir / "extraction_error.txt").write_text(str(exc) + "\n", encoding="utf-8")
        print(str(exc), file=sys.stderr)
        return 3

    pages = extract_text_by_page(reader)
    full_text = "\n\n".join(pages)

    write_page_text(pages, out_dir / "paper_text.md")
    metadata = metadata_to_jsonable(reader, pdf_path, pages)
    (out_dir / "paper_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    snippets = extract_section_snippets(full_text)
    write_section_snippets(snippets, out_dir / "section_snippets.md")

    candidates = find_figure_candidates(pages)
    write_candidates(candidates, out_dir / "figure_candidates.json")

    print(f"Wrote: {out_dir / 'paper_text.md'}")
    print(f"Wrote: {out_dir / 'paper_metadata.json'}")
    print(f"Wrote: {out_dir / 'section_snippets.md'}")
    print(f"Wrote: {out_dir / 'figure_candidates.json'}")
    if metadata["text_extraction_quality"] != "ok":
        print("Warning: extracted text appears empty; try OCR or PDF-to-image conversion.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
