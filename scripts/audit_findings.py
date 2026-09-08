#!/usr/bin/env python3
"""Export every frozen catalog record for the paper's document, score and date analyses."""

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path
from statistics import median

from audit_catalog import LABELS, PAPER, audit, numeric, valid_date


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


def record_evidence(entry, detail):
    """Keep native values and exact identities regardless of measurement eligibility."""
    scores = [
        o
        for payload in detail["scores_by_source"].values()
        for o in payload["rows"]
        if numeric(o["value"])
    ]
    documents = {d["id"]: d for d in detail["record"].get("documents", [])}
    model_ids = {o.get("model_id") for o in scores}
    model_count = (
        len(model_ids) if scores and None not in model_ids and "" not in model_ids else None
    )
    highest = max((o["value"] for o in scores), default=None)
    winners = sorted((o for o in scores if o["value"] == highest), key=lambda o: o["obs_id"])
    eligible = (
        bool(scores)
        and entry.get("unit") == "percent"
        and entry.get("score_direction") == "higher_is_better"
        and all(0 <= o["value"] <= 100 for o in scores)
    )
    dates = Counter()
    for o in scores:
        value = o.get("reported_at") or o.get("reported_date")
        dates[o.get("date_precision") or "unknown" if valid_date(value) else "unknown"] += 1
    return {
        "key": entry["key"],
        "slug": entry["slug"],
        "name": entry["name"],
        "source": entry["source"],
        "numeric_scores": len(scores),
        "model_count": model_count,
        "document_count": len(documents) or None,
        "documents": sorted(documents.values(), key=lambda d: d["id"]),
        "document_organizations": sorted(
            {d["organization"] for d in documents.values() if d.get("organization")}
        ),
        "documents_without_organization": sum(
            not d.get("organization") for d in documents.values()
        ),
        "unit": entry.get("unit"),
        "direction": entry.get("score_direction"),
        "highest_raw_value": highest,
        "highest_observations": winners,
        "highest_display_value": (entry.get("score_summary") or {}).get("display_max"),
        "display_multiplier": (entry.get("score_summary") or {}).get("display_multiplier"),
        "percentage_headroom": round(100 - highest, 8) if eligible else None,
        "headroom_state": "eligible"
        if eligible
        else "other_or_unverified_scale"
        if scores
        else "unscored",
        "release_date": entry.get("released") if valid_date(entry.get("released")) else None,
        "score_date_precision": dict(sorted(dates.items())),
        "score_observation_ids": sorted(o["obs_id"] for o in scores),
    }


def summarize(records):
    """Every analysis has the same population; measurements never select its rows."""
    sources = {}
    for source in LABELS:
        rows = [r for r in records if r["source"] == source]
        docs = {d["id"]: d for r in rows for d in r["documents"]}
        models = [r["model_count"] for r in rows if r["model_count"] is not None]
        dates = sum((Counter(r["score_date_precision"]) for r in rows), Counter())
        sources[source] = {
            "records": len(rows),
            "documented_records": sum(r["document_count"] is not None for r in rows),
            "documents": len(docs),
            "documents_without_organization": sum(not d.get("organization") for d in docs.values()),
            "scored_records": sum(r["numeric_scores"] > 0 for r in rows),
            "unscored_records": sum(r["numeric_scores"] == 0 for r in rows),
            "numeric_scores": sum(r["numeric_scores"] for r in rows),
            "model_count_known_records": len(models),
            "median_scored_models": median(models) if models else None,
            "max_scored_models": max(models, default=None),
            "at_least_100_models": sum(n >= 100 for n in models),
            "release_known_records": sum(r["release_date"] is not None for r in rows),
            "score_date_precision": dict(sorted(dates.items())),
            "headroom_states": dict(Counter(r["headroom_state"] for r in rows)),
        }
    if sum(s["records"] for s in sources.values()) != len(records):
        raise ValueError("Unaccounted catalog source")
    return sources


def calculate(root):
    census = audit(root)
    frozen = json.loads((PAPER / "evidence/catalog-audit.json").read_text())
    if census != frozen:
        raise ValueError("Inputs differ from the frozen v0.11.0 full-catalog census")
    index = json.loads((root / "site/data/benchmark-index.json").read_text())
    entries = {b["key"]: b for b in index["benchmarks"]}
    records = [
        record_evidence(
            entries[r["key"]],
            json.loads((root / f"site/data/benchmarks/{r['slug']}.json").read_text()),
        )
        for r in census["records"]
    ]
    if len(records) != len(entries) or {r["key"] for r in records} != set(entries):
        raise ValueError("Finding rows must preserve every catalog ID exactly once")
    return {
        "schema_version": 1,
        "software_commit": census["software_commit"],
        "discovery_cutoff": census["cutoff"],
        "input_sha256": census["input_sha256"],
        "definitions": {
            "population": (
                "Every frozen catalog source record, without score, date, document "
                "or source filters."
            ),
            "highest_raw_value": (
                "Numeric maximum on each source record's native scale, not a cross-benchmark "
                "ranking or necessarily a best result for lower-is-better metrics. "
                "All tied observations are retained."
            ),
            "models": (
                "Distinct source model IDs per benchmark among numeric observations; incomplete "
                "identities remain unknown. Medians use records with known model counts, "
                "not zero-imputed unscored records."
            ),
            "documents": (
                "Distinct cited document IDs; repeated references do not create documents. "
                "Missing organizations stay unknown; source labels are not organizations."
            ),
            "headroom": (
                "100 minus the maximum only for declared percent, higher-is-better records with "
                "all numeric values in [0,100]. Ineligibility never removes score values "
                "or records."
            ),
            "dates": (
                "Recorded benchmark release dates and per-observation date precision; "
                "model announcement dates are not evaluation dates."
            ),
        },
        "sources": summarize(records),
        "records": records,
    }


def display(value):
    if value is None:
        return "Unknown"
    return f"{value:,g}" if isinstance(value, (float, int)) else tex(value)


def tex_data(data, census):
    records = data["records"]
    by_key = {r["key"]: r for r in records}
    totals = census["totals"]
    sources = data["sources"]
    top_five = sum(sorted(census["discovery_sources"].values(), reverse=True)[:5])
    counts = {
        "FindingsRecords": len(records),
        "FindingsMissingDocuments": len(records) - totals["documents_known"],
        "FindingsMissingRelease": len(records) - totals["release_known"],
        "FindingsModelDateScores": census["score_date_precision"].get("model_announcement", 0),
        "FindingsDocumentDateScores": census["score_date_precision"].get("document_publication", 0),
        "FindingsUndatedScores": sum(r["score_date_precision"].get("unknown", 0) for r in records),
        "FindingsTopFiveObservations": top_five,
        "FindingsTopFiveShare": f"{100 * top_five / totals['observations']:.1f}",
        "FindingsBroadModelRecords": sum(s["at_least_100_models"] for s in sources.values()),
        "FindingsDocumentsUnknownOrganization": len(
            {d["id"] for r in records for d in r["documents"] if not d.get("organization")}
        ),
    }
    for key in ["fetched", "deduplicated", "published", "recommended"]:
        counts["FindingsRun" + key.title()] = census["latest_selection"][key]
    for item in census["latest_health"]:
        if item["kind"] == "evidence":
            name = "".join(word.title() for word in item["source"].split("_"))
            counts["FindingsConnector" + name] = item["item_count"]
    example_keys = {
        "GpqaAA": "artificial-analysis:gpqa-diamond",
        "GpqaReports": "model-reports:gpqa_diamond",
        "HleAA": "artificial-analysis:humanitys-last-exam",
        "SciCodeAA": "artificial-analysis:scicode",
        "CritPtAA": "artificial-analysis:critpt",
    }
    # Exact IDs are reviewed examples, not joins that define any analysis population.
    example_rows = []
    for prefix, key in example_keys.items():
        r = by_key[key]
        for suffix, field in [
            ("Models", "model_count"),
            ("Documents", "document_count"),
            ("Scores", "numeric_scores"),
        ]:
            counts["Findings" + prefix + suffix] = r[field]
        example_rows.append(
            " & ".join(
                [tex(r["name"]), LABELS[r["source"]]]
                + [display(r[k]) for k in ["model_count", "document_count", "numeric_scores"]]
            )
            + r"\\"
        )
    hle = by_key[example_keys["HleAA"]]
    counts["FindingsHleDisplayMax"] = f"{hle['highest_display_value']:.2f}"
    lines = ["% Generated by scripts/audit_findings.py from frozen v0.11.0; do not hand-edit."]
    lines += [rf"\newcommand{{\{k}}}{{{v}}}" for k, v in counts.items()]
    tables = {"FindingsModelDocumentRows": example_rows}
    tables["FindingsDocumentRows"] = [
        " & ".join(
            [LABELS[source]]
            + [
                display(s[k])
                for k in [
                    "records",
                    "documented_records",
                    "documents",
                    "documents_without_organization",
                ]
            ]
        )
        + r"\\"
        for source, s in sources.items()
    ]
    tables["FindingsScoreRows"] = [
        " & ".join(
            [LABELS[source]]
            + [
                display(s[k])
                for k in [
                    "records",
                    "scored_records",
                    "unscored_records",
                    "numeric_scores",
                    "median_scored_models",
                    "max_scored_models",
                ]
            ]
        )
        + r"\\"
        for source, s in sources.items()
    ]
    tables["FindingsDateRows"] = [
        " & ".join(
            [LABELS[source], display(s["records"]), display(s["release_known_records"])]
            + [
                display(s["score_date_precision"].get(k, 0))
                for k in ["document_publication", "model_announcement", "unknown"]
            ]
        )
        + r"\\"
        for source, s in sources.items()
    ]
    for name, rows in tables.items():
        lines += [rf"\newcommand{{\{name}}}{{%", *rows, "}"]
    return "\n".join(lines) + "\n"


def csv_data(data):
    out = io.StringIO(newline="")
    fields = [
        "key",
        "name",
        "source",
        "numeric_scores",
        "model_count",
        "document_count",
        "highest_raw_value",
        "highest_display_value",
        "display_multiplier",
        "unit",
        "direction",
        "headroom_state",
        "percentage_headroom",
        "release_date",
        "score_date_precision",
        "document_organizations",
        "highest_observations",
    ]
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in data["records"]:
        writer.writerow(
            {
                k: json.dumps(row[k], ensure_ascii=False, sort_keys=True)
                if isinstance(row[k], (list, dict))
                else row[k]
                for k in fields
            }
        )
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("software", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = calculate(args.software.resolve())
    census = json.loads((PAPER / "evidence/catalog-audit.json").read_text())
    outputs = {
        PAPER / "evidence/catalog-findings.json": json.dumps(data, indent=2, ensure_ascii=False)
        + "\n",
        PAPER / "evidence/catalog-findings.csv": csv_data(data),
        PAPER / "findings-data.tex": tex_data(data, census),
    }
    for path, content in outputs.items():
        if args.check:
            if path.read_text() != content:
                raise SystemExit(f"Stale full-catalog findings: {path}")
        else:
            path.write_text(content)
    print(json.dumps({"records": len(data["records"]), "sources": data["sources"]}, indent=2))


if __name__ == "__main__":
    main()
