#!/usr/bin/env python3
"""Reproduce the paper's census from a rebuilt, source-preserving catalog.

No YAML-only subset, name join, score imputation, network call, or prose generation.
Run the software's six CI steps before this script. Normal paper builds use the
committed outputs and do not require a software checkout.
"""

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

PAPER = Path(__file__).resolve().parents[1]
LABELS = {
    "llm_stats": "LLM Stats",
    "opencompass_hub": "OpenCompass Hub",
    "artificial_analysis": "Artificial Analysis",
    "model_reports": "Model reports",
}


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def valid_date(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def audit(root):
    hashes = {}

    def read(relative):
        raw = (root / relative).read_bytes()
        hashes[relative] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    index = read("site/data/benchmark-index.json")
    radar = read("site/data/radar.json")
    models = read("site/data/models.json")
    assert (
        models["model_count"] == len(models["models"]) == len({m["key"] for m in models["models"]})
    )
    catalog = index["benchmarks"]
    assert index["count"] == len(catalog) == len({b["key"] for b in catalog})
    assert len(catalog) >= 1259 and len({b["source"] for b in catalog}) >= 4
    assert {b["source"] for b in catalog} <= LABELS.keys(), "Name new sources explicitly"
    documents = index["document_registry"]["documents"]
    document_ids = {d["id"] for d in documents}
    assert len(document_ids) == len(documents) == index["document_registry"]["document_count"]
    sources = {source: Counter() for source in LABELS}
    rows = []
    observation_ids = set()
    cited_document_ids = set()
    date_precision = Counter()
    for entry in sorted(catalog, key=lambda b: (list(LABELS).index(b["source"]), b["key"])):
        detail = read(f"site/data/benchmarks/{entry['slug']}.json")
        record = detail["record"]
        assert record["key"] == entry["key"] and record["source"] == entry["source"]
        observations = []
        for source, payload in detail["scores_by_source"].items():
            assert source == entry["source"], "Do not transfer measurements between sources"
            for obs in payload["rows"]:
                assert obs["key"] == entry["key"] and obs["source"] == source
                assert obs["obs_id"] not in observation_ids, "Duplicate score observation"
                observation_ids.add(obs["obs_id"])
                assert obs["document_id"] in document_ids, "Score citation missing from registry"
                if numeric(obs["value"]):
                    observations.append(obs)
                    date_precision[obs.get("date_precision") or "unknown"] += 1
        assert len(observations) == (entry.get("score_summary") or {}).get("numeric_count", 0)
        assert entry["score_count"] == sum(
            len(p["rows"]) for p in detail["scores_by_source"].values()
        )
        source_models = {o.get("model_id") for o in observations}
        model_count = (
            len(source_models)
            if observations and None not in source_models and "" not in source_models
            else None
        )
        ids = {doc["id"] for doc in record.get("documents", [])}
        assert ids <= document_ids
        cited_document_ids.update(ids)
        document_count = len(ids) if ids else None
        assert model_count == entry["evidence_summary"]["model_count"]
        assert document_count == entry["evidence_summary"]["document_count"]
        values = [o["value"] for o in observations]
        percent = (
            bool(values)
            and entry.get("unit") == "percent"
            and entry.get("score_direction") in {"higher_is_better", "lower_is_better"}
            and min(values) >= 0
            and max(values) <= 100
        )
        status = "percent" if percent else "other_numeric" if values else "unscored"
        row = {
            "key": entry["key"],
            "slug": entry["slug"],
            "name": entry["name"],
            "source": entry["source"],
            "status": status,
            "numeric_scores": len(values),
            "model_count": model_count,
            "document_count": document_count,
            "document_ids": sorted(ids),
            "release_date": entry.get("released") if valid_date(entry.get("released")) else None,
            "has_paper": entry["has_paper"],
            "has_repo": entry["has_repo"],
            "has_dataset": entry["has_dataset"],
        }
        rows.append(row)
        counts = sources[row["source"]]
        counts.update(
            records=1,
            numeric_scores=len(values),
            scored=bool(values),
            unscored=not values,
            percent=percent,
            other_numeric=bool(values) and not percent,
            documents_known=document_count is not None,
            models_known=model_count is not None,
            release_known=row["release_date"] is not None,
            paper_links=row["has_paper"],
            repo_links=row["has_repo"],
            dataset_links=row["has_dataset"],
            no_score_with_links=not values
            and any(row[k] for k in ["has_paper", "has_repo", "has_dataset"]),
        )
    assert cited_document_ids == document_ids, "Document registry does not reconcile with records"
    totals = sum(sources.values(), Counter())
    assert totals["records"] == totals["scored"] + totals["unscored"]
    assert totals["scored"] == totals["percent"] + totals["other_numeric"]
    assert totals["numeric_scores"] == sum(date_precision.values())
    snapshots = [
        read(str(p.relative_to(root))) for p in sorted((root / "data/snapshots").glob("*.json"))
    ]
    latest = next(s for s in snapshots if s["date"] == radar["latest_date"])
    assert len(snapshots) == radar["snapshot_count"]
    artifacts = [e for e in radar["corpus"]["entities"] if e["type"] == "artifact"]
    source_counts = Counter(o["source"] for o in radar["corpus"]["observations"])
    totals.update(
        documents=len(documents),
        models=models["model_count"],
        snapshots=len(snapshots),
        simulated_snapshots=sum(bool(s.get("selection", {}).get("simulated")) for s in snapshots),
        observations=radar["corpus"]["observation_count"],
        artifacts=len(artifacts),
        multisource_artifacts=sum(len(e["sources"]) > 1 for e in artifacts),
        unclassified=radar["kw_bench"]["coverage"]["unclassified_count"],
    )
    assert totals["observations"] == sum(source_counts.values())
    return {
        "schema_version": 1,
        "software_commit": subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip(),
        "cutoff": radar["latest_date"],
        "definitions": {
            "population": (
                "One row per source record from the complete benchmark-index.json; no "
                "name-based merging or surface filters."
            ),
            "numeric_scores": (
                "Finite numeric observations from each record's own detail shard, "
                "unique by obs_id; retained with citation IDs."
            ),
            "model_count": (
                "Distinct source model_id among numeric observations on this source "
                "record; incomplete IDs or no numeric observations yield null."
            ),
            "document_count": (
                "Distinct cited document IDs per source record; no citations yields "
                "null, not zero adoption."
            ),
            "percent": (
                "Numeric record with explicit percent unit, known score direction and "
                "all values in [0,100]; this does not establish matching protocols."
            ),
            "other_numeric": (
                "Numeric scores on other or unverified scales, retained in the census."
            ),
            "release_known": (
                "Valid benchmark release date in the catalog; no model-date or "
                "crawl-date substitution."
            ),
            "links": (
                "Catalog presence flags for paper/repo/dataset links, not verified "
                "current availability or license grants."
            ),
            "dates": (
                "Counts by recorded score-date precision, not inferred evaluation or release dates."
            ),
            "figure_order": (
                "Source order in sources, then exact source key; each record occupies "
                "one linked dot, without score or date filtering."
            ),
        },
        "totals": dict(totals),
        "sources": {s: dict(c) for s, c in sources.items()},
        "score_date_precision": dict(date_precision),
        "document_types": dict(Counter(d["document_type"] for d in documents)),
        "discovery_sources": dict(source_counts),
        "latest_selection": latest["selection"],
        "latest_health": latest["ingest_health"],
        "input_sha256": dict(sorted(hashes.items())),
        "records": rows,
    }


def tex_data(data):
    lines = ["% Generated by scripts/audit_catalog.py from the complete catalog; do not hand-edit."]
    for key, value in data["totals"].items():
        name = "Census" + "".join(part.title() for part in key.split("_"))
        lines.append(rf"\newcommand{{\{name}}}{{{value}}}")
    lines.append(r"\newcommand{\CensusSourceRows}{%")
    for source, counts in data["sources"].items():
        values = [LABELS[source]] + [
            f"{counts[k]:,}" for k in ["records", "scored", "unscored", "numeric_scores"]
        ]
        lines.append(" & ".join(values) + r"\\")
    lines.append("}")
    lines.append(r"\newcommand{\CensusMarks}{%")
    for group, source in enumerate(data["sources"]):
        records = [r for r in data["records"] if r["source"] == source]
        for offset, record in enumerate(records):
            color = {
                "percent": "RadarTeal",
                "other_numeric": "RadarBlue",
                "unscored": "RadarGray",
            }[record["status"]]
            # Four equal-width columns, sorted source keys. 20 dots per row.
            lines.append(
                rf"\CensusDot{{{group}}}{{{offset % 20}}}{{{offset // 20}}}"
                rf"{{{color}}}{{{record['slug']}}}%"
            )
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "software",
        type=Path,
        help="Clean software checkout after the six-step CI rebuild",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = audit(args.software.resolve())
    outputs = {
        PAPER / "evidence/catalog-audit.json": json.dumps(data, indent=2, ensure_ascii=False)
        + "\n",
        PAPER / "catalog-data.tex": tex_data(data),
    }
    for path, text in outputs.items():
        if args.check:
            if path.read_text() != text:
                raise SystemExit(f"Stale audit: {path}")
        else:
            path.write_text(text)
    print(json.dumps(data["totals"], indent=2))


if __name__ == "__main__":
    main()
