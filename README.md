# ARMS: Autonomous Research Manuscript Skills

A system of 13 coordinated [Claude Code](https://claude.com/claude-code) skills that automate the full lifecycle of a research methodology paper — from idea to a polished, adversarially revised manuscript. Twelve skills form the autonomous pipeline, including **House Style**, an exemplar-based house voice judged by a reader-first read, with advisory style metrics; the thirteenth, the **Critic-Revisor**, is an optional adversarial-revision layer that runs on the resulting draft. **Domain-agnostic**: all domain knowledge lives in the research brief, not in the skills.

## Quick Start

```bash
# 1. Copy skills into your project (or install globally to ~/.claude/skills/)
cp -r skills/ your-project/.claude/skills/

# 2. Fill out a research brief from the template
cp research_brief_template.md your-project/research_brief.md
# ... edit research_brief.md ...

# 3. Run the pipeline
cd your-project
claude -p "/research-pipeline research_brief.md" --dangerously-skip-permissions

# Or start from just an idea (Phase 0 auto-expands sparse briefs):
echo "How can we improve conformal prediction under distribution shift?" > idea.md
claude -p "/research-pipeline idea.md" --dangerously-skip-permissions
```

## Architecture

```
research-pipeline (outer orchestrator)
├── Phase 0: SCOPE     → brief-expander (auto-triggered if brief is sparse)
├── Phase 1: THINK     → methodology-architect
├── Phase 2: VALIDATE  → validate-method
├── Phase 3: WRITE     → write-manuscript
│   ├── literature-lead
│   ├── paper-modeler
│   ├── paper-writer
│   ├── paper-critic
│   └── house-style    (final house-voice pass, judged against the exemplar)
├── Phase 4: POLISH    → paper-grader + paper-fixer (+ house-style for flagged paragraphs)
└── Augmentation       → critic-revisor (adversarial review + Codex revision)
```

Each phase is a **separate agent invocation** with its own context window. Communication between phases happens exclusively through **files on disk** (the "anti-telephone-game" pattern — no information is passed through agent summaries that could degrade).

The **critic-revisor** is an optional adversarial-revision layer that runs *after* the pipeline produces a draft. Where Phase 4 fixes execution quality from a single grader, the critic-revisor pits two independent reviewers against the manuscript each round and routes their combined critique to a different model family for the rewrite. See [Augmentation](#augmentation-adversarial-critic-revisor) below.

### Phase Gates and Feedback Loops

- **Phase 0 → Phase 1:** If the input brief has fewer than 5 of 9 required sections, the brief-expander auto-generates a complete brief via web search and literature review (~45 min).
- **Phase 2 → Phase 1 (RETHINK):** If validation fails, the failure diagnosis feeds back to the methodology architect. Max 2 rethink cycles.
- **Phase 4 (POLISH loop):** Grade → fix → re-grade, up to 3 rounds. Fixes are restricted to **execution quality only** (formulas, tables, citations, clarity, house voice) — not methodology. The loop exits as SUCCESS when the score reaches target; the house voice enters through the grader's reader-first read of Clarity (see [Style metrics and the reader-first standard](#style-metrics-advisory-and-the-reader-first-standard)).
- **Kill criteria:** The system can honestly report failure (NO-GO, KILL) rather than producing a paper about a method that doesn't work.

## The 12 Pipeline Skills

These twelve skills form the autonomous pipeline (the thirteenth, the Critic-Revisor, is the augmentation documented in the next section).

### Phase 0: SCOPE (optional)

| Skill | Role | Lines |
|-------|------|-------|
| **`brief-expander`** | Takes a minimal research idea (even one sentence) and expands it into a complete research brief via web search, literature scanning, and field analysis. Scopes the problem — does NOT propose a solution. | 326 |

### Phase 1: THINK

| Skill | Role | Lines |
|-------|------|-------|
| **`research-pipeline`** | Outer orchestrator. Manages the phase flow, checks phase gates, handles RETHINK loops, writes pipeline logs. Does no research itself. | 942 |
| **`methodology-architect`** | Senior researcher agent. Reads literature (via parallel subagent readers), reasons about method combinations using a Provides/Needs matrix, stress-tests candidates, assesses societal impact, and produces a formal methodology specification. Includes a "wildcard search" phase that looks in adjacent fields for importable ideas. | 766 |

### Phase 2: VALIDATE

| Skill | Role | Lines |
|-------|------|-------|
| **`validate-method`** | Validation scientist. Implements the proposed method and comparators, runs quick experiments, judges results against success criteria, then stress-tests for robustness. Computational budgets configurable via research brief. Max 3 iterations with structured diagnosis. Includes the "Beauvais Rule" — don't iterate past fundamental limits. | 484 |

### Phase 3: WRITE

| Skill | Role | Lines |
|-------|------|-------|
| **`write-manuscript`** | Manuscript orchestrator. Plans production evaluations, dispatches sub-agents in sequence (literature → modeling → writing → critique), enforces scope constraints. Ends with a house-style pass judged against the exemplar by the reader-first read. The method is validated; its job is exposition, not discovery. | 656 |
| **`literature-lead`** | Coordinates parallel paper readers for a **writing-focused** review (positioning and citations, not method design). Produces a synthesized briefing with comparative tables, gap analysis, and a draft Related Work section. | 370 |
| **`paper-modeler`** | Scales validated code to production quality. Runs formula-code consistency checks, generates PDF figures, and produces a modeling briefing. Computational budgets configurable via research brief. Reuses Phase 2 code — extends, doesn't rewrite. | 315 |
| **`paper-writer`** | Writes LaTeX manuscript sections one at a time. Includes mandatory protocols: anomaly detection (scan all results for unexplained patterns), claim-vs-data verification (every interpretive claim checked against CSVs), and ablation interpretation. Drafts in the house voice from the first draft and checks each section against the exemplar with the reader-first read. | 449 |
| **`paper-critic`** | Adversarial reviewer (up to 3 rounds). Severity-based escalation: Critical issues must be fixed, Major issues should be fixed, Minor issues are logged. Scope-limited to exposition quality — cannot re-litigate validated methodology. Reports house-voice problems found by the reader-first read as a minor dimension. | 194 |

### Phase 4: POLISH

| Skill | Role | Lines |
|-------|------|-------|
| **`paper-grader`** | Reviewer agent. Scores the manuscript on 7 dimensions (Correctness, Completeness, Rigor, Clarity, Novelty, Impact, Performance) using a calibrated rubric. Dispatches a code auditor subagent for computational correctness checks. Research dimensions (Novelty, Impact, Performance) carry 2x weight. Max score: 50. Caps Clarity at 3.5 when the reader-first read fails. | 523 |
| **`paper-fixer`** | Copy-editor agent. Applies targeted fixes from the grade report. Strict whitelist/blacklist: may fix formula transcription errors, table mismatches, broken references, and clarity issues. May NOT change methodology, re-run experiments, delete unfavorable results, or add new evaluations. Rewrites the paragraphs the reader-first read flags through house-style. | 346 |

### Phases 3–4: STYLE (shared)

| Skill | Role | Lines |
|-------|------|-------|
| **`house-style`** | Exemplar-based house voice. The standard is the exemplar and a reader-first read (problem first, plain doing-verbs, no project shorthand, results in words); the skill rewrites a manuscript into that voice without changing its numbers, claims, citations, or defined terms. `scripts/style_metrics.py` prints advisory cadence metrics beside the exemplar's values (yours, via `--ref`). Used by write-manuscript, paper-writer, paper-grader, paper-fixer, and paper-critic; also runs standalone as `/house-style`. | 460 |

## Style Metrics (Advisory) and the Reader-First Standard

AI-drafted manuscripts can pass every tic check (no em-dashes, no "Furthermore", first-person "we" present) and still read as a results report: long, over-packed sentences, one-point paragraphs, findings written out as rows of numbers, and shorthand coined during the project. The **standard** for the house voice is an approved exemplar and a **reader-first read**: each paragraph says what problem it addresses before the details, says what the authors do with a plain verb, uses terms a reader outside the project already has, and states results in words with only the numbers the argument needs. This is a judgement, made by the writer, the grader, and a judge pass after a rewrite. Writing is adaptive, so no metric value passes or fails a manuscript.

The **advisory style metrics** help a writer see where a draft drifts from the exemplar:

```bash
python3 skills/house-style/scripts/style_metrics.py manuscript.tex --compare --sections [--genre results] [--ref exemplar.tex]
```

The script reads only the main-text prose paragraphs (it drops the preamble, floats, display math, theorem-like environments, proofs, and everything after the appendix or bibliography) and prints seven metrics beside the exemplar's values, each with a note such as "above exemplar" or "close to exemplar". It always exits 0 (`--gate` is kept as an alias of `--compare`). `--sections` adds a per-section table and `--json` gives machine-readable output. The default reference values come from an exemplar *Statistical Science* methods paper; they describe what the exemplar looks like and are not limits:

| Metric | Exemplar | Typical range in the exemplar |
|--------|----------|-------------------------------|
| Mean sentence length (words) | 19.0 | about 17–24 |
| Sentences over 45 words | 1.8% | up to about 5% |
| Sentences per paragraph | 5.3 | about 4–7 |
| "we" per 1,000 words | 11.4 | 7 or more |
| Semicolons per 1,000 words | 2.8 | up to about 3.5 |
| Numbers per 1,000 words | 8.0 | up to about 10 (about 15 with `--genre results`) |
| Sentences with more than 3 numbers | 1.2% | up to about 2% (about 5% with `--genre results`) |

A passage may depart from these values when its argument calls for it: the approved reader-first exemplar abstract averages about 27 words per sentence.

**Compare with your own voice.** The exemplar behind the defaults is not distributed. To target another venue, field, or lab style, choose a published paper whose prose you want to match, place its LaTeX source at `reference/style_exemplar.tex` in your project (research-pipeline picks it up automatically through its `style_ref` argument), or pass it directly with `--ref`. Writers and graders then read it for register, and the script compares against its measured values. An exemplar written in impersonal voice has a low "we" rate, so the comparison does not push first-person prose on a field that avoids it.

**How the pipeline uses it.** paper-writer drafts in the house voice and checks each section against the exemplar with the reader-first read; write-manuscript ends Phase 3 with a house-style pass and a judge pass; paper-grader caps Clarity at 3.5 when the reader-first read fails; paper-fixer rewrites the paragraphs the grader flags; paper-critic reports house-voice problems as a minor dimension. Any of them may consult the metrics as a comparison, and none derives a gate, cap, or retry from them. Numbers may move from prose into tables during a rewrite, but never change or disappear: every move is recorded in a number ledger and checked against the result CSVs.

## Augmentation: Adversarial Critic-Revisor

The 12 pipeline skills above take an idea to a polished draft. The **`critic-revisor`** — the 13th skill — is an optional layer that pushes that draft further through rounds of adversarial review, applied to any LaTeX manuscript (not only ARMS output).

| Skill | Role |
|-------|------|
| **`critic-revisor`** | Autonomous critic-revisor loop. Each round, **two independent Opus reviewers** read the manuscript with differentiated angles — a *methodologist* (math, proofs, simulation design) and an *applied/contextual reader* (framing, positioning, reproducibility). Each writes a capped, ranked critique (≤5 Major, ≤10 Minor) where every comment carries a quoted passage and a concrete fix. A separate **Codex** agent applies the combined critique; **latexmk + latexdiff** rebuild a clean PDF and a colour-tracked diff each round. |

**Why it is separate from Phase 4.** Phase 4 fixes execution quality from a single grader and cannot touch methodology. The critic-revisor is adversarial and many-eyed: two reviewers per round, differentiated by angle, and the model that *reviews* is not the model that *revises* (Opus reviews, Codex rewrites — the "opus review, gpt work" separation). This separation is what lets honest disagreement surface instead of a single agent grading its own prose.

**Hallucination control.** The loop's central failure mode is a reviewer "correcting" a claim it cannot see the source of. Two defenses: (1) reviewers get a tiered per-round web-search budget (8 / 3 / 1 queries) to *verify* citations and prior art rather than reconstruct them from memory; (2) a **source-dependent-claim rule** routes any restated theorem/dataset value/number a reviewer cannot verify to a flags section for a human — the revisor never acts on it.

**Stop conditions.** The loop ends when both reviewers vote `accept`, when neither raises a Major comment, when Codex produces no diff, when the clean build fails, or when the round budget is exhausted.

```bash
# Run the loop on any manuscript (optionally pass a source pack for citation verification)
bash skills/critic-revisor/run_loop.sh path/to/manuscript.tex 5 [venue] [--sources <paths>]
```

Requires `codex` (logged in), `latexmk`, `latexdiff`, and `claude` on `PATH`. Each round is snapshotted under `critic_revisor_logs/run_<timestamp>/`; nothing is destructive to the original `.tex`.

## Why This Architecture

### The Problem It Solves

A simple write-grade-fix loop plateaus at ~65-75% of target quality because the system writes a full paper *before* validating whether the method actually works. Once the paper exists, the polish loop can only fix surface issues — it can't fix fundamental methodology problems.

### Key Design Decisions

1. **Validate before writing.** Phase 2 must return GO before any LaTeX is produced.
2. **Files on disk, not agent memory.** All inter-phase communication uses files. No telephone game.
3. **Scope constraints at every level.** Each skill has explicit whitelists and blacklists.
4. **Honest failure as a first-class outcome.** The pipeline has 6 possible outcomes, 4 of which are graceful failures.
5. **Reuse before rewrite.** Phase 3 imports validated code from Phase 2 — extends, doesn't rewrite.
6. **The Beauvais Rule.** If the method fundamentally doesn't work, stop. Don't iterate past structural limits.
7. **Judge the voice, not only the tics.** The house voice is judged against an exemplar by a reader-first read; tic checks are necessary, never sufficient, and the style metrics are advisory.

### What Works and What Doesn't (Yet)

**Works:** Phase separation eliminates "writing about a broken method." Structured diagnosis produces actionable failure reports. File-based communication prevents information degradation.

**Doesn't (yet):** Self-grading inflates by 1-4 points vs independent human grading. The system is gap-closing, not frontier-pushing — it produces competent papers about validated methods but cannot push the methodological frontier beyond what the architect conceives.

## Adapting to Your Domain

The skills are **domain-agnostic** — all domain knowledge comes from the research brief. To use for any domain:

1. Copy [`research_brief_template.md`](research_brief_template.md) and fill it out
2. Place reference papers in a `reference/` directory
3. Run: `/research-pipeline your_brief.md`

The template covers: problem statement, data assets, domain context, target venue, success criteria, comparator methods, adjacent fields, evaluation design, and scope constraints.

Or start from a single sentence — Phase 0 (brief-expander) will auto-generate the full brief.

See [`examples/conformal_prediction/`](examples/conformal_prediction/) for a worked example.

## Requirements

- Claude Code with access to the Agent/Task tools
- Python environment with numpy, scipy, pandas, matplotlib (for Phase 2-3 code execution)
- LaTeX installation (for Phase 3-4 compilation checks)

## Repository Structure

```
ARMS/
├── README.md                              # This file
├── LICENSE                                # CC BY-NC 4.0
├── DISCLAIMER.md                          # LLM verification disclaimer
├── research_brief_template.md             # Start here — fill this out
├── skills/                                # 13 skills (12 pipeline + Critic-Revisor)
│   ├── research-pipeline/SKILL.md         #   Outer orchestrator
│   ├── brief-expander/SKILL.md            #   Phase 0: SCOPE
│   ├── methodology-architect/SKILL.md     #   Phase 1: THINK
│   ├── validate-method/SKILL.md           #   Phase 2: VALIDATE
│   ├── write-manuscript/SKILL.md          #   Phase 3: WRITE orchestrator
│   ├── literature-lead/SKILL.md           #   Phase 3 sub-agent
│   ├── paper-modeler/SKILL.md             #   Phase 3 sub-agent
│   ├── paper-writer/SKILL.md              #   Phase 3 sub-agent
│   ├── paper-critic/SKILL.md              #   Phase 3 sub-agent
│   ├── paper-grader/SKILL.md              #   Phase 4: POLISH
│   ├── paper-fixer/SKILL.md               #   Phase 4: POLISH
│   ├── house-style/                       #   Phases 3–4: exemplar-based house voice + rewrite
│   │   ├── SKILL.md
│   │   ├── scripts/style_metrics.py       #     Advisory style metrics (--ref to compare with your exemplar)
│   │   └── examples/                      #     Worked rewrite with a number ledger
│   └── critic-revisor/                    #   Augmentation: adversarial review loop
│       ├── SKILL.md                       #     Orchestrator (Opus review, Codex revise)
│       └── run_loop.sh                    #     The loop script
├── examples/
│   └── conformal_prediction/              # Worked example brief
│       └── research_brief.md
└── case-studies/
    └── conformal-prediction/              # DISCOM-CP: fully autonomous, 40/50
        ├── manuscript.tex                 #   NeurIPS-format paper
        ├── code/                          #   Validated implementation
        ├── data/                          #   All result CSVs
        ├── figures/                       #   Publication-quality PDF figures
        ├── methodology_specification.md   #   What the architect designed
        ├── validation_report.md           #   Phase 2 verdict
        ├── paper_grade.md                 #   Final grade report
        └── pipeline_log.md               #   Full pipeline trace
```

## Case Studies

### Conformal Prediction (Machine Learning)

The pipeline was given a research brief about multi-source conformal prediction under distribution shift. With zero human input, it:

1. **Designed DISCOM-CP** — a method that weights calibration sources by KS-statistic discrepancy on nonconformity scores, bypassing density ratio estimation
2. **Validated it** across 5 shift types with 6 iterations of refinement (CONDITIONAL GO)
3. **Wrote a NeurIPS-format paper** with 2 real-world datasets, ablation study, significance tests, and conditional coverage analysis
4. **Polished it** through 3 grade-fix rounds: 32 → 39 → 40 → 41.5/50

| Metric | Value |
|--------|-------|
| Method discovered | DISCOM-CP (discrepancy-guided source weighting) |
| Time | ~1.5 hours |
| Human effort | 0 (fully autonomous) |
| Self-grade | 41.5/50 (Grade B) |
| Independent grade | 40/50 (Grade B) |
| Grading inflation | 1.5 points |

The method was not prescribed in the brief. See [`case-studies/conformal-prediction/`](case-studies/conformal-prediction/) for the full pipeline output.

### Bayesian Clinical Trials (Biostatistics)

Two additional case studies using the biostatistics-specific version of these skills are available at [ARMS-Biostat](https://github.com/koaeraser/ARMS-Biostat):

| | Fully Autonomous (KG-DAP) | Human-Revised (KG-CAR) |
|--|--|--|
| Time | ~3h | ~3h + ~6h human |
| Independent score | 38/50 (B) | 39/50 (B) |

## Provenance

Developed March 2026. The v1 system (simple write-grade-fix loop) identified the plateau problem; the v2 system was designed from scratch to address it. The 11 pipeline skills began as a biostatistics-specific pipeline ([ARMS-Biostat](https://github.com/koaeraser/ARMS-Biostat), KG-DAP run 2026-03-23), then were generalized to domain-agnostic form and first released here on 2026-03-24; the conformal prediction case study was produced the same day, as the first test of the generalized skills. The **Critic-Revisor** augmentation (now the 13th skill) was added on 2026-06-10. The **House Style** skill was added on 2026-09-25, after drafts that passed every tic check were still found to drift from the target voice. Its style metrics began as enforced bands and were made advisory the same day, when an approved exemplar abstract fell outside the sentence-length band; the exemplar and the reader-first read became the standard.

## License

CC BY-NC 4.0 (Creative Commons Attribution-NonCommercial 4.0 International)
