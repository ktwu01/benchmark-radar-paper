# Paper repository instructions

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
