"""
Generate figures for the DISCOM-CP validation report.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "validated_results")


def plot_mve_results():
    """Bar chart of coverage and width for all methods."""
    df = pd.read_csv(os.path.join(RESULTS_DIR, "mve_results.csv"))

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    methods = df['method'].tolist()
    x = np.arange(len(methods))

    # Coverage plot
    ax = axes[0]
    colors = ['#2196F3' if m == 'DISCOM-CP' else '#90CAF9' for m in methods]
    bars = ax.bar(x, df['mean_coverage'], yerr=df['std_coverage']/np.sqrt(500)*1.96,
                  color=colors, edgecolor='black', linewidth=0.5, capsize=3)
    ax.axhline(y=0.90, color='red', linestyle='--', linewidth=1, label='Target (1-alpha=0.90)')
    ax.axhline(y=0.88, color='red', linestyle=':', linewidth=0.8, label='Min valid (0.88)')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Mean Coverage')
    ax.set_title('MVE: Coverage (500 reps)')
    ax.legend(fontsize=8)
    ax.set_ylim(0.85, 1.02)

    # Width plot
    ax = axes[1]
    # Filter out inf widths
    widths = df['mean_width'].replace([np.inf, -np.inf], np.nan)
    colors = ['#4CAF50' if m == 'DISCOM-CP' else '#A5D6A7' for m in methods]
    bars = ax.bar(x, widths, yerr=df['std_width']/np.sqrt(500)*1.96,
                  color=colors, edgecolor='black', linewidth=0.5, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Mean Interval Width')
    ax.set_title('MVE: Interval Width (500 reps)')

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "mve_comparison.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved mve_comparison.png")


def plot_stress_tests():
    """Heatmap of coverage across stress test scenarios."""
    df = pd.read_csv(os.path.join(RESULTS_DIR, "stress_tests_combined.csv"))

    scenarios = df['scenario'].unique()
    methods = df['method'].unique()

    # Coverage heatmap
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # Coverage
    cov_matrix = np.zeros((len(scenarios), len(methods)))
    for i, sc in enumerate(scenarios):
        for j, m in enumerate(methods):
            row = df[(df['scenario'] == sc) & (df['method'] == m)]
            if len(row) > 0:
                cov_matrix[i, j] = row['mean_coverage'].values[0]

    ax = axes[0]
    im = ax.imshow(cov_matrix, cmap='RdYlGn', vmin=0.85, vmax=1.0, aspect='auto')
    ax.set_xticks(np.arange(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(np.arange(len(scenarios)))
    ax.set_yticklabels(scenarios, fontsize=8)
    ax.set_title('Stress Tests: Mean Coverage')
    for i in range(len(scenarios)):
        for j in range(len(methods)):
            ax.text(j, i, f'{cov_matrix[i,j]:.3f}', ha='center', va='center',
                    fontsize=7, color='black' if cov_matrix[i,j] > 0.92 else 'white')
    fig.colorbar(im, ax=ax, shrink=0.8)

    # Width
    width_matrix = np.zeros((len(scenarios), len(methods)))
    for i, sc in enumerate(scenarios):
        for j, m in enumerate(methods):
            row = df[(df['scenario'] == sc) & (df['method'] == m)]
            if len(row) > 0:
                val = row['mean_width'].values[0]
                width_matrix[i, j] = val if np.isfinite(val) else 20.0

    ax = axes[1]
    im = ax.imshow(width_matrix, cmap='YlOrRd_r', aspect='auto')
    ax.set_xticks(np.arange(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(np.arange(len(scenarios)))
    ax.set_yticklabels(scenarios, fontsize=8)
    ax.set_title('Stress Tests: Mean Width')
    for i in range(len(scenarios)):
        for j in range(len(methods)):
            val = width_matrix[i, j]
            ax.text(j, i, f'{val:.1f}', ha='center', va='center',
                    fontsize=7, color='black' if val < 10 else 'white')
    fig.colorbar(im, ax=ax, shrink=0.8)

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "stress_tests.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved stress_tests.png")


def plot_weight_analysis():
    """Plot DISCOM-CP source weights across replications."""
    # Re-run a quick analysis to get weight distribution
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from method import DISCOMCP, compute_ks_statistic
    from run_validation import generate_mve_data
    from sklearn.linear_model import Ridge

    weights_all = []
    discs_all = []

    for rep in range(200):
        seed = 42 + rep
        data = generate_mve_data(seed)
        K = len(data['source_X'])

        X_train = np.concatenate(data['source_X'])
        Y_train = np.concatenate(data['source_Y'])
        model = Ridge(alpha=1.0)
        model.fit(X_train, Y_train)

        source_scores = [np.abs(data['source_Y'][k] - model.predict(data['source_X'][k]))
                         for k in range(K)]
        target_scores = np.abs(data['target_Y'] - model.predict(data['target_X']))

        discom = DISCOMCP(alpha=0.10)
        discom.fit(source_scores, target_scores=target_scores)
        weights_all.append(discom.weights_)
        discs_all.append(discom.source_discrepancies_)

    weights_all = np.array(weights_all)
    discs_all = np.array(discs_all)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Weight distribution
    ax = axes[0]
    labels = ['S1 (mild cov)', 'S2 (mod cov)', 'S3 (label)', 'S4 (joint)', 'S5 (adv)']
    bp = ax.boxplot([weights_all[:, k] for k in range(5)], labels=labels,
                    patch_artist=True, medianprops=dict(color='red'))
    colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    ax.set_ylabel('Weight')
    ax.set_title('DISCOM-CP Source Weights (200 reps)')
    ax.tick_params(axis='x', rotation=20)

    # Discrepancy vs weight scatter
    ax = axes[1]
    mean_w = np.mean(weights_all, axis=0)
    mean_d = np.mean(discs_all, axis=0)
    ax.scatter(mean_d, mean_w, s=100, c=colors, edgecolors='black', zorder=5)
    for k, (d, w) in enumerate(zip(mean_d, mean_w)):
        ax.annotate(f'S{k+1}', (d, w), textcoords="offset points",
                    xytext=(5, 5), fontsize=9)
    ax.set_xlabel('Mean KS Discrepancy')
    ax.set_ylabel('Mean Weight')
    ax.set_title('Discrepancy vs Weight')

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "weight_analysis.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved weight_analysis.png")


if __name__ == "__main__":
    plot_mve_results()
    plot_stress_tests()
    plot_weight_analysis()
    print("All figures generated.")
