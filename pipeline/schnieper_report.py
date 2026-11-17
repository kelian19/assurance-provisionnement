"""Rejoue Schnieper sur l'exemple 5.4 du cours et écrit résultats, rapport et tableaux LaTeX.

Les tableaux de la note (docs/latex/tables_schnieper.tex) sont générés depuis le moteur :
aucun chiffre n'est recopié à la main. Le bootstrap est rejoué (5 000 scénarios, graine 42).
"""
import json
from pathlib import Path
import numpy as np
from reserving.data import load_schnieper
from reserving.mack import mack
from reserving.schnieper import schnieper,schnieper_bootstrap
from reserving.triangle import observed_mask
ROOT=Path(__file__).resolve().parents[1]
SIMULATIONS=5000;SEED=42
# Valeurs imprimées dans le cours (exemples 5.4 et 5.6), pour mesurer l'écart de reproduction.
COURSE={'lambda_e3':[0.450,1.059,1.396,1.150,1.181,0.492,0.499],'delta':[-0.359,0.072,-0.048,-0.054,0.070,0.033],
        'sigma':[0.0538,0.0737,0.1089,0.0795,0.0560,0.0575,0.0],'tau':[0.3874,1.2686,1.1768,3.4603,0.3034,0.0],
        'reserves':[0,4.4,4.8,32.9,60.3,77.2,104.3],'total':283.9,'mack_total':464.2}

def fr(x,d):
    t=f'{abs(x):.{d}f}'.replace('.','{,}')
    return ('$-$' if x<0 and float(f'{abs(x):.{d}f}')!=0 else '')+t
def m(x,d):
    t=f'{abs(x):.{d}f}'.replace('.','{,}')
    return ('-' if x<0 and float(f'{abs(x):.{d}f}')!=0 else '')+t
def grid(matrix,d,n,header='j'):
    cols=' '.join(f'& {j+1}' for j in range(n))
    rows=[]
    for i in range(n):
        cells=' '.join('& '+(fr(matrix[i,j],d) if np.isfinite(matrix[i,j]) else '') for j in range(n))
        rows.append(f'{i+1} {cells} \\\\')
    return '\\begin{tabular}{l'+'r'*n+'}\\toprule\n$i\\backslash j$ '+cols+' \\\\\\midrule\n'+'\n'.join(rows)+'\n\\bottomrule\\end{tabular}'
def macro(name,body):return f'\\newcommand{{\\{name}}}{{%\n{body}\n}}\n'

def main():
    data=load_schnieper();r=schnieper(data);n=data.n;mk=mack(data.cumulative);E=data.exposure
    boot=schnieper_bootstrap(data,simulations=SIMULATIONS,seed=SEED);b=boot.summary();d=boot.diagnostics;R=r.total_reserve
    future=~observed_mask(n)
    # --- Écarts de reproduction par rapport aux valeurs imprimées du cours
    gaps={'lambda':float(np.max(np.abs(np.round(r.lam*1e3,3)-COURSE['lambda_e3']))),'delta':float(np.max(np.abs(np.round(r.delta,3)-COURSE['delta']))),
          'sigma':float(np.max(np.abs(np.round(np.sqrt(r.sigma2),4)-COURSE['sigma']))),'tau':float(np.max(np.abs(np.round(np.sqrt(r.tau2),4)-COURSE['tau']))),
          'reserves':float(np.max(np.abs(np.round(r.reserves,1)-COURSE['reserves']))),'total':abs(round(R,1)-COURSE['total']),'mack_total':abs(round(mk.total_reserve,1)-COURSE['mack_total'])}
    assert max(gaps.values())<1e-9,gaps
    report={'engine':'reserving-v1 + schnieper','source':data.source,'simulations':SIMULATIONS,'seed':SEED,
        'parameters':{'lambda':r.lam.tolist(),'delta':r.delta.tolist(),'sigma2':r.sigma2.tolist(),'tau2':r.tau2.tolist()},
        'by_origin':{'latest':r.latest.tolist(),'ultimate':r.ultimate.tolist(),'reserve':r.reserves.tolist(),'true_ibnr':r.ibnr.tolist(),'ibner':r.ibner.tolist(),'process_std':np.sqrt(r.process_variance).tolist(),'mack_reserve':mk.reserves.tolist()},
        'totals':{'reserve':R,'true_ibnr':float(r.ibnr.sum()),'ibner':float(r.ibner.sum()),'process_std':r.total_process_std,'mack_reserve':mk.total_reserve},
        'bootstrap':{'summary':b,'diagnostics':d},'reproduction_gaps_vs_printed_course_values':gaps,'diagnostics':r.diagnostics,
        'limits':['Variance analytique : processus seul, paramètres supposés connus','σ²_n et τ²_{n-1} fixés à 0 par convention du cours','Un seul triangle (7 années), données pédagogiques','Pas d’inflation, de facteur de queue ni d’actualisation','Plancher à zéro du bootstrap conservé du cours, avec biais haussier documenté','Valeurs imprimées de la Table 6 du cours non reproduites : jeu de données ambigu dans le texte du cours']}
    (ROOT/'reports/schnieper.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    # --- Tableaux LaTeX
    out='% Fichier généré par python -m pipeline.schnieper_report ; ne pas modifier à la main.\n'
    ecol=' & '.join(fr(v,0) for v in E)
    out+=macro('tabSchnieperExposition','\\begin{tabular}{l'+'r'*n+'}\\toprule\n$i$ & '+' & '.join(str(i+1) for i in range(n))+' \\\\\\midrule\n$E_i$ & '+ecol+' \\\\\\bottomrule\\end{tabular}')
    out+=macro('tabSchnieperN',grid(data.new_claims,1,n));out+=macro('tabSchnieperD',grid(data.revisions,1,n));out+=macro('tabSchnieperC',grid(r.cumulative,1,n))
    p=['\\begin{tabular}{crrrrrr}\\toprule','$j$ & $\\widehat\\lambda_j\\times10^3$ & $\\widehat\\sigma_j$ & $\\widehat\\delta_j$ & $\\widehat\\tau_j$ & obs.\\ $N$ & obs.\\ $D$ \\\\\\midrule']
    for j in range(n):
        dl=fr(r.delta[j],4) if j<n-1 else '--';tu=fr(np.sqrt(r.tau2[j]),4) if j<n-1 else '--';od=str(n-1-j) if j<n-1 else '--'
        p.append(f'{j+1} & {fr(r.lam[j]*1e3,3)} & {fr(np.sqrt(r.sigma2[j]),4)} & {dl} & {tu} & {n-j} & {od} \\\\')
    out+=macro('tabSchnieperParams','\n'.join(p)+'\n\\bottomrule\\end{tabular}')
    proj=np.where(future,r.projected,np.nan)
    out+=macro('tabSchnieperProjection',grid(proj,1,n))
    rows=['\\begin{tabular}{lrrrrrr}\\toprule','Origine & $\\widehat C_{i,n}$ & $\\widehat R_i$ & dont IBNR & dont IBNER & $\\sqrt{\\Var}$ proc. & Mack $\\widehat R_i$ \\\\\\midrule']
    for i in range(n):
        rows.append(f'{i+1} & {fr(r.ultimate[i],1)} & {fr(r.reserves[i],1)} & {fr(r.ibnr[i],1)} & {fr(r.ibner[i],1)} & {fr(np.sqrt(r.process_variance[i]),1)} & {fr(mk.reserves[i],1)} \\\\')
    rows.append('\\midrule')
    rows.append(f'Total & {fr(r.ultimate.sum(),1)} & \\textbf{{{fr(R,1)}}} & {fr(r.ibnr.sum(),1)} & {fr(r.ibner.sum(),1)} & {fr(r.total_process_std,1)} & {fr(mk.total_reserve,1)} \\\\')
    out+=macro('tabSchnieperReserves','\n'.join(rows)+'\n\\bottomrule\\end{tabular}')
    rows=['\\begin{tabular}{lrr}\\toprule','Indicateur & Montant & \\% de l\'estimation \\\\\\midrule']
    for label,val in [('Estimation Schnieper (déterministe)',R),('Moyenne des scénarios',b['mean']),('Médiane',b['median']),('Écart-type',b['std']),('dont paramètres seuls',b['parameter_only_std']),
                      ('Écart-type de processus (formule)',r.total_process_std),('Quantile 90\\,\\%',b['q90']),('Quantile 95\\,\\%',b['q95']),('Quantile 99\\,\\%',b['q99']),('Quantile 99,5\\,\\%',b['q995'])]:
        rows.append(f'{label} & {fr(val,1)} & {fr(100*val/R,1)} \\\\')
    rows.append(f'Erreur Monte-Carlo de la moyenne & {fr(b["mean_monte_carlo_se"],2)} & {fr(100*b["mean_monte_carlo_se"]/R,2)} \\\\')
    rows.append(f'Scénarios avec plancher à 0 & {d["floored_simulations"]} sur {SIMULATIONS} & {fr(100*d["floored_rate"],2)} \\\\')
    out+=macro('tabSchnieperBootstrap','\n'.join(rows)+'\n\\bottomrule\\end{tabular}')
    # --- Exemple pas à pas : origine 4 (indices 1-based du cours)
    i=3;k=n-1-i;lines=[]
    prev=f'C_{{{i+1},{k+1}}}={m(r.cumulative[i,k],1)}'
    lines.append(prev)
    for j in range(k+1,n):
        left=f'\\widehat C_{{{i+1},{j+1}}}&=\\widehat\\lambda_{{{j+1}}}E_{{{i+1}}}+(1-\\widehat\\delta_{{{j}}})\\,\\widehat C_{{{i+1},{j}}}'
        pv=r.projected[i,j-1]
        num=f'={m(r.lam[j],6)}\\times {m(E[i],0)}+\\bigl(1-({m(r.delta[j-1],4)})\\bigr)\\times {m(pv,1)}={m(r.projected[i,j],1)}'
        lines.append(left+num)
    body='\\begin{align*}\n'+' \\\\\n'.join(l if idx else l.replace('=','&=',1) for idx,l in enumerate(lines))+f' \\\\\n\\widehat R_{{{i+1}}}&=\\widehat C_{{{i+1},{n}}}-C_{{{i+1},{k+1}}}={m(r.ultimate[i],1)}-{m(r.cumulative[i,k],1)}={m(r.reserves[i],1)}\n\\end{{align*}}'
    ex=body.replace('\\begin{align*}','\\begin{align*}',1)
    out+=macro('tabSchnieperExemple',ex)
    # --- Contrôles contre le cours
    chk=['\\begin{tabular}{lrr}\\toprule','Quantité (arrondie comme le cours) & Écart maximal & Statut \\\\\\midrule']
    for label,key in [('$\\widehat\\lambda_j\\times10^3$, 7 valeurs','lambda'),('$\\widehat\\delta_j$, 6 valeurs','delta'),('$\\widehat\\sigma_j$, 7 valeurs','sigma'),('$\\widehat\\tau_j$, 6 valeurs','tau'),
                      ('$\\widehat R_i$, 7 années','reserves'),('Provision totale (283,9)','total'),('Mack sur le même triangle (464,2)','mack_total')]:
        chk.append(f'{label} & {gaps[key]:.0e} & identique \\\\'.replace('e+00','').replace('0e+00','0'))
    out+=macro('tabSchnieperControles','\n'.join(chk)+'\n\\bottomrule\\end{tabular}')
    (ROOT/'docs/latex/tables_schnieper.tex').write_text(out,encoding='utf-8')
    md=f'''# Résultats Schnieper — exemple 5.4 du cours

Données : {data.source} (unités du cours, non précisées). Modèle et estimateurs : cours de N. Baradel §5, bootstrap §6.4.1.

| Année | Dernier cumul | Ultime | Provision | dont vrais IBNR | dont IBNER | Écart-type de processus | Mack |
|---|---:|---:|---:|---:|---:|---:|---:|
'''+'\n'.join(f'| {i+1} | {r.latest[i]:.1f} | {r.ultimate[i]:.1f} | {r.reserves[i]:.1f} | {r.ibnr[i]:.1f} | {r.ibner[i]:.1f} | {np.sqrt(r.process_variance[i]):.1f} | {mk.reserves[i]:.1f} |' for i in range(n))+f'''
| **Total** | | {r.ultimate.sum():.1f} | **{R:.1f}** | {r.ibnr.sum():.1f} | {r.ibner.sum():.1f} | {r.total_process_std:.1f} | {mk.total_reserve:.1f} |

Reproduction des valeurs imprimées dans le cours : λ, δ, σ, τ, ultimes, provisions par année, total 283,9 et Mack 464,2 sont identiques à l'arrondi du cours (écart maximal {max(gaps.values()):.0e}). L'exemple 5.6 (nombres au-dessus d'un seuil, total 7,97) est testé dans `tests/test_schnieper.py`.

## Bootstrap non paramétrique ({SIMULATIONS} scénarios, graine {SEED})
Moyenne {b['mean']:.1f} ({100*b['mean']/R:.1f} % de l'estimation), médiane {b['median']:.1f}, écart-type {b['std']:.1f} (paramètres seuls {b['parameter_only_std']:.1f}), Q95 {b['q95']:.1f}, Q99 {b['q99']:.1f}. {d['floored_simulations']} scénarios sur {SIMULATIONS} ({100*d['floored_rate']:.2f} %) contiennent un cumul négatif ramené à zéro, comme le `pmax` du cours ; ils sont conservés. L'écart-type du bootstrap est cohérent avec la somme quadratique de l'erreur de paramètres seule et de la variance de processus analytique.

## Limites
- Variance analytique : processus seul. σ²_n = τ²_{{n−1}} = 0 par convention du cours : l'année 2 (une seule cellule future) a une variance nulle, ce qui sous-estime son risque.
- Un seul triangle pédagogique de 7 années ; aucune validation rétrospective possible sans autre jeu N/D/E.
- La Table 6 du cours (écart-type relatif ≈ 43 %) n'est pas reproduite : le texte du cours la rattache à un jeu de données ambigu (§5.6 ou §5.4). Notre bootstrap sur l'exemple 5.4 donne {100*b['std']/R:.0f} %.
- Aucune inflation, aucun facteur de queue, aucune actualisation ; pas de SCR à un an.
'''
    (ROOT/'reports/RESULTATS_SCHNIEPER.md').write_text(md,encoding='utf-8')
    print("Rapport Schnieper écrit : reports/schnieper.json, reports/RESULTATS_SCHNIEPER.md, docs/latex/tables_schnieper.tex")

if __name__=='__main__':main()
