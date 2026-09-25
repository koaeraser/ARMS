# Example: dense results paragraph (numbers carried in prose)

**The problem.** A results paragraph that reads as a table written out in sentences: long
sentences, several numbers in each, and the argument buried between them. It can pass every tic
check and still fail the gate.

**Maps to.** SKILL.md, "Numbers in prose" and "Measured style gate". This is the paragraph-level
form of what `scripts/style_metrics.py` measures at document level.

**The fix.** Argue from the one or two numbers that carry each point, and move the rest to a
table that the prose points to. Every number stays in the document with its value unchanged.
Moving numbers is a restructuring edit, so it needs `--relocate-numbers` or an explicit
authorization from the calling pipeline.

The paragraph and its numbers are synthetic, written for this example.

---

## Before

> For nominal $95\%$ intervals under the heavy-tailed scenario, the proposed estimator attains
> empirical coverage of $0.947$ at $n=200$ and $0.951$ at $n=800$, compared with $0.912$ and
> $0.918$ for the bootstrap interval and $0.883$ and $0.890$ for the Wald interval
> (Table~\ref{tab:heavy}); its mean interval width at $n=200$ is $0.42$, which is $11\%$ wider
> than the bootstrap ($0.38$) and $24\%$ wider than Wald ($0.34$). When the tail index falls to
> $2.5$ at the same sample size the gap widens: coverage of the proposed estimator stays at
> $0.943$ while the bootstrap drops to $0.861$ and Wald to $0.802$, and the width premium grows
> to $17\%$ and $31\%$ respectively. The computational cost is $1.8$ seconds per replicate
> against $0.9$ for the bootstrap and $0.01$ for Wald, averaged over $2000$ replicates with
> Monte Carlo standard errors below $0.005$ for all coverage estimates.

## After (numbers moved to a table)

> Table~\ref{tab:heavy} reports coverage and width of nominal $95\%$ intervals under the
> heavy-tailed scenario. We find that the proposed estimator keeps its coverage close to the
> nominal level at both sample sizes, while the bootstrap and Wald intervals undercover. The
> price is width: at $n=200$ our intervals are $11\%$ wider than the bootstrap intervals. The
> coverage gap grows as the tails become heavier, and when the tail index falls to $2.5$ the
> bootstrap coverage drops to $0.861$ while ours stays at $0.943$. Our width premium over the
> bootstrap grows to $17\%$ in that setting. The proposed estimator is also the slowest of the
> three, and the table reports its cost per replicate.

```latex
\begin{table}[t]
\centering
\caption{Nominal 95\% intervals under the heavy-tailed scenario. Width premium is the
proposed estimator's mean width relative to the method in that row. Averages over $2000$
replicates; Monte Carlo standard errors are below $0.005$ for all coverage estimates.}
\label{tab:heavy}
\begin{tabular}{lccccc}
\toprule
\multicolumn{6}{l}{\emph{Default tail index}} \\
Method & Coverage, $n=200$ & Coverage, $n=800$ & Width, $n=200$ & Width premium & Seconds per replicate \\
\midrule
Proposed  & $0.947$ & $0.951$ & $0.42$ & ref.   & $1.8$  \\
Bootstrap & $0.912$ & $0.918$ & $0.38$ & $11\%$ & $0.9$  \\
Wald      & $0.883$ & $0.890$ & $0.34$ & $24\%$ & $0.01$ \\
\midrule
\multicolumn{6}{l}{\emph{Tail index $2.5$, $n=200$}} \\
Method & Coverage & & & Width premium & \\
\midrule
Proposed  & $0.943$ & & & ref.   & \\
Bootstrap & $0.861$ & & & $17\%$ & \\
Wald      & $0.802$ & & & $31\%$ & \\
\bottomrule
\end{tabular}
\end{table}
```

## Measured (`style_metrics.py` on the paragraph alone)

| Metric | Before | After |
|---|---|---|
| mean sentence words | 45.7 | 18.5 |
| sentences in the paragraph | 3 | 6 |
| numbers per 1k prose words | 189.8 | 63.1 |
| most numbers in one sentence | 15 | 3 |
| sentences with more than three numbers | 100% | 0% |
| "we" per 1k | 0.0 | 9.0 |
| semicolons per 1k | 7.3 | 0.0 |

## Number ledger

| Number | Old location | New location |
|---|---|---|
| $95\%$, $200$, $11\%$, $2.5$, $0.861$, $0.943$, $17\%$ | prose | prose (and in the table) |
| $0.947$, $0.951$, $800$, $0.912$, $0.918$, $0.883$, $0.890$ | prose, sentence 1 | table, first panel |
| $0.42$, $0.38$, $0.34$, $24\%$ | prose, sentence 1 | table, first panel |
| $0.802$, $31\%$ | prose, sentence 2 | table, second panel |
| $1.8$, $0.9$, $0.01$ | prose, sentence 3 | table, first panel |
| $2000$, $0.005$ | prose, sentence 3 | table caption |

No number is new and none has vanished. The number inventory therefore shows added occurrences
only (the seven numbers kept in prose now also appear in the table), which is the expected
signature of a relocation.

## Why

The original's first sentence carries fifteen numbers, and the reader must hold three methods,
two sample sizes, and two quantities at once to see the point: the proposed intervals keep their
coverage and pay for it in width. The rewrite states that point in plain sentences, keeps the
numbers that prove it (the $11\%$ width premium, and the $0.861$ against $0.943$ coverage when
the tails get heavier), and leaves the settings and secondary comparisons to the table. The
semicolon hinge is split, and "we" returns where the authors report a finding. A single results
paragraph may stay above the document band for numbers per 1k (here $63.1$); the band is judged
over the whole document, and the exemplar's own simulation section reaches $26$.
