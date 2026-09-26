# Example: abstract that passes the metrics and still reads as generated

**The problem.** The prose passes the measured bands and every tic check, yet a reader finds
it hard to follow and its author would not have written it. It opens on a rule instead of the
problem, its sentences state findings without saying what the authors did, it compresses ideas
into shorthand coined during the project, and it lists results with numbers in clipped
sentences.

**Maps to.** SKILL.md, "Reader-first voice (what the metrics cannot see)", all eight rules.

**The fix.** Carry the reader through an argument: the problem, what we do, what we find, and
what we provide. Name every idea in full words, say what each result means, and leave the
supporting numbers and secondary findings to the body.

The abstract, its numbers, the guideline, and the trial are synthetic, written for this
example.

---

## Before

> Guideline G-7 (lines 88--91) requires that the analysis of a stepped-wedge trial "account
> for secular trends", and most published sample size formulas meet it with a linear trend
> term. We size stepped-wedge trials under this requirement and, as an extension, allow
> nonlinear trends in the analysis model. We separate four entangled variances. Linear and
> categorical trend models share the cluster effect but not the design effect. Categorical
> trends need more clusters than linear ones when the ICC is below 0.05 and there are more
> than five periods (Section 4). Read linearly, a curved trend understates the variance by
> 18% and raises the Type I error rate from 0.025 to 0.083 (Table 3). Shrinkage of the period
> effects toward a smooth curve restores 0.027 at the cost of 12 extra clusters. A three-step
> hand-hygiene design with R code and a protocol checklist applies them.

## After

> In stepped-wedge cluster randomized trials, every cluster eventually receives the
> intervention, so the treatment effect is entangled with changes over calendar time. Most
> sample size formulas assume that this time trend is linear, while guidance asks only that
> the analysis account for it. We study how the choice of trend model affects the number of
> clusters a trial needs and the validity of its conclusions. We show that modelling each
> period separately requires more clusters than a linear trend only when there are many
> periods and the correlation within clusters is small. When the true trend is curved,
> assuming that it is linear makes the variance look smaller than it is, and the Type I error
> rate more than triples. We then examine a middle course that shrinks the period effects
> toward a smooth curve, and we find that it keeps the Type I error rate close to its nominal
> level at the cost of a modest number of additional clusters. To help trial teams apply
> these results, we provide a worked design of a hand-hygiene trial in nursing homes, with R
> code and a protocol checklist.

## Side by side, with the rule each change applies

| Before | After | Rule |
|---|---|---|
| Opens on the guideline's wording and line numbers. | Opens on why time trends matter in this design, then paraphrases the guidance and the usual linear assumption. | 1 problem first, 6 quote only when wording matters |
| "We size stepped-wedge trials under this requirement and, as an extension, allow nonlinear trends in the analysis model." | "We study how the choice of trend model affects the number of clusters a trial needs and the validity of its conclusions." | 2 doing-verbs |
| "We separate four entangled variances." | Dropped. Each variance is named in the body where it matters. | 3 describe |
| "Linear and categorical trend models share the cluster effect but not the design effect. Categorical trends need more clusters ... when the ICC is below 0.05 and there are more than five periods (Section 4)." | "We show that modelling each period separately requires more clusters than a linear trend only when there are many periods and the correlation within clusters is small." | 2 doing-verbs, 3 describe ("categorical trends", "ICC"), 4 numbers out, 5 pointer out |
| "Read linearly, a curved trend understates the variance by 18% and raises the Type I error rate from 0.025 to 0.083 (Table 3)." | "When the true trend is curved, assuming that it is linear makes the variance look smaller than it is, and the Type I error rate more than triples." | 3 describe ("read linearly"), 4 results in words |
| "Shrinkage of the period effects toward a smooth curve restores 0.027 at the cost of 12 extra clusters." | "We then examine a middle course that shrinks the period effects toward a smooth curve, and we find that it keeps the Type I error rate close to its nominal level at the cost of a modest number of additional clusters." | 2 doing-verbs, 3 describe, 4 results in words, 8 lean connective |
| "A three-step hand-hygiene design with R code and a protocol checklist applies them." | "To help trial teams apply these results, we provide a worked design of a hand-hygiene trial in nursing homes, with R code." | 1 purpose first, 2 doing-verbs |

In a real rewrite, every number removed from the abstract (here 0.05, five periods, 18%,
0.025, 0.083, 0.027, and 12 clusters) must already appear in the body or its tables with its
value unchanged.

## Why

The first version was written for someone who already knew the paper. Each sentence is a
compressed finding, so the reader has to supply the question it answers, the reason it
matters, and the meaning of terms such as "read linearly" or "the four variances". The
rewrite carries the reader through an argument: the problem, what we study, what we find about
sample size, what goes wrong under a misspecified trend, how we address it, and what we
provide. The findings and their calibration are unchanged. The difference lies in the order,
the verbs, and the vocabulary, none of which the bands measure. The first version averages
about 18 words per sentence and sits inside the default band; the rewrite averages about 27
and sits above it, so on a passage this short the band points the wrong way. The bands are
read over the whole main text, and the reader-first read decides the voice paragraph by
paragraph.
