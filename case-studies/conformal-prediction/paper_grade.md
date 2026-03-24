# Paper Grade Report — Round 3 (FINAL)

## Paper Assessment

### Manuscript: DISCOM-CP: Discrepancy-Guided Source Weighting for Multi-Source Conformal Prediction Under Heterogeneous Shift
### Date: 2026-03-24

---

## Previous Round Issues — Status

| # | Issue from Round 2 | Status | Evidence |
|---|---------------------|--------|----------|
| 1 | Conditional coverage analysis missing | **FIXED** | Section 6.5 adds conditional coverage analysis with two sub-analyses: (a) coverage by target value quartile (Table 12 in Appendix F) showing DISCOM-CP's conditional gap (0.146) comparable to WCP (0.142) and Oracle (0.158); (b) coverage by source weight concentration (Table 13) showing stable coverage across concentrated (HHI>0.5: 0.916) and moderate (0.25<HHI<=0.5: 0.917) weight regimes. Discussion paragraph in Section 7 synthesizes the findings. Data files `conditional_coverage_quartile.csv` and `conditional_coverage_concentration.csv` back all claims. |
| 2 | Wine Quality width-coverage tradeoff framing | **FIXED** | Explicit "Width-coverage tradeoff" paragraph added to Section 6.6.2: "DISCOM-CP is 3--9% wider than WCP across the wine scenarios but achieves more reliably valid coverage (all three scenarios above 0.906 vs. WCP's range of 0.893--0.909). This width premium reflects the cost of shift-type agnosticism..." Clear, honest, and well-framed. |
| 3 | Abstract length (~200 words) | **FIXED** | Abstract trimmed to 151 words. Last sentence now efficiently adds the conditional coverage result: "Conditional coverage analysis confirms comparable subgroup coverage to existing methods." |

All 3 priority issues from Round 2 have been addressed.

---

### 1. Correctness: 4/5

The proof of Proposition 1 remains mathematically sound with proper DKW union bound, explicit failure probability delta, and correct constants c_k = sqrt(log(2K/delta)/(2n_k)). The three-step proof structure is clean and correct. The LP relaxation is honestly characterized as a heuristic surrogate. Remark 4 explicitly addresses the data-dependent weights gap.

All numerical claims verified against data CSVs: MVE Table 1 (7 methods), label shift Table 2, joint shift Table 3, stress tests Table 4, California Housing Table 5, Wine Quality Table 6, ablation Table 8, significance Table 11, high-dim Table 7, conditional coverage Tables 12-13, and sensitivity Tables 9-10. No discrepancies found after appropriate rounding. The code audit from prior rounds found no FAIL items.

The remaining theoretical gap (Proposition 1 applies to fixed weights, deployed method uses data-dependent weights) is explicitly acknowledged in Remark 4 and Limitation (4), which is appropriate treatment. To reach 5, the paper would need a formal bound for data-dependent weights (e.g., via the data-splitting approach mentioned in Remark 4).

### 2. Completeness: 5/5

The manuscript now includes all standard sections plus a comprehensive appendix with: detailed proof (Appendix A), proxy discrepancy for unlabeled targets (Appendix B), full stress test results (Appendix C), implementation details with Kish citation (Appendix D), scalability (Appendix E), and sensitivity/ablation/significance/high-dim/conditional coverage (Appendix F). The 15 references cover the key literature.

The completeness case is now strong across all dimensions:
- **Theory**: Proposition 1 with full proof, Corollary 1, Remarks 1-4.
- **Synthetic evaluation**: MVE (2,000 reps), label shift, joint shift, 5 stress tests, higher-dimensional (d=50/100/200).
- **Real-world data**: Two datasets from distinct domains (California Housing, UCI Wine Quality) with 6 natural shift scenarios total.
- **Sensitivity analysis**: Shift magnitude, K (2-10), n_k (50-1000).
- **Ablation**: 4 variants decomposing safety net, KS-weighting, and LP optimization.
- **Statistical significance**: Wilcoxon signed-rank tests for synthetic and wine scenarios.
- **Conditional coverage**: Coverage by target value quartile and by weight concentration -- this was the key gap from Round 2 and is now addressed with two complementary analyses showing DISCOM-CP's conditional coverage profile is comparable to WCP and Oracle.
- **Robustness checks**: Adversarial source exclusion, all-bad sources, single source degeneracy, exact match recovery.

This reaches the threshold for "Exhaustive: + comprehensive robustness checks + ablation" (score 5). The conditional coverage analysis was the final missing piece.

### 3. Rigor: 4/5

Statistical rigor is strong. Monte Carlo standard errors are reported in all tables (2,000 replications for main results, 500 for sensitivity and real-world). Wilcoxon signed-rank tests provide formal significance testing for key comparisons, with both p-values and win/loss counts reported. The ablation study provides controlled evaluation of component contributions. The DKW-based coverage bound has correct probability qualifiers.

The conditional coverage analysis adds meaningful rigor: it demonstrates that the discrepancy-based weighting does not introduce or exacerbate conditional coverage disparities (max gap 0.146 for DISCOM-CP vs. 0.142 for WCP and 0.158 for Oracle). The weight concentration analysis (Table 13) shows stable performance across weight regimes, addressing a potential concern about robustness to optimization outcomes.

Remaining limitations preventing a 5: (a) No formal multiple testing correction across scenarios in significance tables (though results are extreme enough that Bonferroni would not change conclusions). (b) The conditional coverage analysis covers the MVE scenario but not the real-world scenarios -- a comprehensive paper would check conditional coverage on California Housing and Wine Quality too. (c) No formal theoretical guarantees connecting conditional coverage to the method's properties.

### 4. Clarity: 5/5

The paper is well-organized and follows NeurIPS structure. Notation is introduced clearly and used consistently. The abstract is now concise (151 words) and quantitative, efficiently mentioning both real-world datasets, the key result (label shift), and the new conditional coverage finding. The method overview figure (Figure 1) is a well-designed TikZ schematic showing the four-step workflow with labeled boxes. Algorithm 1 provides a clear procedural summary.

The shift construction details for both datasets are well-specified and reproducible. The LP relaxation section is honest about the surrogate nature of L(w). The width-coverage tradeoff paragraph in the Wine Quality section is a model of honest scientific reporting -- it explicitly quantifies the tradeoff and explains why it is favorable. The discussion section organizes findings clearly with paragraph headings, including a dedicated "Conditional coverage" paragraph. Remark 4 on data-dependent weights is thorough without being overly technical.

The narrative arc is compelling: problem (multi-source shift) -> insight (score-level discrepancy) -> method -> theory -> comprehensive validation (synthetic + 2 real-world domains) -> conditional coverage -> honest limitations. Every paragraph earns its place.

### 5. Novelty: 3/5

The core insight -- measuring source-target discrepancy via KS statistics on nonconformity scores rather than on covariates -- remains a meaningful contribution that enables shift-type agnosticism. This is genuinely useful: by operating at the score level, DISCOM-CP avoids density ratio estimation and handles label/joint shift where WCP fails.

However, the individual components remain well-established (KS statistics, weighted conformal prediction from Barber et al. 2023, LP-based weight optimization, safety net via max quantile). The coverage bound (Proposition 1) is a relatively direct application of DKW + triangle inequality + union bound. The novelty score remains at 3: a meaningful extension with clear technical contribution, but the conceptual distance from prior work is moderate. This is intrinsic to the contribution and cannot be changed by revision.

### 6. Impact: 4/5

The method addresses a genuine practical problem (multi-source calibration under unknown shift types) and the manuscript provides strong evidence for practical value with two real-world datasets from distinct domains. Across 6 real-world scenarios, DISCOM-CP achieves valid coverage in every case, while WCP fails in 1 of 6 and is borderline in 2 others.

Key impact strengths: shift-type agnosticism (practitioners do not need to identify shift type), computational efficiency (7ms per prediction set), interpretable source weights, and post-hoc wrapper design requiring no model retraining. The conditional coverage analysis strengthens the impact argument by showing the method preserves coverage uniformity -- practitioners can trust that the method works consistently across subgroups. The cross-domain validation (housing + wine) strengthens the generalizability argument.

Impact limitation: the width advantage over WCP is marginal when covariate shift holds; DISCOM-CP is sometimes wider than WCP in exchange for more reliable coverage; and the method requires n_0 >= 10 labeled target points.

### 7. Performance: 4/5

Performance is strong and well-characterized across multiple scenarios. The method's key performance advantages are demonstrated with statistical significance:

- **Label shift**: DISCOM-CP achieves valid coverage (0.907) where WCP fails entirely (0.807) -- the paper's most decisive result.
- **Joint shift**: 14% tighter than WCP with valid coverage; p < 10^{-10}, wins 1958/2000 replications.
- **High-dimensional (d=200)**: WCP's coverage drops to 0.855 (invalid); DISCOM-CP maintains 0.908.
- **Real-world temporal shift**: 22% tighter than WCP (2.59 vs 3.33) at near-oracle efficiency.
- **Cross-domain consistency**: Valid coverage across all 6 real-world scenarios (2 datasets, 3 shift types each).
- **Adversarial robustness**: 0% width increase from adversarial contamination.
- **Oracle recovery**: 22.8% tighter than WCP when a source matches target exactly.
- **Conditional coverage**: Comparable to WCP and Oracle (max gap 0.146 vs 0.142 vs 0.158).

The wine quality results honestly show that under scenarios where WCP's covariate-shift correction remains partially effective, DISCOM-CP trades 3-9% wider intervals for more reliable coverage. The MVE advantage over WCP is small (0.3%). At d=50, WCP is 3% tighter. The method does not dominate across all scenarios.

Performance remains at 4: "Clear improvement over all comparators; well-quantified; advantages hold across scenarios" -- but not dominant across ALL scenarios (which would require 5).

---

### Raw Score: 29/35

### Weighted Score: 41.5/50

| Dimension | Score (1-5) | Weight | Weighted | Key Strength/Issue |
|-----------|:-----------:|:------:|:--------:|-----------|
| Correctness | 4 | 2.0 | 8.0 | Proof sound; LP honest; data-dependent gap explicitly addressed; all numbers verified |
| Completeness | 5 | 1.5 | 7.5 | Two real-world datasets; 6 shift scenarios; ablation + significance + sensitivity + conditional coverage |
| Rigor | 4 | 1.5 | 6.0 | Wilcoxon tests; proper UQ; sensitivity across 3 axes; conditional coverage analysis |
| Clarity | 5 | 1.0 | 5.0 | Concise abstract (151 words); method figure; width-tradeoff paragraph; compelling narrative |
| Novelty | 3 | 1.0 | 3.0 | Meaningful extension; score-level discrepancy insight; moderate conceptual distance |
| Impact | 4 | 1.0 | 4.0 | Cross-domain validation; shift-agnostic wrapper; 6/6 real-world scenarios valid; conditional coverage preserved |
| Performance | 4 | 2.0 | 8.0 | Strong under label/joint/high-dim shift; 6 real-world scenarios; statistically confirmed; conditional coverage comparable |
| **Total** | | | **41.5/50** | |

### Grade: B (>=34)

---

### Code Audit Summary

| Category | PASS | FLAG | FAIL |
|----------|------|------|------|
| Formula Correctness (1-4) | 4 | 0 | 0 |
| Parameter Consistency (5-9) | 4 | 1 | 0 |
| Methodological Completeness (10-13) | 4 | 0 | 0 |

**PASS items (12):**
- KS statistic via `scipy.stats.ks_2samp`: correct.
- Weighted quantile: sort, normalize, cumulative sum, searchsorted -- correct.
- Mixture quantile: per-source weight w_k/n_k per observation -- correct.
- LP formulation matches manuscript Eq. (8): minimize sum w_k Q_k, s.t. sum w_k d_k <= epsilon, w in simplex.
- Coverage = `mean(test_scores <= q)`: correct.
- Width = `2.0 * q`: correct for symmetric absolute residual intervals.
- Alpha = 0.10 consistent throughout code and manuscript.
- Base seed 42, increment 1 per replication: consistent.
- All 7 methods appear in every evaluation.
- Ablation uses 2,000 replications matching manuscript claim.
- Significance tests use Wilcoxon on paired replication differences: correct methodology.
- All comparators implement correct methodological approaches matching their references.

**FLAG items (1):**
- `optimize_weights` line 105: `RandomState(0)` is used for perturbation candidates, making random exploration identical across all replications. Not a correctness bug but limits diversity of weight search. Does not affect manuscript claims.

**No FAIL items found.** The code audit does not require any score adjustments.

---

### Top 3 Strengths

1. **Exhaustive evaluation with conditional coverage closing the completeness loop.** The addition of conditional coverage analysis (by target value quartile and by weight concentration) addresses the last remaining evaluation gap. The paper now has theory, synthetic evaluation, two real-world domains, sensitivity, ablation, significance testing, and conditional coverage -- covering every dimension of evaluation expected at a top venue. The finding that DISCOM-CP's conditional gap (0.146) is comparable to WCP (0.142) and Oracle (0.158) is an important result that shows the method does not sacrifice coverage uniformity for marginal tightness.

2. **Honest and well-framed presentation of tradeoffs.** The wine quality width-coverage tradeoff paragraph is exemplary scientific reporting: it acknowledges that DISCOM-CP is 3-9% wider than WCP in the wine experiments, explains why (cost of shift-type agnosticism), and argues why this is favorable in practice (consistent validity guarantee). The abstract is now concise at 151 words. The discussion section addresses limitations forthrightly, including the data-dependent weights gap, conditional coverage variation, and the DKW bound conservatism.

3. **Strong and decisive label-shift result with cross-domain confirmation.** The label shift experiment remains the paper's strongest empirical contribution: WCP coverage drops to 0.807 while DISCOM-CP maintains 0.907. This is confirmed across two real-world domains (6 scenarios, all with valid DISCOM-CP coverage vs. WCP failures/borderline in 3 of 6). The high-dimensional experiments (d=200) provide a second clear regime where DISCOM-CP dominates.

### Top 3 Weaknesses (with suggested improvement)

1. **Novelty remains moderate (score 3).** The contribution is a meaningful extension of Barber et al. (2023) with KS-based source weighting, but the conceptual distance from prior work is moderate. The individual components (KS statistics, LP optimization, safety net) are standard. This is intrinsic to the contribution and **cannot be addressed by revision** -- it is a property of the research itself. This is the primary barrier to reaching the A threshold (42/50).

2. **Conditional coverage analysis limited to MVE scenario.** The conditional coverage by target value quartile is only computed for the synthetic MVE (2,000 replications). Computing the same analysis for the California Housing and Wine Quality experiments would strengthen the rigor further. However, this is a minor gap given that the MVE analysis already demonstrates the key finding (comparable conditional gap across methods). *Suggested fix: add quartile-conditional coverage for at least one real-world scenario.*

3. **Rigor score capped at 4.** To reach 5, the paper would need: formal theoretical guarantees connecting the method to conditional coverage properties, multiple testing corrections for the significance tables, and conditional coverage analysis on real-world data. The first of these is a substantial theoretical contribution in its own right. *Suggested fix: a brief formal argument connecting the marginal coverage bound to conditional coverage under mild assumptions could push this toward 5, but this would require new theoretical work.*

### Fixable Issues (for paper-fixer)

1. **Conditional coverage on real-world data.** Adding quartile-conditional coverage for one real-world scenario (e.g., California Housing temporal shift) would marginally strengthen completeness and rigor. This requires computing per-quartile coverage from the existing 500-replication data.

2. **Minor: Bonferroni note.** Adding a brief note in Table 11's caption that Bonferroni correction across the 3 scenarios would not change any conclusion (since all p-values are either < 10^{-6} or p=1.0) would preempt a reviewer concern.

### Score Trajectory

| Round | Score | Change | Key Improvements |
|-------|:-----:|:------:|------------------|
| 0 | 32.0/50 | -- | Baseline with synthetic-only, proof gap, no ablation |
| 1 | 39.0/50 | +7.0 | Proof fixed, real-world data added, ablation + significance + sensitivity |
| 2 | 40.0/50 | +1.0 | Second real-world dataset, method figure, data-dependent remark, Kish citation |
| 3 | 41.5/50 | +1.5 | Conditional coverage analysis, wine width-tradeoff framing, abstract trimmed, Completeness 4->5 |

### Path to 42.0/50

The paper is 0.5 points short of the A threshold. The only feasible path:
- **Rigor 4 -> 4.33** (not possible with integer scoring) or **Correctness 4 -> 4.33** (not possible).
- With integer scoring, reaching exactly 42.0 requires either Rigor to 5 (+1.5, total 43.0) or Correctness to 5 (+2.0, total 43.5). Both require substantial new work: Correctness 5 needs a formal bound for data-dependent weights; Rigor 5 needs theoretical conditional coverage guarantees and multiple testing correction.
- Alternatively, one could argue Completeness is 5 and Rigor is at the very high end of 4 (effectively 4.33), but the rubric uses integer scoring.

The score of 41.5/50 is the honest assessment. The 0.5-point gap from 42 is attributable to the Novelty ceiling (intrinsic to the contribution, score 3) and the gap between Rigor at 4 and at 5 (which would require formal conditional coverage theory).

### Verdict

The Round 3 manuscript represents a well-polished contribution to conformal prediction under multi-source distribution shift. All priority issues from Round 2 have been addressed: conditional coverage analysis closes the completeness loop, the wine width-coverage tradeoff is honestly framed, and the abstract is concise. At 41.5/50, the paper falls 0.5 points short of the A threshold (42/50), with the primary barriers being Novelty at 3 (intrinsic, worth only 3.0 weighted) and the gap between Rigor at 4 and at 5 (which would require new theoretical work on conditional coverage).

**Recommendation**: This is a borderline-accept paper at NeurIPS. It addresses a genuine practical problem with a well-engineered solution, provides exhaustive empirical evidence across two real-world domains with 6 shift scenarios, and presents its findings with exemplary honesty. The label shift result (WCP 0.807 vs. DISCOM-CP 0.907) is decisive, and the cross-domain validation is compelling. A reviewer panel would likely produce a mix of "weak accept" and "borderline" scores, with the comprehensiveness of evaluation and the label-shift/high-dimensional results being the strongest arguments for acceptance. The novelty limitation (score-level KS discrepancy is useful but conceptually moderate) is the most likely basis for pushback.
