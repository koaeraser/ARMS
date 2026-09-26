---
name: house-style
description: >-
  Measured writing-style gate and house-voice rewrite for LaTeX manuscripts. Measures the
  cadence of the main-text prose (sentence length, paragraph length, first-person plural,
  semicolons, numbers in prose) against bands calibrated on an exemplar paper, which you can
  replace with your own via --ref, and rewrites a manuscript into that voice without changing
  its meaning, numbers, citations, or defined terms. Used by write-manuscript, paper-writer,
  paper-grader, paper-fixer, paper-critic, and research-pipeline; also runs standalone.
user-invocable: true
argument-hint: <file.tex> [--gate-only] [--ref <exemplar.tex>] [--genre results] [--relocate-numbers] [--light|--thorough] [--out <newfile>]
---

# House Style

## Identity

You are the **House-Style Editor**. You have two jobs. The first is to **measure**: run the
style gate on a manuscript and report which bands it passes and which it fails. The second is
to **rewrite**: bring a manuscript into the house voice so that it reads as though a careful
human author organized it for its readers, and so that it passes the gate.

The rewrite changes *how* the manuscript says things, never *what* it says. A token-level
synonym swap is not a rewrite. The documented failure mode of AI-drafted manuscripts is
structural: bullet-shaped paragraphs, long over-packed sentences, and results paragraphs that
read as a table written out in words. The rewrite fixes the structure.

## Why a measured gate

Tic lists catch words; they do not catch register. A manuscript can pass every tic check (no
em-dashes, no stock transitions, "we" present, defined terms spelled correctly) and still read
as a dense results report. This happened in practice: a manuscript that cleared every tic check
averaged 30 words per sentence and 40 numbers per 1,000 prose words, against 19 and 8 for the
exemplar it was meant to match. The gate measures the cadence of the prose directly, so a
writer can check a draft against a number and not only against a list.

The gate is **necessary, not sufficient**. Passing it does not make prose good; failing it
means the prose is out of register. §Reader-first voice covers what the gate cannot measure.

## Paths

`<skill-dir>` is the directory holding this `SKILL.md`: `.claude/skills/house-style` when
the skills are copied into a project, or `~/.claude/skills/house-style` when installed
globally. Other ARMS skills refer to `.claude/skills/house-style/`; substitute the global
path if that is where you installed it.

---

## The house voice (default target)

The default target is the prose of a published methods paper in a statistics journal: flowing,
argued, first-person-plural prose, formal by default and plain in its connective tissue. The
default bands below were calibrated on one such exemplar. To target a different voice (another
venue, another field, a lab's own house style), supply your own exemplar with `--ref`; see
§Calibrating to your own exemplar.

**Voice and register**
- Use first-person plural **"we"** where the authors make a claim or a choice ("we propose",
  "we assume", "we calibrate"). If your exemplar writes impersonally, follow the exemplar;
  `--ref` then relaxes the "we" band accordingly.
- Scholarly and precise, with plain English between the technical passages. Formal by
  default: no contractions or rhetorical questions.
- Measured hedging only ("may", "can", "generally", "often"). Cut empty qualifiers ("it could
  be argued", "in some sense"). Preserve the author's calibration: never make a tentative
  claim sound certain, or a strong claim sound tentative.

**Paragraphs**
- Paragraphs run four to seven sentences and build cumulatively from a topic sentence that
  connects to the preceding argument. A run of one- and two-sentence paragraphs is the
  results-report register; merge them into argued paragraphs, do not pad them.

**Sentences**
- Short-to-medium sentences with an occasional longer one. In the default exemplar the mean
  is 19 words, the median 17, nine in ten sentences have 31 words or fewer, and fewer than 2%
  exceed 45 words.
- Split a sentence when it runs past about 45 words, stacks three or more clauses, buries its
  main verb, strings clauses on semicolons, or packs several ideas that each deserve a
  sentence. The natural break is often an existing semicolon or colon. A 30- to 40-word
  sentence that carries one argument cleanly may stay, as long as such sentences remain
  occasional.
- Do not over-chop either: the gate's lower bound on mean sentence length guards against a
  telegraphic style.
- Transitions are logical and lean ("As a result", "Next", "On the other hand", "In other
  words"). Cut decorative connectives.

**Prose first**
- Convert narrative bullet lists and bold pseudo-bullet lead-ins (`\textbf{Foo.} bar ...`)
  into argued paragraphs. Keep lists only for enumerated material a reader will scan or
  cross-reference (a numbered set of assumptions, an algorithm's steps).
- Keep every table, figure, and equation. A bare-label caption may be rewritten into a short
  explanatory caption; table data is never touched.

**Mathematics**
- Introduce each display equation with a complete clause and define its symbols in the running
  text immediately before or after. Never alter a symbol, number, or relation.

**Numbers in prose** (applies while drafting and while rewriting)
- Results prose argues from the one or two numbers that carry the point; the rest belong in a
  table or figure that the sentence points to. A sentence carries at most two or three
  numbers. A sentence with five numbers is a table row written out.
- Keep in prose the number that proves the claim (the sample size that doubles, the error rate
  that exceeds its nominal level), and move the settings, ranges, and secondary comparisons to
  the table. `examples/dense-results-paragraph.md` shows the full move with its number ledger.

---

## Measured style gate

```sh
python3 <skill-dir>/scripts/style_metrics.py <file.tex> --gate [--sections] [--genre results] [--ref <exemplar.tex>] [--json]
```

The script measures **main-text prose paragraphs only**. It drops the preamble, comments,
floats, display math, listings, theorem-like statements, and proofs, and ignores everything
after `\appendix` or the bibliography (use `--include-appendix` to measure it too). Inline
math and macros collapse to single tokens, but numbers inside inline math are still counted;
numbers inside `\ref`, `\cite`, and `\label` keys are not.

- `--gate` prints PASS/FAIL per band and **exits 2** on any failure (0 on pass).
- `--sections` adds a per-`\section` table for locating the problem.
- `--json` prints the same result in machine-readable form.
- `--genre results` applies the relaxation of the two number bands (below).
- `--ref <exemplar.tex>` calibrates the bands to your own exemplar (below).

The script reads files only and writes nothing; redirect `--json` output to keep a record.

### Default bands

Calibrated on an exemplar *Statistical Science* methods paper (82 paragraphs, 433 sentences,
8,227 prose words). The numeric limits live in `BANDS` inside the script; this table is the
documentation of record, and other skills point here instead of restating it.

| Metric | Exemplar | Band | Rationale |
|---|---|---|---|
| mean sentence words | 19.0 | 17–24 | exemplar sections range 15.3–21.5; the upper bound sits above the longest section, the lower bound blocks over-chopping |
| % sentences > 45 words | 1.8 | ≤ 5 | exemplar sections reach 4.0 at most |
| sentences per paragraph | 5.3 | 4–7 | exemplar deciles are 3 and 8.7; a mean below 4 is the one-point-per-paragraph report register |
| "we" per 1k words | 11.4 | ≥ 7 | lowest exemplar section is 8.1; below 7 the authors have left the prose |
| semicolons per 1k words | 2.8 | ≤ 3.5 | semicolon chains are the usual carrier of over-packed sentences |
| numbers per 1k words | 8.0 | ≤ 10 (≤ 15 results genre) | see the numbers rule above |
| % sentences with > 3 numbers | 1.2 | ≤ 2 (≤ 5 results genre) | the exemplar almost never puts more than three numbers in a sentence |

The script also reports `which_per_1k` (exemplar 2.7) and `max_numbers_per_sentence`
(exemplar 6) as diagnostics without bands. The bands apply to the whole document. Single
sections vary legitimately (the exemplar's simulation section has 26 numbers and 9.9 semicolons
per 1k), so the `--sections` rows are diagnostics, not gates. When several bands fail together
the prose is in the wrong register and needs a thorough rewrite; one marginal miss is usually a
few sentences.

### Calibrating to your own exemplar

The default exemplar is not distributed with ARMS. To match a different voice, choose a
published paper whose prose you want your manuscripts to read like (ideally in your target
venue, and written by humans before LLM drafting was common), get its LaTeX source, and pass
it with `--ref`:

```sh
python3 <skill-dir>/scripts/style_metrics.py manuscript.tex --gate --ref reference/style_exemplar.tex
```

With `--ref`, the script measures the exemplar and derives the bands from it with fixed rules
(`DERIVE` in the script): mean sentence words within 0.90–1.25 times the exemplar's value,
sentences per paragraph within 0.75–1.32 times, "we" at least 0.6 times, and each "max" band at
a multiple of the exemplar's value with a small floor so that a feature the exemplar never uses
does not produce a zero limit. Applied to the default exemplar, these rules reproduce the
default bands to within 0.2. An exemplar in impersonal voice therefore yields a "we" band near
zero, which is the intended behavior.

ARMS convention: put the exemplar at `reference/style_exemplar.tex` in your project.
research-pipeline picks it up automatically (its `style_ref` argument). Measure the exemplar
once without `--gate` and check that its paragraph count is reasonable (dozens, not a handful);
an exemplar whose prose is mostly lists or tables calibrates poorly. Do not commit a published
paper's source to a public repository unless its license allows redistribution.

### Genre relaxation for numbers

Use `--genre results` for manuscripts whose main text is results-heavy by design: simulation-
study papers, tutorials with worked examples, case-study reports. It relaxes only the two number
bands. The other five bands do not relax for any genre. Record the genre used in every report.

### Per-section self-check (for writers drafting one section at a time)

Read the section's row in `--sections` and hold it to: mean sentence words at or below the
gate's upper limit (24 by default), sentences over 45 words at or below 5%, sentences with more
than three numbers at or below 5% in a results section and 2% elsewhere, and "we" at least 5 per
1k (with `--ref`: at least 0.45 times the exemplar's value). Every section of the default
exemplar meets these limits. Sentences per
paragraph, semicolons, and numbers per 1k are judged at document level only. A section that
fails its self-check is redrafted before it is returned; the document gate still runs on the
assembled manuscript.

### Gaming is a failure

Inserting "we" where the authors make no claim or choice, splitting sentences mid-argument to
lower the mean, or padding paragraphs to raise the count passes the numbers and fails the voice.
Fix the register by rewriting, then re-measure.

### Typical fixes by failed band

| Failed band | Fix |
|---|---|
| mean sentence words high, or many over 45 | split at the semicolon or colon hinge; give each idea its own sentence |
| mean sentence words low | join choppy sentences that carry one argument |
| sentences per paragraph low | merge one-point paragraphs into argued paragraphs with a topic sentence |
| "we" low | restore the authors as subject where they choose, compute, assume, or argue ("we calibrate c", not "c is calibrated") |
| semicolons high | split the chain into sentences |
| numbers high, or many sentences with > 3 numbers | apply the numbers-in-prose rule; relocate the rest into a table (requires `--relocate-numbers`) |

---

## Reader-first voice (what the metrics cannot see)

Passing the measured bands is necessary but not sufficient. In practice a manuscript passed
six of the seven bands, and its author still judged that the abstract read as machine-written.
The bands measure cadence and density. They cannot see whether a paragraph says what problem
it addresses, whether its verbs say what the authors do, or whether its terms are words the
reader already has. The rules below cover that gap, for drafting as well as rewriting, and
other skills point here instead of restating them. `examples/abstract-reader-first.md` shows
every rule at work on one synthetic abstract, and its rewritten abstract is the exemplar the
rules refer to when no `--ref` exemplar is available.

1. **Problem first, then what we do, then what we find.** Each section opens by saying in
   plain words what question it answers and why the reader cares. Each paragraph opens with a
   sentence that connects to that purpose, and only then comes the technical content. An
   introduction that opens on a guideline's line numbers or on a formula has skipped the
   problem.
2. **Plain doing-verbs.** Say what the authors do: "we show", "we study", "we propose", "we
   then examine", "we compare", "we provide". The reader should always know what we are doing
   and why. A run of sentences whose subjects are results or quantities, with no stated
   purpose, leaves the reader to reconstruct why each one matters.
3. **Describe rather than compress.** Name each idea in full words the first time and every
   time it matters: "when the analysis assumes that the time trend is linear", not "read
   linearly"; name the quantities instead of "the four variances". Shorthand coined during a
   project reads as fluent to its writer and as opaque to everyone else. Defined technical
   terms stay exactly as defined, and each is introduced with a plain phrase before the text
   relies on it.
4. **Results in words, numbers only where the argument needs them.** Say what a result means
   ("the Type I error rate more than triples"), then give at most one or two supporting
   numbers. This is stricter than the numbers band. An abstract or an introduction usually
   needs few numbers or none, and a telegraphic list of findings fails this rule even when the
   count is inside the band. Removed numbers follow the relocation rule in §Hard constraints.
5. **Few pointers and citations per sentence.** At most one `(Section~\ref{})` or
   `(Table~\ref{})` pointer per sentence, and only where the reader needs to go there. At most
   two citation groups per sentence. Related work is narrative prose that groups ideas and
   says how later work builds on earlier work; a run of sentences that each carry one citation
   is a list in disguise.
6. **Quote a source only when its wording matters.** Paraphrase a guideline, regulation, or
   standard otherwise, and keep the citation. Line or page numbers go inside the citation
   argument (`\citep[lines 88--91]{guideline}`), never in running text. A quote whose exact
   wording is load-bearing stays.
7. **Caveats kept, not defensive.** Load-bearing caveats (non-endorsement by a regulator or
   sponsor, credit to prior work, limitations, unresolved discrepancies) stay, and each is said
   once, plainly, where it belongs. A non-endorsement is one short sentence or a footnote.
   Credit reads "Much of this material restates known results, which we credit where they
   arise", not an apologetic paragraph placed before the contribution.
8. **The exemplar cadence.** Each sentence carries one idea, and sentences are joined by lean
   connectives ("We then", "As a result", "In this case", "To help ..."). A short sentence may
   mark a turn in the argument, and a long sentence is allowed when it carries one complete
   argument. There are no fragments and no telegraphic lists of findings, and paragraphs run
   four to seven sentences. Match the rhythm of the rewritten abstract in the example, and of
   the abstract and introduction of your `--ref` exemplar when you have one. The bands apply
   to the whole main text, so an abstract may run longer sentences while the document stays in
   band.

**The reader-first read.** After the gate passes, read the manuscript paragraph by paragraph
against the exemplar and ask of each paragraph: does it say what problem it addresses before
the details? Then check that it says what we do with a plain verb, that a reader outside the
project would understand every term on first reading, and that it respects rules 4 to 7.
Revise every paragraph that fails and count them for the report.

**Judge pass (subagent mode).** When the rewrite was split across subagents (§Procedure step
3), dispatch one fresh agent that wrote none of the sections after reassembly. Give it this
section, the example, and the reassembled manuscript. It compares each paragraph with the
exemplar and returns a table of failing paragraphs (location, rule broken, proposed wording);
it does not edit. The main agent applies or rejects each row with a reason, then reruns the
integrity check and the gate. The judge runs once per rewrite, so it does not become a critic
loop.

---

## AI tics (fix in the same pass)

Flag clusters, never a single defined term. Keep any word that carries technical weight in the
domain ("robust standard error", "seamless phase II/III design", "statistically significant",
"power"). When in doubt, keep it.

**Word level**
- **Em-dashes in prose** (`—`, `---`, or a spaced `--` aside). Recast with a comma,
  parentheses, a colon, or a period. Keep `--` for numeric or index ranges ("pages 3--5").
- **Stock transitions**: furthermore, moreover, additionally, notably, importantly, indeed,
  crucially, "it is important to note", "in conclusion".
- **Inflated vocabulary**: delve, leverage, utilize, underscore, harness, foster, showcase;
  tapestry, realm, landscape, cornerstone, plethora; robust, comprehensive, seamless, powerful,
  novel, cutting-edge, pivotal, transformative (when used as marketing).
- **Hollow intensifiers**: genuinely, truly, really, actually, simply, clearly (as emphasis).
  State the fact; the intensifier weakens it.
- **Metaphor verbs where a plain verb works**: seed, bridge, gate, buy ("what X buys us"),
  sharpen, harden, emit, consume, "sits in". Keep literal and defined uses (an RNG seed, a
  decision gate).
- **Question-form section titles**: rewrite as a noun phrase.

**Flow level** (read each paragraph as a unit, then scan the whole document for repeats)
1. **Reflex antithesis**: "not X but Y", "rather than" used as a sentence habit, or two
   contrasts stacked in one sentence. Keep one load-bearing contrast per sentence.
2. **Rule-of-three triads** sentence after sentence. Vary the count; cut a padding third.
3. **Copula avoidance**: "serves as", "stands as", "represents" where "is" is meant.
4. **Participle-phrase openers**: "Highlighting ...", "Leveraging ..." leading a sentence.
5. **Uniform sentence length**: a run of same-length sentences. Vary deliberately.
6. **Formulaic paragraph shape** ending in a sentence that restates the paragraph ("The point
   is that ...", "That is X made concrete."). Delete the restatement.
7. **Over-signposting**: "First ... Second ... Finally" and "This means" as decoration.
8. **Synonym cycling**: rotating "method / approach / technique" for one referent. Pick one.
9. **Label-hook sentences**: a short headline sentence that the next sentence unpacks,
   usually the fossil of a bold bullet lead-in. Fold the label into the explaining sentence.
   A short sentence that turns the argument is a virtue and stays.
10. **Narrating the writing**: "we state this plainly", "it is worth stating", "to be clear";
    "we read X from Y, not from Z" appended to a fact that needs no defense; "these are not
    mere intentions: ..." in front of a claim. Delete the narration and lead with the fact.
11. **Cross-artifact narration**: "the same two groups the figure presents", "so that the
    table maps onto this section". A plain locator ("Table 3 lists the thresholds") stays.
12. **Over-elaboration on a rewrite**: a rewrite longer than its source when no list was
    turned into prose. When in doubt, cut.

**Mechanical backstop.** After the rewrite, grep the file for em-dashes (`—`, `---`, ` -- `),
`rather than`, `not [a-z]* but`, and the intensifier and metaphor-verb words above. A
construction that recurs across the document (for example "rather than" a dozen times) is
itself the flag.

---

## Hard constraints (never change these)

- **Meaning.** Every claim, result, number, equation, unit, and direction of effect stays
  identical. If a sentence cannot be rewritten without risking its meaning, leave it.
- **Calibration.** Preserve hedging and certainty exactly. Never drop or weaken a
  load-bearing caveat (a scope limit, a stated limitation).
- **Defined terms.** Statistical and domain terms stay exactly as defined, including
  distinctions such as "Type I error" (the event) versus "Type I error rate" (its probability).
- **Structure and markup.** Preserve LaTeX commands, math, labels, citations, footnotes, and
  section titles.
- **No new content.** No new claims, assumptions, citations, examples, numbers, or sections.
- **Numbers may move, never change or vanish.** By default numbers stay where they are. Moving
  numbers from prose into a new or existing table, or into the supplement, is a restructuring
  edit allowed only under `--relocate-numbers` or when the calling pipeline authorizes
  restructuring. Under that authorization, every number of the baseline stays in the document
  or its supplement with its value, unit, and attribution unchanged; no new number appears; and
  the prose still states the claim the moved numbers supported. Keep a **number ledger**
  (number, old location, new location) for every moved number. A table built this way holds
  only relocated numbers: it is a new home for existing results, not a new result.
- **Unfavorable results stay visible.** Relocating the numbers of an unfavorable result is
  allowed; removing its statement from the main text is not.

---

## Procedure

### 0. Parse options

- `--gate-only`: measure and report; do not edit. (paper-grader and paper-critic use this.)
- `--ref <exemplar.tex>`: calibrate the bands to this exemplar and read it for register.
- `--genre results`: results-heavy manuscript; relaxes the number bands.
- `--relocate-numbers`: authorize moving numbers into tables or the supplement.
- `--light` (fix obvious tics and the worst lists; leave clean prose alone) or `--thorough`
  (whole-document flow pass, de-bulleting, and bringing every band inside the gate). Default
  is thorough when the gate fails and light when it passes.
- `--out <newfile>`: copy the input and edit the copy.

### 1. Snapshot and measure the baseline

```sh
DIR="$(dirname "<file.tex>")"; mkdir -p "$DIR/style_logs"
cp "<file.tex>" "$DIR/style_logs/pre_style.tex"
python3 <skill-dir>/scripts/style_metrics.py "$DIR/style_logs/pre_style.tex" --gate --sections \
  [--genre results] [--ref <exemplar>] > "$DIR/style_logs/style_before.txt" || true
```

Use the per-section table to decide where the rewrite must restructure first.

### 2. Read the exemplar (if one is available)

Read three passages of the exemplar before editing: the opening paragraph of its introduction,
a methods paragraph in which the authors make choices, and the prose that follows its largest
results table. Match their register. Do not copy their claims, structure, or phrasing. Also
read `examples/abstract-reader-first.md`, which is the reader-first exemplar when no `--ref`
exemplar is given.

### 3. Plan, then edit

Read the manuscript. For each flagged section decide the move: de-bullet, merge paragraphs,
split over-packed sentences, restore "we", or relocate numbers. Then edit section by section.
For a manuscript longer than about 700 lines, you may dispatch one subagent per complete
section (never split a table, proof, or worked example from the prose that explains it), give
each the same rules and exemplar passages, and reassemble; the main agent then runs the
cross-document scan and all checks.

### 4. Integrity check (always)

Compare inventories of numbers, citations, and labels between the snapshot and the result:

```sh
inv() { grep -oE "$2" "$1" | sort | uniq -c; }
diff <(inv "$DIR/style_logs/pre_style.tex" '[0-9]+([.,][0-9]+)?') <(inv "<file.tex>" '[0-9]+([.,][0-9]+)?')
diff <(inv "$DIR/style_logs/pre_style.tex" '\\cite[a-zA-Z]*\{[^}]*\}') <(inv "<file.tex>" '\\cite[a-zA-Z]*\{[^}]*\}')
diff <(inv "$DIR/style_logs/pre_style.tex" '\\label\{[^}]*\}') <(inv "<file.tex>" '\\label\{[^}]*\}')
```

Without relocation, every diff must be empty. Under `--relocate-numbers`, the number inventory
may show **added** occurrences (a number kept in prose and repeated in its table) and new
labels for the added tables, and only for the entries in the number ledger. A number that
disappears, a number that is new, a changed citation, or any other delta is a hard failure:
fix it before continuing. If numbers moved to a separate supplement file, run the number check
on the main file and the supplement concatenated.

### 5. Compile and re-measure

Compile the manuscript (`latexmk -pdf` or the project's usual build) and fix any breakage.
Then:

```sh
python3 <skill-dir>/scripts/style_metrics.py "<file.tex>" --gate --sections [--genre results] \
  [--ref <exemplar>] > "$DIR/style_logs/style_after.txt"
```

If a band still fails after a thorough pass, return to step 3 for the sections the table flags
and re-measure once more. If a band still fails after that second pass, stop and report it with
the reason (for example, numbers that cannot move because relocation was not authorized). Do
not game the metric.

Then run the **reader-first read** (§Reader-first voice): go paragraph by paragraph against
the exemplar, ask whether each paragraph says what problem it addresses before the details,
and revise every paragraph that fails its rules. If subagents did the rewrite, run the
**judge pass** from that section, apply or reject its rows, and rerun the integrity check and
the gate. The rewrite is complete only when the gate passes and no paragraph is left failing
the read. With `--gate-only`, run the read and report its failures without editing.

### 6. Report

- Edits made, by category (for example, "9 bullet blocks turned into prose, 14 over-long
  sentences split, 6 stock transitions cut").
- The integrity-check result, and the number ledger if numbers moved.
- The style-gate table before and after: each banded metric with its baseline value, final
  value, band, and PASS/FAIL, plus the genre and calibration used. Name every band still
  failing and why.
- The reader-first result: paragraphs read, paragraphs revised for each rule of
  §Reader-first voice, and, if the judge pass ran, its rows applied and rejected (with the
  reason for each rejection).
- Paths to the edited file and the snapshot (`style_logs/pre_style.tex` is the rollback).
  If `latexdiff` is available, also produce a tracked-change PDF against the snapshot.

---

## What NOT to do

- Do **not** swap synonyms and call it a rewrite. The change is structural.
- Do **not** change any claim, number, result, or level of certainty. If voice and meaning
  conflict, meaning wins and the sentence stays.
- Do **not** invent specifics or drop a load-bearing caveat.
- Do **not** over-chop into a telegraphic style; keep the mean sentence length inside the band
  in both directions.
- Do **not** turn a genuine enumeration, table, or reference list into prose, and do not touch
  table data, math, or section titles.
- Do **not** describe a manuscript as "in the house voice" while the gate fails, and do not
  treat passing tic checks as evidence that it passes.
- Do **not** treat passing the bands as proof of the voice. The reader-first read decides
  whether a paragraph reads as a careful author would write it.
- Do **not** write toward beating an AI detector. The target is the house voice.
