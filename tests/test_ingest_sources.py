"""The ingest source count is derived, so the manuscript cannot drift from the code."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))

from export_report_figure_data import count_ingest_sources  # noqa: E402

FIGURE_DATA = ROOT / "docs/technical-report/latex/figure-data.tex"


def _macro(name: str) -> int:
    match = re.search(rf"\\newcommand\{{\\{name}\}}\{{(\d+)\}}", FIGURE_DATA.read_text())
    assert match, f"{name} is missing from figure-data.tex"
    return int(match.group(1))


def test_exported_counts_match_the_live_registry() -> None:
    connectors, feeds = count_ingest_sources(ROOT)
    assert _macro("ReportConnectorCount") == connectors
    assert _macro("ReportFirstPartyFeedCount") == feeds
    assert _macro("ReportIngestSourceCount") == connectors + feeds


def test_ingest_total_is_the_sum_of_its_parts() -> None:
    total = _macro("ReportIngestSourceCount")
    assert total == _macro("ReportConnectorCount") + _macro("ReportFirstPartyFeedCount")


def test_first_party_rollup_is_not_double_counted() -> None:
    """`fetch_first_party_feeds` expands into the feeds; counting both would inflate it."""
    connectors, _ = count_ingest_sources(ROOT)
    fetchers = re.findall(
        r"^def (fetch_\w+)", (ROOT / "src/benchmark_radar/sources.py").read_text(), re.M
    )
    assert "fetch_first_party_feeds" in fetchers
    assert connectors == len(set(fetchers)) - 1
