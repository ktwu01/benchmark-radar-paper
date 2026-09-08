"""Regression cases for population loss in the paper's analyses."""

import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_findings import csv_data, record_evidence, summarize  # noqa: E402


def make_record(source, values, *, unit=None, direction="higher_is_better", models=None, docs=None):
    key = source + ":test"
    entry = {
        "key": key,
        "slug": key,
        "name": "Same benchmark name",
        "source": source,
        "unit": unit,
        "score_direction": direction,
        "released": None,
    }
    scores = [
        {
            "value": v,
            "obs_id": f"{key}:{n}",
            "model_id": models[n] if models else f"m{n}",
            "reported_date": "2026-08-01",
            "date_precision": "model_announcement",
        }
        for n, v in enumerate(values)
    ]
    detail = {"record": {"documents": docs or []}, "scores_by_source": {source: {"rows": scores}}}
    return record_evidence(entry, detail)


def test_every_source_and_missing_measurements_survive_all_analyses():
    records = [
        make_record("llm_stats", [0, 0.99]),
        make_record("artificial_analysis", [55.47]),
        make_record("opencompass_hub", []),
        make_record("model_reports", [99], unit="percent"),
    ]
    groups = summarize(records)
    assert sum(g["records"] for g in groups.values()) == 4
    assert all(g["records"] == 1 for g in groups.values())
    assert sum(g["numeric_scores"] for g in groups.values()) == 4
    assert records[0]["highest_raw_value"] == 0.99
    assert records[0]["percentage_headroom"] is None
    assert records[2]["highest_raw_value"] is None
    assert records[3]["percentage_headroom"] == 1
    exported = list(csv.DictReader(io.StringIO(csv_data({"records": records}))))
    assert {r["key"] for r in exported} == {r["key"] for r in records}
    assert len(exported) == len(records)
    assert exported[2]["model_count"] == ""


def test_zero_scores_ties_and_repeated_models_keep_correct_units():
    row = make_record("llm_stats", [0, 0], models=["same-model", "same-model"])
    assert row["numeric_scores"] == 2
    assert row["model_count"] == 1
    assert row["highest_raw_value"] == 0
    assert len(row["highest_observations"]) == 2
    assert row["document_count"] is None


def test_incomplete_model_ids_are_unknown_instead_of_undercounted():
    row = make_record("artificial_analysis", [1, 2], models=["known", None])
    group = summarize([row])["artificial_analysis"]
    assert row["model_count"] is None
    assert group["scored_records"] == 1
    assert group["model_count_known_records"] == 0
    assert group["median_scored_models"] is None


def test_source_names_never_fill_unknown_organizations_and_documents_deduplicate():
    doc = {"id": "registry:one", "source": "llm_stats", "source_url": "https://example.org"}
    row = make_record("llm_stats", [1], docs=[doc, doc])
    assert row["document_count"] == 1
    assert row["document_organizations"] == []
    assert row["documents_without_organization"] == 1


def test_lower_is_better_and_undeclared_scales_keep_native_maxima_without_headroom():
    for source in ["llm_stats", "artificial_analysis", "model_reports"]:
        for unit, direction in [(None, "higher_is_better"), ("percent", "lower_is_better")]:
            row = make_record(source, [0.3, 0.9], unit=unit, direction=direction)
            assert row["highest_raw_value"] == 0.9
            assert row["percentage_headroom"] is None
        eligible = make_record(source, [99], unit="percent")
        assert eligible["percentage_headroom"] == 1


def test_unknown_dates_keep_scored_record_and_model_coverage():
    entry = {"key": "llm_stats:x", "slug": "x", "name": "x", "source": "llm_stats"}
    detail = {
        "record": {},
        "scores_by_source": {
            "llm_stats": {
                "rows": [
                    {
                        "value": 10,
                        "obs_id": "x1",
                        "model_id": "m1",
                        "reported_date": "not-a-date",
                        "date_precision": "model_announcement",
                    }
                ]
            }
        },
    }
    row = record_evidence(entry, detail)
    assert row["score_date_precision"] == {"unknown": 1}
    assert row["model_count"] == 1
    assert row["highest_raw_value"] == 10


def test_main_findings_tables_use_the_full_catalog_exports():
    manuscript = (Path(__file__).resolve().parents[1] / "main.tex").read_text()
    assert r"\input{findings-data.tex}" in manuscript
    assert r"\Example" not in manuscript
    for rows, label in [
        ("FindingsDocumentRows", "tab:report-mentions"),
        ("FindingsScoreRows", "tab:reported-headroom"),
        ("FindingsDateRows", "tab:score-coverage-gaps"),
    ]:
        table = manuscript[: manuscript.index(r"\label{" + label + "}")].rsplit(
            r"\begin{tabularx}", 1
        )[1]
        assert "\\" + rows in table
        assert r"\CensusRecords" in table
