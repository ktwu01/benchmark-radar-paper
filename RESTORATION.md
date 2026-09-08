# Paper restoration review

The paper again presents **Benchmark RADAR: Living Search Engine for Retrieval and Discovery of AI Benchmark Research**. Daily discovery, benchmark retrieval, task materials, and reporting evidence lead the narrative; the full-catalog audit supports it.

## Restored

- The exact original title in the manuscript and PDF metadata, and the broad introduction covering evaluation, scientific and industrial applications, benchmark families, fragmented discovery, and the system's contribution. All 36 citation keys from the original introduction remain cited. ASI-Bench, ESM-BENCH, and ResearchClawBench now accompany descriptions of their own tasks.
- The original overview illustration on page one, with the frozen count corrected to 1,283 source records across four sources. Illustrative ordinal labels are removed; bars and connections are labelled schematic. Figure 3 shows the supplied Humanity’s Last Exam score-inspection snapshot; the complete linked census is in the appendix.
- Main-text collection and reader interfaces, discovery coverage and source concentration, a prior-art workflow with its outcome table, and concrete reporting examples. Detailed settings, source inventories, and session screenshots remain in the appendix.
- Generated tables for all 16 benchmark records mentioned by at least six organizations, all eight near-ceiling records among the 82 eligible percentage-scale records, and all six report-publication gaps of at least 180 days. The new example audit records source keys, score IDs, settings, document IDs, eligibility, and input hashes.

## Retained

- The v0.11.0 release, software commit `8f46bbf`, September 7 discovery cutoff, and original frozen input hashes. Neither the census inputs nor its existing generated data changed.
- All 1,283 source records, including 493 without numeric scores; 12,916 numeric observations; and separate model, document, and observation counts. The same score-scale rule is applied to every source. All eight qualifying near-ceiling records happen to come from Model reports.
- Source-preserving identities, shared query behavior, the BM25F citation, scale and date limitations, and the distinction between candidate retrieval and suitability judgment.
- All five authors, affiliations, and contribution credit. The v0.9.0 Zenodo deposit is unchanged.

## Corrected or excluded, with reasons

- The old adoption statement named eight records, but 16 meet its stated six-organization threshold in the frozen documents. The restored table lists every qualifying record. This remains a report-collection finding, not an estimate of field-wide adoption.
- The unsupported protocol-controlled saturation appendix remains excluded. Repeated archive labels and dates do not verify independent matching runs; different AIME years cannot establish one comparable test sequence. The eight raw reported-score examples return with their settings and without a saturation claim.
- The earlier mention-gap interpretation does not return as score stagnation. Its endpoints are document-publication dates, and the gaps describe archive coverage within a source record.
- The original broad claim that no existing system combines these functions remains replaced by a concrete description of Benchmark RADAR's functions; this revision does not establish an exhaustive novelty comparison.
- The unrelated space-science education bibliography entry remains excluded because it supports no restored claim.
- The contributor's issue targets papers published in August; it does not date the session to August. The restored account makes that distinction and identifies the artifact-status screenshots as discovery records.

## Verification

The six software CI steps passed in a fresh detached checkout of the frozen release, including all 1,314 tests. The census and software figure exporter match the committed frozen inputs. The example generator passes its `--check` mode. Negative checks reject a truncated index, duplicate benchmark ID, missing detail shard, duplicate score observation, and changed date basis.

The rebuilt 24-page manuscript and extracted arXiv package compile without undefined references or overfull boxes, and their extracted text matches on every page. All 24 manuscript pages were visually reviewed. The manuscript retains exactly 1,283 census hyperlinks, each appearing once and matching the frozen record IDs.

Figure 3 preserves the supplied HLE screenshot byte-for-byte and links to the requested interactive view. The frozen record verifies its 577 observations and displayed best score of 55.47. `evidence/hle-score-history.json` records the image hash, source record, maximum observation, display scaling, and model-announcement date basis. The caption distinguishes model release dates from evaluation dates; the live link may later change. The complete linked census remains in Appendix A.

The main Results section also includes the supplied Leaderboard and Trends snapshots, each linked to its live page. Both image files are unchanged. The Trends cards agree with the frozen September 7 rebuild; captions distinguish filtered score browsing from the full census and overlapping discovery categories from benchmark records. Image hashes and scope notes are recorded in `evidence/interface-snapshots.json`.

## Author-credit correction

Commit `557393e` removed the dedicated Contributor Credit section and distributed credit across an author note and two footnotes. The subsequent restoration retained that fragmented arrangement: the author note named only Koutian Wu, Ergan Shang, and Pengqian Han, while Junjie Zhou and Jiayu Wang were credited elsewhere. The manuscript now has one formal Author Contributions section naming all five authors and their previously recorded roles. Informal issue references have been removed from the manuscript; the worked example, screenshots, and scholarly citations remain.
