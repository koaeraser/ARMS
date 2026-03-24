"""
DISCOM-CP: Discrepancy-Guided Multi-Source Conformal Prediction

Implements the DISCOM-CP methodology as specified in the methodology specification.

Iteration 6: Addresses coverage floor and adversarial robustness:
  1. Use discrepancy-penalized weight optimization (Lagrangian formulation).
  2. Compute the weighted mixture quantile at a conformal-corrected level.
  3. Add a coverage safety net: take the max of (weighted quantile, target quantile)
     where the target quantile uses the small labeled target set directly.
     This ensures coverage >= the single-source conformal guarantee on the target.
  4. Exclude sources with extreme discrepancies (> threshold) from the optimization
     to improve robustness.
"""

import numpy as np
from scipy import stats
from scipy.optimize import linprog


def compute_ks_statistic(scores_a, scores_b):
    """Compute two-sample KS statistic."""
    result = stats.ks_2samp(scores_a, scores_b)
    return result.statistic


def weighted_quantile(scores, weights, level):
    """Compute the weighted quantile of scores."""
    scores = np.asarray(scores, dtype=float)
    weights = np.asarray(weights, dtype=float)

    order = np.argsort(scores)
    sorted_scores = scores[order]
    sorted_weights = weights[order]

    total_weight = sorted_weights.sum()
    if total_weight <= 0:
        return np.inf
    sorted_weights = sorted_weights / total_weight
    cum_weights = np.cumsum(sorted_weights)

    idx = np.searchsorted(cum_weights, level)
    if idx >= len(sorted_scores):
        return np.inf
    return sorted_scores[idx]


def mixture_quantile(w, source_scores, level):
    """Compute quantile of weighted mixture of source score distributions."""
    all_scores = []
    all_weights = []
    for k, scores_k in enumerate(source_scores):
        n_k = len(scores_k)
        if n_k == 0 or w[k] <= 0:
            continue
        all_scores.append(scores_k)
        all_weights.append(np.full(n_k, w[k] / n_k))

    if len(all_scores) == 0:
        return np.inf

    all_scores = np.concatenate(all_scores)
    all_weights = np.concatenate(all_weights)
    return weighted_quantile(all_scores, all_weights, level)


def solve_weight_lp(source_quantiles, discrepancies, budget, K):
    """
    Solve the LP relaxation:
        minimize   sum_k w_k * Q_k(1-alpha)
        subject to sum_k w_k * d_k <= budget
                   sum_k w_k = 1, w_k >= 0
    """
    c = source_quantiles.copy()
    A_ub = discrepancies.reshape(1, -1)
    b_ub = np.array([budget])
    A_eq = np.ones((1, K))
    b_eq = np.array([1.0])
    bounds = [(0.0, 1.0) for _ in range(K)]

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                     bounds=bounds, method='highs')

    if result.success:
        w = result.x
        w = np.maximum(w, 0.0)
        w = w / w.sum()
        return w, True
    else:
        return np.ones(K) / K, False


def optimize_weights(source_scores, source_quantiles, discrepancies, alpha, K,
                     n_ks, n_grid=100, delta_refine=0.1):
    """
    Find optimal source weights via Lagrangian-style optimization.

    The selection criterion evaluates each candidate weight vector at the
    conformal quantile level, penalizing weighted discrepancy.

    Returns
    -------
    best_w : array, shape (K,)
    """
    rng = np.random.RandomState(0)
    level = 1.0 - alpha

    candidates = []

    # Strategy 1: LP with various discrepancy budgets
    min_d = np.min(discrepancies)
    for budget_mult in [1.0, 1.5, 2.0, 3.0, 5.0, 10.0]:
        budget = min_d * budget_mult
        w, success = solve_weight_lp(source_quantiles, discrepancies, budget, K)
        if success:
            candidates.append(w)

    # Strategy 2: Lagrangian single-source solutions
    for lam in [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0]:
        penalized = source_quantiles + lam * discrepancies
        k_star = np.argmin(penalized)
        w = np.zeros(K)
        w[k_star] = 1.0
        candidates.append(w)

    # Strategy 3: Single-source candidates
    for k in range(K):
        w = np.zeros(K)
        w[k] = 1.0
        candidates.append(w)

    # Strategy 4: Convex combinations
    if K > 1:
        order = np.argsort(discrepancies)
        for i in range(min(K, 4)):
            for j in range(i + 1, min(K, 5)):
                k1, k2 = order[i], order[j]
                for t in np.linspace(0.1, 0.9, 9):
                    w = np.zeros(K)
                    w[k1] = t
                    w[k2] = 1 - t
                    candidates.append(w)

        # 3-source combos
        for i in range(min(K, 3)):
            for j in range(i + 1, min(K, 4)):
                for m in range(j + 1, min(K, 5)):
                    k1, k2, k3 = order[i], order[j], order[m]
                    for t1 in [0.2, 0.4, 0.6]:
                        for t2 in [0.2, 0.3]:
                            if t1 + t2 < 1.0:
                                w = np.zeros(K)
                                w[k1] = t1
                                w[k2] = t2
                                w[k3] = 1 - t1 - t2
                                candidates.append(w)

    # Strategy 5: Random perturbations
    for idx in range(min(5, len(candidates))):
        base_w = candidates[idx]
        for _ in range(n_grid // 5):
            perturbation = rng.randn(K) * delta_refine
            w_cand = base_w + perturbation
            w_cand = np.maximum(w_cand, 0.0)
            w_sum = w_cand.sum()
            if w_sum > 0:
                w_cand = w_cand / w_sum
                candidates.append(w_cand)

    # Strategy 6: Special candidates
    candidates.append(np.ones(K) / K)
    inv_d = 1.0 / (discrepancies + 1e-10)
    candidates.append(inv_d / inv_d.sum())

    # Evaluate: minimize mixture quantile with discrepancy penalty
    scale = np.median(source_quantiles) if len(source_quantiles) > 0 else 1.0
    lam_penalty = scale * 0.5

    best_w = None
    best_obj = np.inf

    for w in candidates:
        q = mixture_quantile(w, source_scores, level)
        disc_penalty = np.dot(w, discrepancies) * lam_penalty
        obj = q + disc_penalty
        if obj < best_obj:
            best_obj = obj
            best_w = w.copy()

    if best_w is None:
        k_star = np.argmin(discrepancies)
        best_w = np.zeros(K)
        best_w[k_star] = 1.0

    return best_w


class DISCOMCP:
    """
    Discrepancy-Guided Multi-Source Conformal Prediction.

    Parameters
    ----------
    alpha : float
        Significance level (default 0.10).
    epsilon_safety : float
        Safety margin for proxy discrepancy (default 0.005).
    n_grid : int
        Refinement grid size (default 100).
    delta_refine : float
        Refinement step size (default 0.1).
    disc_threshold : float
        Discard sources with KS discrepancy above this threshold (default 0.3).
    """

    def __init__(self, alpha=0.10, epsilon_safety=0.005,
                 n_grid=100, delta_refine=0.1, disc_threshold=0.3):
        self.alpha = alpha
        self.epsilon_safety = epsilon_safety
        self.n_grid = n_grid
        self.delta_refine = delta_refine
        self.disc_threshold = disc_threshold

        self.weights_ = None
        self.quantile_threshold_ = None
        self.source_discrepancies_ = None
        self.source_quantiles_ = None
        self.diagnostics_ = {}

    def fit(self, source_scores, target_scores=None, target_predictions=None,
            source_predictions=None):
        """
        Fit DISCOM-CP: estimate discrepancies and optimize source weights.
        """
        K = len(source_scores)
        n_ks = [len(s) for s in source_scores]

        # Step 1: Compute source-wise quantiles
        source_quantiles = np.array([
            np.quantile(scores_k, 1.0 - self.alpha)
            for scores_k in source_scores
        ])
        self.source_quantiles_ = source_quantiles

        # Step 2: Estimate discrepancies
        if target_scores is not None:
            mode = "labeled"
            discrepancies = np.array([
                compute_ks_statistic(scores_k, target_scores)
                for scores_k in source_scores
            ])
        elif target_predictions is not None and source_predictions is not None:
            mode = "unlabeled"
            discrepancies = np.array([
                compute_ks_statistic(source_predictions[k], target_predictions)
                for k in range(K)
            ])
            discrepancies = discrepancies + self.epsilon_safety
        else:
            raise ValueError("Must provide either target_scores (labeled) "
                             "or target_predictions + source_predictions (unlabeled).")

        self.source_discrepancies_ = discrepancies

        # Step 3: Filter out highly discrepant sources
        # Sources with discrepancy above threshold are excluded from optimization
        active_mask = discrepancies <= self.disc_threshold
        if not np.any(active_mask):
            # All sources are above threshold - use the best one
            active_mask = np.zeros(K, dtype=bool)
            active_mask[np.argmin(discrepancies)] = True

        # Step 4: Optimize weights
        if K == 1 or np.sum(active_mask) == 1:
            weights = np.zeros(K)
            weights[np.argmin(discrepancies)] = 1.0
        else:
            # Work with only active sources
            active_idx = np.where(active_mask)[0]
            K_active = len(active_idx)
            active_scores = [source_scores[k] for k in active_idx]
            active_quantiles = source_quantiles[active_idx]
            active_disc = discrepancies[active_idx]
            active_nks = [n_ks[k] for k in active_idx]

            w_active = optimize_weights(
                active_scores, active_quantiles, active_disc,
                self.alpha, K_active, active_nks,
                n_grid=self.n_grid,
                delta_refine=self.delta_refine
            )

            # Map back to full weight vector
            weights = np.zeros(K)
            for i, k in enumerate(active_idx):
                weights[k] = w_active[i]

        self.weights_ = weights

        # Step 5: Compute prediction threshold
        # Pool source scores with optimized weights
        all_scores = []
        all_weights = []

        for k in range(K):
            n_k = n_ks[k]
            if weights[k] <= 0:
                continue
            all_scores.append(source_scores[k])
            all_weights.append(np.full(n_k, weights[k] / n_k))

        all_scores_arr = np.concatenate(all_scores)
        all_weights_arr = np.concatenate(all_weights)

        # Effective sample size
        N_eff_num = (np.sum(all_weights_arr))**2
        N_eff_den = np.sum(all_weights_arr**2)
        N_eff = N_eff_num / N_eff_den if N_eff_den > 0 else 1.0

        # Conformal quantile level (standard +1/(N+1) correction)
        conformal_level = np.ceil((N_eff + 1) * (1 - self.alpha)) / N_eff
        conformal_level = min(conformal_level, 1.0 - 1e-10)

        q_mixture = weighted_quantile(all_scores_arr, all_weights_arr, conformal_level)

        # Coverage safety net: use target calibration data if available.
        # The target quantile provides a direct (noisy but unbiased) estimate
        # of what the threshold should be. We take the max of the mixture
        # quantile and the target quantile to ensure we never undercover
        # more than standard conformal on the target data alone would.
        if target_scores is not None and len(target_scores) >= 10:
            n_0 = len(target_scores)
            target_level = np.ceil((n_0 + 1) * (1 - self.alpha)) / n_0
            target_level = min(target_level, 1.0 - 1e-10)
            q_target = np.quantile(target_scores, target_level)

            # Final threshold: max of mixture and target quantile (no discount).
            # This guarantees coverage >= min(conformal_on_mixture, conformal_on_target).
            self.quantile_threshold_ = max(q_mixture, q_target)
        else:
            self.quantile_threshold_ = q_mixture

        # Diagnostics
        self.diagnostics_['mode'] = mode
        self.diagnostics_['discrepancies'] = discrepancies
        self.diagnostics_['coverage_gap_bound'] = np.dot(weights, discrepancies)
        self.diagnostics_['effective_sample_size'] = N_eff
        self.diagnostics_['conformal_level'] = conformal_level
        self.diagnostics_['q_mixture'] = q_mixture
        self.diagnostics_['feasible'] = True
        if target_scores is not None and len(target_scores) >= 10:
            self.diagnostics_['q_target'] = q_target

        return self

    def predict(self, X=None):
        """Return the prediction set threshold."""
        if self.quantile_threshold_ is None:
            raise ValueError("Must call fit() before predict().")
        return self.quantile_threshold_

    def coverage_and_width(self, test_scores):
        """Evaluate coverage and interval width on test data."""
        q = self.quantile_threshold_
        coverage = np.mean(test_scores <= q)
        avg_width = 2.0 * q
        return coverage, avg_width
