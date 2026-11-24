"""Visuel 1080 × 1350 pour les réseaux, tiré des résultats versionnés (aucun chiffre saisi à la main).

python -m pipeline.social_visual      (écrit docs/social_provisionnement.png)
"""
import json
from pathlib import Path
import numpy as np
from pipeline.social_card import render,fr,ACCENT,WARN,SOFT,SAND,INK,MUTED
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports'

def main():
    mw=json.loads((R/'merz_wuthrich.json').read_text(encoding='utf-8'));c=mw['datasets']['course'];chk=mw['check_mw2008']
    sch=json.loads((R/'schnieper.json').read_text(encoding='utf-8'));b=json.loads((R/'validation.json').read_text(encoding='utf-8'))['bootstrap']['course']['summary']
    o=np.arange(len(c['origins']));res=np.array(c['reserve'])/1e6;mack=np.array(c['mack_rmsep'])/1e6;cdr=np.array(c['cdr_rmsep'])/1e6;t=c['totals']
    def cl(ax):
        ax.bar(o+1,res,color=ACCENT,width=0.7);ax.set_ylabel('M',fontsize=8);ax.set_xticks(o+1)
    def mk(ax):
        ax.bar(o+1,res,color=SOFT,width=0.7);ax.errorbar(o+1,res,yerr=mack,fmt='none',ecolor=WARN,elinewidth=1.6,capsize=2);ax.set_xticks(o+1)
    def bs(ax):
        q=[('médiane',b['median']),('Q75',b['q75']),('Q90',b['q90']),('Q95',b['q95']),('Q99',b['q99'])]
        ax.hlines(0,16,28,color=SAND,lw=6);xs=[v/1e6 for _,v in q]
        ax.scatter(xs,[0]*5,s=[30,40,50,90,60],color=[SOFT,SOFT,SOFT,WARN,SOFT],zorder=3)
        for (n,_),x_ in zip(q,xs):ax.text(x_,0.35 if n!='Q95' else -0.55,n,ha='center',fontsize=8,color=WARN if n=='Q95' else MUTED)
        ax.set_ylim(-1,1);ax.set_yticks([]);ax.set_xlabel('développement futur simulé (M)',fontsize=8);ax.spines['left'].set_visible(False)
    def sc(ax):
        i=np.arange(len(sch['by_origin']['true_ibnr']));ib=np.array(sch['by_origin']['true_ibnr']);ie=np.array(sch['by_origin']['ibner'])
        ax.bar(i+1,ib,color=ACCENT,width=0.7,label='vrais IBNR');ax.bar(i+1,ie,color=WARN,width=0.7,label='révisions (IBNER)');ax.axhline(0,color=MUTED,lw=0.6)
        ax.legend(fontsize=7,frameon=False,loc='upper left');ax.set_xticks(i+1)
    def mwf(ax):
        ax.bar(o+1-0.18,mack,width=0.36,color=SOFT,label='Mack (ultime)');ax.bar(o+1+0.18,cdr,width=0.36,color=ACCENT,label='à un an')
        ax.legend(fontsize=7,frameon=False,loc='upper left');ax.set_xticks(o+1)
    cards=[('Chain-Ladder',f'Triangle du cours reproduit :\n{fr(t["reserve"]/1e6,2)} M de développement futur',('draw',cl)),
           ('Mack',f'Erreur de prédiction : {fr(t["mack_rmsep"]/1e6,2)} M,\nsoit {fr(100*t["mack_rmsep"]/t["reserve"])} % de l’estimation',('draw',mk)),
           ('Bootstrap ODP',f'{fr(5000)} scénarios : une distribution,\npas seulement un écart-type',('draw',bs)),
           ('Schnieper','Séparer les vrais IBNR\ndes révisions des sinistres connus',('draw',sc)),
           ('Merz–Wüthrich',f'Vue à un an : {fr(100*t["one_year_share"])} % de l’incertitude\nse révèle dès l’année suivante',('draw',mwf)),
           ('Le contrôle',"Totaux de l’article d’origine\nrecalculés à moins d’une unité",('big',f'publié   {fr(chk["published"]["cdr_rmsep_total"])}\nmoteur  {fr(chk["ours"]["cdr_rmsep"],1)}',ACCENT,24))]
    render(ROOT/'docs/social_provisionnement.png','PROVISIONNEMENT · SOLVABILITÉ II','Mack dit de combien\non peut se tromper.','Pas quand on le découvrira : la vue à un an',cards,
           f'{fr(100*t["one_year_share"])} % de l’incertitude se révèle en un an',
           'Python · Streamlit  ·  github.com/kelian19/assurance-provisionnement')

if __name__=='__main__':main()
