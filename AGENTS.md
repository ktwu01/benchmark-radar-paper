# Paper repository instructions

- Follow the README's v0.11.0 data cutoff rule: software commit
  `8f46bbfa91f5d9900c8b08a5d552c3df5c9597b0`, discovery through 2026-09-07,
  and the recorded input hashes. Preserve these released inputs during routine
  edits. Publishing unchanged audited inputs does not require a new audit; a
  changed cutoff requires an explicitly agreed new paper version.
- Edit `main.tex` directly; it is the single source of manuscript prose.
- Keep `references.bib`, all required images, native figure sources, and dated
  `figure-data.tex` in this repository so it builds without the software checkout.
- Run `make` after manuscript or figure changes. Visually inspect the resulting
  PDF and commit `main.pdf` plus any rebuilt figure PDFs with their sources.
- Run `make arxiv` and compile the extracted archive before a submission.
- Do not infer current corpus counts from the paper. Before changing quantitative
  claims, run and audit the software repository's six-step clean-checkout CI
  sequence as described in its AGENTS.md and report README. Missing measurements
  must not remove benchmark records; investigate any unexplained loss below the
  full-corpus baseline of 1,259+ records across 4+ sources.
- Refresh `figure-data.tex` only through the software repository's exporter after
  that audit. Cite the software commit, input evidence, and cutoff for new claims.
- The v0.9.0 Zenodo deposit remains frozen in the software repository.
- Preserve author contribution statements, final approval, and accountability.
  Overleaf's Git commit author does not represent all coauthors' contributions.
- Read the README for Overleaf sync and submodule updates. Push the paper commit
  before advancing the software repository's pointer. Do not add submodules or
  symlinks here: this repository must be importable by Overleaf.
- Merge pull requests with a merge commit; never squash-merge.

## Full-catalog findings

- Read the software repository's `principle.md` before revising benchmark claims.
  Start from every source record in a cleanly rebuilt shared catalog.
- Use `scripts/audit_catalog.py` to refresh `catalog-data.tex` and
  `evidence/catalog-audit.json`; its `--check` mode must pass against that rebuild.
  Refresh `figure-data.tex` only with the software exporter as described above.
- A statistic may require a score, scale, date, or protocol. State its eligible
  coverage and keep records with missing measurements in the population census.
  Do not substitute a model-report-only audit for the paper's main findings.
- Distinct scored models, numeric observations, and cited documents are different
  units. Preserve source-record identities; do not sum similarly named records.
- Keep one mark per source record in the corpus overview and preserve its detail
  link when building the manuscript. Check the links against the census IDs.
