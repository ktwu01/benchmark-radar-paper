#!/usr/bin/env python3
"""Warn about every extracted numeric occurrence below 100 in the rendered paper.

This is a review alarm, not evidence that a number is wrong. No categories are
exempt: page numbers, references, dates, model versions, scores and percentages
are included. Values and frozen evidence are never changed by this scanner.

The default scan combines the PDF text layer with OCR of every rendered page.
The two extraction methods may report the same visible occurrence; each warning
names its method. OCR improves image coverage but cannot guarantee recognition
of every glyph. ``--text-only`` explicitly opts out of checking image-only text.

Numeric literals support signs, decimals, e notation, and comma, apostrophe or
nonbreaking/thin-space thousands groups. Ordinary spaces delimit numbers, since
merging them would join separate table columns. Hyphens following a word or a
number (for example GPT-6 or 2026-09-07) delimit components rather than negate
them. The pure ``iter_numbers`` and ``find_small_numbers`` APIs preserve every
occurrence and its location in the supplied text.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

WARNING_MESSAGE = (
    "less than 100 is abnormal, ref to "
    "https://github.com/ktwu01/benchmark-radar/blob/main/principle.md"
)
INCOMPLETE_IMAGE_WARNING = (
    "incomplete image coverage: --text-only skips image-only numbers; "
    "run the default OCR scan to review rendered figures and screenshots"
)
OCR_CAVEAT = (
    "OCR was attempted on every rendered page; recognition can miss or misread "
    "glyphs, so this scan does not replace visual review."
)
THRESHOLD = Decimal("100")
_GROUP_SEPARATOR = r"[,\u00a0\u2009\u202f'\u2019]"
_MANTISSA = (
    rf"(?:[0-9]{{1,3}}(?:{_GROUP_SEPARATOR}[0-9]{{3}})+|[0-9]+)"
    r"(?:\.[0-9]+)?|\.[0-9]+"
)
# A sign following a name/date component is a separator. Exponent signs belong
# to the exponent and are consumed together with the complete numeric literal.
_NUMBER = re.compile(
    rf"(?:(?<![\w.)])[-+\u2212])?(?:{_MANTISSA})"
    r"(?:[eE][-+\u2212]?[0-9]+)?"
)
_REMOVE_GROUPING = re.compile(_GROUP_SEPARATOR)


class ScanError(RuntimeError):
    """A missing input/tool or failed extraction prevents a complete scan."""


@dataclass(frozen=True)
class NumberOccurrence:
    text: str
    value: Decimal
    start: int
    end: int
    line: int
    column: int
    context: str


@dataclass(frozen=True)
class PaperNumberWarning:
    page: int
    method: str
    occurrence: NumberOccurrence

    def to_dict(self) -> dict:
        record = asdict(self.occurrence)
        record["value"] = str(self.occurrence.value)
        return {
            "page": self.page,
            "method": self.method,
            **record,
            "message": WARNING_MESSAGE,
        }


@dataclass(frozen=True)
class PdfScan:
    pdf: str
    pages: int
    ocr: bool
    warnings: tuple[PaperNumberWarning, ...]

    def to_dict(self) -> dict:
        return {
            "pdf": self.pdf,
            "pages": self.pages,
            "threshold": str(THRESHOLD),
            "methods": ["pdftotext", "ocr"] if self.ocr else ["pdftotext"],
            "image_coverage": "ocr_attempted" if self.ocr else "not_scanned",
            "coverage_note": OCR_CAVEAT if self.ocr else INCOMPLETE_IMAGE_WARNING,
            "warning_count": len(self.warnings),
            "warnings": [warning.to_dict() for warning in self.warnings],
        }


def iter_numbers(text: str) -> Iterator[NumberOccurrence]:
    """Yield numeric literals with 1-based lines/columns and exact text offsets."""
    for match in _NUMBER.finditer(text):
        literal = match.group()
        normalized = _REMOVE_GROUPING.sub("", literal).replace("\u2212", "-")
        try:
            value = Decimal(normalized)
        except InvalidOperation as error:
            raise ValueError(f"Cannot parse numeric literal {literal!r}") from error
        start, end = match.span()
        line_start = text.rfind("\n", 0, start) + 1
        context_start = max(0, start - 65)
        context_end = min(len(text), end + 65)
        yield NumberOccurrence(
            text=literal,
            value=value,
            start=start,
            end=end,
            line=text.count("\n", 0, start) + 1,
            column=start - line_start + 1,
            context=" ".join(text[context_start:context_end].split()),
        )


def find_small_numbers(text: str, threshold: Decimal = THRESHOLD) -> list[NumberOccurrence]:
    """Return every occurrence strictly below the threshold, without exemptions."""
    return [occurrence for occurrence in iter_numbers(text) if occurrence.value < threshold]


def _tool(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise ScanError(f"required tool {name!r} is not available on PATH")
    return executable


def _run(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except FileNotFoundError as error:
        raise ScanError(f"required tool is missing: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "no diagnostic output").strip()
        raise ScanError(f"{Path(command[0]).name} failed: {detail}") from error
    except OSError as error:
        raise ScanError(f"cannot run {command[0]}: {error}") from error
    return result.stdout


def _pages(text: str) -> list[str]:
    pages = text.split("\f")
    # Poppler writes a form feed after the last page, including an empty page.
    if pages and not pages[-1].strip():
        pages.pop()
    if not pages:
        raise ScanError("pdftotext did not produce any PDF pages")
    return pages


def scan_pdf(pdf: Path | str, *, ocr: bool = True, dpi: int = 200) -> PdfScan:
    """Scan PDF text and, by default, OCR of every rendered page; fail visibly."""
    path = Path(pdf).resolve()
    if not path.is_file():
        raise ScanError(f"PDF does not exist: {path}")
    if dpi <= 0:
        raise ScanError("render resolution must be positive")
    pdftotext = _tool("pdftotext")
    # Check all requested tools before doing an expensive partial extraction.
    pdftoppm = _tool("pdftoppm") if ocr else None
    tesseract = _tool("tesseract") if ocr else None
    pages = _pages(_run([pdftotext, "-layout", "-enc", "UTF-8", str(path), "-"]))
    warnings = [
        PaperNumberWarning(page=page_number, method="pdftotext", occurrence=occurrence)
        for page_number, page_text in enumerate(pages, start=1)
        for occurrence in find_small_numbers(page_text)
    ]
    if ocr:
        with tempfile.TemporaryDirectory(prefix="paper-small-numbers-") as directory:
            prefix = Path(directory) / "page"
            _run([pdftoppm, "-png", "-r", str(dpi), str(path), str(prefix)])
            images = sorted(
                Path(directory).glob("page-*.png"),
                key=lambda image: int(image.stem.rsplit("-", 1)[1]),
            )
            page_numbers = [int(image.stem.rsplit("-", 1)[1]) for image in images]
            expected = list(range(1, len(pages) + 1))
            if page_numbers != expected:
                raise ScanError(
                    f"page extraction mismatch: pdftotext has {len(pages)} pages, "
                    f"pdftoppm rendered page numbers {page_numbers}"
                )
            for page_number, image in zip(page_numbers, images, strict=True):
                page_text = _run([tesseract, str(image), "stdout", "--psm", "11"])
                warnings.extend(
                    PaperNumberWarning(page=page_number, method="ocr", occurrence=occurrence)
                    for occurrence in find_small_numbers(page_text)
                )
    return PdfScan(pdf=str(path), pages=len(pages), ocr=ocr, warnings=tuple(warnings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", nargs="?", type=Path, default=Path("main.pdf"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--text-only",
        dest="ocr",
        action="store_false",
        help="scan the PDF text layer only; explicitly reports incomplete image coverage",
    )
    mode.add_argument(
        "--ocr", dest="ocr", action="store_true", help="scan PDF text and page OCR (default)"
    )
    parser.set_defaults(ocr=True)
    parser.add_argument("--dpi", type=int, default=200, help="OCR rendering DPI (default: 200)")
    parser.add_argument("--json-output", type=Path, help="write the complete occurrence report")
    args = parser.parse_args(argv)
    try:
        result = scan_pdf(args.pdf, ocr=args.ocr, dpi=args.dpi)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(
                json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    except (ScanError, OSError, ValueError) as error:
        print(f"ERROR: small-number scan failed: {error}", file=sys.stderr)
        return 2
    if not result.ocr:
        print(f"WARNING: {INCOMPLETE_IMAGE_WARNING}", file=sys.stderr)
    for warning in result.warnings:
        occurrence = warning.occurrence
        print(
            f"WARNING: {WARNING_MESSAGE} | {result.pdf}:page {warning.page}:"
            f"line {occurrence.line}:column {occurrence.column} [{warning.method}] "
            f"number={occurrence.text!r}, value={occurrence.value} | {occurrence.context}",
            file=sys.stderr,
        )
    print(
        f"Scanned {result.pages} pages with "
        f"{'pdftotext and OCR' if result.ocr else 'pdftotext only'}; "
        f"{len(result.warnings)} numeric occurrences below {THRESHOLD}. "
        f"{OCR_CAVEAT if result.ocr else INCOMPLETE_IMAGE_WARNING}",
        file=sys.stderr,
    )
    # Small numbers are review warnings. Extraction/report failures are errors.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
