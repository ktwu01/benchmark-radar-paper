"""Inventory checks work in a standalone paper checkout, including CI."""

import re
import sys
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER / "scripts"))

from verify_frozen_findings import ingest_counts, with_ingest_inventory  # noqa: E402


def inventory(tmp_path):
    sources = tmp_path / "src/benchmark_radar"
    sources.mkdir(parents=True)
    (sources / "sources.py").write_text(
        "def fetch_arxiv(): pass\n"
        "def fetch_github(): pass\n"
        "def fetch_first_party_feeds(): pass\n"
        "def helper(): pass\n"
    )
    (tmp_path / "config.yml").write_text(
        "sources:\n  first_party_feeds:\n    feeds:\n"
        "      - name: Lab A\n      - name: Lab B\n      - name: Lab C\n"
    )
    return tmp_path


def test_feed_rollup_and_helpers_are_not_connectors(tmp_path):
    assert ingest_counts(inventory(tmp_path)) == (2, 3)


def test_inventory_extension_preserves_all_original_figure_lines(tmp_path):
    original = (
        "% frozen input hash\n"
        "\\newcommand{\\ReportCatalogSourceCount}{4}\n"
        "\\newcommand{\\ReportCatalogCount}{1283}\n"
    )
    augmented = with_ingest_inventory(original, inventory(tmp_path))
    assert "\\newcommand{\\ReportConnectorCount}{2}\n" in augmented
    assert "\\newcommand{\\ReportFirstPartyFeedCount}{3}\n" in augmented
    assert "\\newcommand{\\ReportIngestSourceCount}{5}\n" in augmented
    restored = re.sub(
        r"\\newcommand\{\\Report(?:Connector|FirstPartyFeed|IngestSource)Count\}\{\d+\}\n",
        "",
        augmented,
    )
    assert restored == original


def test_missing_inventory_fails_visibly(tmp_path):
    root = inventory(tmp_path)
    (root / "config.yml").write_text("sources:\n  first_party_feeds:\n    feeds: []\n")
    with pytest.raises(ValueError, match="Missing frozen"):
        ingest_counts(root)


def test_committed_ingest_total_reconciles():
    text = (PAPER / "figure-data.tex").read_text()
    values = dict(re.findall(r"\\newcommand\{\\(Report\w+Count)\}\{(\d+)\}", text))
    assert int(values["ReportIngestSourceCount"]) == (
        int(values["ReportConnectorCount"]) + int(values["ReportFirstPartyFeedCount"])
    )
