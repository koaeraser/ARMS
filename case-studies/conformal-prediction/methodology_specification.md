# Methodology Specification: Discrepancy-Guided Multi-Source Conformal Prediction (DISCOM-CP)

## One-Sentence Summary

DISCOM-CP optimally weights calibration data from multiple heterogeneous source domains by minimizing a discrepancy-penalized prediction set size objective subject to a finite-sample coverage bound derived from the weighted total variation framework of Barber et al. (2023), yielding prediction sets that are provably valid and empirically tight on the target domain without requiring knowledge of the shift type or density ratio estimation.

---

## Core Idea

The central challenge in multi-source conformal prediction is deciding how much to trust each source's calibration data when constructing prediction sets for a target domain. Sources that are "close" to the target should contribute heavily, while distant or adversarial sources should be downweighted or excluded. But the type and magnitude of shift from each source to the target is unknown, and assuming a specific shift type (covariate, label, joint) is fragile.

Our key insight is to bypass shift-type identification entirely and instead directly estimate the *discrepancy between nonconformity score distributions* from each source and the target. Regardless of whether the underlying shift is covariate, label, or joint, what matters for conformal prediction is how the distribution of conformity scores s(X, Y) changes. Two sources with very different covariate distributions may produce similar score distributions (e.g., if the model generalizes well), and conversely, mild covariate shift may cause large score distribution changes (e.g., if the model is poorly calibrated in a subregion). By operating at the score level, we capture what actually matters for prediction set validity.

Concretely, DISCOM-CP uses a small amount of target-domain data (labeled or unlabeled depending on the variant) to estimate each source's score distribution discrepancy to the target. These discrepancies feed into a constrained optimization problem: minimize the expected prediction set size (a function of the weighted quantile of scores) subject to the constraint that the coverage gap, bounded by a weighted sum of discrepancies following Barber et al. (2023), remains below a tolerance epsilon. The resulting weights are interpretable (source k gets weight w_k reflecting its contribution), automatically sparse (irrelevant sources get zero weight), and yield prediction sets with finite-sample coverage guarantees. When no target labels are available, we use a proxy discrepancy based on the conformity score evaluated at the model's point prediction, which requires only unlabeled target data.

---

## Mathematical Specification

### Input

- **Base predictor**: A pre-trained model f: X -> Y (regression) or f: X -> Delta(Y) (classification), where X is the feature space and Y is the label space.
- **Nonconformity score function**: s: X x Y -> R. For regression, typically s(x, y) = |y - f(x)|. For classification, s(x, y) = 1 - f_y(x) where f_y(x) is the predicted probability for class y.
- **Source calibration data**: For each source k in {1, ..., K}, a calibration set D_k = {(X_i^k, Y_i^k)}_{i=1}^{n_k} drawn from distribution P_k.
- **Target data**: Either:
  - (a) A small labeled target calibration set D_0 = {(X_i^0, Y_i^0)}_{i=1}^{n_0} drawn from P_target, with n_0 possibly small (even n_0 = 0 in the fully unsupervised variant), OR
  - (b) An unlabeled target set D_0^X = {X_i^0}_{i=1}^{n_0} drawn from P_target(X).
- **Significance level**: alpha in (0, 1), typically 0.10.
- **Coverage tolerance**: epsilon >= 0, the acceptable gap below nominal coverage (default epsilon = 0.01).
- **New test point**: X_{test} from P_target(X).

### Output

- **Source weights**: w = (w_1, ..., w_K) in Delta_K (the K-simplex), interpretable as the contribution of each source.
- **Prediction set**: C_alpha(X_{test}) = {y in Y : s(X_{test}, y) <= q_hat_w}, where q_hat_w is the weighted quantile threshold.
- **Coverage guarantee**: P(Y_{test} in C_alpha(X_{test})) >= 1 - alpha - epsilon (finite-sample).

### Key Quantities

**Definition 1 (Source nonconformity scores).** For each source k in {1, ..., K}, compute scores:
  R_i^k = s(X_i^k, Y_i^k), for i = 1, ..., n_k.

**Definition 2 (Score CDF).** For source k, the empirical CDF of scores is:
  F_hat_k(t) = (1/n_k) * sum_{i=1}^{n_k} I(R_i^k <= t).

**Definition 3 (Target score CDF estimate).** When target labels are available:
  F_hat_0(t) = (1/n_0) * sum_{i=1}^{n_0} I(R_i^0 <= t).

When only unlabeled target data is available, we use a proxy (see Section on Proxy Discrepancy below).

**Definition 4 (Score distribution discrepancy).** For source k, define:
  d_k = d_SD(F_hat_k, F_hat_0)

where d_SD is a statistical distance between score distributions. We use the Kolmogorov-Smirnov (KS) statistic:
  d_k = sup_t |F_hat_k(t) - F_hat_0(t)|

as the default, which bounds the TV distance of the score distributions and can be computed in O(n_k log n_k) time.

**Remark:** The KS statistic is chosen because (1) it upper-bounds the TV distance between one-dimensional distributions, (2) it has well-known finite-sample concentration properties (DKW inequality), and (3) it is nonparametric and does not require density estimation.

**Definition 5 (Weighted quantile).** Given weights w = (w_1, ..., w_K) in Delta_K, define the pooled weighted score distribution:
  F_hat_w(t) = sum_{k=1}^K w_k * F_hat_k(t)

and the weighted quantile:
  q_hat_w(beta) = inf{t : F_hat_w(t) >= beta}

which is the beta-quantile of the weighted mixture of source score distributions.

**Definition 6 (Prediction set size surrogate).** The expected prediction set size under the target distribution is approximated by:
  L(w) = q_hat_w(1 - alpha + epsilon_q)

where epsilon_q is a small upward adjustment to the quantile level to account for finite-sample effects (see below). For regression, |C_alpha(X)| = 2 * q_hat_w (interval width). For classification, the set size is the number of classes y with s(X, y) <= q_hat_w. In both cases, minimizing q_hat_w minimizes the prediction set size.

### Coverage Guarantee (Theoretical Foundation)

**Assumption 1 (Independence across sources).** The calibration datasets D_1, ..., D_K are drawn independently from P_1, ..., P_K respectively. The target test point (X_{test}, Y_{test}) is drawn independently from P_target.

**Assumption 2 (Bounded score discrepancy).** For each source k, the total variation distance between the score distribution under P_k and the score distribution under P_target satisfies:
  d_TV(P_k^S, P_target^S) <= delta_k

where P_k^S and P_target^S denote the marginal distributions of the nonconformity score s(X, Y) under P_k and P_target respectively.

**Proposition 1 (Coverage bound for weighted score mixture).** Under Assumptions 1 and 2, for any weights w in Delta_K:

  P(Y_{test} in C_alpha(X_{test})) >= 1 - alpha - sum_{k=1}^K w_k * delta_k - gamma_n

where gamma_n = sum_{k=1}^K w_k / (2 * n_k)^{1/2} is a finite-sample correction from the DKW inequality applied to each source's empirical CDF.

*Proof sketch:* The true score CDF under the target is F_target(t) = P_target(s(X, Y) <= t). By definition of TV distance, for each source k: |F_k(t) - F_target(t)| <= d_TV(P_k^S, P_target^S) <= delta_k for all t. The weighted mixture CDF satisfies:

|F_w(t) - F_target(t)| = |sum_k w_k F_k(t) - F_target(t)| = |sum_k w_k (F_k(t) - F_target(t))| <= sum_k w_k delta_k.

By the DKW inequality, |F_hat_k(t) - F_k(t)| <= sqrt(log(2)/2n_k) with probability >= 1 - exp(-2n_k*eps^2). Combining the approximation error and the discrepancy bound, the empirical weighted quantile q_hat_w(1-alpha) satisfies:

F_target(q_hat_w(1-alpha)) >= 1 - alpha - sum_k w_k delta_k - gamma_n.

Therefore P(Y_{test} in C_alpha(X_{test})) = P(s(X_{test}, Y_{test}) <= q_hat_w) = F_target(q_hat_w) >= 1 - alpha - sum_k w_k delta_k - gamma_n.

**Corollary 1.** To guarantee coverage >= 1 - alpha - epsilon, it suffices to find weights w such that:
  sum_{k=1}^K w_k * delta_k + gamma_n <= epsilon.

### The Optimization Problem

DISCOM-CP solves:

  minimize_{w in Delta_K}   q_hat_w(1 - alpha)
  subject to:                sum_{k=1}^K w_k * d_k <= epsilon - gamma_n(w)
                             w_k >= 0 for all k
                             sum_{k=1}^K w_k = 1

where d_k is the estimated score distribution discrepancy (Definition 4) and gamma_n(w) = sum_k w_k / sqrt(2 * n_k) is the finite-sample correction. This is the key optimization: minimize the prediction set size (via the quantile threshold) while ensuring the coverage gap remains bounded.

**Remark on tractability.** The constraint sum_k w_k * d_k <= epsilon - gamma_n(w) is linear in w (since gamma_n(w) is also linear in w). The objective q_hat_w(1 - alpha) is a quantile of a mixture of empirical distributions, which is piecewise constant in w. We solve this via:
1. A relaxation where the objective is replaced by the smooth surrogate: L_smooth(w) = sum_k w_k * Q_k(1 - alpha), where Q_k(1-alpha) is the (1-alpha)-quantile of source k's score distribution. This is a linear program.
2. Refinement: given the LP solution, perform a grid search over nearby weight vectors to find the one minimizing the exact mixture quantile.

**Alternative: Lagrangian formulation.** Equivalently, for a Lagrange multiplier lambda >= 0:

  minimize_{w in Delta_K}   q_hat_w(1 - alpha) + lambda * (sum_{k=1}^K w_k * (d_k + 1/sqrt(2*n_k)))

This trades off prediction set size against the coverage gap penalty, with lambda controlling the tradeoff. The solution for large lambda yields the most conservative (coverage-safe) weights; lambda = 0 yields the weights that minimize set size ignoring coverage.

### Proxy Discrepancy (Unlabeled Target Variant)

When target labels are unavailable, we cannot compute target score CDFs directly. We use a proxy based on the model's behavior on target covariates.

**Definition 7 (Proxy score).** For a regression model f, define the proxy score at a target point X_i^0 as:
  R_proxy_i = s(X_i^0, f(X_i^0)) = |f(X_i^0) - f(X_i^0)| = 0 (trivially zero for absolute residual).

This is uninformative. Instead, we use the *distribution of model predictions* as a proxy:

For regression: Compare the distribution of f(X^k) (source k predictions) with f(X^0) (target predictions). If these differ substantially, the source is less relevant.

  d_k^proxy = d_KS(F_hat_{f,k}, F_hat_{f,0})

where F_hat_{f,k}(t) = (1/n_k) sum_i I(f(X_i^k) <= t) and F_hat_{f,0}(t) = (1/n_0) sum_i I(f(X_i^0) <= t).

For classification: Compare the distribution of softmax outputs (or predicted class probabilities):
  d_k^proxy = d_KS(F_hat_{max-prob,k}, F_hat_{max-prob,0})

where F_hat_{max-prob,k} is the empirical CDF of max_y f_y(X^k) across source k, and similarly for target.

**Justification:** Under mild conditions, if the model f is Lipschitz, then the distribution of f(X) is close to the distribution of f(X') when X and X' have similar distributions. More importantly, the distribution of model outputs reflects the model's effective "operating region," which is what matters for score distribution similarity.

**Remark:** The proxy discrepancy is an upper bound on the true score discrepancy only under additional assumptions (e.g., model calibration). When using the proxy, the coverage guarantee of Proposition 1 becomes approximate rather than exact. We address this by adding a safety margin epsilon_safety to the constraint.

### Finite-Sample Correction

**Definition 8 (Adjusted quantile).** To account for the discreteness of empirical distributions and ensure the coverage bound holds in finite samples, we use:

  q_hat_w = Q_{ceil((N_eff + 1)(1 - alpha + epsilon))/N_eff}(pooled weighted scores)

where N_eff = 1 / sum_k w_k^2 / n_k is the effective sample size of the weighted pool (analogous to the effective sample size in importance sampling), and Q_p denotes the p-th quantile.

### Edge Cases

**K = 1 (single source):** DISCOM-CP reduces to standard split conformal prediction with a possible quantile adjustment based on the estimated discrepancy d_1. If d_1 is small enough to satisfy the constraint, we use standard conformal. Otherwise, we inflate the quantile by d_1 + gamma_n, recovering a conservative guarantee similar to Cauchois et al. (2024).

**All sources equally bad (d_k large for all k):** The constraint sum_k w_k d_k <= epsilon may be infeasible. In this case, DISCOM-CP issues a warning and falls back to the robust conformal approach: inflate the quantile by min_k d_k (use the best available source) and report that the coverage guarantee is degraded by this amount.

**Adversarial source:** An adversarial source k* will have large d_{k*}. The optimization will automatically assign w_{k*} = 0 because including it increases the constraint violation without reducing the quantile (or increases the quantile). This is the key robustness property.

**Target matches one source exactly:** Source k* with d_{k*} = 0 will dominate: the optimizer can assign w_{k*} = 1, recovering standard conformal on the best source. The constraint is automatically satisfied.

---

## Algorithm

```
Algorithm: DISCOM-CP (Discrepancy-Guided Multi-Source Conformal Prediction)

Input:
  - Base model f
  - Score function s
  - Source calibration sets {D_k}_{k=1}^K, each of size n_k
  - Target data D_0 (labeled) or D_0^X (unlabeled), size n_0
  - Significance level alpha
  - Coverage tolerance epsilon (default 0.01)
  - Safety margin epsilon_safety (default 0.005, used for proxy discrepancy only)

Output:
  - Source weights w* = (w_1*, ..., w_K*)
  - Prediction set function C(x) for any new test point x

Procedure:

1. COMPUTE SOURCE SCORES
   For k = 1, ..., K:
     For i = 1, ..., n_k:
       R_i^k <- s(X_i^k, Y_i^k)
     Sort R^k in ascending order.
     Compute empirical CDF F_hat_k.

2. COMPUTE TARGET REFERENCE
   If D_0 is labeled (n_0 > 0):
     For i = 1, ..., n_0:
       R_i^0 <- s(X_i^0, Y_i^0)
     Compute F_hat_0 from {R_i^0}.
     mode <- "labeled"
   Else if D_0^X is unlabeled:
     For i = 1, ..., n_0:
       P_i^0 <- f(X_i^0)  // model predictions on target
     Compute F_hat_{f,0} from {P_i^0}.
     For k = 1, ..., K:
       Compute F_hat_{f,k} from {f(X_i^k)}_{i=1}^{n_k}.
     mode <- "unlabeled"

3. ESTIMATE DISCREPANCIES
   For k = 1, ..., K:
     If mode == "labeled":
       d_k <- sup_t |F_hat_k(t) - F_hat_0(t)|   // KS statistic on scores
     Else:
       d_k <- sup_t |F_hat_{f,k}(t) - F_hat_{f,0}(t)|  // KS on predictions
       d_k <- d_k + epsilon_safety  // safety margin for proxy

4. COMPUTE FINITE-SAMPLE CORRECTIONS
   For k = 1, ..., K:
     c_k <- 1 / sqrt(2 * n_k)   // DKW correction per source
   If mode == "labeled":
     c_0 <- 1 / sqrt(2 * n_0)   // DKW correction for target estimate
     // Adjust d_k for estimation error: d_k <- d_k + c_0
     For k = 1, ..., K:
       d_k <- d_k + c_0

5. SOLVE WEIGHT OPTIMIZATION
   // Constraint budget
   budget <- epsilon  // total allowable coverage gap

   // Check feasibility: can any single source satisfy the constraint?
   For k = 1, ..., K:
     gap_k <- d_k + c_k
   If min_k gap_k > budget:
     // Infeasible: fall back to best single source
     k* <- argmin_k gap_k
     w* <- e_{k*}  (unit vector)
     coverage_warning <- "Coverage gap bounded by " + gap_{k*} + " > epsilon"
   Else:
     // Solve the constrained optimization:
     // minimize_{w in Delta_K}  sum_k w_k * Q_k(1 - alpha)
     //   s.t. sum_k w_k * (d_k + c_k) <= budget
     //        w_k >= 0, sum_k w_k = 1
     //
     // This is a linear program. Solve via standard LP solver.

     w_LP <- solve_LP(
       objective: [Q_1(1-alpha), ..., Q_K(1-alpha)],  // source-wise quantiles
       A_ub: [d_1 + c_1, ..., d_K + c_K],             // coverage constraint
       b_ub: budget,
       A_eq: [1, ..., 1],                              // simplex constraint
       b_eq: 1,
       bounds: [0, 1] for each w_k
     )

     // Refinement: evaluate exact mixture quantile for nearby weights
     w* <- refine(w_LP, {R^k}, alpha, budget, {d_k + c_k})

6. CONSTRUCT PREDICTION SETS
   // Pool scores with weights
   Pooled scores: {(R_i^k, weight w*_k / n_k)} for all i, k

   // Compute weighted quantile
   q_hat <- weighted_quantile(pooled_scores, level = 1 - alpha)

   // Apply finite-sample inflation
   // Following Barber et al. (2023), add point mass at +infty:
   q_hat <- weighted_quantile(
     pooled_scores ∪ {(+infty, 1/(N_total + 1))},
     level = 1 - alpha
   )
   where N_total = sum_k n_k

   // For a new test point x:
   C(x) = {y in Y : s(x, y) <= q_hat}

7. RETURN w*, C(.), and diagnostics:
   - Per-source discrepancies d_k
   - Per-source quantiles Q_k(1-alpha)
   - Effective sample size N_eff = 1 / sum_k (w*_k)^2 / n_k
   - Coverage gap bound: sum_k w*_k * (d_k + c_k)
   - Any warnings (infeasibility, large discrepancies)

---
Subroutine: refine(w_init, {R^k}, alpha, budget, {gap_k})
  // Grid refinement around LP solution
  // Generate perturbations of w_init on the simplex
  best_w <- w_init
  best_q <- mixture_quantile(w_init, {R^k}, 1 - alpha)
  For each perturbation w' in grid around w_init (within simplex, satisfying constraint):
    q' <- mixture_quantile(w', {R^k}, 1 - alpha)
    If q' < best_q and sum_k w'_k * gap_k <= budget:
      best_w <- w'
      best_q <- q'
  Return best_w

Subroutine: mixture_quantile(w, {R^k}, level)
  // Compute the level-quantile of the weighted mixture of empirical score distributions
  Collect all scores: S = {(R_i^k, w_k / n_k) : k=1,...,K, i=1,...,n_k}
  Sort S by score value.
  Cumulative weight <- 0
  For each (r, wt) in sorted S:
    Cumulative weight += wt / sum(all wt)  // normalize
    If Cumulative weight >= level:
      Return r
  Return +infty
```

---

## Parameters

| Parameter Name | Symbol | Default Value | Valid Range | Description |
|---|---|---|---|---|
| Significance level | alpha | 0.10 | (0, 1) | Target miscoverage rate. Prediction sets aim for 1-alpha coverage. |
| Coverage tolerance | epsilon | 0.01 | [0, alpha) | Acceptable additional coverage gap beyond alpha. Controls conservatism-efficiency tradeoff. |
| Safety margin | epsilon_safety | 0.005 | [0, 0.05] | Extra margin added to proxy discrepancies when target labels unavailable. Accounts for proxy approximation error. |
| LP solver tolerance | tol_LP | 1e-8 | (0, 1e-4] | Numerical tolerance for the linear program solver. |
| Refinement grid size | n_grid | 50 | [10, 500] | Number of perturbation directions explored in the weight refinement step. Higher = better but slower. |
| Refinement step size | delta_refine | 0.05 | (0, 0.2] | Step size for perturbations in the grid refinement around the LP solution. |
| Minimum source weight | w_min | 0.0 | [0, 1/K] | Minimum weight per source. Set > 0 to prevent complete exclusion of any source (useful for exploration/diagnostics). |
| Score function | s | abs. residual (reg.) / 1-softmax (class.) | -- | The nonconformity score function. Must be specified by user for their task. |

---

## Comparators

### 1. Split Conformal (Pooled)
**Reference:** Vovk, Gammerman, Shafer (2005). Algorithmic Learning in a Random World.
**Description:** Pool all source calibration data, compute the (1-alpha)(1+1/N)-quantile of pooled scores, use as threshold. Ignores distribution shift entirely.
**Why DISCOM-CP should outperform:** Split conformal treats all sources equally, so adversarial or irrelevant sources contaminate the quantile estimate. When sources have heterogeneous shift, the pooled quantile is biased. DISCOM-CP downweights bad sources, yielding tighter prediction sets when some sources are informative and others are not. Under no shift (all sources exchangeable with target), DISCOM-CP should match pooled conformal since all d_k -> 0 and uniform weights become optimal.

### 2. Weighted Conformal Prediction (WCP)
**Reference:** Tibshirani, Barber, Candes, Ramdas (2019). Conformal Prediction Under Covariate Shift. NeurIPS 2019.
**Description:** Estimate density ratios w(x) = p_target(x)/p_source(x) for each calibration point and compute the weighted quantile. Assumes covariate shift only (P(Y|X) invariant).
**Why DISCOM-CP should outperform:** WCP requires accurate density ratio estimation (fragile in d > 10) and assumes covariate shift only. Under label or joint shift, WCP's coverage guarantee is violated. DISCOM-CP operates on score distributions and handles any shift type. Additionally, WCP is single-source; with multiple sources, one must choose which source to apply it to, whereas DISCOM-CP optimally combines all.

### 3. Robust Conformal Prediction (RCP)
**Reference:** Cauchois, Gupta, Ali, Duchi (2024). Robust Validation: Confident Predictions Even When Distributions Shift. JASA 2024.
**Description:** Inflate the prediction set to guarantee coverage for any distribution within an f-divergence ball of the calibration distribution. The radius must be specified by the user.
**Why DISCOM-CP should outperform:** RCP is conservative because it hedges against the worst-case shift within the entire divergence ball, including adversarial shifts that may not occur. DISCOM-CP estimates the actual discrepancy rather than assuming a worst-case bound, yielding tighter prediction sets when the true shift is less severe than the worst case. Also, RCP does not leverage multi-source structure.

### 4. Adaptive Conformal Inference (ACI)
**Reference:** Gibbs & Candes (2021). Adaptive Conformal Inference Under Distribution Shift. NeurIPS 2021.
**Description:** Online method that updates alpha_t based on observed coverage. Requires sequential target labels.
**Why DISCOM-CP should outperform (in our setting):** ACI requires streaming access to target labels, which is unavailable in the batch multi-source setting we consider. ACI's coverage guarantee is asymptotic (long-run average), not finite-sample. DISCOM-CP operates in the batch setting and provides finite-sample guarantees. In settings where ACI is applicable (streaming labels), it may outperform DISCOM-CP, but this is outside our scope.

### 5. Oracle Single-Source
**Reference:** N/A (evaluation baseline).
**Description:** Use only the source with the smallest true discrepancy to the target (identified using ground truth). This is the best possible single-source method.
**Why DISCOM-CP should outperform:** Oracle single-source uses only one source's calibration data, discarding information from other useful sources. When multiple sources are moderately informative, DISCOM-CP's weighted combination yields a larger effective sample size and therefore tighter prediction sets. The advantage grows with K and when multiple sources are partially informative.

### 6. Uniform Mixture
**Reference:** N/A (evaluation baseline).
**Description:** Assign equal weight w_k = 1/K to all sources.
**Why DISCOM-CP should outperform:** Uniform mixture ignores source quality, so adversarial or irrelevant sources dilute the calibration pool. DISCOM-CP's learned weights focus on informative sources. The advantage is largest when source quality is heterogeneous (some good, some bad).

---

## Minimum Viable Evaluation

### Data Generation Procedure

1. **Feature space:** X in R^d with d = 10.
2. **Target distribution:** X_target ~ N(0, I_d). Y_target | X_target ~ N(X_target^T beta_target, sigma^2) with beta_target = (1, 1, 0, ..., 0) / sqrt(2), sigma = 1.
3. **Source distributions (K = 5):**
   - Source 1 (mild covariate shift): X ~ N(0.5 * e_1, I_d). P(Y|X) same as target.
   - Source 2 (moderate covariate shift): X ~ N(1.5 * e_1, I_d). P(Y|X) same as target.
   - Source 3 (label shift): X ~ N(0, I_d). Y | X ~ N(X^T beta_target + 0.5, sigma^2). (Shifted mean.)
   - Source 4 (joint shift): X ~ N(e_1, 1.5 * I_d). Y | X ~ N(X^T beta_target, 1.5 * sigma^2). (Both shift.)
   - Source 5 (adversarial): X ~ N(3 * e_1, 0.5 * I_d). Y | X ~ N(X^T beta_adversarial, 2 * sigma^2) with beta_adversarial = (0, 0, 1, 1, 0, ..., 0) / sqrt(2). (Completely different relationship.)
4. **Sample sizes:** n_k = 300 per source, n_0 = 50 (target labeled), n_test = 1000.
5. **Base model:** Ridge regression trained on pooled source data.
6. **Score function:** s(x, y) = |y - f(x)|.
7. **Alpha:** 0.10 (target coverage = 0.90).

### Metrics to Compute

1. **Empirical coverage:** (1/n_test) * sum_i I(Y_i^test in C(X_i^test)). Must be >= 0.88 (allowing 0.02 tolerance).
2. **Average prediction interval width:** (1/n_test) * sum_i |C(X_i^test)|.
3. **Relative efficiency:** Average width of method / Average width of oracle single-source.
4. **Source weight correlation:** Spearman correlation between learned weights w* and true source-target similarity (measured as 1 - d_TV(P_k^S, P_target^S)).
5. **Adversarial robustness:** Coverage and width when source 5 is included vs excluded.

### Success Threshold

The method passes the MVE if, across 500 replications:
- **Coverage:** Mean empirical coverage >= 0.89 (within [0.89, 0.95]).
- **Efficiency:** Mean interval width <= 1.15 x Oracle single-source interval width.
- **Source weight quality:** Spearman correlation between weights and true similarity >= 0.6.
- **Adversarial robustness:** Including the adversarial source (source 5) increases interval width by <= 5% compared to the oracle that excludes it.
- **Computational time:** < 5 seconds per replication on a single CPU core.

---

## Success Criterion

- **Primary metric:** Average prediction set size on the target domain, conditional on valid coverage (>= 1 - alpha - 0.02).
- **Minimum advantage over best comparator:** At least 5% smaller average prediction set size than the best comparator method that achieves valid coverage, averaged across all experimental scenarios.
- **Comparison target:** The method must simultaneously achieve valid coverage and produce tighter prediction sets than WCP, RCP, Pooled, and Uniform Mixture across the majority (>= 4/6) of evaluation scenarios. It should be competitive with Oracle Single-Source (within 15%).
- **Robustness requirement:** Coverage must not drop below 1 - alpha - 0.05 in any single experimental scenario across 500 replications. No catastrophic failure modes.

---

## Theoretical Properties (Expected)

### Property 1: Finite-Sample Marginal Coverage Guarantee

**Property:** DISCOM-CP provides a finite-sample lower bound on marginal coverage that depends only on the source-target score distribution discrepancies and sample sizes.

**Formal Statement:** Under Assumptions 1-2, let w* be the output of the DISCOM-CP weight optimization with coverage tolerance epsilon. For any new test point (X_{test}, Y_{test}) ~ P_target, independent of the calibration data:

  P(Y_{test} in C_alpha(X_{test})) >= 1 - alpha - epsilon

provided that the true TV distances delta_k = d_TV(P_k^S, P_target^S) satisfy delta_k <= d_k + c_0 + c_k for all k (i.e., the estimated discrepancies are conservative enough).

**Status:** CONJECTURED (proof sketch provided above in Proposition 1; the bound follows from the triangle inequality on TV distances and the DKW inequality, but a complete proof requires careful handling of the optimization over w being data-dependent, which introduces a selection bias. A union bound over a finite grid of weight vectors, combined with the LP structure, should close this gap.)

**Proof sketch:** The proof proceeds in three steps: (1) For fixed weights, the coverage bound follows from the TV distance bound between the weighted mixture and the target. (2) The DKW inequality controls the estimation error of each source CDF. (3) The optimization over w introduces dependence between the weights and the data, but since the constraint set is defined by linear inequalities and the discrepancies d_k are computed on the calibration data (not the test point), the coverage guarantee for any weight vector in the feasible set holds simultaneously. The selected w* is in this set, so the guarantee transfers.

### Property 2: Oracle Adaptivity (Source Selection Consistency)

**Property:** When one source k* has zero discrepancy to the target (d_{k*} = 0) and all other sources have bounded discrepancy, DISCOM-CP assigns weight w_{k*} -> 1 as n_k -> infinity.

**Formal Statement:** Suppose delta_{k*} = 0 and delta_k >= delta_min > 0 for all k != k*. Then for the DISCOM-CP weight vector w*:

  w*_{k*} >= 1 - O(1/sqrt(n_{k*}))

as min_k n_k -> infinity.

**Status:** CONJECTURED (follows from the consistency of the KS statistic: d_{k*} -> 0 and d_k -> delta_k > 0, so the LP assigns all weight to source k* once d_{k*} + c_{k*} < budget and the quantile Q_{k*}(1-alpha) is smallest).

### Property 3: Graceful Degradation Under Increasing Shift

**Property:** As all source-target discrepancies increase uniformly, the DISCOM-CP prediction set width increases continuously (no cliff-edge failure), and the coverage gap bound increases linearly.

**Formal Statement:** Let delta_k = delta for all k (uniform shift). Then the DISCOM-CP coverage gap bound equals delta + gamma_n, which increases linearly in delta. The prediction set width is q_hat_w(1 - alpha) where w = argmin_{w in Delta_K} sum_k w_k Q_k(1-alpha), which varies continuously with the source distributions.

**Status:** CONJECTURED (follows from continuity of quantiles and linearity of the coverage bound).

---

## Expected Strengths

1. **Shift-type agnostic:** DISCOM-CP does not require specifying or identifying the shift type (covariate, label, joint). By operating at the nonconformity score distribution level, it captures all forms of shift through a single discrepancy measure. This is a significant practical advantage: practitioners do not need to diagnose the shift mechanism before applying the method.

2. **Finite-sample coverage guarantee with interpretable slack:** Unlike asymptotic methods (Liu et al. 2024), DISCOM-CP provides a non-asymptotic coverage bound that explicitly decomposes into interpretable terms: per-source discrepancies and finite-sample corrections. The user can inspect the coverage gap bound and understand exactly how much coverage slack is consumed by each source.

3. **Automatic source selection and weighting:** The LP-based optimization naturally produces sparse weights. Sources that are too discrepant or too small are automatically excluded (assigned zero weight). This provides robustness to adversarial or irrelevant sources without requiring a separate detection step.

4. **Computational efficiency:** The main computation is K one-dimensional KS statistics (O(n_k log n_k) each) plus one linear program (O(K) variables). The total complexity is O(sum_k n_k log n_k + K^2), which is fast even for large K and n_k. No density ratio estimation, no neural network training, no cross-fitting.

5. **Post-hoc wrapper:** DISCOM-CP wraps around any pre-trained model. It only requires the model's predictions on the calibration and target data. No retraining, no access to model internals.

6. **Interpretability:** Source weights sum to 1 and have a clear interpretation: w_k is the fraction of calibration information contributed by source k. The diagnostics (per-source discrepancies, effective sample size, coverage gap bound) provide actionable insights.

---

## Expected Weaknesses

1. **Dependence on score distribution as a summary:** By reducing the multi-dimensional distribution shift to a one-dimensional score distribution discrepancy, DISCOM-CP may miss structure that could be exploited by methods operating at the covariate level. For example, under pure covariate shift with known density ratios, the WCP approach of Tibshirani et al. (2019) is optimal because it reweights individual calibration points rather than entire sources. DISCOM-CP treats each source as a monolithic block, which is suboptimal when shift is spatially varying within a source.

2. **Requires some target-domain data:** Even in the labeled variant, DISCOM-CP needs at least a small target calibration set (n_0 >= 30 recommended) to estimate discrepancies. In the fully unlabeled variant, the proxy discrepancy is less reliable. If n_0 = 0 and no target data is available at all, the method cannot estimate discrepancies and falls back to heuristics or the user must specify discrepancies manually.

3. **Potential conservatism of the TV-based bound:** The coverage guarantee via TV distance bounds can be loose, especially when the score distributions have different shapes but similar quantiles. The bound is worst-case over all measurable events, but for coverage we only care about a specific quantile. This means DISCOM-CP may produce prediction sets that are wider than necessary to achieve coverage.

4. **LP relaxation may not be tight:** The objective surrogate (sum of source quantiles weighted by w) is a linear approximation to the true mixture quantile. The mixture quantile can be strictly smaller than this weighted average of quantiles (when source score distributions have different shapes). The refinement step mitigates this, but the LP solution may not be globally optimal for the true objective.

5. **Static weights:** DISCOM-CP computes a single weight vector for all test points. In settings where source relevance varies with x (e.g., source k is informative for some regions of X but not others), point-wise weights would be more efficient. Extending to conditional weights is possible but would require additional assumptions and computation.
