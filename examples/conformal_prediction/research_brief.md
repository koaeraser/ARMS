# Research Brief: Multi-Source Conformal Prediction Under Heterogeneous Distribution Shift

## 1. Problem Statement

**Domain**: Machine learning — uncertainty quantification and distribution-free inference
**Research area**: Conformal prediction under distribution shift

**Core challenge**: Conformal prediction provides distribution-free coverage guarantees,
but these guarantees break when the test distribution differs from the calibration
distribution. In practice, calibration data often comes from *multiple* source domains
(e.g., hospitals, time periods, geographic regions) that each differ from the target
deployment domain in unknown ways. The question is **how to combine calibration data
from heterogeneous sources to produce prediction sets that are both valid and tight on
the target domain**.

**Why existing approaches fall short**:
- Standard split conformal assumes exchangeability between calibration and test data — violated under any shift.
- Weighted conformal prediction (Tibshirani et al., 2019) handles covariate shift via density ratios, but requires knowing the shift type and estimating ratios accurately — fragile under joint or label shift.
- Robust conformal methods (Cauchois et al., 2024) hedge against worst-case shift within a divergence ball, producing conservative (wide) prediction sets.
- Adaptive conformal inference (Gibbs & Candes, 2021) adjusts online but requires a stream of target-domain labels — unavailable in many deployment settings.
- No existing method addresses the *multi-source* setting where each source has a different (unknown) relationship to the target, and the method must decide how much to trust each source's calibration data.

**Abstract problem formulation**:
> Given K heterogeneous information sources with known calibration data and a target
> domain with limited or no labeled calibration data, how do you optimally weight and
> combine information from sources to construct prediction sets on the target — while
> guaranteeing coverage and minimizing set size, without knowing the type or magnitude
> of shift from each source?

## 2. Data Assets

### Primary Dataset: Synthetic Multi-Source Shift Benchmark
- **Description**: Synthetic regression/classification data generated from known distributions with controlled shift types and magnitudes. Each "source" has calibration data (X, Y pairs); the target has unlabeled test points (and held-out labels for evaluation only).
- **Generation**: To be implemented in Phase 2. Generate K=5-10 source domains with:
  - Covariate shift (P(X) changes, P(Y|X) constant)
  - Label shift (P(Y) changes, P(X|Y) constant)
  - Joint shift (both change)
  - Mixed: some sources have mild shift, others severe, one adversarial
- **Size**: n_k = 200-500 calibration points per source, n_target = 1000 test points
- **Ground truth**: Known true conditional distributions for computing oracle prediction sets

### Secondary Datasets
- **Tabular regression with temporal shift**: Use publicly available datasets where natural temporal splits create distribution shift (e.g., year-over-year economic data, air quality monitoring across stations/years, or energy consumption data with seasonal shift). Select 2-3 datasets at experiment time.
- **Tabular classification with demographic shift**: UCI-scale datasets with known subgroup structure where train/test splits across subgroups create natural covariate shift.

### Data Quirks and Known Issues
- Synthetic data gives full experimental control but may not capture real-world shift complexity — real datasets provide complementary evidence.
- Density ratio estimation (needed by baselines) degrades in high dimensions — keep feature dimensions moderate (d ≤ 50) to give baselines a fair chance.

### Infrastructure Code
- None provided. Phase 2 builds all code from scratch.

## 3. Domain Context

### Key Terminology
- **Conformal prediction (CP)**: Framework for constructing prediction sets C(X) that contain the true Y with probability ≥ 1-α, without distributional assumptions beyond exchangeability.
- **Conformity score / nonconformity score**: s(X, Y) — measures how "unusual" the pair (X, Y) is. Common choices: absolute residual |Y - f(X)| for regression, 1 - f_Y(X) for classification.
- **Coverage**: P(Y ∈ C(X)) — the probability that the prediction set contains the true value. Target: 1-α (typically 0.90 or 0.95).
- **Marginal coverage**: Coverage averaged over the test distribution. Easier to guarantee.
- **Conditional coverage**: Coverage conditional on X = x. Harder, more useful.
- **Prediction set size / interval width**: |C(X)| — smaller is better, given valid coverage.
- **Exchangeability**: The assumption that the joint distribution of (Z_1, ..., Z_n, Z_{n+1}) is invariant to permutation. Standard CP requires this; distribution shift violates it.
- **Covariate shift**: P_target(X) ≠ P_source(X), but P(Y|X) is invariant.
- **Label shift**: P_target(Y) ≠ P_source(Y), but P(X|Y) is invariant.
- **Joint shift**: Both P(X) and P(Y|X) change.
- **Density ratio**: w(x) = p_target(x) / p_source(x) — used in weighted CP.

### Domain Constraints
- Methods must be **distribution-free** — the coverage guarantee should not depend on parametric assumptions about the data distribution.
- Theoretical results should specify coverage guarantees in terms of verifiable or estimable quantities (e.g., divergence between source and target, not unverifiable assumptions).
- All prediction set constructions must be **computationally tractable** — no exponential-time set optimization.

### Practitioner Expectations
- A method they can wrap around any base predictor (regression model, classifier) without retraining it.
- Clear guidance on when to use the method vs simpler alternatives.
- Interpretable source weights — "this source contributed X% to the prediction set."
- Coverage guarantees that degrade gracefully as shift increases (not cliff-edge failure).

## 4. Target Venue

**Name**: NeurIPS (Conference on Neural Information Processing Systems)

### Format Requirements
- **Template**: NeurIPS 2025 LaTeX style (`neurips_2025.sty`)
- **Page limit**: 9 pages main text + unlimited appendix/supplementary
- **Citation style**: Numbered, `\citep{}` and `\citet{}` (natbib)
- **Supplementary**: Separate appendix after references, same document

### Audience
Machine learning researchers and practitioners. Strong theory track. Expects both theoretical contributions and empirical validation.

### Quality Expectations
- [x] Rigorous theory (finite-sample coverage bounds, not just asymptotic)
- [x] Comprehensive empirical evaluation
- [x] Comparison to established baselines
- [x] Real-world application / case study
- [x] Reproducibility (code, synthetic data generation)
- [x] Clear practical value

### Typical Structure
Abstract, Introduction, Related Work, Problem Setup, Proposed Method, Theoretical Analysis, Experiments, Discussion/Conclusion, References, Appendix (proofs, additional experiments)

## 5. Success Criteria

### Primary Metric(s)
- **Empirical coverage on target domain**: Must be ≥ 1-α (e.g., ≥ 0.90 for α=0.10). This is a hard constraint, not a metric to optimize — invalid coverage means the method fails.
- **Average prediction set size / interval width**: Primary optimization target, conditional on valid coverage. Smaller is better. Report relative to the oracle (which knows the target distribution).

### Secondary Metrics
- **Conditional coverage gap**: max_g |Coverage(g) - (1-α)| across subgroups g. Measures coverage uniformity.
- **Source weight quality**: Correlation between learned source weights and true source-target similarity (measurable in synthetic experiments with known ground truth).
- **Computational overhead**: Wall-clock time relative to standard split conformal.

### Calibration / Uncertainty
- Coverage must be within [1-α - 0.02, 1-α + 0.05] empirically (slightly conservative is acceptable; undercoverage is not).
- Report coverage ± standard error across experimental replications.

### Robustness
- Adding irrelevant/adversarial source domains should cause ≤ 5% increase in prediction set size vs oracle source selection.
- Method should not catastrophically fail (coverage dropping below 1-α - 0.05) under any tested shift scenario.

### Computational Requirements
- Prediction set construction for n=1000 test points with K=10 sources should complete in < 60 seconds on a single CPU core.
- No GPU required for the method itself (base model training may use GPU, but the CP wrapper should not).

### Deployability
- Method should work as a post-hoc wrapper: take any pre-trained model + multi-source calibration data → produce prediction sets. No model retraining.

### Interpretability
- Source weights should be inspectable and sum to 1 (or be otherwise normalized). Practitioners need to understand which sources the method trusts and why.

## 6. Comparator Methods

| # | Name | Reference | Brief Description | Why Included |
|---|------|-----------|-------------------|--------------|
| 1 | Split Conformal | Vovk et al. (2005) | Pool all sources, ignore shift | Simplest baseline |
| 2 | Weighted Conformal (WCP) | Tibshirani et al. (2019) | Reweight by density ratio, covariate shift only | Standard shift-aware method |
| 3 | Robust Conformal (RCP) | Cauchois et al. (2024) | Worst-case over divergence ball | Conservative baseline |
| 4 | Adaptive Conformal Inference (ACI) | Gibbs & Candes (2021) | Online alpha adjustment | Requires target labels (streaming) |
| 5 | Oracle Single-Source | — | Use only the best source (known via ground truth) | Upper bound on source selection |
| 6 | Uniform Mixture | — | Equal-weight combination of all sources | Naive multi-source baseline |

## 7. Adjacent Fields

**Abstract version of the problem**:
Given K heterogeneous information sources of varying relevance to a target task,
how do you optimally weight and combine them — without knowing which sources are
relevant or how they differ from the target?

**Fields with analogous challenges**:

| Field | Analogous Concept | Key Reference |
|-------|-------------------|---------------|
| Multi-source domain adaptation | Source selection and weighting for transfer learning | Mansour, Mohri & Rostamizadeh (2009) |
| Robust statistics | Contamination-robust estimation from mixture of clean and corrupted data | Diakonikolas & Kane (2019) |
| Expert aggregation / forecast combination | Combining predictions from experts with heterogeneous accuracy | Cesa-Bianchi & Lugosi (2006) |
| Bayesian model averaging | Weighting models by posterior probability given data | Hoeting et al. (1999) |
| Sensor fusion | Combining measurements from sensors with different noise profiles | Hall & Llinas (1997) |
| Meta-learning | Few-shot adaptation using experience from related tasks | Finn et al. (2017) |

## 8. Evaluation Design

### Computational Budgets

| Stage | Replicates | Time Limit | Purpose |
|-------|-----------|------------|---------|
| Quick validation | 200 | 5 min | Sanity check during development |
| Stress test | 500 | 30 min | Robustness under edge cases |
| Production | 2000 | 2 hr | Final numbers for the paper |

### Evaluation Types
- [x] Simulation study (synthetic multi-source data, known ground truth, controlled shift)
- [x] Sensitivity analysis (vary K, n_k, shift magnitude, shift type)
- [x] Robustness / stress tests (adversarial sources, extreme shift, K=1 degenerate case)
- [x] Held-out real data (2-3 tabular datasets with natural shift)
- [x] Scalability benchmarks (wall-clock time vs K and n)

### Random Seed Convention
Base seed 42, increment by 1 per replicate.

### Key Stress-Test Scenarios
1. **Adversarial source**: One of K sources has data from a completely unrelated distribution. Verify coverage holds and set size increases minimally.
2. **All sources equally bad**: Every source has significant shift from target. Verify graceful degradation.
3. **Single source (K=1)**: Degenerate case — method should reduce to standard weighted CP or better.
4. **Target matches one source exactly**: Method should discover and upweight the matching source.
5. **High-dimensional features (d=50)**: Density ratio estimation becomes unreliable. Verify robustness.

## 9. Scope and Non-Goals

### What the Paper Should NOT Try to Do
- Do not propose a new base predictor (regression model, classifier). The method is a post-hoc CP wrapper.
- Do not address the online/streaming setting where target labels arrive sequentially (this is ACI's territory). Focus on the batch multi-source setting.
- Do not attempt image-scale experiments (CIFAR, ImageNet). Tabular data is sufficient and keeps computation tractable.

### Known Limitations to Acknowledge
- Coverage guarantees may depend on quality of source-target divergence estimation.
- Conditional coverage is fundamentally harder than marginal coverage — finite-sample guarantees for conditional coverage may require structural assumptions.
- Source weight estimation adds computational overhead vs simple pooling.

### Methods or Approaches Out of Scope
- Deep learning for conformity score design (would require retraining base models).
- Causal inference for shift identification (interesting but orthogonal).
- Conformal prediction for structured outputs (sequences, graphs) — restrict to regression and classification.

## 10. Reference Papers

**Directory**: reference/

### Key Papers
- Vovk et al. (2005) — Algorithmic Learning in a Random World (foundational CP reference)
- Tibshirani et al. (2019) — Conformal prediction under covariate shift
- Gibbs & Candes (2021) — Adaptive conformal inference under distribution shift
- Cauchois et al. (2024) — Robust conformal prediction using Wasserstein balls
- Snell & Griffiths (2025) — Conformal prediction as Bayesian quadrature (ICML 2025 outstanding paper)
- Barber et al. (2023) — Conformal prediction beyond exchangeability
