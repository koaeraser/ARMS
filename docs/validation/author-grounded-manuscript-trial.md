# Author-grounded manuscript trial — 19 October 2026

Tested branch: `author-grounded-manuscript-scope`, behavior commit `06cc43b`.
Base: `c5e7df6`.

## Test and result

Applied the revised writer/critic instructions to an existing, source-verified
statistics manuscript whose author found it overwhelming. This was an editorial
revision of validated work, not a rerun of the discovery phases. Original author
papers supplied the structure; the previous version remained immutable. Unpublished
sources and detailed review records remain local to the author's project.

| Observation | Before | After |
|---|---:|---:|
| PDF pages, unchanged 11pt/one-inch layout | 62, combined article/support | 10 main + 7 separate supplement |
| Main numbered sections | 8 | 6 |
| Main tables + figures | 9 + 8 | 4 + 1 |
| Main prose words, Introduction through Discussion | 15,282 | 3,040 |

Word counts use TeXcount text words, excluding abstract, captions, references and
appendices. Pages include references; page counts alone are not the acceptance
criterion. The provisional word budget was shortened with an explicit justification,
not filled by padding. Detailed results excluded from the article remain traceable
in an evidence-disposition ledger and preserved archive.

A separate manuscript critic read the main paper and supplement, checked essential
assumptions and adverse findings against the baseline, and checked selected numerical
tables against their CSVs. Verdict: self-contained argument, no critical or major
fidelity issue. Two minor findings (a disposition claim and definition order) were
corrected. Both PDFs compile without unresolved references or overfull boxes; all
rendered pages were inspected for layout defects.

The unchanged calculation bundle was separately replayed: all 22 deterministic
checks passed and all 24 comparable regenerated CSVs matched. This confirms numerical
reproduction, not a new simulation experiment or scientific sign-off.

## Repository checks

Independent standards and spec reviews identified five instruction conflicts and
verified their resolution in `06cc43b`. `git diff --check` passed. A fresh copied-skills
installation resolves shared guidance from all six writer/reviewer/orchestrator
consumers. The optional author example contains no machine-specific source paths.

This single successful application supports the workflow change; it is not a
multi-domain benchmark or evidence that future manuscripts need no author review.
