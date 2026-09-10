# Benchmark Radar paper

[Read the paper](main.pdf) · [Edit the LaTeX](main.tex) · [Benchmark Radar](https://github.com/ktwu01/benchmark-radar)

**Benchmark Radar: A Living Database and Search Engine for AI Benchmarks and Evaluation** describes how researchers can discover evaluations, retrieve candidates, and inspect their task materials and reported scores. Its document, score, and date analyses each retain the complete frozen benchmark catalog.

This repository contains the manuscript, bibliography, dated figure inputs, and all images needed to build the paper independently. The software repository pins a reviewed commit here as its `docs/technical-report/latex` submodule.

## Data cutoff rule: v0.11.0

**All data used in this paper is cut off at the
[Benchmark Radar v0.11.0 release](https://github.com/ktwu01/benchmark-radar/releases/tag/v0.11.0)**,
which pins software commit
[`8f46bbfa91f5d9900c8b08a5d552c3df5c9597b0`](https://github.com/ktwu01/benchmark-radar/commit/8f46bbfa91f5d9900c8b08a5d552c3df5c9597b0).
The discovery cutoff remains **2026-09-07**; registry snapshots retain their
recorded collection dates.

This rule covers discovery snapshots, registry inputs, model reports, scores,
tables, and figures. Routine paper edits must preserve the released inputs and
the hashes in `figure-data.tex`. Do not refresh from later data, current `main`,
or the live website. Changing the cutoff requires an explicitly agreed new
paper version.

The release preserves the inputs already audited for this paper. Publishing
those unchanged inputs does not require repeating the audit. A correction that
changes inputs or quantitative claims requires verification of the affected
claims. Rebuild and inspect the PDF after manuscript or figure edits.

The release includes
[`benchmark-radar-paper-data-v0.11.0.zip`](https://github.com/ktwu01/benchmark-radar/releases/download/v0.11.0/benchmark-radar-paper-data-v0.11.0.zip),
containing the catalog index, detail shards, model registry, discovery JSON, and
dated snapshots used by the audit. `SHA256SUMS` verifies the release assets;
`release-data.json` inside the archive records the commit and individual input
hashes. These fixed assets, rather than the rolling `cli-data` release, are the
paper's data reference.

```text
site/data/radar.json SHA-256: 029dc413770f39cad1fcd1c3ec2abeeea214544e3c909e2772b1fe2d9c52c4b9
site/data/benchmark-index.json SHA-256: b8d10892e25fe0fe63856f31e1645b41ee7d0f277fedaf308bd8f707852dbff2
```

## Write together in Overleaf

The project owner links their GitHub account in Overleaf account settings, then
chooses **New project → GitHub repo → ktwu01/benchmark-radar-paper**. Set
`main.tex` as the main document and use pdfLaTeX. Invite coauthors through Share.
UT Austin's eligible institutional premium accounts include GitHub integration.

Use **Integrations → GitHub** to pull accepted GitHub changes before a writing
session and push completed revisions afterward. This is manual synchronization;
saving in Overleaf does not push to GitHub. GitHub sync uses the default branch,
so review the manuscript in Overleaf before pushing. It does not open a PR.

Finish active comment and tracked-change review before pulling GitHub edits:
Git synchronization can displace those annotations. Overleaf may bundle several
authors' changes into a commit under the connected account; retain contribution
statements and review records for author credit.

After syncing, rebuild and inspect `main.pdf`, then commit and push it here.
Keep paper-only work in this repository by default. Update Benchmark Radar's
submodule pointer through a separate PR only when the user explicitly requests
it. A paper push alone does not change the version pinned by the software repository.

See [Overleaf's GitHub sync documentation](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/github-synchronization).

## Build locally

Install a TeX distribution with `latexmk`, pdfLaTeX, TikZ, and the manuscript's
LaTeX packages (TeX Live or TinyTeX), plus Python 3, Poppler (`pdftotext` and
`pdftoppm`), and Tesseract OCR. From this repository's root:

```bash
make
make arxiv
```

`make` builds the native TikZ figures and `main.pdf`. Commit the rebuilt PDF with
manuscript edits. Inspect the cover, changed pages, figures, and references before
committing. Overleaf compiles the manuscript using the checked-in figure PDFs;
after editing a figure's `.tex` source, rebuild it locally and sync its PDF too.

Every `make` or `make arxiv` scans the rendered PDF text and page images. Each
detected number below 100 prints:

```text
less than 100 is abnormal, ref to https://github.com/ktwu01/benchmark-radar/blob/main/principle.md
```

Warnings include the page, value, extraction method, and surrounding text.
Page numbers, citations, dates, percentages, model versions, and individual
source counts are included. Warnings do not rewrite evidence or fail the build;
missing tools and unreadable PDFs do. OCR can misread or miss small image text,
so inspect the flagged pages as part of visual review. The full warning report
is written to `build/small-number-warnings.json` and uploaded by CI. Run
`python scripts/check_small_numbers.py main.pdf --text-only` only for an explicit
partial scan; it warns that image coverage is incomplete.

`make arxiv` writes `arxiv.tar.gz`, including `main.bbl` and all figure inputs.
Unpack and compile that archive independently before submitting it. The archive
is a submission package, not evidence of an arXiv publication.

CI builds the manuscript and submission package and uploads them as artifacts.
Those artifacts do not update the checked-in `main.pdf` automatically.
On pull requests, CI runs the rendered-number scan only when the diff adds or
removes a digit on a `.tex` line. Pushes to `main` and manual workflow runs keep
the full scan. Other PR changes still compile and test the paper, while
superseded runs for the same PR are cancelled.

## Reproduce the paper's numbers

`figure-data.tex` is generated by the **Benchmark Radar software repository**.
Reproduction is optional; normal paper builds use the committed TeX inputs.
To reproduce from source, use a separate clean software checkout at the release
commit above and run the six-step CI sequence in its
[repository instructions](https://github.com/ktwu01/benchmark-radar/blob/v0.11.0/AGENTS.md#before-opening-a-pull-request).
Then run these commands from that software checkout's root:

```bash
git submodule update --init --recursive
git -C docs/technical-report/latex switch -c paper/reproduce-v0.11.0
python scripts/export_report_figure_data.py
python scripts/export_report_figure_data.py --check
```

The exporter reads `site/data/benchmark-index.json` and `site/data/radar.json`
and writes this repository's `figure-data.tex` through the submodule. Its header
records the input SHA-256 hashes; `--check` verifies the complete export against
those local inputs. Do not edit the numbers or hashes by hand.

The paper's full-catalog census uses those same rebuilt records. After copying
the software-generated `figure-data.tex` into this paper checkout, run from the
paper root:

```bash
python scripts/audit_catalog.py /path/to/benchmark-radar
python scripts/audit_catalog.py /path/to/benchmark-radar --check
python scripts/audit_findings.py /path/to/benchmark-radar
python scripts/audit_findings.py /path/to/benchmark-radar --check
make arxiv
```

The script reads the complete index, all its detail shards, the shared model
and document registries, and discovery snapshots. It writes `catalog-data.tex`
and `evidence/catalog-audit.json`, with one audit row per source record and
SHA-256 hashes of its inputs. It checks record IDs, observation uniqueness,
model and document counts, and scored/unscored reconciliation. Missing or
malformed artifacts fail visibly. It preserves source identities and applies
the same measurement rules across sources.

`figures/corpus-evidence-body.tex` draws one linked mark per census record.
The manuscript includes that TikZ source directly so the PDF keeps the links;
`figures/corpus-evidence.pdf` provides a standalone figure. Normal paper builds
use the committed data and require no software checkout.

The v0.11.0 audit uses software commit
[`8f46bbf`](https://github.com/ktwu01/benchmark-radar/commit/8f46bbfa91f5d9900c8b08a5d552c3df5c9597b0)
and a **2026-09-07** discovery cutoff. Registry snapshots retain their August
collection dates. The census has 1,283 source records, including 790 scored and
493 unscored records, with 12,916 numeric observations. Of the unscored records,
464 provide artifact links. These counts preserve separate source records for
related benchmarks; they do not count distinct underlying tests.

Keep the release cutoff fixed and review the prose, figures, and rendered PDF
together. Commit the analysis outputs, figure sources and PDFs, and `main.pdf`
together. Push the reviewed paper commit. Update the parent pointer only when
the user explicitly requests it, using the workflow below. The full-corpus rules in
[principle.md](https://github.com/ktwu01/benchmark-radar/blob/main/principle.md)
apply to paper tables and figures as well as the website.

## Full-catalog findings

`scripts/audit_findings.py` verifies the rebuilt inputs against the frozen census, then exports `findings-data.tex`, `evidence/catalog-findings.json`, and `evidence/catalog-findings.csv`. The JSON and CSV each contain all 1,283 source records. Documentation, reported scores, and dates use the same record IDs across all four sources. Numeric maxima, every tied observation and its settings, document identities, model counts, units, and date evidence stay attached to their source record. Missing measurements remain unknown.

The previous reporting tables restricted the main findings to a report-document subset and eight percentage-headroom examples. The percentage-unit requirement removed 708 scored records from the displayed score analysis. Recomputing that exporter reproduced the small tables without fixing their coverage. The replacement retains all 790 scored records and 493 unscored records, with native score maxima in the complete CSV and JSON. Percentage headroom is an optional field, not an inclusion rule. Document counts never substitute for benchmark-record counts, and source labels never substitute for unknown organization identities.

The cutoff and released input hashes are unchanged. Paper CI checks generated findings against the checksummed v0.11.0 archive before compiling the manuscript. Run `python -m pytest -q tests` for population, missing-evidence, and numeric-warning regression cases. The obsolete `example-data.tex`, its `audit_examples.py` generator, and `evidence/restored-examples.json` have been removed; Git history preserves that earlier subset.

The paper's opening illustration is schematic: its bars and connections are illustrative, ordinal labels have been removed, and its count uses the frozen release. The Results section uses the supplied Humanity’s Last Exam interface snapshot, linked to its interactive view. The full linked census appears in the appendix. A restoration review is recorded in [RESTORATION.md](RESTORATION.md).

## Updating the paper used by Benchmark Radar

Run this workflow only when the user explicitly requests an update to the parent
Benchmark Radar repository or its pinned paper revision. Push the reviewed paper
commit to this repository first. From a clean Benchmark Radar checkout, on a new
branch:

```bash
git submodule update --init --recursive
git -C docs/technical-report/latex fetch origin
git -C docs/technical-report/latex checkout <reviewed-paper-commit>
git add docs/technical-report/latex
git commit -m "Update reviewed paper version"
```

Run Benchmark Radar's required clean-checkout CI sequence before opening the PR.
Merge PRs with a merge commit, never squash. New clones should use
`git clone --recurse-submodules`; existing clones use
`git submodule update --init --recursive` after pulling.

## Evidence and publication

The published [v0.9.0 Zenodo deposit](https://doi.org/10.5281/zenodo.22167102)
remains frozen in the software repository. A new deposit requires a separately
reviewed version; this migration does not change that deposit or its metadata.

## History and license

The LaTeX directory's commit history was extracted from Benchmark Radar at
`7e8ed74`; extraction preserves authors, dates, and messages but changes commit
IDs. The original history remains in the software repository. Use-case images
were copied unchanged from its `assets/use-case-492/` directory.

The paper and original editorial content use [CC BY-NC 4.0](LICENSE-CONTENT.md).
Third-party material retains its original terms.

The image `figures/hle-score-history.png` is the supplied screenshot, preserved byte-for-byte. Its provenance and comparison with the frozen HLE record are recorded in `evidence/hle-score-history.json`. Its 577 scores and displayed maximum of 55.47 agree with the frozen release. The horizontal axis uses model announcement dates, not evaluation dates; the chart does not establish matched protocols or percentage-scale eligibility. The interactive link may show later updates.

The additional supplied `figures/leaderboard-frontier.png` and `figures/discovery-trends.png` snapshots appear in the main Results section and link to their respective interactive pages. `evidence/interface-snapshots.json` preserves both image hashes, scope notes, and the frozen September 7 category counts used to verify the Trends cards. Both original images are kept without cropping or retouching.
