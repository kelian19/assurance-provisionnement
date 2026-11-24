"""Incertitude à un an : erreur de prédiction du résultat de développement (CDR) de Merz et Wüthrich (2008).

Mack mesure l'incertitude sur la charge ultime (tout le run-off). Pour Solvabilité II, on veut l'incertitude sur ce qui
sera révélé en **un an** : le CDR de l'année calendaire I+1, CDR_i = Ĉ_{i,J}^{(I)} − Ĉ_{i,J}^{(I+1)}, écart entre l'ultime
estimé aujourd'hui et l'ultime réestimé après observation de la prochaine diagonale. Son espérance conditionnelle est nulle ;
on estime son écart quadratique moyen (msep) autour de 0.

Formules (Merz et Wüthrich, « Modelling the claims development result for solvency purposes », CAS E-Forum 2008,
éq. 3.9-3.11, approximation linéaire), avec les f_j et σ²_j de Mack, en indices 0 :
    S_j^I = Σ_{i ≤ I−j−1} C_{i,j}   (colonnes servant à f_j aujourd'hui)
    S_j^{I+1} = S_j^I + C_{I−j,j}    (colonnes après observation de la diagonale)
    pour l'origine i, d = I − i (dernier âge observé) et la somme Σ' sur j = d+1 … J−1 (diagonale C_{I−j,j}) :
    Δ_i = σ²_d/(f_d² S_d^I) + Σ' (C_{I−j,j}/S_j^{I+1})² σ²_j/(f_j² S_j^I)                 (estimation)
    Φ_i = Σ' (C_{I−j,j}/S_j^{I+1})² σ²_j/(f_j² C_{I−j,j})
    Γ_i = Φ_i + σ²_d/(f_d² C_{i,d})                                                       (processus)
    msep_i = Ĉ_{i,J}² (Γ_i + Δ_i)
    agrégé : Σ msep_i + 2 Σ_{i<k} Ĉ_{i,J} Ĉ_{k,J} (Ξ_i + Λ_i), avec
    Ξ_i = Φ_i + σ²_d/(f_d² S_d^{I+1}),   Λ_i = (C_{i,d}/S_d^{I+1}) σ²_d/(f_d² S_d^I) + Σ' (C_{I−j,j}/S_j^{I+1})² σ²_j/(f_j² S_j^I).

Contrôles (tests) : pour l'origine à qui il ne reste qu'une période, tout se révèle en un an et le msep à un an égale celui
de Mack ; sur le triangle de l'article (MW2008), le total redonne la valeur publiée.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .mack import mack
from .triangle import validate

@dataclass
class MerzWuthrichResult:
    ultimate: np.ndarray
    reserves: np.ndarray
    msep_cdr: np.ndarray        # msep à un an par origine
    total_msep_cdr: float
    mack_msep: np.ndarray       # msep Mack (ultime) par origine, pour comparaison
    mack_total_msep: float
    process: np.ndarray         # part « processus » Ĉ² Γ_i
    estimation: np.ndarray      # part « estimation » Ĉ² Δ_i
    @property
    def rmsep_cdr(self):return np.sqrt(self.msep_cdr)
    @property
    def total_rmsep_cdr(self):return float(np.sqrt(self.total_msep_cdr))
    @property
    def total_rmsep_mack(self):return float(np.sqrt(self.mack_total_msep))
    @property
    def one_year_share(self):
        """Part de l'incertitude ultime (en écart-type) révélée en un an."""
        return self.total_rmsep_cdr/self.total_rmsep_mack if self.mack_total_msep>0 else float('nan')
    def summary(self,triangle):
        return pd.DataFrame({'origin':triangle.origins,'ultimate':self.ultimate,'reserve':self.reserves,
                             'cdr_rmsep':self.rmsep_cdr,'mack_rmsep':np.sqrt(self.mack_msep)})

def merz_wuthrich(cumulative):
    """msep du CDR de l'année calendaire à venir, par origine et agrégé (paramètres de Mack, alpha = 1, sans queue)."""
    c=validate(cumulative);n=len(c);m=mack(c);f=m.factors;s2=m.sigma2;u=m.ultimate
    s_now=np.array([c[:n-j-1,j].sum() for j in range(n-1)])
    diag=np.array([c[n-1-j,j] for j in range(n-1)])          # C_{I−j,j}
    s_next=s_now+diag
    a=s2/f**2                                                  # σ²_j / f_j²
    w=(diag/s_next)**2                                         # (C_{I−j,j}/S_j^{I+1})²
    gamma=np.zeros(n);delta=np.zeros(n);xi=np.zeros(n);lam=np.zeros(n)
    for i in range(1,n):
        d=n-1-i;later=np.arange(d+1,n-1)
        phi=np.sum(w[later]*a[later]/diag[later])
        tail_est=np.sum(w[later]*a[later]/s_now[later])
        delta[i]=a[d]/s_now[d]+tail_est
        gamma[i]=phi+a[d]/c[i,d]
        xi[i]=phi+a[d]/s_next[d]
        lam[i]=c[i,d]/s_next[d]*a[d]/s_now[d]+tail_est
    process=u**2*gamma;estimation=u**2*delta;msep=process+estimation
    total=float(msep.sum())
    for i in range(1,n):
        for k in range(i+1,n):total+=2*u[i]*u[k]*(xi[i]+lam[i])
    return MerzWuthrichResult(u,m.reserves,msep,total,m.msep,m.total_msep,process,estimation)
