# Research Pipeline

End-to-end orchestrator for autonomous Bayesian biostatistics paper production. Takes a research brief and drives 5 phases from problem statement to graded manuscript, dispatching specialist sub-skills at each stage and enforcing structural gates between them.

For execution detail and prompt content see `SKILL.md`. For the brief format, see `research_brief_template.md`.

---

## Quick start

```
/research-pipeline research_brief.md [target=42] [max_polish=3] [max_rethinks=2] [max_phase_retries=2] [venue_compliance=on]
```

The orchestrator creates a `pipeline/` directory in the project root and writes every phase's outputs to disk. Resume from any interruption by re-invoking with the same brief — `pipeline_state.md` is the source of truth, with filesystem-based recovery if the state file is corrupt.

Final outcomes: `SUCCESS` | `VALIDATED_BELOW_TARGET` | `MARGINAL_STOP` | `NO_GO` | `KILL` | `PHASE_1_INCOMPLETE` | `PHASE_3_INCOMPLETE` | `CONSISTENCY_FAILURE` | `VALIDATED_BUT_VENUE_NONCOMPLIANT`.

---

## Architecture

```
                   ┌──────────────────┐
                   │ Phase 0: SCOPE   │
                   │ (brief-expander) │
                   │ if brief sparse  │
                   └──────┬───────────┘
                          ▼
                   ┌──────────────┐
                   │ Phase 1:     │
                   │ THINK        │   →  brief_audit.md
                   │ methodology- │   →  literature_briefing.md  ──┐
                   │ architect    │                                │
                   └──────┬───────┘                                │
                          ▼                                        │
                   ┌──────────────┐                                │
             ┌───▶ │ Phase 2:     │   →  comparator_inventory.md   │
             │     │ VALIDATE     │   →  formula_audit_seed.md     │
             │     │ validate-    │                                │
             │     │ method       │                                │
             │     └──────┬───────┘                                │
             │            │                                        │
             │      GO / COND. GO / MARGINAL / NO-GO               │
             │            │                                        │
             │  NO-GO → failure-diagnoser → RETHINK (max N)        │
             │  MARGINAL → MARGINAL_decision_required.md (paused)  │
             │            ▼                                        │
             │     ┌──────────────┐                                │
             │     │ Phase 3:     │ ←──────────────────────────────┘
             │     │ WRITE        │                  (READS Phase 1 lit briefing)
             │     │ write-       │   →  formula_code_audit.md
             │     │ manuscript   │   →  anomaly_log.md
             │     │ ├ literature-lead    (incremental — reuses Phase 1)
             │     │ ├ paper-modeler      (canonical formula+anomaly owner)
             │     │ ├ paper-writer
             │     │ └ paper-critic
             │     └──────┬───────┘
             │            ▼
             │     ┌──────────────┐
             │     │ Phase 4:     │
             │     │ POLISH       │
             │     │ paper-grader │ ⇄ paper-fixer  (max_polish rounds)
             │     │ + venue-compliance-gate (sub-gate)
             │     └──────┬───────┘
             │            ▼
             │     ┌──────────────┐
             │     │ Phase 4.5:   │
             │     │ CONSISTENCY  │   consistency-auditor verifies
             │     │ AUDIT        │   formula↔code↔manuscript
             │     └──────┬───────┘
             │   PASS  ◀──┴──▶  FAIL → 1 extra fixer round; 2nd FAIL = CONSISTENCY_FAILURE
             │            ▼
             │       final_report.md
             │
             └── (RETHINK loop)
```

---

## Sub-skills it dispatches

| Phase | Skill | Role |
|-------|-------|------|
| 0 | `brief-expander` | Expand sparse brief to all 9 canonical sections |
| 1 | `methodology-architect` | Design methodology; produce spec + brief audit + Phase 3 literature bridge |
| 2 | `validate-method` | Implement, validate, build comparator inventory; verdict GO/COND/MARGINAL/NO-GO |
| 2 (RETHINK) | `failure-diagnoser` | Convert NO-GO into structured 5-category diagnosis for the architect |
| 3 | `write-manuscript` | Orchestrates literature-lead, paper-modeler, paper-writer, paper-critic |
| 3 sub | `literature-lead` | Phase 3 positioning review (reuses Phase 1 work, fills coverage gaps) |
| 3 sub | `paper-modeler` | Production evals + canonical `formula_code_audit.md` + `anomaly_log.md` |
| 3 sub | `paper-writer` | LaTeX prose; reads canonical artifacts, does not re-derive |
| 3 sub | `paper-critic` | Adversarial review (max 3 rounds, severity-tagged per shared rubric) |
| 4 | `paper-grader` ↔ `paper-fixer` | Score + targeted fixes (max_polish rounds) |
| 4 sub | `venue-compliance-gate` | Verify abstract/page/figure/table/section limits per target venue |
| 4.5 | `consistency-auditor` | End-to-end formula/claim/comparator/anomaly/bib audit |

---

## Cross-skill canonical artifacts (single source of truth)

| Artifact | Owner | Read by |
|----------|-------|---------|
| `pipeline/phase1_think/brief_audit.md` | methodology-architect | research-pipeline (Phase 3 fidelity check) |
| `pipeline/phase1_think/briefings/literature_briefing.md` | methodology-architect | literature-lead (Phase 3) |
| `pipeline/phase2_validate/comparator_inventory.md` | validate-method | paper-modeler, paper-writer, paper-grader |
| `pipeline/phase2_validate/failure_diagnosis.md` | failure-diagnoser | methodology-architect (RETHINK) |
| `pipeline/phase3_write/briefings/formula_code_audit.md` | paper-modeler | paper-writer, paper-grader, paper-fixer |
| `pipeline/phase3_write/briefings/anomaly_log.md` | paper-modeler | paper-writer (Discussion), paper-grader |
| `pipeline/phase4_polish/round_N/consistency_report.md` | consistency-auditor | research-pipeline (4.5 gate) |
| `pipeline/phase4_polish/round_N/venue_compliance.md` | venue-compliance-gate | research-pipeline (Phase 4 sub-gate) |

Downstream skills READ these; they do NOT re-derive. This is enforced in each consumer's SKILL.md.

---

## Shared scoring rubric

`~/.claude/skills/_shared/scoring_rubric.md` is the canonical mapping between:
- `paper-grader`'s 7-dimension rubric (Correctness, Completeness, Rigor, Clarity, Novelty, Impact, Performance — weighted /50)
- `paper-critic`'s severities (critical / major / minor)
- `revision-loop`'s compliance statuses (FULLY_ADDRESSED / PARTIALLY_ADDRESSED / NOT_ADDRESSED / REGRESSION)

Plus the downgrade rule (round-3 reclassification) and the rule that Novelty/Impact/Performance are Phase 1–2 properties (revision-loop cannot lift them through prose edits — exit with `NOVELTY_CEILING`).

---

## Self-improvement loop

The pipeline is instrumented end-to-end so it can learn from its own runs.

```
            Stop hook                                /skill-auditor                       apply-proposal.sh
              fires                                    (weekly via                        (snapshots,
              after every                              launchd or                         applies, can
              pipeline run                             on demand)                         rollback)
                  │                                        │                                   │
                  ▼                                        ▼                                   ▼
      ~/.claude/skill-telemetry/         ~/.claude/skill-proposals/         ~/.claude/skills/_snapshots/
       research-pipeline/*.json           <ts>--research-pipeline/           <ts>/
       (one per finished run)             ├─ proposal.md                     (per-file backup before each apply)
                                          ├─ aggregate.json
                                          └─ NN-<slug>.diff (each cites a run_id)
```

- **Telemetry**: every finished `pipeline/final_report.md` triggers `~/.claude/hooks/research-pipeline-telemetry.sh`, which extracts a structured JSON snapshot (outcome, scores, gate failures, rethinks, residual issues, lessons-learned excerpt) into `~/.claude/skill-telemetry/research-pipeline/`. Idempotent via `(path, mtime)` fingerprint; never blocks the Stop event.
- **Audit**: `/skill-auditor research-pipeline --last 10` reads the corpus, aggregates failure patterns, and proposes ≤7 surgical SKILL.md edits as unified diffs. Every edit cites at least one `run_id`. Frontmatter changes require ≥3-run signal (high blast radius).
- **Apply**: `~/.claude/scripts/apply-proposal.sh <proposal-dir>` snapshots affected SKILL.md files to `~/.claude/skills/_snapshots/<ts>/`, validates ALL diffs (atomic — either all apply or none), and applies them. Rollback with `apply-proposal.sh --rollback <ts>`.
- **Cadence**: `~/Library/LaunchAgents/com.yuanj.skill-auditor.plist` schedules a weekly run (Mondays 09:15) headlessly via `claude -p`.

The loop is human-in-the-loop: the auditor never modifies skills directly; you review proposals and apply them.

---

## Files

- `SKILL.md` — full orchestrator behavior (gates, dispatch prompts, retry logic, anti-patterns)
- `research_brief_template.md` — required structure for input briefs (9 canonical sections)
- `README.md` — this file

## Versioning

- Per-round backups before any major refactor: `~/.claude/skills_backup_pre_round_{A,B,C}_<timestamp>/`
- Per-apply snapshots from `apply-proposal.sh`: `~/.claude/skills/_snapshots/<timestamp>/`
- All apply/rollback events logged in `~/.claude/skills/_snapshots/_history.log`
