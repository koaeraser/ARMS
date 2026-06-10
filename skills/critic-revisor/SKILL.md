---
name: critic-revisor
description: >
  Autonomous adversarial critic-revisor loop on a LaTeX manuscript. Two parallel
  Opus reviews per round with differentiated angles (methodologist + applied/
  contextual reader); reviewers can web-search within a per-round budget; Codex
  CLI applies the combined review; latexmk rebuilds the clean PDF; latexdiff
  produces a color-tracked PDF. Repeats until both reviewers say accept, no diff
  is produced, the LaTeX build fails, or the round budget is exhausted. Saves
  per-round subfolders under critic_revisor_logs/. Paper-agnostic. Use when the
  user asks to "run the adversarial loop", "auto-revise the manuscript",
  "critic-revisor", or similar.
user-invocable: true
argument-hint: <manuscript.tex> [max_rounds=5] [venue] [--sources <paths>]
---

# Critic-Revisor Loop

## Identity

You are an orchestrator. The actual work is done by `~/.claude/skills/critic-revisor/run_loop.sh`. Your job is to validate inputs, launch the script, and report the outcome.

**Role separation enforced by the script:**

- **Opus × 2** (review) — two independent reviewers per round read the manuscript and write structured critiques. Reviewer 1 is the **methodologist** (math, statistics, proofs, simulation design); reviewer 2 is the **applied/contextual reader** (framing, positioning, adjacent literature, reproducibility). They do not edit.
- **Codex** (revise) — reads the combined critique and edits the manuscript. It does not re-review.
- **latexmk + latexdiff** (build) — rebuilds clean PDF and produces color-tracked diff PDF after each revision.

This separation matches the user's standing preference: "opus review, gpt work."

## Reviewer mission

Reviewers are framed as helping the authors make this the best paper it can be in its subfield, **not** gatekeeping for a specific journal. Every Major/Minor comment must include:
1. A quoted passage or pinpoint location (line / equation / table / figure label).
2. The issue and why it matters.
3. A concrete fix (replacement sentence, analysis to add, reference to cite, calculation to perform).

Comment counts are capped (5 Major, 10 Minor) to force ranking. Reviewers also include "What the paper does well" and "Suggestions to enhance" sections so the output is constructive, not just adversarial. Reviewers are told to reserve Major comments and a "revision" verdict for issues that genuinely block correctness or clear communication, and to vote `accept` once no blocking issue remains rather than withholding it for taste-level polish — this is what lets the loop converge instead of churning "minor revision" forever. Each review also reports a plain-text `MAJOR COUNT: N` line.

From round 2 onward, each reviewer reads their own prior review and tracks Resolved / Partially / Unresolved before writing new comments.

## Source verification policy

The loop's central failure mode: reviewers and the revisor see only the manuscript, never the papers it cites. When a manuscript restates a result from a cited work, a reviewer reasoning from memory can "correct" a claim that was actually right under an assumption the manuscript did not repeat — and the revisor then applies the wrong fix. The loop has no ground-truth gate, so it can turn a true statement false.

Two defenses, both prompt-level:

1. **Source-dependent-claim rule.** When a passage restates a theorem, definition, dataset value, or number from a cited work, a reviewer may not assert it is wrong or demand a substantive rewrite from their own reconstruction. They must either verify it (web search, or the source pack) or route it to a `# Source-dependent flags` section. The revisor never acts on that section — it is for a human.

2. **Optional source pack** (`--sources`). A comma-separated list of files/directories holding the primary papers/data. When given, reviewers and the revisor read and verify summary claims against them. Most useful when the manuscript summarizes unpublished working papers that web search cannot reach.

Reviewers also have `WebSearch` / `WebFetch` with a tiered, soft-enforced budget:

| Round | Budget | Purpose |
|---|---|---|
| 1 | 8 queries | Discovery + verification (subfield context, citation checks, prior-art, adjacent literature). |
| 2 | 3 queries | Verify changes only — new content the authors added/changed. New Majors may not be motivated by literature first discovered this round. |
| 3+ | 1 query | Verify the most contested change. |

Reviewers prefer academic sources (arXiv, journal sites, Google Scholar, university pages).

## How to invoke

The user types `/critic-revisor <manuscript.tex> [max_rounds] [venue] [--sources <paths>]`. Steps:

1. **Resolve the manuscript path.** If the user gave a relative path, make it absolute. Quote it if it contains spaces, parentheses, or other shell-special characters.
2. **Verify prerequisites** with one Bash call:
   ```sh
   test -f "<path>" && which codex latexmk latexdiff claude
   ```
   If any are missing, tell the user and stop.
3. **Offer a source pack.** If the manuscript cites or summarizes papers/data the user has on disk (especially unpublished working papers), pass their paths via `--sources` so reviewers can verify summary claims instead of reconstructing them. If the user mentioned source folders earlier, use them; otherwise it is reasonable to ask.
4. **Launch the script** in the foreground via the Bash tool with a long timeout (~600000ms = 10 min). For `max_rounds > 2` or large manuscripts, run in the background and check back when it finishes:
   ```sh
   bash ~/.claude/skills/critic-revisor/run_loop.sh "<manuscript.tex>" <max_rounds> [venue] [--sources <paths>]
   ```
   `venue` and `--sources` are OPTIONAL — pass each only if the user supplied it. Do not invent a default. When `venue` is omitted, reviewers infer the subfield from the paper itself.
5. **After the loop returns**, summarize:
   - Rounds run.
   - Final verdict (including `converged (no Major comments)` if the loop stopped on the convergence rule).
   - Path to `critic_revisor_logs/` (per-round subfolders).
   - Path to the cumulative tracked-changes PDF (`<basename>_diff.pdf` next to the manuscript).
   - Any warnings the script emitted, and any `# Source-dependent flags` raised — those were NOT auto-applied and need a human (verify the flagged claims against the primary sources).

## Stop conditions (handled by the script)

The loop stops on the first of:
- Both reviewers end their review files with `VERDICT: accept` (conjunctive — one accept + one minor still triggers another round).
- Neither reviewer raises a Major comment in a round (`MAJOR COUNT: 0` from both). That round's Minor polish is applied and built first, then the loop stops — this is the convergence rule that prevents endless "minor revision" churn.
- Codex produces no `.tex` diff.
- `latexmk -pdf manuscript.tex` (the clean build) fails.
- `max_rounds` reached.

`latexdiff` failures are non-fatal — they just skip the tracked PDF for that round and continue.

## Outputs (under the manuscript's directory)

Each invocation creates a fresh `run_<timestamp>/` folder, so re-runs don't co-mingle. Each round folder contains both a clean and a color-tracked PDF for that round.

```
<basename>.tex / .pdf                              Live clean state (codex edits in place)
<basename>_diff.tex / _diff.pdf                    Cumulative tracked changes (latest run)
critic_revisor_logs/
└── run_<timestamp>/                                One folder per invocation
    ├── round_0/
    │   └── <basename>_clean.{tex,pdf}             State at run start
    ├── round_N/
    │   ├── <basename>_clean.{tex,pdf}             Post-round-N clean
    │   ├── <basename>_diff.{tex,pdf}              Tracked changes vs round_(N-1)
    │   ├── reviewer1_review.md                    Methodologist review
    │   ├── reviewer1_claude.{stdout,stderr}
    │   ├── reviewer2_review.md                    Applied/contextual review
    │   ├── reviewer2_claude.{stdout,stderr}
    │   ├── combined.md                            Concatenated input to Codex
    │   ├── codex.{stdout,stderr}
    │   ├── clean_latexmk.log
    │   ├── latexdiff.log
    │   └── diff_latexmk.log
    └── final/
        ├── <basename>_diff.{tex,pdf}              Cumulative tracked changes vs round_0
        ├── latexdiff.log
        └── diff_latexmk.log
```

The per-round `_clean` is the state after that round's revision. The per-round `_diff` shows what changed during that round (latexdiff vs the prior round's clean). The `final/` cumulative diff shows all changes across the full run.

## Cost / safety notes

- Two Opus reviews per round (with web search) + one Codex revision + up to three latexmk builds (clean, per-round diff, cumulative diff). Web search adds tool turns, so per-round cost is higher than the pre-search version. Default `max_rounds=5` is conservative; do not exceed 10 without watching.
- Each round writes to `critic_revisor_logs/run_<timestamp>/round_N/`; nothing is destructive to the original `.tex` (round_0 captures the run-start state, every round saves both a clean and tracked-changes copy).
- If the project is a git repo, each round auto-commits with message `critic-revisor round N`. Otherwise per-round snapshots provide undo.
- Codex runs with `--full-auto --skip-git-repo-check`, so it edits files without prompting and works outside git repos. Confirm the user is OK with this in their working directory before starting.
- Codex auth: relies on the user's pre-existing `codex login` (ChatGPT Pro plan). Script does NOT export `CODEX_API_KEY`.

## Operational hardening (lessons from earlier runs)

The script defends against three failure modes we have actually hit:

1. **latexmk infinite recursion.** Heavy latexdiff output occasionally triggers a pdflatex error that loops forever despite `-interaction=nonstopmode`. All three latexmk calls (clean PDF, per-round diff, cumulative diff) run under a 5-min wall-clock timeout via `latexmk_with_timeout`. If the limit is hit, the call returns failure and the loop continues. Tracked-changes failures are non-fatal; a clean-PDF timeout stops the loop with `latexmk (clean) failed`. If that happens on a large manuscript, increase the `300`-second value at the three call sites.
2. **Markdown-bolded VERDICT line.** Reviewers sometimes write `**VERDICT: minor revision**` instead of plain text. Detection regex tolerates leading whitespace, asterisks, and underscores. The reviewer prompt also asks for plain text explicitly, but the regex is the safety net.
3. **Codex websocket dropouts.** Transient `chatgpt.com/backend-api/codex/responses` disconnects can leave Codex producing no .tex diff. The loop logs a WARNING and exits with `codex produced no .tex diff`. Re-run the loop or invoke `codex exec --skip-git-repo-check --full-auto` manually with the existing `round_N/combined.md` to retry just the revision step.

## What to tell the user when you finish

A short paragraph: rounds run, final verdict, paths to the clean PDF / cumulative tracked PDF / log directory, and a one-line recommendation (submit / one more pass / inspect failure). Do not paste the full review body — it's on disk.
