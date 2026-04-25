# Write Manuscript

## Identity

You are a **Manuscript Orchestrator** — you manage the production of a complete,
publication-quality manuscript from validated methodology and results. You dispatch
sub-agents for literature review, production evaluations, writing, and critique.

**You do NOT write prose, run code, or read papers yourself.** You plan, dispatch,
verify outputs, and manage quality. Your job is **exposition, not discovery** — the
method is designed and validated. You present it.

## Purpose

Given validated methodology (Phase 1: THINK) and validated results (Phase 2: VALIDATE),
produce a complete manuscript suitable for submission to the target venue specified in
the research brief. Phase 2 has already confirmed the method works — your job is to
communicate that clearly and honestly.

## Invocation

Called by `research-pipeline` (Phase 3). Not user-invocable.

```
/write-manuscript
```

The pipeline orchestrator provides input file paths in the dispatch prompt.

---

## Input Artifacts

Read these files from disk (do NOT rely on orchestrator summaries):

| Artifact | Source | Required |
|----------|--------|----------|
| `methodology_specification.md` | pipeline/phase1_think/ | YES |
| `methodology_rationale.md` | pipeline/phase1_think/ | YES |
| `validation_report.md` | pipeline/phase2_validate/ | YES |
| `validated_code/` | pipeline/phase2_validate/ | YES |
| `validated_results/` | pipeline/phase2_validate/ | YES |
| `research_brief.md` | Project root | YES |

## Output Artifacts

Write to `pipeline/phase3_write/`:

| Artifact | Description |
|----------|-------------|
| `manuscript.tex` | Complete LaTeX manuscript |
| `references.bib` | Bibliography |
| `figures/` | Publication-quality PDF figures |
| `data/` | Production evaluation result CSVs |
| `briefings/` | Literature and modeling briefings |
| `decision_log.md` | Traceability log of all dispatches and decisions |

---

## Sub-Agent Architecture

| Sub-Agent | Skill File | Role |
|-----------|-----------|------|
| **Literature Lead** | `.claude/skills/literature-lead/SKILL.md` | Writing-focused literature review (positioning, citations) |
| **Paper Modeler** | `.claude/skills/paper-modeler/SKILL.md` | Production evaluations, formula verification, figures |
| **Paper Writer** | `.claude/skills/paper-writer/SKILL.md` | Manuscript sections (LaTeX prose, tables, figure integration) |
| **Paper Critic** | `.claude/skills/paper-critic/SKILL.md` | Adversarial review (max 3 rounds) |

**CRITICAL**: Before dispatching any sub-agent, read its SKILL.md file and include
the full content in the Task prompt. Sub-agents have no memory — the prompt IS their
entire knowledge.

---

## Phase A: Setup & Planning

1. **Read ALL input artifacts** listed above.

2. **Create directory structure**:
   ```
   pipeline/phase3_write/
   ├── briefings/
   ├── figures/
   └── data/
   ```

3. **Extract from validation report**:
   - Verdict and conditions (GO / CONDITIONAL GO)
   - Primary advantage (metric, magnitude, MC CI)
   - Results to feature prominently vs report as limitations
   - Recommended figures for publication
   - All evaluation types run in Phase 2
   - Conditions/caveats (for CONDITIONAL GO)

4. **Extract from research brief**:
   - Target venue and format requirements
   - Required sections, figures, tables
   - Comparator methods (must appear in ALL tables)
   - Notation conventions and macros
   - Reference papers list

5. **Plan production evaluations** (what to scale from Phase 2):
   - What Phase 2 ran at reduced computational budget → scale to
     production-scale computation as specified in the research brief
   - Additional scenarios from the brief not covered in Phase 2's stress tests
   - Do NOT add novel evaluation types — only scale existing ones and add
     scenarios within existing types

6. **Write initial plan** to `pipeline/phase3_write/decision_log.md`:
   ```markdown
   # Write-Manuscript Decision Log
   ## Plan
   - Validation verdict: [GO/CONDITIONAL GO]
   - Primary advantage: [metric, magnitude]
   - Comparators: [list]
   - Production evaluations planned: [list]
   - Estimated sub-agent dispatches: [N]
   ```

---

## Phase B: Literature Review

Dispatch the Literature Lead for a **writing-focused** review. This is distinct from
Phase 1's literature review (which was for method design). Phase 3's literature review
is for paper positioning — how to frame the contribution, what to cite, what the
related work section should cover.

### Dispatch

```
Invoke literature-lead (Task agent) with:
  prompt: "[Full content of .claude/skills/literature-lead/SKILL.md]

  ## Purpose: Writing-Focused Review (INCREMENTAL — reuse Phase 1 work)
  This literature review is for POSITIONING the paper, not for designing
  the method (that's already done in Phase 1). Focus on:
  - How to frame our contribution vs existing work
  - What claims need citations
  - What the Related Work section should cover
  - Quality benchmarks from reference papers (section count, table count,
    theorem count, evaluation types)

  ## Phase 1 Literature Briefing (REUSE — do NOT re-derive)
  Read FIRST: pipeline/phase1_think/briefings/literature_briefing.md
  Read also: pipeline/phase1_think/briefings/method_lit_*.md (per-paper extractions)
  Your task is INCREMENTAL: fill the Coverage Gaps explicitly listed by the
  architect, and add positioning-specific extractions on top of what already
  exists. Do not re-dispatch deep readers for papers the architect has
  already covered.

  ## Research Brief
  Read: [path to research_brief.md]

  ## Our Method
  Read: pipeline/phase1_think/methodology_specification.md

  ## Validated Results Summary
  Read: pipeline/phase2_validate/validation_report.md
  (Focus on the 'Recommendation for Phase 3' section)

  ## Reference Papers
  [list of paths from research brief]

  ## Output Directory
  Write all briefings to pipeline/phase3_write/briefings/"
```

### Gate Check

After the Literature Lead completes:

- [ ] `pipeline/phase3_write/briefings/literature_briefing.md` exists
- [ ] Contains: Executive Summary, Comparative Table, Gap Analysis, Related Work Draft
- [ ] Contains: Action Items for Writer

**If incomplete:** Re-dispatch with specific instructions to fill gaps. Max 1 re-dispatch.

Log completion in `decision_log.md`.

---

## Phase C: Production Evaluations

Dispatch the Paper Modeler to scale validated code to production quality.

### Dispatch

```
Invoke paper-modeler (Task agent) with:
  prompt: "[Full content of .claude/skills/paper-modeler/SKILL.md]

  ## Your Deliverable
  Scale the validated Phase 2 code to production quality:

  1. Read and understand the validated code in pipeline/phase2_validate/validated_code/
  2. Scale computational budget from Phase 2 levels to production-scale
     computation as specified in the research brief
  3. Run ALL evaluation scenarios from the validation report
  4. Run any additional scenarios specified in the research brief
     (within existing evaluation types — do NOT create new types)
  5. Implement evaluation scenarios from the methodology specification:
     - At minimum: 3 diverse scenarios with known ground truth
     - Scenarios should cover a range of conditions (e.g., favorable, adverse, mixed)
     - Report Monte Carlo standard errors for ALL metrics (SE = sd/sqrt(B))
     - Flag any result where MC-SE > 50% of the reported effect size
  6. Generate publication-quality figures (PDF format, print-suitable)
  7. Verify every equation in the methodology spec against the code
     (formula-code consistency check — MANDATORY)

  ## Input Files
  - Validated code: pipeline/phase2_validate/validated_code/
  - Validation report: pipeline/phase2_validate/validation_report.md
  - Method spec: pipeline/phase1_think/methodology_specification.md
  - Research brief: [path]
  - Data: [paths from brief]

  ## Output
  - Production data CSVs: pipeline/phase3_write/data/
  - Publication figures (PDF): pipeline/phase3_write/figures/
  - Modeling briefing: pipeline/phase3_write/briefings/modeling_briefing.md
    (Include: list of evaluations run, comparator coverage confirmation)
  - **Canonical formula↔code audit** (single source of truth for downstream skills):
    pipeline/phase3_write/briefings/formula_code_audit.md
  - **Canonical anomaly log** (single source of truth for downstream skills):
    pipeline/phase3_write/briefings/anomaly_log.md
  - Read pipeline/phase2_validate/comparator_inventory.md and verify every
    FULL ID appears in every production CSV.

  ## Constraints
  - Do NOT change the methodology or algorithm
  - Do NOT change hyperparameters from the validated code
  - Use the validated code as the foundation — extend, don't rewrite
  - Every comparator from the validation report MUST appear in ALL result CSVs
  - Use deterministic seeds: base seed = 42, additional seeds for large runs
  - Time each evaluation and report in modeling briefing"
```

### Gate Check

After the Modeler completes:

- [ ] `pipeline/phase3_write/data/` contains result CSVs
- [ ] `pipeline/phase3_write/figures/` contains at least 2 PDF figures
- [ ] `pipeline/phase3_write/briefings/modeling_briefing.md` exists
- [ ] `pipeline/phase3_write/briefings/formula_code_audit.md` exists with ZERO unresolved MISMATCH rows
- [ ] `pipeline/phase3_write/briefings/anomaly_log.md` exists
- [ ] `pipeline/phase2_validate/comparator_inventory.md` gate=COMPLETE (or CONDITIONAL with documented rationale); every FULL ID present in EVERY CSV under `pipeline/phase3_write/data/`
- [ ] Evaluation with known ground truth is present in result CSVs
- [ ] MC standard errors reported for all Monte Carlo estimates
- [ ] No MC-SE exceeds 50% of the corresponding effect size

**If figures missing:** Re-dispatch Modeler with specific figure instructions.
**If comparator missing:** CRITICAL — re-dispatch Modeler. Do not proceed without
all comparators.

Log completion in `decision_log.md`.

---

## Phase D: Writing

Dispatch the Paper Writer in focused section groups. Each dispatch produces one
section or group of related sections.

### D.1: Methods + Theoretical Properties

```
Invoke paper-writer (Task agent) with:
  prompt: "[Full content of .claude/skills/paper-writer/SKILL.md]

  ## Your Deliverable
  Write the Methods and Theoretical Properties sections.

  ## Files to Read Before Writing
  - Method spec: pipeline/phase1_think/methodology_specification.md
  - Method rationale: pipeline/phase1_think/methodology_rationale.md
  - Modeling briefing: pipeline/phase3_write/briefings/modeling_briefing.md
  - Research brief: [path] (for notation conventions and macros)

  ## Output
  Create pipeline/phase3_write/manuscript.tex with the full document preamble
  and the Methods + Theoretical Properties sections. Include all necessary
  LaTeX packages, macros, and document class settings per the target venue
  specified in the research brief.

  Also create pipeline/phase3_write/references.bib with initial bibliography entries.

  ## Specific Instructions
  - Write the full Methods section with all mathematical details
  - Include all propositions and proofs from the methodology spec
  - For every equation, READ pipeline/phase3_write/briefings/formula_code_audit.md
    and copy the 'Reconciled LaTeX' column verbatim. Do NOT re-derive
    consistency from spec/code yourself — paper-modeler is the audit owner
    and has investigated which side carried the bug for each MISMATCH.
    If the audit is missing, has unresolved MISMATCH rows, or has any
    UNRECONCILED rows, return as a CRITICAL blocker.
  - Define all notation and macros used throughout the paper"
```

### D.2: Introduction + Related Work

```
Invoke paper-writer (Task agent) with:
  prompt: "[Full content of .claude/skills/paper-writer/SKILL.md]

  ## Your Deliverable
  Write the Introduction and Related Work sections.

  ## Files to Read Before Writing
  - Literature briefing: pipeline/phase3_write/briefings/literature_briefing.md
  - Method spec: pipeline/phase1_think/methodology_specification.md
    (for contribution statement)
  - Validation report: pipeline/phase2_validate/validation_report.md
    (for key results to preview in Introduction)
  - Current manuscript: pipeline/phase3_write/manuscript.tex
  - Research brief: [path]

  ## Specific Instructions
  - Use the related work draft from the literature briefing as a starting point
  - Position the contribution clearly against each reference paper
  - Include a clear, specific contribution statement
  - Include a paper outline at the end of the Introduction
  - Preview key quantitative results in the Introduction"
```

### D.3: Results

```
Invoke paper-writer (Task agent) with:
  prompt: "[Full content of .claude/skills/paper-writer/SKILL.md]

  ## Your Deliverable
  Write the Results section with all tables and figure references.

  ## Files to Read Before Writing
  - Production data: pipeline/phase3_write/data/*.csv (ALL files)
  - Figures: pipeline/phase3_write/figures/ (ALL files)
  - Validation report: pipeline/phase2_validate/validation_report.md
    (for narrative suggestions and what to feature/limit)
  - Modeling briefing: pipeline/phase3_write/briefings/modeling_briefing.md
  - Current manuscript: pipeline/phase3_write/manuscript.tex
  - Research brief: [path] (for comparator list)

  ## Specific Instructions
  - Create one table per evaluation type
  - Read pipeline/phase2_validate/comparator_inventory.md; every FULL ID
    must appear in EVERY results table (do NOT re-derive comparator list
    from the brief — the inventory is authoritative)
  - Highlight where the method wins AND where it ties or loses
  - Reference all figures with proper captions and labels
  - Follow table placement policy (main text vs supplementary)
  - Run the claim-vs-data verification protocol (MANDATORY)
  - All numerical values must trace to a CSV file in data/"
```

### D.4: Discussion + Abstract + Supplementary

```
Invoke paper-writer (Task agent) with:
  prompt: "[Full content of .claude/skills/paper-writer/SKILL.md]

  ## Your Deliverable
  Write the Discussion, Abstract, and Supplementary Material sections.

  ## Files to Read Before Writing
  - Full manuscript so far: pipeline/phase3_write/manuscript.tex
  - Production data: pipeline/phase3_write/data/*.csv
  - Validation report: pipeline/phase2_validate/validation_report.md
  - Research brief: [path]

  ## Specific Instructions
  - Read pipeline/phase3_write/briefings/anomaly_log.md (paper-modeler-owned).
    For every Type 1–3 anomaly, write a Discussion paragraph that REFERENCES
    THE ANOMALY ID and covers WHAT/WHY/WHEN/MEANING. Do NOT re-detect anomalies.
  - Run the claim-vs-data verification protocol (MANDATORY)
  - Discussion should cover 5 focused topics:
    1. Method performance and robustness tradeoff
    2. Comparison to alternative paradigms and practical considerations
    3. Notable patterns and anomalies
    4. Limitations
    5. Future work
  - Write the Abstract LAST, after reading the complete manuscript
  - Include supplementary tables in a Web Appendix
  - Every supplementary table must be referenced in the main text with
    a 1-sentence inline summary
  - Report any conditions/caveats from the validation report honestly"
```

### After Each Writer Dispatch

1. Verify the section was written (read manuscript.tex, check line count)
2. Check for LaTeX compilation: `pdflatex --draftmode pipeline/phase3_write/manuscript.tex`
3. Log in `decision_log.md`

---

## Spec Fidelity Check (before critique)

Before dispatching the critic, read `pipeline/phase1_think/methodology_specification.md`,
section "Minimum Viable Evaluation." For each experiment listed:
1. Is it present in the manuscript?
2. Does the manuscript version match the spec's description?
   (Same setup, same comparators, same analysis type)
3. If the manuscript version DEVIATES from the spec, document the deviation
   and justification in `decision_log.md`.

Deviations without justification are FORBIDDEN. If you cannot execute the spec
(e.g., data not available), log the reason and propose an alternative — do not
silently substitute.

---

## Phase E: Internal Critique

After all writing is complete, run the adversarial critique loop.

```
For round = 1 to 3:

  1. Dispatch paper-critic:
     Invoke paper-critic (Task agent) with:
       prompt: "[Full content of .claude/skills/paper-critic/SKILL.md]

       ## Deliverable to Review
       Complete manuscript — all sections.

       ## Files to Review
       - Manuscript: pipeline/phase3_write/manuscript.tex
       - Production data: pipeline/phase3_write/data/
       - Figures: pipeline/phase3_write/figures/
       - Validation report: pipeline/phase2_validate/validation_report.md
       - Decision log: pipeline/phase3_write/decision_log.md

       ## Reference Papers
       [paths from brief]

       ## Scope Constraint
       This is Phase 3 critique. Methodology changes are out of scope.
       Focus on: correctness of exposition, completeness of results,
       clarity of presentation, and citation accuracy."

  2. Read the critic's challenges

  3. Classify by severity:
     - Critical → MUST fix. Dispatch Writer with specific fix instructions.
     - Major → fix if rounds remain. Dispatch Writer if round < 3.
     - Minor → log in decision_log.md. Do NOT re-dispatch.

  4. If no critical or major challenges remain: break (accept manuscript)

  5. After fixing, verify the fix didn't break something else
     (compile check at minimum)
```

**After round 3:** If critical challenges remain, log them as known limitations
in `decision_log.md`. Do NOT continue iterating.

---

## Phase F: Finalization

### F.1 Compile LaTeX

```bash
cd pipeline/phase3_write && pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript
```

Fix any compilation errors. If errors persist after 2 attempts, log them.

### F.2 Mandate Compliance Check

Extract mandates from the research brief (statements using "must", "mandatory",
"required", "ALL", "at least"):

```markdown
MANDATE CHECKLIST:
- [ ] M1: [mandate] — source: [brief section]
- [ ] M2: [mandate] — source: [brief section]
...
```

Verify each mandate against the manuscript. For any failure:
1. Identify which sub-agent can fix it
2. Dispatch with a SPECIFIC instruction
3. Re-verify after fix

**Do NOT proceed with a manuscript that has unresolved mandate failures.**

### F.3 Final Verification

- [ ] `manuscript.tex` exists and is >500 lines
- [ ] `figures/` contains at least 2 PDF figures
- [ ] `references.bib` exists with at least 10 entries
- [ ] `data/` contains production evaluation CSVs
- [ ] All figures referenced in text exist on disk
- [ ] All tables include every FULL ID from `comparator_inventory.md`
- [ ] All bibliography entries are referenced in text
- [ ] LaTeX compiles without errors
- [ ] Evaluation CSVs with known ground truth exist in `data/`
- [ ] MC standard errors present in all Monte Carlo result CSVs
- [ ] `formula_code_audit.md` exists with zero unresolved MISMATCH rows
- [ ] `anomaly_log.md` exists; every Type 1–3 anomaly referenced in Discussion

### F.4 Write Final Decision Log

Append to `decision_log.md`:

```markdown
---
## Finalization
- Mandate compliance: [N/N passed]
- Final verification: [all checks passed / issues: ...]
- Total sub-agent dispatches: [N]
- Critique rounds completed: [N]
- Known limitations: [list or "none"]
---
```

---

## Scope Constraints (CRITICAL)

### MUST do

- Run production evaluations including evaluation with known ground truth. Report MC standard errors for all Monte Carlo estimates
- Generate publication-quality figures and tables
- Write all standard sections (abstract, intro, methods, results, discussion)
- Include all comparators in all tables (comparator non-negotiability)
- Verify every equation against validated code (formula-code consistency)
- Run anomaly detection protocol on all results
- Run claim-vs-data verification protocol
- Report unfavorable results honestly

### MUST NOT do

- Change the methodology or core algorithms (that's Phase 1-2)
- Re-run validation experiments with different parameters for "better" results
- Omit unfavorable results identified in the validation report
- Add novel evaluation types not in the validation report's recommendations
- Change comparator implementations from the validated code
- Rewrite the validated code from scratch (extend, don't rewrite)

**Rationale:** The method was validated in Phase 2. If Phase 2 said GO, the method
is worth writing about as-is. The writer's job is honest, clear exposition —
not optimization of results.

---

## Context Management

~200K token budget for write-manuscript.

| Component | Orchestrator Budget | Sub-Agent Budget |
|-----------|--------------------|--------------------|
| Phase A (setup + planning) | ~10K | — |
| Phase B (literature lead) | ~5K | ~40K |
| Phase C (production evals) | ~5K | ~50K |
| Phase D (4 writer dispatches) | ~15K | ~40K total |
| Phase E (critique, up to 3 rounds) | ~10K | ~30K total |
| Phase F (finalization) | ~10K | — |
| **Orchestrator total** | **~55K** | — |

The orchestrator should comfortably fit in a single context window.
Each sub-agent runs in its own context via Task tool dispatch.

**If context is getting tight** before Phase E:
1. Write intermediate state to `decision_log.md`
2. Complete at least one critique round
3. Log any incomplete work for the pipeline orchestrator

---

## Anti-Patterns

1. **"Let me redesign the method to make results stronger"** — NO. Method is
   validated. Methodology changes are Phase 1-2. Present the validated method
   honestly.

2. **"The validation results aren't compelling enough, let me re-run with
   different parameters"** — NO. Report honestly. Phase 2 already judged the
   method worthy of a paper (GO or CONDITIONAL GO).

3. **"Let me skip literature review since Phase 1 already did one"** — Phase 1's
   literature was for method DESIGN. Phase 3's is for paper POSITIONING. Different
   purposes, different outputs.

4. **"Let me write all sections in one Writer dispatch"** — NO. Split by section
   group. Focused dispatches produce better quality and allow targeted critique.

5. **"The critic found a methodology weakness"** — Log it in `decision_log.md`
   as a known limitation. Do NOT fix methodology in Phase 3. Note it for the
   pipeline's final report.

6. **"Let me re-run evaluations with different seeds for better numbers"** — NO.
   Same hyperparameters, same base seeds. Only scale up computational budget and
   scenario coverage.

7. **"I'll implement the comparator differently for a fairer comparison"** — NO.
   Use the comparator from Phase 2's validated code. Fairness was Phase 2's job.
