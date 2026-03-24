"""
Comparator methods for DISCOM-CP evaluation.

Implements all 6 comparator methods from the methodology specification:
1. Split Conformal (Pooled)
2. Weighted Conformal Prediction (WCP)
3. Robust Conformal Prediction (RCP)
4. Adaptive Conformal Inference (ACI)
5. Oracle Single-Source
6. Uniform Mixture
"""

import numpy as np
from scipy import stats


def weighted_quantile(scores, weights, level):
    """Compute weighted quantile (same as in method.py)."""
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


# ============================================================
# 1. Split Conformal (Pooled)
# ============================================================

class SplitConformal:
    """
    Pool all source calibration data, compute the (1-alpha)(1+1/N)-quantile
    of pooled scores. Ignores distribution shift entirely.

    Reference: Vovk, Gammerman, Shafer (2005).
    """

    def __init__(self, alpha=0.10):
        self.alpha = alpha
        self.quantile_threshold_ = None

    def fit(self, source_scores, **kwargs):
        pooled = np.concatenate(source_scores)
        N = len(pooled)
        # Standard conformal quantile level with finite-sample correction
        level = np.ceil((N + 1) * (1 - self.alpha)) / N
        level = min(level, 1.0)
        self.quantile_threshold_ = np.quantile(pooled, min(level, 1.0))
        return self

    def predict(self, X=None):
        return self.quantile_threshold_

    def coverage_and_width(self, test_scores):
        q = self.quantile_threshold_
        coverage = np.mean(test_scores <= q)
        avg_width = 2.0 * q
        return coverage, avg_width


# ============================================================
# 2. Weighted Conformal Prediction (WCP)
# ============================================================

class WeightedConformal:
    """
    Weighted conformal prediction using density ratios.
    Estimates density ratios p_target(x)/p_source(x) for covariate shift correction.

    Reference: Tibshirani et al. (2019).

    For multi-source: pool all sources, estimate density ratio of target vs pooled.
    Uses logistic regression for density ratio estimation.
    """

    def __init__(self, alpha=0.10):
        self.alpha = alpha
        self.quantile_threshold_ = None

    def fit(self, source_scores, source_X=None, target_X=None, **kwargs):
        """
        Parameters
        ----------
        source_scores : list of arrays
        source_X : list of arrays
            Covariates for each source.
        target_X : array
            Covariates for the target.
        """
        from sklearn.linear_model import LogisticRegression

        pooled_scores = np.concatenate(source_scores)

        if source_X is not None and target_X is not None:
            pooled_X = np.concatenate(source_X)
            n_source = len(pooled_X)
            n_target = len(target_X)

            # Binary classification: source=0, target=1
            X_all = np.vstack([pooled_X, target_X])
            y_all = np.concatenate([np.zeros(n_source), np.ones(n_target)])

            # Fit logistic regression for density ratio
            clf = LogisticRegression(max_iter=1000, C=1.0, solver='lbfgs')
            try:
                clf.fit(X_all, y_all)
                # Density ratio: p(target|x) / p(source|x) * p(source) / p(target)
                proba = clf.predict_proba(pooled_X)
                if proba.shape[1] == 2:
                    p_target = proba[:, 1]
                    p_source = proba[:, 0]
                    # Clip to avoid division by zero
                    p_source = np.clip(p_source, 1e-6, 1.0)
                    p_target = np.clip(p_target, 1e-6, 1.0)
                    ratios = (p_target / p_source) * (n_source / n_target)
                else:
                    ratios = np.ones(n_source)
            except Exception:
                ratios = np.ones(n_source)

            # Clip extreme ratios for stability
            ratios = np.clip(ratios, 0.01, 100.0)

            # Add +inf with weight for finite-sample correction
            scores_aug = np.append(pooled_scores, np.inf)
            weights_aug = np.append(ratios, 1.0)

            self.quantile_threshold_ = weighted_quantile(
                scores_aug, weights_aug, 1.0 - self.alpha
            )
        else:
            # Fallback: no covariates available, use uniform weights
            N = len(pooled_scores)
            level = np.ceil((N + 1) * (1 - self.alpha)) / N
            self.quantile_threshold_ = np.quantile(pooled_scores, min(level, 1.0))

        return self

    def predict(self, X=None):
        return self.quantile_threshold_

    def coverage_and_width(self, test_scores):
        q = self.quantile_threshold_
        coverage = np.mean(test_scores <= q)
        avg_width = 2.0 * q
        return coverage, avg_width


# ============================================================
# 3. Robust Conformal Prediction (RCP)
# ============================================================

class RobustConformal:
    """
    Inflate the prediction set to guarantee coverage for any distribution
    within a TV-distance ball of the calibration distribution.

    Reference: Cauchois et al. (2024).

    Uses the pooled calibration data and inflates the quantile level
    by the estimated maximum TV distance.
    """

    def __init__(self, alpha=0.10, rho=None):
        """
        Parameters
        ----------
        alpha : float
        rho : float or None
            Divergence ball radius. If None, estimated from data.
        """
        self.alpha = alpha
        self.rho = rho
        self.quantile_threshold_ = None

    def fit(self, source_scores, target_scores=None, **kwargs):
        pooled = np.concatenate(source_scores)
        N = len(pooled)

        if self.rho is None:
            # Estimate rho as the max KS distance between any source and target
            if target_scores is not None and len(target_scores) > 0:
                max_ks = 0.0
                for scores_k in source_scores:
                    ks_stat = stats.ks_2samp(scores_k, target_scores).statistic
                    max_ks = max(max_ks, ks_stat)
                rho = max_ks
            else:
                # Default conservative estimate
                rho = 0.1
        else:
            rho = self.rho

        # Robust quantile level: inflate by rho to hedge against worst-case
        robust_level = min((1.0 - self.alpha + rho), 1.0)
        level = np.ceil((N + 1) * robust_level) / N
        level = min(level, 1.0)

        sorted_scores = np.sort(pooled)
        idx = int(np.ceil(level * N)) - 1
        idx = min(idx, N - 1)
        self.quantile_threshold_ = sorted_scores[idx]

        return self

    def predict(self, X=None):
        return self.quantile_threshold_

    def coverage_and_width(self, test_scores):
        q = self.quantile_threshold_
        coverage = np.mean(test_scores <= q)
        avg_width = 2.0 * q
        return coverage, avg_width


# ============================================================
# 4. Adaptive Conformal Inference (ACI)
# ============================================================

class AdaptiveConformal:
    """
    Adaptive conformal inference: online alpha adjustment based on observed coverage.
    In batch setting, simulates ACI by iterating through test points sequentially.

    Reference: Gibbs & Candes (2021).

    Note: ACI requires streaming target labels, which may not be available.
    Here we simulate it with a batch of labeled target calibration data.
    """

    def __init__(self, alpha=0.10, gamma=0.005):
        """
        Parameters
        ----------
        alpha : float
        gamma : float
            Step size for alpha adjustment.
        """
        self.alpha = alpha
        self.gamma = gamma
        self.quantile_threshold_ = None

    def fit(self, source_scores, target_scores=None, **kwargs):
        pooled = np.concatenate(source_scores)

        if target_scores is not None and len(target_scores) > 0:
            # Simulate ACI: iterate through target data, adjusting alpha
            alpha_t = self.alpha
            for i in range(len(target_scores)):
                # Current quantile
                q_t = np.quantile(pooled, 1.0 - alpha_t)
                # Check coverage for this point
                covered = target_scores[i] <= q_t
                # Update alpha
                alpha_t = alpha_t + self.gamma * (self.alpha - (1.0 if not covered else 0.0))
                alpha_t = np.clip(alpha_t, 0.01, 0.5)

            # Final quantile with adapted alpha
            self.quantile_threshold_ = np.quantile(pooled, 1.0 - alpha_t)
        else:
            # No target labels: fall back to standard conformal
            N = len(pooled)
            level = np.ceil((N + 1) * (1 - self.alpha)) / N
            self.quantile_threshold_ = np.quantile(pooled, min(level, 1.0))

        return self

    def predict(self, X=None):
        return self.quantile_threshold_

    def coverage_and_width(self, test_scores):
        q = self.quantile_threshold_
        coverage = np.mean(test_scores <= q)
        avg_width = 2.0 * q
        return coverage, avg_width


# ============================================================
# 5. Oracle Single-Source
# ============================================================

class OracleSingleSource:
    """
    Use only the source with the smallest true discrepancy to the target.
    Identified using ground truth (test scores).

    This is a cheating baseline: it uses the test data to pick the best source.
    """

    def __init__(self, alpha=0.10):
        self.alpha = alpha
        self.quantile_threshold_ = None
        self.best_source_ = None

    def fit(self, source_scores, target_scores=None, **kwargs):
        """
        Pick the source with smallest KS distance to target scores,
        then use that source for conformal prediction.
        """
        K = len(source_scores)

        if target_scores is not None and len(target_scores) > 0:
            best_k = 0
            best_ks = np.inf
            for k in range(K):
                ks_stat = stats.ks_2samp(source_scores[k], target_scores).statistic
                if ks_stat < best_ks:
                    best_ks = ks_stat
                    best_k = k
        else:
            # No target data: default to largest source
            best_k = np.argmax([len(s) for s in source_scores])

        self.best_source_ = best_k
        scores_best = source_scores[best_k]
        N = len(scores_best)
        level = np.ceil((N + 1) * (1 - self.alpha)) / N
        level = min(level, 1.0)
        self.quantile_threshold_ = np.quantile(scores_best, level)

        return self

    def predict(self, X=None):
        return self.quantile_threshold_

    def coverage_and_width(self, test_scores):
        q = self.quantile_threshold_
        coverage = np.mean(test_scores <= q)
        avg_width = 2.0 * q
        return coverage, avg_width


# ============================================================
# 6. Uniform Mixture
# ============================================================

class UniformMixture:
    """
    Equal-weight combination of all sources.
    """

    def __init__(self, alpha=0.10):
        self.alpha = alpha
        self.quantile_threshold_ = None

    def fit(self, source_scores, **kwargs):
        K = len(source_scores)
        w = np.ones(K) / K

        # Compute weighted quantile of mixture
        all_scores = []
        all_weights = []
        N_total = sum(len(s) for s in source_scores)

        for k in range(K):
            n_k = len(source_scores[k])
            all_scores.append(source_scores[k])
            all_weights.append(np.full(n_k, w[k] / n_k))

        # Add +inf for finite-sample correction
        all_scores.append(np.array([np.inf]))
        all_weights.append(np.array([1.0 / (N_total + 1)]))

        all_scores = np.concatenate(all_scores)
        all_weights = np.concatenate(all_weights)

        self.quantile_threshold_ = weighted_quantile(
            all_scores, all_weights, 1.0 - self.alpha
        )
        return self

    def predict(self, X=None):
        return self.quantile_threshold_

    def coverage_and_width(self, test_scores):
        q = self.quantile_threshold_
        coverage = np.mean(test_scores <= q)
        avg_width = 2.0 * q
        return coverage, avg_width
