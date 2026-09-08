#!/usr/bin/env python3
"""Reproduce scoped paper examples from the frozen full catalog, without network access."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

import yaml
from audit_catalog import PAPER, audit, numeric, valid_date


def tex(value):
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(c, c) for c in str(value))


def calculate(root):
    census = audit(root)
    frozen = json.loads((PAPER / "evidence/catalog-audit.json").read_text())
    if census != frozen:
        raise ValueError("Inputs differ from the frozen full-catalog census")
    index = json.loads((root / "site/data/benchmark-index.json").read_text())
    registry = {d["id"]: d for d in index["document_registry"]["documents"]}
    raw_metrics = (root / "data/benchmark_scores.yml").read_bytes()
    metrics = {
        "model-reports:" + b["benchmark_id"]: b for b in yaml.safe_load(raw_metrics)["benchmarks"]
    }
    by_key = {b["key"]: b for b in index["benchmarks"]}
    eligibility, near, mentions, gaps = [], [], [], []
    for state in census["records"]:
        entry = by_key[state["key"]]
        detail = json.loads((root / f"site/data/benchmarks/{entry['slug']}.json").read_text())
        scores = [
            o
            for payload in detail["scores_by_source"].values()
            for o in payload["rows"]
            if numeric(o["value"])
        ]
        docs = detail["record"]["documents"]
        # The scale test applies identically to every source; never transfer a unit.
        reason = state["status"]
        if reason == "percent" and entry["score_direction"] != "higher_is_better":
            reason = "lower_is_better_not_in_upper_ceiling_analysis"
        eligibility.append({"key": entry["key"], "headroom_state": reason})
        if reason == "percent":
            best_value = max(o["value"] for o in scores)
            if best_value >= 95:
                winners = sorted(
                    (o for o in scores if o["value"] == best_value), key=lambda o: o["obs_id"]
                )
                for o in winners:
                    assert o["instrument"] and o["protocol"] and o["source_url"]
                    assert o["document_id"] in registry
                meta = metrics.get(entry["key"])
                if meta:
                    assert meta["unit"] == entry["unit"]
                    assert meta["direction"] == entry["score_direction"]
                near.append(
                    {
                        "key": entry["key"],
                        "name": entry["name"],
                        "source": entry["source"],
                        "metric": meta["metric"] if meta else "not recorded",
                        "value": best_value,
                        "headroom": round(100 - best_value, 8),
                        "observations": winners,
                    }
                )
        # Mentions require the report-document evidence, not an inferred adoption count.
        report_docs = [d for d in docs if d["source"] == "model_reports"]
        if not report_docs:
            continue
        assert entry["source"] == "model_reports"
        organizations = sorted({d["organization"] for d in report_docs if d.get("organization")})
        mentions.append(
            {
                "key": entry["key"],
                "name": entry["name"],
                "document_ids": sorted(d["id"] for d in report_docs),
                "organizations": organizations,
                "documents": report_docs,
            }
        )
        dated = [o for o in scores if valid_date(o.get("reported_at"))]
        dated_docs = [d for d in report_docs if valid_date(d.get("published"))]
        if not dated or not dated_docs:
            continue
        # All numeric rows must carry the same explicit document-date basis.
        assert len(dated) == len(scores)
        assert all(o["date_precision"] == "document_publication" for o in dated)
        last_score = max(o["reported_at"] for o in dated)
        last_mention = max(d["published"] for d in dated_docs)
        gap = (date.fromisoformat(last_mention) - date.fromisoformat(last_score)).days
        if gap >= 180:
            gaps.append(
                {
                    "key": entry["key"],
                    "name": entry["name"],
                    "gap_days": gap,
                    "latest_score_document_date": last_score,
                    "latest_mention_document_date": last_mention,
                    "score_observations": [o for o in dated if o["reported_at"] == last_score],
                    "mention_documents": [d for d in dated_docs if d["published"] == last_mention],
                }
            )
    mentions.sort(key=lambda x: (-len(x["organizations"]), -len(x["document_ids"]), x["key"]))
    near.sort(key=lambda x: x["name"].casefold())
    gaps.sort(key=lambda x: (-x["gap_days"], x["key"]))
    report_registry = [d for d in registry.values() if d["source"] == "model_reports"]
    return {
        "software_commit": "8f46bbfa91f5d9900c8b08a5d552c3df5c9597b0",
        "discovery_cutoff": "2026-09-07",
        "input_sha256": {
            **census["input_sha256"],
            "data/benchmark_scores.yml": hashlib.sha256(raw_metrics).hexdigest(),
        },
        "rules": {
            "population": "Every source record in the frozen, validated full catalog.",
            "near_ceiling": "Highest archived value per source record; declared percent, higher "
            "is better, all numeric values in [0,100], highest >=95. Preserve every tied "
            "observation and its instrument, protocol, model and citation. Not a repeated-run "
            "or saturation claim. Unknown scales and scores remain in the census.",
            "mentions": "Distinct model-report documents and named organizations per source "
            "record. Table includes every record mentioned by at least six organizations. "
            "Report registry scope only; not field-wide adoption or unique test versions.",
            "gaps": "At least 180 days between the latest publication date of a document "
            "supplying an archived score and the latest publication date of a mentioning "
            "report, within the same source record. Not evaluation dates or stagnation.",
            "metric": "Exact model-reports record key joins the frozen score archive only "
            "to annotate metric names; no records, scores, or scales are added by this join.",
        },
        "counts": {
            "population": len(eligibility),
            "headroom_states": dict(Counter(r["headroom_state"] for r in eligibility)),
            "near_ceiling": len(near),
            "report_records_with_mentions": len(mentions),
            "report_documents": len(report_registry),
            "report_organizations": len({d["organization"] for d in report_registry}),
            "six_organization_records": sum(len(m["organizations"]) >= 6 for m in mentions),
            "mention_gaps": len(gaps),
        },
        "eligibility": eligibility,
        "near_ceiling": near,
        "mentions": mentions,
        "mention_gaps": gaps,
    }


def tex_data(data):
    c = data["counts"]
    lines = ["% Generated by scripts/audit_examples.py; do not hand-edit."]
    for name, value in {
        "ExampleAdoptionCount": c["six_organization_records"],
        "ExampleReportDocuments": c["report_documents"],
        "ExampleReportOrganizations": c["report_organizations"],
        "ExampleNearCount": c["near_ceiling"],
        "ExampleHeadroomEligible": c["headroom_states"].get("percent", 0),
        "ExampleGapCount": c["mention_gaps"],
    }.items():
        lines.append(rf"\newcommand{{\{name}}}{{{value}}}")
    lines.append(r"\newcommand{\ExampleAdoptionRows}{%")
    for m in data["mentions"]:
        if len(m["organizations"]) >= 6:
            lines.append(
                f"{tex(m['name'])} & {len(m['document_ids'])} & {len(m['organizations'])}" + r"\\"
            )
    lines.append("}")
    lines.append(r"\newcommand{\ExampleNearRows}{%")
    for item in data["near_ceiling"]:
        for obs in item["observations"]:
            lines.append(
                tex(item["name"])
                + " & "
                + tex(obs["model_name"])
                + rf" \href{{{obs['source_url']}}}{{[source]}} & "
                + f"{item['value']:g} & {item['headroom']:g} & "
                + tex(item["metric"] + "; " + obs["protocol"])
                + r"\\"
            )
    lines.append("}")
    lines.append(r"\newcommand{\ExampleGapRows}{%")
    for g in data["mention_gaps"]:
        score = g["score_observations"][0]
        mention = g["mention_documents"][0]
        lines.append(
            tex(g["name"])
            + " & "
            + rf"\href{{{score['source_url']}}}{{{g['latest_score_document_date']}}} & "
            + rf"\href{{{mention['source_url']}}}{{{g['latest_mention_document_date']}}} & "
            + str(g["gap_days"])
            + r"\\"
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("software", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = calculate(args.software.resolve())
    outputs = {
        PAPER / "evidence/restored-examples.json": json.dumps(data, indent=2, ensure_ascii=False)
        + "\n",
        PAPER / "example-data.tex": tex_data(data),
    }
    for path, content in outputs.items():
        if args.check:
            if path.read_text() != content:
                raise SystemExit(f"Stale examples: {path}")
        else:
            path.write_text(content)
    print(json.dumps(data["counts"], indent=2))


if __name__ == "__main__":
    main()
