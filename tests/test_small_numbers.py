"""A small number must warn wherever it appears in the rendered paper."""

import json
import shutil
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_small_numbers as scanner  # noqa: E402
from check_small_numbers import find_small_numbers  # noqa: E402


def values(text):
    return [hit.value for hit in find_small_numbers(text)]


def test_threshold_is_strict_and_decimals_are_not_split():
    assert values("0 1 37 82 99 99.999 100 100.001 1259 1,283") == [
        Decimal("0"),
        Decimal("1"),
        Decimal("37"),
        Decimal("82"),
        Decimal("99"),
        Decimal("99.999"),
    ]


def test_thousands_separators_never_create_false_small_fragments():
    assert values("1,283 12,916 100.0 1\u2009283 1\u00a0283 1'283 1\u2019283") == []


def test_signed_numbers_and_scientific_notation_use_the_whole_value():
    assert values("-1000 -0.5 +99.2 1e2 1e3 9.9e1 1e-3") == [
        Decimal("-1000"),
        Decimal("-0.5"),
        Decimal("99.2"),
        Decimal("99"),
        Decimal("0.001"),
    ]


def test_page_numbers_citations_versions_percentages_and_dates_are_not_exempt():
    assert values("Page 11; Table 7; references [2, 3]; 4 sources; 55.47%; GPT-6") == [
        Decimal("11"),
        Decimal("7"),
        Decimal("2"),
        Decimal("3"),
        Decimal("4"),
        Decimal("55.47"),
        Decimal("6"),
    ]
    assert values("2026-09-07 v0.11.0 MATH-500") == [
        Decimal("9"),
        Decimal("7"),
        Decimal("0.11"),
        Decimal("0"),
    ]


def test_repeated_numbers_warn_separately_with_their_own_locations():
    hits = list(find_small_numbers("37 reports\n37 models"))
    assert len(hits) == 2
    assert hits[0].line == 1 and hits[1].line == 2
    assert hits[0].start != hits[1].start
    assert "reports" in hits[0].context
    assert "models" in hits[1].context


def test_removed_subset_values_all_trigger_the_warning_condition():
    assert values("16 37 12 8 82 6") == [Decimal(n) for n in [16, 37, 12, 8, 82, 6]]


def test_default_pdf_scan_warns_for_text_and_image_numbers_with_exact_message(
    tmp_path, monkeypatch, capsys
):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"test PDF; extraction mocked at tool boundary")
    report = tmp_path / "warnings.json"
    requested_tools = []

    def tool(name):
        requested_tools.append(name)
        return name

    def run(command):
        if command[0] == "pdftotext":
            return "37 reports\f1283 records\f"
        if command[0] == "pdftoppm":
            prefix = Path(command[-1])
            for page in [1, 2]:
                prefix.with_name(f"page-{page}.png").write_bytes(b"rendered page")
            return ""
        assert command[0] == "tesseract"
        return "99.2 in a raster figure" if command[1].endswith("page-1.png") else "1283"

    monkeypatch.setattr(scanner, "_tool", tool)
    monkeypatch.setattr(scanner, "_run", run)
    assert scanner.main([str(pdf), "--json-output", str(report)]) == 0
    output = capsys.readouterr().err
    message = (
        "less than 100 is abnormal, ref to "
        "https://github.com/ktwu01/benchmark-radar/blob/main/principle.md"
    )
    assert output.count(message) == 2
    assert "page 1" in output and "[pdftotext]" in output and "[ocr]" in output
    assert "number='37'" in output and "number='99.2'" in output
    assert requested_tools == ["pdftotext", "pdftoppm", "tesseract"]
    data = json.loads(report.read_text())
    assert data["pages"] == 2
    assert data["warning_count"] == 2
    assert data["image_coverage"] == "ocr_attempted"
    assert all(w["message"] == message for w in data["warnings"])


def test_missing_ocr_tool_fails_instead_of_silently_skipping_images(tmp_path, monkeypatch, capsys):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"test PDF")
    monkeypatch.setattr(scanner.shutil, "which", lambda name: None if name == "tesseract" else name)
    assert scanner.main([str(pdf)]) == 2
    assert "required tool 'tesseract' is not available" in capsys.readouterr().err


def test_text_only_scan_explicitly_warns_about_unchecked_images(tmp_path, monkeypatch, capsys):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"test PDF")
    monkeypatch.setattr(scanner, "_tool", lambda name: name)
    monkeypatch.setattr(scanner, "_run", lambda command: "1283 records\f")
    assert scanner.main([str(pdf), "--text-only"]) == 0
    output = capsys.readouterr().err
    assert "WARNING: incomplete image coverage" in output


def test_missing_pdf_is_an_error_not_a_clean_warning_scan(tmp_path, capsys):
    assert scanner.main([str(tmp_path / "missing.pdf")]) == 2
    assert "PDF does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("target", ["all", "arxiv"])
def test_standard_build_targets_always_schedule_the_full_number_scan(target):
    if not shutil.which("make"):
        pytest.skip("make is not installed")
    paper = Path(__file__).resolve().parents[1]
    planned = subprocess.check_output(
        ["make", "--no-print-directory", "-n", "-o", "main.pdf", target], cwd=paper, text=True
    )
    assert "scripts/check_small_numbers.py main.pdf" in planned
    assert "--json-output build/small-number-warnings.json" in planned
    assert "--text-only" not in planned


def test_ci_can_skip_number_scan_when_no_numeric_latex_line_changed():
    if not shutil.which("make"):
        pytest.skip("make is not installed")
    paper = Path(__file__).resolve().parents[1]
    planned = subprocess.check_output(
        [
            "make",
            "--no-print-directory",
            "-n",
            "-o",
            "main.pdf",
            "CHECK_SMALL_NUMBERS=0",
            "arxiv",
        ],
        cwd=paper,
        text=True,
    )
    assert "scripts/check_small_numbers.py" not in planned
    assert "Skipping rendered-number scan" in planned
