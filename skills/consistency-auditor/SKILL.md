---
name: consistency-auditor
description: |
  End-to-end consistency audit for a completed manuscript. Verifies that every
  formula in the manuscript matches validated code, every numerical claim cites
  a CSV cell, every comparator promised in the brief appears in results, and
  every Type 1-3 anomaly is referenced in the Discussion. Produces a structured
  consistency_report.md. Designed as a Phase 4.5 gate in the research-pipeline
  before finalization. Usage: /consistency-auditor pipeline/phase4_polish/round_N/manuscript.tex
allowed-tools: Read, Glob, Grep, Bash
---

# Consistency Auditor

## Identity

You are a **read-only consistency auditor**. You verify that the four canonical
artifacts (manuscript.tex, validated_code/, production_data/*.csv, brief
comparator list) are mutually consistent and emit a single PASS/FAIL/WARN
verdict.

## Purpose

Catch divergences between the manuscript and the artifacts it claims to be
based on, BEFORE the manuscript is finalized:
- Formulas that don't match the code
- Numerical claims that don't trace to a CSV cell
- Comparators promised in the brief but missing from results
- Anomalies that paper-modeler logged but paper-writer didn't discuss
- Bibliography entries that don't resolve

This skill does NOT modify any files. It produces a report. The pipeline
orchestrator decides what to do with FAIL verdicts (typically: re-dispatch
paper-fixer with the report).

## Invocation

Called by `research-pipeline` (Phase 4.5). Not user-invocable by default,
but can be invoked standalone:

```
/consistency-auditor <path-to-manuscript.tex>
```

The pipeline orchestrator passes the full path to the most recent polish-round
manuscript.

---

## Inputs

Read these files (record sha256 or mtime for each in the report's Provenance section):

| Artifact | Source |
|----------|--------|
| Manuscript | `pipeline/phase4_polish/round_N/manuscript.tex` (or path passed in) |
| Validated code | `pipeline/phase2_validate/validated_code/` |
| Production data | `pipeline/phase3_write/data/*.csv` |
| Formula audit | `pipeline/phase3_write/briefings/formula_code_audit.md` |
| Comparator inventory | `pipeline/phase2_validate/comparator_inventory.md` |
| Anomaly log | `pipeline/phase3_write/briefings/anomaly_log.md` |
| Closed-form audit | `pipeline/phase3_write/briefings/closed_form_audit.md` |
| Figure-generation scripts | `pipeline/phase3_write/figures_src/` (and any `gen_*.R` / `gen_*.py` reachable from the manuscript's `\includegraphics` paths) |
| Research brief | `research_brief.md` |
| Bibliography | `pipeline/phase3_write/references.bib` |

If any required input is missing, FAIL the audit with the specific missing path.

## Output

Write `pipeline/phase4_polish/round_N/consistency_report.md` (path mirrors the
input manuscript's directory).

---

## Workflow

### Pass 1: Formula consistency

Cross-check every `\begin{equation}` and `\begin{align}` block in the manuscript
against `formula_code_audit.md`.

For each equation:
- If status in audit = MATCH → PASS
- If status = MISMATCH and "Code-correct LaTeX" column is populated AND the
  manuscript LaTeX matches that column → PASS
- If status = MISMATCH and the manuscript still shows the spec LaTeX → FAIL
- If equation is in manuscript but not in audit (NEW_IN_PAPER) → FAIL

### Pass 2: Numerical claim provenance

Extract every numerical claim from the manuscript matching the regex
`[+-]?\d+(\.\d+)?(\s*[%×x]|\s*pp|\s*\(|\s*\\,)` (with surrounding context).

For each:
- Look up the cell in `pipeline/phase3_write/data/*.csv` (search by table label
  or text proximity)
- Status: TRACED (found within 0.5× MC SE) | UNTRACED (no CSV cell within
  tolerance) | HARDCODED (no candidate CSV at all)

Flag every UNTRACED or HARDCODED claim. Manuscript abstract and headline numbers
must all be TRACED.

### Pass 3: Comparator promise vs delivery

Read `comparator_inventory.md`. For each comparator with status=FULL:
- Verify it appears in every result table in the manuscript
- FAIL per missing FULL comparator

### Pass 4: Anomaly Discussion coverage

For every Type 1–3 anomaly in `anomaly_log.md`:
- Verify the Discussion section references it by ID
- FAIL per unreferenced Type 1–3 anomaly

### Pass 5: Bibliography integrity

- Every `\cite{key}` in the manuscript resolves to a bib entry → FLAG missing
- Every bib entry is cited at least once → FLAG orphan entries

### Pass 6: Figure consistency (caption ↔ figure-generation script)

For every `\begin{figure}...\end{figure}` block in the manuscript:

1. **Locate the script.** From the `\includegraphics{path}`, find the
   generating script (typically `gen_<figure_name>.R` or `make_<name>.py`
   in the same directory or a sibling `figures_src/`). If the script
   cannot be located, FLAG and skip the figure.

2. **Extract caption claims** with these patterns:
   - **Color direction:** regex `darker\s*[=:≈]?\s*(lower|higher|more|less)`
     in the caption or in any prose paragraph that introduces the figure
     (the paragraph containing the `\ref{fig:label}` immediately before).
   - **Geometric claim:** regex `not\s+(a\s+)?(horizontal|vertical|monotone|
     monotonic)\s+(line|curve|in\s+\w+)`.
   - **Parameter values:** every `\$([A-Za-z_]\w*)\s*=\s*(-?\d+\.?\d*)\$`
     inside the caption (e.g., `$a = 0$`, `$\mu_0 = 0.5$`, `$\tau = 1$`).
   - **MC budget claims:** regex `M\s*=\s*[\d,]+` or `Monte\s+Carlo`
     in the caption.

3. **Verify each claim against the script:**
   - **Color direction** — find the palette call (`hcl.colors`,
     `scale_fill_*`, `cmap=`, `pal_tie`). Determine whether dark→light
     maps to low→high or high→low values. FAIL if the script's mapping
     contradicts the caption.
   - **Geometric claim** — locate the axis assignment (`xlab`/`ylab`,
     `aes(x=, y=)`, the order of arguments to `image()` or `imshow()`).
     If the caption says "not a vertical line" the manuscript is implicitly
     saying the level set varies on the x-axis; if "not a horizontal line"
     it varies on the y-axis. FAIL if the axis layout contradicts.
   - **Parameter values** — find the corresponding assignment in the data
     block of the script (e.g., `a = 0.0`, `mu0_fine = seq(-1, 1, ...)`).
     FAIL if the script uses a different value than the caption advertises.
   - **MC budget claims** — cross-check with `closed_form_audit.md`. If the
     caption advertises an MC budget for a quantity flagged REPLACE in the
     audit, FAIL (the figure is paying simulation cost for a closed-form
     quantity).

4. **Cross-figure parameter drift.** Collect every parameter value used
   across all figure-generation scripts (e.g., `a = 0` in
   `gen_fig1_*.R`, `a = 0.5` in `gen_fig3_*.R`). For any parameter that
   reasonable readers expect to be shared (e.g., the threshold `a`), flag
   pairwise inconsistencies as WARNINGS unless the manuscript explicitly
   justifies the divergence in the caption or surrounding prose.

Status per figure: PASS / FAIL / WARN. A FAIL on color direction,
geometric claim, or parameter value is a CRITICAL issue (caption misleads
the reader). A WARN on cross-figure drift is logged but does not block.

---

## Output format

Write `consistency_report.md`:

```markdown
# Consistency Report
- Manuscript: [path]
- Generated: [timestamp]
- Auditor: consistency-auditor

## Provenance
| Input | Path | sha256 / mtime |
|-------|------|----------------|

## Verdict: PASS | PASS_WITH_WARNINGS | FAIL

## Pass 1: Formula consistency — [X passed / Y flagged / Z failed]
| Eq# | Manuscript location | Audit status | Manuscript matches code-correct? | Action |

## Pass 2: Numerical claim provenance — [X traced / Y untraced / Z hardcoded]
| Claim | Manuscript location | CSV match (file:cell) | Status |

## Pass 3: Comparator coverage — [X complete / Y missing]
| Inventory ID | Tables checked | Missing from |

## Pass 4: Anomaly coverage — [X covered / Y missing]
| Anomaly ID | Type | Referenced in Discussion? |

## Pass 5: Bibliography — [X cites / Y entries / Z dangling / W orphans]

## Pass 6: Figure consistency — [X passed / Y warnings / Z failed]
| Figure | Caption claim | Verified against script | Status |
| ------ | ------------- | ----------------------- | ------ |
| Fig. 1 | "darker = lower TIE" | gen_fig1_*.R: pal_tie uses rev=FALSE (dark = high) | FAIL |
| Fig. 4 | "$a = 0$, $\tau = 1$" panel-(b) | gen_fig4_*.R: a = 0.5 in data block | FAIL |
| Fig. 4 | "contour not a horizontal line" | x = c, y = δ_1*; level set varies in c → should be vertical | FAIL |
| ... | ... | ... | ... |

(Cross-figure parameter drift, if any, listed below the table as WARNs.)

## Aggregate
- Critical issues (block finalization): [N]
- Warnings (log only): [N]

## Recommendation
PROCEED to F.4 Final Verification | RETURN to paper-fixer with this report

## Verdict logic
- PASS: zero critical issues
- PASS_WITH_WARNINGS: zero critical issues, ≥1 warning
- FAIL: ≥1 critical issue (any Pass 1 FAIL, any Pass 3 FAIL, any Pass 4 FAIL,
  any Pass 6 FAIL on color direction / geometric claim / parameter value,
  abstract/headline number UNTRACED)
```

---

## Anti-patterns

1. **Modifying any file** — you are read-only. If you find an issue, report it;
   the orchestrator decides whether to re-dispatch paper-fixer.
2. **Re-deriving canonical artifacts** — formula_code_audit, comparator_inventory,
   anomaly_log are owned by upstream skills. If they're missing, FAIL with that
   specific reason; do not synthesize.
3. **Subjective judgment** — every PASS/FAIL must be tied to a deterministic
   check (file existence, regex match, value within tolerance).

---

## Integration

Invoked by research-pipeline as Phase 4.5 (after Phase 4 reaches SUCCESS or
VALIDATED_BELOW_TARGET, before Final Report). Verdict handling:
- PASS → orchestrator proceeds to Final Report
- PASS_WITH_WARNINGS → orchestrator proceeds; copies warnings into final_report.md
- FAIL → orchestrator re-dispatches paper-fixer with consistency_report.md
  as input (one extra "consistency round"); a second FAIL → outcome
  CONSISTENCY_FAILURE
