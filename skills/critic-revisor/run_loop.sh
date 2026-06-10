#!/usr/bin/env bash
# critic-revisor — autonomous adversarial loop for LaTeX manuscripts.
# Opus reviews x2 (no edits, differentiated angles); Codex revises (no review);
# latexmk + latexdiff build. Per-invocation run folder; per-round folder
# contains both clean and color-tracked PDFs. Conjunctive accept rule.

set -uo pipefail

usage() {
  cat <<'EOF'
Usage: run_loop.sh <manuscript.tex> [max_rounds=5] [venue] [--sources <paths>]

Two parallel Opus reviews per round (reviewer 1 = methodologist,
reviewer 2 = applied/contextual reader); Codex revises; latexmk rebuilds
the clean PDF; latexdiff produces a color-tracked diff PDF. Stops on
(both reviewers accept) | (neither reviewer raises a Major comment) |
(codex produces no diff) | (clean latexmk fails) | (max_rounds).

`venue` is OPTIONAL. When provided, it is used as an expertise HINT
(e.g., "biometrics", "annals of statistics") to shape the reviewers'
domain background. It is NOT used as an acceptance bar — the reviewers'
goal is helping the authors make this the best paper it can be in its
subfield, not gatekeeping for a specific journal.

--sources is OPTIONAL: a comma-separated list of files or directories
holding the primary papers/data the manuscript cites or summarizes.
When given, reviewers and the revisor verify summary claims against
these sources rather than reconstructing them from memory.

Outputs are written under critic_revisor_logs/run_<timestamp>/, with
round_0 (run-start state), round_1..round_N (post-round clean + tracked
PDFs), and final/ (cumulative tracked PDF vs round_0).
EOF
  exit 2
}

SOURCE_SPEC=""
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --sources)
      SOURCE_SPEC="${2:-}"; shift
      [[ $# -gt 0 ]] && shift
      ;;
    --sources=*)
      SOURCE_SPEC="${1#--sources=}"; shift
      ;;
    *)
      POSITIONAL+=("$1"); shift
      ;;
  esac
done

MANUSCRIPT="${POSITIONAL[0]:-}"
[[ -z "$MANUSCRIPT" ]] && usage
[[ ! -f "$MANUSCRIPT" ]] && { echo "ERROR: manuscript not found: $MANUSCRIPT" >&2; exit 2; }

MAX_ROUNDS="${POSITIONAL[1]:-5}"
VENUE="${POSITIONAL[2]:-}"

# Resolve absolute path and switch to the manuscript's directory
MANUSCRIPT="$(cd "$(dirname "$MANUSCRIPT")" && pwd)/$(basename "$MANUSCRIPT")"
WORK_DIR="$(dirname "$MANUSCRIPT")"
MANU_FILE="$(basename "$MANUSCRIPT")"
MANU_BASE="${MANU_FILE%.tex}"
cd "$WORK_DIR" || exit 2

LOG_DIR="$WORK_DIR/critic_revisor_logs"
RUN_TS="$(date +%Y-%m-%dT%H-%M-%S)"
RUN_DIR="$LOG_DIR/run_${RUN_TS}"
mkdir -p "$RUN_DIR/round_0" "$RUN_DIR/final"
echo "[setup] run folder: $RUN_DIR"

# ---- Source pack -----------------------------------------------------------
# Optional primary papers/data the manuscript cites or summarizes. Reviewers
# and the revisor verify source-dependent claims against these rather than
# reconstructing them from memory.
SOURCE_FILES=""
if [[ -n "$SOURCE_SPEC" ]]; then
  IFS=',' read -ra _SPARTS <<< "$SOURCE_SPEC"
  for _sp in "${_SPARTS[@]}"; do
    _sp="$(echo "$_sp" | xargs 2>/dev/null)"
    [[ -z "$_sp" ]] && continue
    if [[ -d "$_sp" ]]; then
      _abs="$(cd "$_sp" && pwd)"
      while IFS= read -r _f; do
        [[ -n "$_f" ]] && SOURCE_FILES+="${_f}"$'\n'
      done < <(find "$_abs" -maxdepth 2 -type f \
                 \( -name '*.tex' -o -name '*.pdf' -o -name '*.md' -o -name '*.txt' \) 2>/dev/null)
    elif [[ -f "$_sp" ]]; then
      SOURCE_FILES+="$(cd "$(dirname "$_sp")" && pwd)/$(basename "$_sp")"$'\n'
    else
      echo "[setup] WARNING: source path not found, skipping: $_sp" >&2
    fi
  done
fi

if [[ -n "$SOURCE_FILES" ]]; then
  SOURCE_PACK_NOTE="SOURCE PACK. The primary sources below are provided so you can verify
claims the manuscript summarizes. When a passage restates a result, theorem,
definition, dataset value, or number from one of these, READ the source and
check it against the manuscript before commenting:
${SOURCE_FILES}"
  echo "[setup] source pack: $(printf '%s' "$SOURCE_FILES" | grep -c .) file(s)"
else
  SOURCE_PACK_NOTE=""
fi

# ---- Helpers ---------------------------------------------------------------

md5of() {
  if command -v md5 >/dev/null 2>&1; then
    md5 -q "$1"
  else
    md5sum "$1" | awk '{print $1}'
  fi
}

USE_GIT=0
if git -C "$WORK_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  USE_GIT=1
fi

# Run latexmk with a hard wall-clock timeout. Some pdflatex errors trigger
# infinite recursion that -interaction=nonstopmode does not stop; without a
# timeout the script can hang indefinitely.
latexmk_with_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout --kill-after=10 "$secs" latexmk "$@"
    return $?
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout --kill-after=10 "$secs" latexmk "$@"
    return $?
  fi
  latexmk "$@" &
  local pid=$!
  ( sleep "$secs"; kill -TERM "$pid" 2>/dev/null; sleep 10; kill -KILL "$pid" 2>/dev/null ) &
  local watch=$!
  wait "$pid"
  local rc=$?
  kill "$watch" 2>/dev/null
  return $rc
}

round_dir() { echo "$RUN_DIR/round_$1"; }

# Capture run-start state into round_0
{
  cp "$MANUSCRIPT" "$RUN_DIR/round_0/${MANU_BASE}_clean.tex"
  [[ -f "${MANU_BASE}.pdf" ]] && cp "${MANU_BASE}.pdf" "$RUN_DIR/round_0/${MANU_BASE}_clean.pdf" 2>/dev/null
} || true

# Build the clean PDF for the current manuscript (working dir).
build_clean() {
  local logpath="$1"
  echo "  [build] clean PDF (latexmk)..."
  if latexmk_with_timeout 300 -pdf -interaction=nonstopmode -halt-on-error "$MANU_FILE" \
       >"$logpath" 2>&1; then
    return 0
  fi
  echo "  WARNING: latexmk failed or timed out (see $logpath)"
  return 1
}

# Save the post-round clean state into round_N.
save_round_clean() {
  local round="$1"
  local rd
  rd="$(round_dir "$round")"
  cp "$MANUSCRIPT" "$rd/${MANU_BASE}_clean.tex"
  [[ -f "${MANU_BASE}.pdf" ]] && cp "${MANU_BASE}.pdf" "$rd/${MANU_BASE}_clean.pdf" 2>/dev/null || true
}

# Build the per-round tracked-changes PDF: latexdiff(prior round's clean,
# current manuscript), then latexmk. Non-fatal.
build_round_diff() {
  local round="$1"
  local rd prev_rd
  rd="$(round_dir "$round")"
  prev_rd="$(round_dir "$((round - 1))")"
  local prior_tex="$prev_rd/${MANU_BASE}_clean.tex"
  local diff_tex="$rd/${MANU_BASE}_diff.tex"

  if [[ ! -f "$prior_tex" ]]; then
    echo "  WARNING: prior-round clean .tex not found ($prior_tex); skipping per-round diff."
    return 1
  fi

  echo "  [build] color-tracked PDF (latexdiff round_$((round - 1)) → round_${round})..."
  if ! latexdiff "$prior_tex" "$MANUSCRIPT" >"$diff_tex" 2>"$rd/latexdiff.log"; then
    echo "  WARNING: latexdiff failed (see $rd/latexdiff.log)."
    return 1
  fi
  if ! latexmk_with_timeout 300 -pdf -interaction=nonstopmode "$diff_tex" \
       >"$rd/diff_latexmk.log" 2>&1; then
    echo "  WARNING: tracked-changes PDF failed or timed out (see $rd/diff_latexmk.log)."
    return 1
  fi
  return 0
}

# Cumulative tracked changes vs round_0 (this run's baseline). Writes to
# both run/final/ and the working directory (for muscle memory).
build_cumulative_diff() {
  local round0_tex="$RUN_DIR/round_0/${MANU_BASE}_clean.tex"
  local final_diff_tex="$RUN_DIR/final/${MANU_BASE}_diff.tex"
  local working_diff_tex="$WORK_DIR/${MANU_BASE}_diff.tex"

  echo
  echo "[final] cumulative track-changes vs round_0..."
  if [[ ! -f "$round0_tex" ]]; then
    echo "  WARNING: round_0 baseline missing; cannot build cumulative diff."
    return 1
  fi
  if ! latexdiff "$round0_tex" "$MANUSCRIPT" >"$final_diff_tex" 2>"$RUN_DIR/final/latexdiff.log"; then
    echo "  WARNING: cumulative latexdiff failed (see $RUN_DIR/final/latexdiff.log)."
    return 1
  fi
  if ! latexmk_with_timeout 300 -pdf -interaction=nonstopmode "$final_diff_tex" \
       >"$RUN_DIR/final/diff_latexmk.log" 2>&1; then
    echo "  WARNING: cumulative tracked-changes PDF failed or timed out."
    return 1
  fi
  cp "$final_diff_tex" "$working_diff_tex" 2>/dev/null || true
  [[ -f "${final_diff_tex%.tex}.pdf" ]] && cp "${final_diff_tex%.tex}.pdf" "${working_diff_tex%.tex}.pdf" 2>/dev/null || true
  echo "  produced: ${final_diff_tex%.tex}.pdf"
  return 0
}

# ---- Prompts ---------------------------------------------------------------

review_prompt() {
  local round="$1"
  local reviewer="$2"
  local other_reviewer persona_self persona_other angle
  if [[ "$reviewer" == "1" ]]; then
    other_reviewer=2
    persona_self="the methodologist"
    persona_other="the applied/contextual reader"
    angle="Focus on TECHNICAL CORRECTNESS: math, statistics, identifiability, asymptotic claims, simulation design, code-table consistency, proofs and lemmas. Spot mathematical gaps, mis-cited results, unstated assumptions, and overclaims. When you cite outside literature, prefer methodological/theoretical sources."
  else
    other_reviewer=1
    persona_self="the applied/contextual reader"
    persona_other="the methodologist"
    angle="Focus on FRAMING, POSITIONING, AND IMPACT: literature positioning (including ADJACENT fields), motivating example fit, generalizability, reproducibility, what a practitioner would actually do with this. Spot missing comparators, missing references the authors should know about, and unclear framing of the contribution."
  fi
  local rd
  rd="$(round_dir "$round")"
  local out_file="$rd/reviewer${reviewer}_review.md"
  mkdir -p "$rd"

  local search_budget search_purpose
  case "$round" in
    1) search_budget=8
       search_purpose="DISCOVERY + VERIFICATION. Identify subfield context, verify cited references, check whether claimed novelty has prior art, surface adjacent literature the authors may have missed."
       ;;
    2) search_budget=3
       search_purpose="VERIFY CHANGES ONLY. Verify NEW content (claims, citations, results) the authors added or changed since the prior round. New Major comments may NOT be motivated by literature you discover for the first time this round — they must be motivated by gaps in the revised text."
       ;;
    *) search_budget=1
       search_purpose="MINIMAL. At most one search, used only to verify the most contested change."
       ;;
  esac

  local venue_hint=""
  if [[ -n "$VENUE" ]]; then
    venue_hint="The authors are aiming this at *${VENUE}*. Use that ONLY as a hint about the field and readership — bring expert knowledge of that area. Do NOT use it as a checklist of journal-specific style or acceptance standards. The goal is helping the authors, not matching a venue's bar."
  fi

  local prior_round_rule resolution_section=""
  if [[ "$round" == "1" ]]; then
    prior_round_rule="Do NOT read prior-round review files (none exist)."
  else
    local prev=$((round - 1))
    prior_round_rule="READ the previous round's review at $RUN_DIR/round_${prev}/reviewer${reviewer}_review.md FIRST. For each Major comment from that review, mark it Resolved / Partially / Unresolved at the top of your new review (under \"# Resolution check\") before writing new comments."
    resolution_section="
# Resolution check
For each Major from your prior review (round $((round - 1))), one bullet: Resolved / Partially / Unresolved + a one-line justification quoting the relevant new text.
"
  fi

  cat <<EOF
You are reviewer ${reviewer} of two reading this manuscript independently in round ${round} of an autonomous review loop. The two reviews are differentiated on purpose: you are ${persona_self}; reviewer ${other_reviewer} is ${persona_other}.

YOUR GOAL is to HELP THE AUTHORS make this the best paper it can be in its subfield. Critique only when it serves enhancement. The output should be useful and constructive, not adversarial for its own sake.

Read the manuscript at:
${MANUSCRIPT}

${venue_hint}

${SOURCE_PACK_NOTE}

How to do the work (in order):
1. Read the whole manuscript first. Identify the subfield, the actual contribution, and the claims it rests on.
2. Put on the expert hat for that subfield. If you are uncertain about prior art or a technical claim, you MAY use web search.
   - Budget this round: ${search_budget} queries.
   - Purpose this round: ${search_purpose}
   - Prefer academic sources (arXiv, journal sites, Google Scholar, university and society pages); avoid news, marketing, and tutorial-level pages.
   - Do NOT use search to learn the subject from scratch — bring expertise you already have, or admit uncertainty.
3. Verify source-dependent claims. When the manuscript restates a theorem, result, definition, dataset value, or number from a CITED work or external source, do NOT treat your own reconstruction as the ground truth — the cited work may rely on assumptions the manuscript did not repeat. If the cited work is public, web-search to verify it (within budget). If a source pack is listed above, read the relevant source and check the claim against it. If you can neither find nor verify the source, you may NOT assert the claim is wrong or demand a rewrite that changes its substance — route it to "# Source-dependent flags" (see structure below) instead. A confident, well-argued critique of a source-dependent claim you could not verify is exactly how this loop introduces errors; when in doubt, flag rather than rewrite.
4. Spot real mistakes (math, statistics, code-table consistency, mis-cited results, overclaims) and real omissions (missing comparator, missing reference, unstated assumption).
5. For every issue, propose the constructive fix: a sentence the authors should write instead, an analysis they should add, a reference they should cite, or a calculation they should perform.

Reviewer ${reviewer} angle: ${angle}

Write a focused, honest review and save it to:
${out_file}

Required structure:

# Summary
One paragraph: what is the paper, what is the contribution, who is it for.

# What the paper does well
2–4 bullets. Specific, not flattering.
${resolution_section}
# Major comments (cap: 5)
Numbered. Each comment MUST include:
  - QUOTE: the passage or pinpoint location (line / equation / table / figure label).
  - ISSUE: what is wrong or missing, and why it matters.
  - FIX: a replacement sentence, an analysis to add, a reference to cite, or a calculation to perform.

# Minor comments (cap: 10)
Numbered, specific, actionable. Same QUOTE / ISSUE / FIX discipline.

# Suggestions to enhance the paper
Forward-looking ideas the authors may not have considered: a robustness check, a connection to adjacent literature, a generalization, a clearer framing. Gifts, not required fixes.

# Source-dependent flags
Claims that restate or depend on a cited work or external source you could NOT verify (not public, not in any source pack). For each: the passage, what to check, and against which source. May be empty. The revisor does NOT act on this section — it is routed to a human. Do not duplicate these as Major or Minor comments.

# Verdict
One paragraph reconciling what is strong and what is weak. Reserve Major comments and a "major/minor revision" verdict for issues that genuinely block the paper from being correct or clearly communicated. Once no such blocking issue remains, your verdict should be "accept" even if you still list optional Minor polish or Suggestions — withholding acceptance for taste-level items only keeps the loop running with no benefit.

Then on a NEW line by itself, write your verdict in PLAIN TEXT (no markdown asterisks, no italics, no bold) — exactly one of:
VERDICT: accept
VERDICT: minor revision
VERDICT: major revision
VERDICT: reject

On the NEXT line, also in plain text, report how many Major comments you raised:
MAJOR COUNT: <integer 0-5>

Hard rules:
- DO NOT edit the manuscript.
- DO NOT read the other reviewer's file ($rd/reviewer${other_reviewer}_review.md). Form your judgment independently.
- ${prior_round_rule}
- Cite real, verifiable references only — author, year, title, venue. No fabricated citations.
- If a slot can't be filled with something genuinely actionable, leave it empty rather than padding.
- Stay within your web-search budget (${search_budget}). Going over is a process violation.
- A source-dependent claim you could not verify goes under "# Source-dependent flags" — never into Major or Minor comments.
- After your structured Verdict paragraph, set the rubric aside and add one final sentence stating "what bothered me most about this paper" — your gut, in your own voice.
EOF
}

revise_prompt() {
  local round="$1"
  local combined
  combined="$(round_dir "$round")/combined.md"
  cat <<EOF
You are a manuscript revisor working autonomously in round ${round} of a critic-revisor loop. Two independent reviews of the manuscript at:
${MANUSCRIPT}
have been combined into:
${combined}

Apply every actionable Major and Minor comment from BOTH reviewers to ${MANUSCRIPT}. Treat "Suggestions to enhance" as optional — apply only those that are clearly improvements at low cost.

${SOURCE_PACK_NOTE}

Hard rules:
- Never apply anything under a reviewer's "# Source-dependent flags" heading — those are routed to a human; leave that text unchanged.
- If a Major or Minor comment would change the substance of a claim the manuscript attributes to a citation or external source: verify it against the source pack above if one is listed, and apply the change only if the source supports it; if no source is available, make only the smallest wording fix and do NOT invert or alter the claim's substance.
- Make the smallest edit that addresses each comment. Do not restructure unless the reviews demand it.
- Preserve all LaTeX commands, citations, figure references, equation labels.
- Ignore the "VERDICT:" lines and any "Resolution check" section — they are for the loop controller, not for you.
- Do NOT compile or run latexmk. The loop controller handles builds.
- Do NOT add commentary, todo notes, or response-letter material to the .tex file — just edit the manuscript.
- If a reviewer asks for new content, add it; if they ask for deletion, delete it; if they ask for clarification, clarify.
- Edit ${MANUSCRIPT} in place. Do not create a new file.
EOF
}

# ---- Main loop -------------------------------------------------------------

ROUND_RAN=0
EXIT_REASON=""
FINAL_VERDICT=""

REVIEWER_TOOLS="Read,Write,Glob,Grep,WebSearch,WebFetch"

for r in $(seq 1 "$MAX_ROUNDS"); do
  ROUND_RAN=$r
  RD="$(round_dir "$r")"
  mkdir -p "$RD"

  echo
  echo "=== Round $r/$MAX_ROUNDS ==="

  R1_FILE="$RD/reviewer1_review.md"
  R2_FILE="$RD/reviewer2_review.md"
  rm -f "$R1_FILE" "$R2_FILE"

  echo "  [opus x2] reviewing in parallel (R1=methodologist, R2=applied)..."
  PROMPT_R1="$(review_prompt "$r" 1)"
  PROMPT_R2="$(review_prompt "$r" 2)"

  claude -p "$PROMPT_R1" \
    --permission-mode acceptEdits \
    --allowed-tools "$REVIEWER_TOOLS" \
    >"$RD/reviewer1_claude.stdout" \
    2>"$RD/reviewer1_claude.stderr" &
  R1_PID=$!

  claude -p "$PROMPT_R2" \
    --permission-mode acceptEdits \
    --allowed-tools "$REVIEWER_TOOLS" \
    >"$RD/reviewer2_claude.stdout" \
    2>"$RD/reviewer2_claude.stderr" &
  R2_PID=$!

  wait $R1_PID || echo "  WARNING: reviewer 1 exited non-zero"
  wait $R2_PID || echo "  WARNING: reviewer 2 exited non-zero"

  if [[ ! -f "$R1_FILE" || ! -f "$R2_FILE" ]]; then
    EXIT_REASON="reviews missing (see *_claude.stderr logs)"
    echo "  ERROR: $EXIT_REASON"
    break
  fi

  # Tolerate markdown bold/italic around the VERDICT line.
  V1=$(grep -iE "^[[:space:]]*[*_]*VERDICT:" "$R1_FILE" | tail -1 || echo "VERDICT: <not found>")
  V2=$(grep -iE "^[[:space:]]*[*_]*VERDICT:" "$R2_FILE" | tail -1 || echo "VERDICT: <not found>")
  echo "  reviewer 1 (methodologist):  $V1"
  echo "  reviewer 2 (applied/contextual): $V2"

  # Major-comment counts drive the convergence stop. Absent line => treat high.
  M1=$(grep -iE "^[[:space:]]*[*_]*MAJOR COUNT:" "$R1_FILE" | tail -1 | grep -oE "[0-9]+" | tail -1)
  M2=$(grep -iE "^[[:space:]]*[*_]*MAJOR COUNT:" "$R2_FILE" | tail -1 | grep -oE "[0-9]+" | tail -1)
  M1="${M1:-99}"; M2="${M2:-99}"

  if echo "$V1" | grep -qi "accept" && echo "$V2" | grep -qi "accept"; then
    FINAL_VERDICT="ACCEPTED"
    EXIT_REASON="both reviewers accept"
    echo "  >>> ACCEPTED at round $r."
    break
  fi

  COMBINED="$RD/combined.md"
  {
    echo "# Combined reviews — round $r"
    echo
    echo "## Reviewer 1 (methodologist)"
    echo
    cat "$R1_FILE"
    echo
    echo
    echo "---"
    echo
    echo "## Reviewer 2 (applied/contextual)"
    echo
    cat "$R2_FILE"
  } > "$COMBINED"

  echo "  [codex] revising..."
  PRE_MD5=$(md5of "$MANUSCRIPT")
  REVISE_PROMPT_TEXT="$(revise_prompt "$r")"
  if ! codex exec --full-auto --skip-git-repo-check "$REVISE_PROMPT_TEXT" \
       >"$RD/codex.stdout" 2>"$RD/codex.stderr"; then
    echo "  WARNING: codex exit non-zero (see $RD/codex.stderr)"
  fi
  POST_MD5=$(md5of "$MANUSCRIPT")

  if [[ "$PRE_MD5" == "$POST_MD5" ]]; then
    EXIT_REASON="codex produced no .tex diff"
    echo "  WARNING: $EXIT_REASON. Stopping."
    break
  fi

  if ! build_clean "$RD/clean_latexmk.log"; then
    EXIT_REASON="latexmk (clean) failed"
    break
  fi

  save_round_clean "$r"
  build_round_diff "$r"  # non-fatal

  if [[ $USE_GIT -eq 1 ]]; then
    git -C "$WORK_DIR" add -A 2>/dev/null
    git -C "$WORK_DIR" commit -m "critic-revisor round $r" --quiet 2>/dev/null || true
  fi

  # Convergence: neither reviewer raised a Major comment this round. The
  # round's Minor polish has been applied and built above; stop here rather
  # than churning further rounds of taste-level edits.
  if [[ "$M1" -eq 0 && "$M2" -eq 0 ]]; then
    FINAL_VERDICT="converged (no Major comments)"
    EXIT_REASON="no Major comments from either reviewer (round $r minor polish applied)"
    echo "  >>> CONVERGED at round $r — no Major comments remain."
    break
  fi
done

# ---- Post-loop --------------------------------------------------------------

build_cumulative_diff || true

echo
echo "============================================================"
echo "critic-revisor loop complete"
echo "  Manuscript:    $MANUSCRIPT"
echo "  Venue hint:    ${VENUE:-<none>}"
echo "  Source pack:   ${SOURCE_SPEC:-<none>}"
echo "  Rounds run:    $ROUND_RAN / $MAX_ROUNDS"
echo "  Stop reason:   ${EXIT_REASON:-max_rounds reached}"
echo "  Verdict:       ${FINAL_VERDICT:-not accepted (see latest reviews)}"
echo "  Run dir:       $RUN_DIR"
echo "  Clean PDF:     ${WORK_DIR}/${MANU_BASE}.pdf"
[[ -f "${WORK_DIR}/${MANU_BASE}_diff.pdf" ]] && \
  echo "  Cumulative tracked PDF: ${WORK_DIR}/${MANU_BASE}_diff.pdf"
echo "============================================================"
