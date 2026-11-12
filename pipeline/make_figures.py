"""Figures vectorielles de la note LaTeX, générées depuis le moteur (aucun chiffre saisi à la main).

    python -m pipeline.prepare_data
    python -m pipeline.make_figures

Sorties : docs/latex/figures/*.pdf. Le bootstrap du cours est rejoué (graine 42, 5 000
scénarios) et comparé aux statistiques publiées dans reports/calculation_course.json.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from reserving.backtest import backtest_summary, diagonal_backtest
from reserving.bootstrap import odp_bootstrap
from reserving.data import load_dataset
from reserving.mack import mack
from reserving.triangle import observed_mask

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/latex/figures'
FOREST, AMBER, MUTED, INK, SAGE = '#174F43', '#80633D', '#65756A', '#243C35', '#EDF2E6'
SEQ = ['#174F43', '#2E7D6B', '#5BA392', '#8DC2B3', '#B9DCD1']
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8.5, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
    'xtick.color': INK, 'ytick.color': INK, 'text.color': INK, 'axes.spines.top': False,
    'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#D9DFD6', 'grid.linewidth': .5,
    'axes.axisbelow': True, 'pdf.fonttype': 42, 'savefig.bbox': 'tight', 'legend.frameon': False,
})


def millions(x, _=None):
    return f'{x / 1e6:g}'


def fig_triangle(t, m):
    """Facteurs individuels vs facteur pondéré par volume, et courbes de développement."""
    c, n = t.cumulative, t.n
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.1, 2.9), gridspec_kw={'width_ratios': [1, 1.15]})
    rng = np.random.default_rng(0)
    for j in range(n - 1):
        k = n - j - 1
        ratios = c[:k, j + 1] / c[:k, j]
        a.scatter(np.full(k, j + 1) + rng.uniform(-.12, .12, k), ratios, s=14, color=SEQ[2], alpha=.85, lw=0, zorder=3)
        a.plot([j + .7, j + 1.3], [m.factors[j]] * 2, color=AMBER, lw=2.2, zorder=4)
    a.scatter([], [], s=14, color=SEQ[2], label='facteur individuel $C_{i,j+1}/C_{i,j}$')
    a.plot([], [], color=AMBER, lw=2.2, label='facteur pondéré $\\widehat f_j$')
    a.set_yscale('log')
    a.set_yticks([1, 1.5, 2, 3, 4])
    a.set_yticklabels(['1', '1,5', '2', '3', '4'])
    a.set_xticks(range(1, n))
    a.set_xlabel('âge de développement $j\\to j+1$')
    a.set_ylabel('facteur de passage')
    a.legend(loc='upper right', fontsize=7)
    a.set_title('Dispersion des facteurs', loc='left', fontsize=9, fontweight='bold', color=FOREST)
    mask = observed_mask(n)
    for i in range(n):
        ages = np.arange(1, n + 1)
        color = plt.cm.YlGn_r(.05 + .6 * i / n)
        obs = mask[i]
        b.plot(ages[obs], c[i, obs] / 1e6, color=FOREST if i == 0 else color, lw=1.3, zorder=3)
        if (~obs).any():
            start = obs.sum() - 1
            b.plot(ages[start:], m.projected[i, start:] / 1e6, color=color, lw=1.1, ls='--', zorder=2)
            b.scatter(ages[-1], m.projected[i, -1] / 1e6, s=10, color=AMBER, zorder=4)
    b.plot([], [], color=FOREST, lw=1.3, label='observé')
    b.plot([], [], color=SEQ[2], lw=1.1, ls='--', label='projeté (Chain-Ladder)')
    b.scatter([], [], s=10, color=AMBER, label='ultime $\\widehat U_i$')
    b.set_xlabel('âge de développement $j$')
    b.set_ylabel('cumul (millions, unités du cours)')
    b.set_xticks(range(1, n + 1))
    b.legend(loc='upper left', fontsize=7)
    b.set_title('Cumuls observés et projetés', loc='left', fontsize=9, fontweight='bold', color=FOREST)
    fig.tight_layout(w_pad=2)
    return fig


def fig_mack(t, m):
    """Provision par origine avec RMSEP de Mack, part processus/estimation."""
    n = t.n
    x = np.arange(2, n + 1)
    res = m.reserves[1:]
    proc, param = m.process_msep[1:], np.diag(m.parameter_covariance)[1:]
    rmsep = np.sqrt(proc + param)
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.1, 2.8), gridspec_kw={'width_ratios': [1.25, 1]})
    a.bar(x, res / 1e6, color=SEQ[1], width=.62, zorder=3, label='provision $\\widehat R_i$')
    a.errorbar(x, res / 1e6, yerr=rmsep / 1e6, fmt='none', ecolor=AMBER, elinewidth=1.4, capsize=3, zorder=4, label='$\\pm$ RMSEP Mack')
    a.set_xticks(x)
    a.set_xlabel("année d'origine $i$")
    a.set_ylabel('millions (unités du cours)')
    a.legend(loc='upper left', fontsize=7)
    a.set_title('Provision et erreur de prédiction', loc='left', fontsize=9, fontweight='bold', color=FOREST)
    share = proc / (proc + param) * 100
    b.bar(x, share, color=SEQ[0], width=.62, zorder=3, label='processus')
    b.bar(x, 100 - share, bottom=share, color=AMBER, width=.62, zorder=3, label='estimation')
    b.set_ylim(0, 100)
    b.set_xticks(x)
    b.set_xlabel("année d'origine $i$")
    b.set_ylabel('part de la MSEP (%)')
    b.legend(loc='lower center', ncol=2, fontsize=7, bbox_to_anchor=(.5, 1.0))
    fig.tight_layout(w_pad=2)
    return fig


def fig_bootstrap(t, m, boot):
    """Distribution bootstrap ODP + processus, point Chain-Ladder, lecture Mack."""
    r = boot.predictive_reserves / 1e6
    q95, q99 = np.quantile(r, [.95, .99])
    fig, ax = plt.subplots(figsize=(7.1, 2.7))
    ax.hist(r, bins=60, density=True, color=SEQ[2], edgecolor='white', linewidth=.3, zorder=3, label='bootstrap ODP + processus (5 000 scénarios)')
    grid = np.linspace(r.min(), r.max(), 400)
    mu, sd = m.total_reserve / 1e6, m.total_rmsep / 1e6
    ax.plot(grid, np.exp(-.5 * ((grid - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)), color=AMBER, lw=1.6, ls='--', zorder=4,
            label='lecture normale (moyenne CL, écart-type = RMSEP Mack) — illustrative')
    ax.axvline(mu, color=FOREST, lw=1.6, zorder=5, label=f'Chain-Ladder : {mu:.2f}')
    ax.axvline(q95, color=INK, lw=1.1, ls=':', zorder=5)
    ax.axvline(q99, color=INK, lw=1.1, ls=':', zorder=5)
    peak = ax.get_ylim()[1]
    ax.set_ylim(0, peak * 1.55)
    ax.text(q95, peak * .55, f' Q95 % = {q95:.2f}', fontsize=7.5, va='top')
    ax.text(q99, peak * .38, f' Q99 % = {q99:.2f}', fontsize=7.5, va='top')
    ax.set_xlabel('provision totale simulée (millions, unités du cours)')
    ax.set_ylabel('densité')
    ax.legend(loc='upper right', fontsize=7)
    fig.tight_layout()
    return fig


def fig_backtest(datasets):
    """Ratios observé/prédit des incréments sur les diagonales masquées."""
    labels = {'course': 'Cours', 'genins': 'GenIns', 'raa': 'RAA', 'cas': 'CAS/NAIC'}
    stops = ['arrêt le plus récent', 'arrêt précédent', 'troisième arrêt']
    colors = [FOREST, SEQ[2], AMBER]
    fig, ax = plt.subplots(figsize=(7.1, 2.35))
    width = .24
    for s in range(3):
        vals = []
        for key in labels:
            summary = backtest_summary(diagonal_backtest(datasets[key].cumulative)).set_index('hidden_diagonals')
            vals.append(float(summary.loc[s + 1, 'observed_predicted']) * 100)
        pos = np.arange(len(labels)) + (s - 1) * width
        ax.bar(pos, vals, width=width * .92, color=colors[s], zorder=3, label=stops[s])
        for p, v in zip(pos, vals):
            ax.text(p, v + 1.5, f'{v:.0f}'.replace('.', ','), ha='center', fontsize=7)
    ax.axhline(100, color=INK, lw=1, zorder=4)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels.values())
    ax.set_ylabel('observé / prédit (%)')
    ax.set_ylim(0, 140)
    ax.legend(loc='upper center', ncol=3, fontsize=7.5, bbox_to_anchor=(.5, 1.13))
    fig.tight_layout()
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    datasets = {k: load_dataset(k) for k in ('course', 'genins', 'raa', 'cas')}
    t = datasets['course']
    m = mack(t.cumulative)
    boot = odp_bootstrap(t.cumulative, simulations=5000, seed=42)
    published = json.loads((ROOT / 'reports/calculation_course.json').read_text(encoding='utf-8'))['bootstrap']['summary']
    stats = boot.summary()
    for key in ('mean', 'median', 'q95', 'q99'):
        assert abs(stats[key] - published[key]) < 1e-6 * abs(published[key]), f'Bootstrap non reproduit : {key}'
    figures = {'fig_triangle': fig_triangle(t, m), 'fig_mack': fig_mack(t, m), 'fig_bootstrap': fig_bootstrap(t, m, boot),
               'fig_backtest': fig_backtest(datasets)}
    for name, fig in figures.items():
        fig.savefig(OUT / f'{name}.pdf')
        plt.close(fig)
        print('écrit', OUT / f'{name}.pdf')


if __name__ == '__main__':
    main()
