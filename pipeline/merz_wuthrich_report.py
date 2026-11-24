"""Incertitude à un an (Merz-Wüthrich) sur tous les triangles du projet et contrôle sur le triangle de l'article.

Écrit reports/merz_wuthrich.json, reports/RESULTATS_MERZ_WUTHRICH.md et docs/latex/tables_mw.tex (tableaux de la note,
générés depuis le moteur : aucun chiffre recopié à la main).

python -m pipeline.merz_wuthrich_report
"""
import json
from pathlib import Path
import numpy as np
import chainladder as cl
from reserving.data import DATASETS,load_dataset
from reserving.merz_wuthrich import merz_wuthrich
ROOT=Path(__file__).resolve().parents[1]
# Valeurs publiées par Merz et Wüthrich (2008) pour leur triangle (jeu « mw2008 » de chainladder) : racines des msep totaux.
PUBLISHED={'cdr_rmsep_total':81080,'mack_rmsep_total':108401,'reserve_total':2237826}

def fr(x,d=0):
    t=f'{abs(x):,.{d}f}'.replace(',','\\,').replace('.','{,}')
    return ('$-$' if x<0 and float(f'{abs(x):.{d}f}')!=0 else '')+t
def macro(name,body):return f'\\newcommand{{\\{name}}}{{%\n{body}\n}}\n'

def analyse(c,origins):
    r=merz_wuthrich(c)
    return r,{'origins':list(origins),'reserve':r.reserves.tolist(),'cdr_rmsep':r.rmsep_cdr.tolist(),'mack_rmsep':np.sqrt(r.mack_msep).tolist(),
              'cdr_process_std':np.sqrt(r.process).tolist(),'cdr_estimation_std':np.sqrt(r.estimation).tolist(),
              'totals':{'reserve':float(r.reserves.sum()),'cdr_rmsep':r.total_rmsep_cdr,'mack_rmsep':r.total_rmsep_mack,'one_year_share':r.one_year_share}}

def main():
    t=cl.load_sample('mw2008');mw,mwres=analyse(t.values[0,0],[str(v) for v in t.origin])
    check={'ours':{k:mwres['totals'][k] for k in ('reserve','cdr_rmsep','mack_rmsep')},'published':PUBLISHED,
           'abs_gap':{'reserve':abs(mwres['totals']['reserve']-PUBLISHED['reserve_total']),'cdr_rmsep':abs(mwres['totals']['cdr_rmsep']-PUBLISHED['cdr_rmsep_total']),
                      'mack_rmsep':abs(mwres['totals']['mack_rmsep']-PUBLISHED['mack_rmsep_total'])}}
    assert max(check['abs_gap'].values())<1,check
    res={'method':'Merz & Wüthrich (2008), approximation linéaire ; paramètres de Mack (alpha = 1, variance finale « Mack », queue = 1)',
         'check_mw2008':check,'mw2008':mwres,'datasets':{}}
    for key in DATASETS:
        tri=load_dataset(key);_,out=analyse(tri.cumulative,tri.origins);out['name']=DATASETS[key];out['unit']=tri.unit;res['datasets'][key]=out
    res['limits']=['Horizon d’un an : ne donne pas le SCR, qui demande aussi la marge de risque et une mesure de risque (VaR 99,5 %)',
                   'msep, pas un quantile : passer à un quantile exige une hypothèse de loi','Mêmes hypothèses que Mack (indépendance des origines, pas de queue, pas d’inflation)',
                   'Approximation linéaire de Merz-Wüthrich (termes d’ordre supérieur négligés)']
    (ROOT/'reports/merz_wuthrich.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    # --- Tableaux LaTeX
    out='% Fichier généré par python -m pipeline.merz_wuthrich_report ; ne pas modifier à la main.\n'
    rows=[f"Développement futur total & {fr(PUBLISHED['reserve_total'])} & {fr(check['ours']['reserve'],1)}",
          f"$\\sqrt{{\\mathrm{{msep}}}}$ Mack (ultime) & {fr(PUBLISHED['mack_rmsep_total'])} & {fr(check['ours']['mack_rmsep'],1)}",
          f"$\\sqrt{{\\mathrm{{msep}}}}$ CDR à un an & {fr(PUBLISHED['cdr_rmsep_total'])} & {fr(check['ours']['cdr_rmsep'],1)}"]
    out+=macro('tabMWCheck','\\begin{tabular}{lrr}\\toprule\nTriangle de Merz et Wüthrich (2008) & Article & Moteur \\\\\\midrule\n'+' \\\\\n'.join(rows)+' \\\\\n\\bottomrule\\end{tabular}')
    c=res['datasets']['course'];rows=[]
    for i,o in enumerate(c['origins']):
        if c['reserve'][i]==0:continue
        rows.append(f"{o} & {fr(c['reserve'][i],1)} & {fr(c['mack_rmsep'][i],1)} & {fr(c['cdr_rmsep'][i],1)} & {fr(c['cdr_process_std'][i],1)} & {fr(c['cdr_estimation_std'][i],1)} & {fr(100*c['cdr_rmsep'][i]/c['mack_rmsep'][i],0)}\\,\\%")
    tt=c['totals'];rows.append(f"\\midrule Total & {fr(tt['reserve'],1)} & {fr(tt['mack_rmsep'],1)} & {fr(tt['cdr_rmsep'],1)} & & & {fr(100*tt['one_year_share'],0)}\\,\\%")
    out+=macro('tabMWCourse','\\begin{tabular}{lrrrrrr}\\toprule\nOrigine & Développement futur & Mack (ultime) & CDR à un an & dont processus & dont estimation & Un an / ultime \\\\\\midrule\n'+' \\\\\n'.join(rows)+' \\\\\n\\bottomrule\\end{tabular}')
    rows=[f"{d['name']} & {fr(d['totals']['reserve'],0)} & {fr(d['totals']['mack_rmsep'],0)} & {fr(d['totals']['cdr_rmsep'],0)} & {fr(100*d['totals']['one_year_share'],0)}\\,\\%" for d in res['datasets'].values()]
    out+=macro('tabMWDatasets','\\begin{tabular}{lrrrr}\\toprule\nTriangle & Développement futur & Mack (ultime) & CDR à un an & Un an / ultime \\\\\\midrule\n'+' \\\\\n'.join(rows)+' \\\\\n\\bottomrule\\end{tabular}')
    (ROOT/'docs/latex/tables_mw.tex').write_text(out,encoding='utf-8')
    # --- Rapport Markdown
    f=lambda x,d=0:f'{x:,.{d}f}'.replace(',',' ').replace('.',',')
    md=['# Incertitude à un an — Merz et Wüthrich (2008)','',
        'Erreur de prédiction du **résultat de développement (CDR)** de la prochaine année calendaire, comparée à l’erreur de Mack sur l’ultime. Paramètres de Mack identiques (facteurs pondérés, variance finale « Mack », queue = 1). Généré par `python -m pipeline.merz_wuthrich_report`.','',
        '## Contrôle sur le triangle de l’article','','| | Article | Moteur |','|---|---:|---:|',
        f"| Développement futur total | {f(PUBLISHED['reserve_total'])} | {f(check['ours']['reserve'],1)} |",
        f"| √msep Mack (ultime) | {f(PUBLISHED['mack_rmsep_total'])} | {f(check['ours']['mack_rmsep'],1)} |",
        f"| √msep CDR à un an | {f(PUBLISHED['cdr_rmsep_total'])} | {f(check['ours']['cdr_rmsep'],1)} |",'',
        'Contrôle exact supplémentaire (tests) : pour l’origine à qui il ne reste qu’une période de développement, l’incertitude à un an égale celle de Mack.','',
        '## Triangles du projet','','| Triangle | Développement futur | √msep Mack (ultime) | √msep CDR à un an | Un an / ultime |','|---|---:|---:|---:|---:|']
    md+=[f"| {d['name']} | {f(d['totals']['reserve'])} | {f(d['totals']['mack_rmsep'])} | {f(d['totals']['cdr_rmsep'])} | {f(100*d['totals']['one_year_share'])} % |" for d in res['datasets'].values()]
    md+=['','Lecture : la part « un an / ultime » indique quelle fraction de l’incertitude totale (en écart-type) se révèle dès l’année calendaire suivante. Elle est élevée quand le développement est rapide.','','## Limites','']+[f'- {x}.' for x in res['limits']]
    (ROOT/'reports/RESULTATS_MERZ_WUTHRICH.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({'check':check['abs_gap'],**{k:v['totals'] for k,v in res['datasets'].items()}},ensure_ascii=False,indent=1))

if __name__=='__main__':main()
