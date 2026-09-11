#!/usr/bin/env python3
"""Check paper outputs against the immutable, checksummed v0.11.0 input archive."""

import argparse
import ast
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import yaml
from audit_catalog import PAPER

ARCHIVE = "benchmark-radar-paper-data-v0.11.0.zip"
ARCHIVE_SHA256 = "346a039375129154ceddb2c13c187c80b9af94532244da4e0254cd87a1f766e9"
COMMIT = "8f46bbfa91f5d9900c8b08a5d552c3df5c9597b0"


def ingest_counts(root):
    """Read the frozen code/config inventory, never the live parent checkout."""
    tree = ast.parse((root / "src/benchmark_radar/sources.py").read_text())
    connectors = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("fetch_")
    } - {"fetch_first_party_feeds"}
    config = yaml.safe_load((root / "config.yml").read_text())
    feeds = config["sources"]["first_party_feeds"]["feeds"]
    if not connectors or not isinstance(feeds, list) or not feeds:
        raise ValueError("Missing frozen connector/feed inventory")
    return len(connectors), len(feeds)


def with_ingest_inventory(rendered, root):
    """The released exporter predates these three macros, but not their inputs.

    Validate their exact values against the same frozen software revision while
    retaining the byte-for-byte comparison for every original exported line.
    """
    connectors, feeds = ingest_counts(root)
    lines = rendered.splitlines(keepends=True)
    position = next(
        i + 1
        for i, line in enumerate(lines)
        if line.startswith(r"\newcommand{\ReportCatalogSourceCount}")
    )
    lines[position:position] = [
        f"\\newcommand{{\\{name}}}{{{value}}}\n"
        for name, value in [
            ("ReportConnectorCount", connectors),
            ("ReportFirstPartyFeedCount", feeds),
            ("ReportIngestSourceCount", connectors + feeds),
        ]
    ]
    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("software", type=Path, help="Disposable clean checkout of frozen v0.11.0")
    parser.add_argument("--archive", type=Path, help="Use an already downloaded release ZIP")
    args = parser.parse_args()
    root = args.software.resolve()
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != COMMIT:
        raise SystemExit("Expected a checkout of frozen v0.11.0, not current main")
    with tempfile.TemporaryDirectory(prefix="paper-frozen-inputs-") as tmp:
        archive = args.archive or Path(tmp) / ARCHIVE
        if not args.archive:
            urllib.request.urlretrieve(
                "https://github.com/ktwu01/benchmark-radar/releases/download/v0.11.0/" + ARCHIVE,
                archive,
            )
        if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
            raise SystemExit("Frozen release ZIP checksum mismatch")
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (root / member.filename).resolve()
                if not target.is_relative_to(root):
                    raise SystemExit("Release archive member escapes the checkout")
            bundle.extractall(root)
    for script in ["audit_catalog.py", "audit_findings.py"]:
        subprocess.run(
            [sys.executable, str(PAPER / "scripts" / script), str(root), "--check"], check=True
        )
    spec = importlib.util.spec_from_file_location(
        "frozen_figure_export", root / "scripts/export_report_figure_data.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = with_ingest_inventory(module.render_data(root), root)
    if expected != (PAPER / "figure-data.tex").read_text():
        raise SystemExit("Stale figure data against frozen inputs")
    print(f"All paper exports match frozen v0.11.0 ({COMMIT}); archive SHA-256 verified.")


if __name__ == "__main__":
    main()
