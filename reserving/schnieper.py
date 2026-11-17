"""Modèle de Schnieper : vrais IBNR (nouveaux sinistres N) et IBNER (révisions D).

Référence : N. Baradel, « Mathématiques de l'assurance dommages », §5 (estimation,
variance de processus) et §6.4 (bootstrap non paramétrique) ; R. Schnieper (1991),
« Separating true IBNR and IBNER claims », ASTIN Bulletin 21(1).

Convention : C[i,j+1] = C[i,j] + N[i,j+1] - D[i,j+1]. D > 0 est une baisse de charge,
D < 0 une hausse. Indices 0-based : la ligne i est observée pour j <= n-1-i.

La variance analytique livrée est la variance de PROCESSUS (lemme 5.13 du cours), les
paramètres étant remplacés par leurs estimations. L'erreur d'estimation des paramètres
n'est pas incluse : elle est captée par le bootstrap.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .triangle import observed_mask

CHUNK=1000

@dataclass(frozen=True)
class SchnieperData:
    new_claims: np.ndarray
    revisions: np.ndarray
    exposure: np.ndarray
    origins: tuple[str,...]
    name: str = 'Schnieper'
    unit: str = 'unités'
    source: str = ''

    def __post_init__(self):
        N=np.array(self.new_claims,dtype=float,copy=True);D=np.array(self.revisions,dtype=float,copy=True);E=np.array(self.exposure,dtype=float,copy=True)
        validate_schnieper(N,D,E)
        if len(self.origins)!=len(E) or len(set(self.origins))!=len(E):raise ValueError('Les origines doivent être uniques et correspondre aux lignes.')
        for a in (N,D,E):a.setflags(write=False)
        object.__setattr__(self,'new_claims',N);object.__setattr__(self,'revisions',D);object.__setattr__(self,'exposure',E)

    @property
    def n(self):return len(self.exposure)
    @property
    def cumulative(self):return cumulative_from(self.new_claims,self.revisions)

def validate_schnieper(N,D,E):
    if N.ndim!=2 or N.shape[0]!=N.shape[1] or D.shape!=N.shape or not 4<=len(N)<=30:raise ValueError('Triangles N et D carrés de même taille requis : 4 à 30 années.')
    n=len(N);mask=observed_mask(n)
    if E.shape!=(n,) or not np.isfinite(E).all() or (E<=0).any():raise ValueError('Une exposition strictement positive et finie est requise pour chaque année de survenance.')
    for name,a in (('N',N),('D',D)):
        if not np.isfinite(a[mask]).all():raise ValueError(f'Une cellule observée de {name} est manquante ou non finie.')
        if not np.isnan(a[~mask]).all():raise ValueError(f'Les cellules futures de {name} doivent être vides/NA, pas nulles.')
    if (N[mask]<0).any():raise ValueError('Les montants de nouveaux sinistres N doivent être positifs ou nuls.')
    if (D[:,0]!=0).any():raise ValueError('Par construction D[i,1] = 0 : aucune révision en première année de développement.')
    if (cumulative_from(N,D)[mask]<=0).any():raise ValueError('Les cumuls C = ΣN − ΣD doivent être strictement positifs (résidus Pearson et facteurs définis par C).')

def cumulative_from(N,D):
    inc=np.where(observed_mask(len(N)),N-D,np.nan)
    c=np.full_like(inc,np.nan);mask=observed_mask(len(N))
    cum=np.cumsum(np.where(mask,inc,0.),axis=1)
    c[mask]=cum[mask];return c

def estimate_parameters(N,D,C,E):
    """λ_j, δ_j (meilleurs estimateurs linéaires, prop. 5.5) et variances σ²_j, τ²_j (lemme 5.12)."""
    n=len(E)
    lam=np.array([N[:n-j,j].sum()/E[:n-j].sum() for j in range(n)])
    delta=np.array([D[:n-j-1,j+1].sum()/C[:n-j-1,j].sum() for j in range(n-1)])
    s2=np.zeros(n);tau2=np.zeros(n-1)
    for j in range(n-1):s2[j]=np.sum(E[:n-j]*(N[:n-j,j]/E[:n-j]-lam[j])**2)/(n-j-1)
    for j in range(n-2):tau2[j]=np.sum(C[:n-j-1,j]*(D[:n-j-1,j+1]/C[:n-j-1,j]-delta[j])**2)/(n-j-2)
    return lam,delta,s2,tau2

@dataclass
class SchnieperResult:
    cumulative: np.ndarray
    projected: np.ndarray
    lam: np.ndarray
    delta: np.ndarray
    sigma2: np.ndarray
    tau2: np.ndarray
    latest: np.ndarray
    ultimate: np.ndarray
    reserves: np.ndarray
    ibnr: np.ndarray
    ibner: np.ndarray
    process_variance: np.ndarray
    diagnostics: dict
    @property
    def total_reserve(self):return float(self.reserves.sum())
    @property
    def total_process_variance(self):return float(self.process_variance.sum())
    @property
    def total_process_std(self):return float(np.sqrt(self.total_process_variance))
    def summary(self,data):
        return pd.DataFrame({'origin':data.origins,'exposure':data.exposure,'latest':self.latest,'ultimate':self.ultimate,'reserve':self.reserves,
            'true_ibnr':self.ibnr,'ibner':self.ibner,'process_std':np.sqrt(self.process_variance)})
    def parameters(self):
        n=len(self.lam)
        return pd.DataFrame({'development':[f'D{j+1}' for j in range(n)],'lambda':self.lam,'sigma2':self.sigma2,
            'delta':np.append(self.delta,np.nan),'tau2':np.append(self.tau2,np.nan)})

def process_variance(projected,E,delta,s2,tau2):
    """Var(C_{i,n} | F_n) par la récurrence du lemme 5.13 : σ²_j E_i + τ²_{j-1} E(C_{i,j-1}) + (1-δ_{j-1})² Var(C_{i,j-1}),
    sous Cov(N,D)=0 et paramètres connus. Les paramètres sont ici ceux fournis, sans erreur d'estimation."""
    n=len(E);var=np.zeros(n)
    for j in range(1,n):
        rows=np.arange(n-j,n)
        var[rows]=s2[j]*E[rows]+tau2[j-1]*projected[rows,j-1]+(1-delta[j-1])**2*var[rows]
    return var

def schnieper(data):
    N,D,E=data.new_claims,data.revisions,data.exposure;n=data.n
    C=data.cumulative
    lam,delta,s2,tau2=estimate_parameters(N,D,C,E)
    projected=C.copy();ibnr=np.zeros(n);ibner=np.zeros(n);process=np.zeros(n)
    for j in range(1,n):
        rows=np.arange(n-j,n)
        projected[rows,j]=lam[j]*E[rows]+(1-delta[j-1])*projected[rows,j-1]
        ibnr[rows]+=lam[j]*E[rows]
        ibner[rows]-=delta[j-1]*projected[rows,j-1]
    var=process_variance(projected,E,delta,s2,tau2)
    latest=C[np.arange(n),n-1-np.arange(n)];ultimate=projected[:,-1];reserves=ultimate-latest
    diag={'model':'Schnieper (cours N. Baradel §5)','terminal_variances':'σ²_n = τ²_{n-1} = 0 (convention du cours, non testée)',
          'tail_factor':1.,'independent_origins_assumed':True,'cov_N_D_zero_assumed':True,'variance_scope':'processus seul, paramètres supposés connus',
          'negative_projected_cells':int(np.sum(projected[~observed_mask(n)]<0)),'negative_delta_count':int(np.sum(delta<0)),
          'currency_inflation_adjusted':False,'calendar_effects_tested':False,'sample_size_by_lambda':list(range(n,0,-1)),'sample_size_by_delta':list(range(n-1,0,-1))}
    return SchnieperResult(C,projected,lam,delta,s2,tau2,latest,ultimate,reserves,ibnr,ibner,var,diag)

def pearson_residuals(data,result):
    """Résidus ajustés des degrés de liberté puis centrés (formules (11) du cours)."""
    N,D,E=data.new_claims,data.revisions,data.exposure;C=result.cumulative;n=data.n
    s=np.sqrt(result.sigma2);tau=np.sqrt(result.tau2)
    # Variance nulle à la précision numérique près : division par s_j ou τ_j impossible.
    if any(result.sigma2[j]<=1e-12*np.mean(N[:n-j,j]**2/E[:n-j]) for j in range(n-1)):raise ValueError('Une variance σ²_j est nulle : résidus de nouveaux sinistres non définis.')
    if any(result.tau2[j]<=1e-12*np.mean(D[:n-j-1,j+1]**2/C[:n-j-1,j]) for j in range(n-2)):raise ValueError('Une variance τ²_j est nulle : résidus de révision non définis.')
    rn=np.concatenate([(N[:n-j,j]-result.lam[j]*E[:n-j])/(s[j]*np.sqrt(E[:n-j]))*np.sqrt((n-j)/(n-j-1)) for j in range(n-1)])
    rd=np.concatenate([(D[:n-j-1,j+1]-result.delta[j]*C[:n-j-1,j])/(tau[j]*np.sqrt(C[:n-j-1,j]))*np.sqrt((n-j-1)/(n-j-2)) for j in range(n-2)])
    return rn-rn.mean(),rd-rd.mean()

@dataclass
class SchnieperBootstrapResult:
    predictive_reserves: np.ndarray
    parameter_reserves: np.ndarray
    by_origin: np.ndarray
    diagnostics: dict
    def summary(self):
        x=self.predictive_reserves
        return {'mean':float(x.mean()),'median':float(np.median(x)),'std':float(x.std(ddof=1)),
                'q75':float(np.quantile(x,.75)),'q90':float(np.quantile(x,.90)),'q95':float(np.quantile(x,.95)),
                'q99':float(np.quantile(x,.99)),'q995':float(np.quantile(x,.995)),'mean_monte_carlo_se':float(x.std(ddof=1)/np.sqrt(len(x))),
                'parameter_only_std':float(self.parameter_reserves.std(ddof=1))}

def _estimate_batch(Nm,Dm,C,E):
    """Réestimation vectorisée sur M pseudo-historiques (mêmes formules que estimate_parameters)."""
    n=len(E);M=Nm.shape[0]
    lam=np.stack([Nm[:,:n-j,j].sum(1)/E[:n-j].sum() for j in range(n)],axis=1)
    delta=np.stack([Dm[:,:n-j-1,j+1].sum(1)/C[:n-j-1,j].sum() for j in range(n-1)],axis=1)
    s2=np.zeros((M,n));tau2=np.zeros((M,n-1))
    for j in range(n-1):s2[:,j]=np.sum(E[:n-j]*(Nm[:,:n-j,j]/E[:n-j]-lam[:,[j]])**2,axis=1)/(n-j-1)
    for j in range(n-2):tau2[:,j]=np.sum(C[:n-j-1,j]*(Dm[:,:n-j-1,j+1]/C[:n-j-1,j]-delta[:,[j]])**2,axis=1)/(n-j-2)
    return lam,delta,s2,tau2

def schnieper_bootstrap(data,*,simulations=5000,seed=42):
    """Bootstrap non paramétrique des résidus (cours §6.4.1) : reconstruction du passé
    pour réestimer les paramètres, puis projection stochastique du futur avec plancher à 0
    (pmax du cours). Les simulations planchées sont comptées, jamais écartées."""
    if not isinstance(simulations,(int,np.integer)) or not 100<=simulations<=100000:raise ValueError('Choisir entre 100 et 100 000 simulations.')
    if not isinstance(seed,(int,np.integer)) or not 1<=seed<=2**32-2:raise ValueError('La graine doit être comprise entre 1 et 2³²−2.')
    result=schnieper(data);rn,rd=pearson_residuals(data,result)
    n=data.n;E=data.exposure;C=result.cumulative;Cobs=np.where(observed_mask(n),C,0.)
    lam0,delta0=result.lam,result.delta;s0=np.sqrt(result.sigma2);tau0=np.sqrt(result.tau2)
    latest=result.latest;rng=np.random.default_rng(int(seed))
    predictive=[];param_only=[];by_origin=[];floored=[]
    done=0
    while done<simulations:
        m=min(CHUNK,simulations-done);done+=m
        Nm=np.zeros((m,n,n));Dm=np.zeros((m,n,n))
        for j in range(n):
            r=n-j;Nm[:,:r,j]=lam0[j]*E[:r]+s0[j]*np.sqrt(E[:r])*rng.choice(rn,size=(m,r))
        for j in range(n-1):
            r=n-j-1;Dm[:,:r,j+1]=delta0[j]*Cobs[:r,j]+tau0[j]*np.sqrt(Cobs[:r,j])*rng.choice(rd,size=(m,r))
        lam,delta,s2,tau2=_estimate_batch(Nm,Dm,C,E)
        s=np.sqrt(s2);tau=np.sqrt(tau2)
        Cm=np.repeat(Cobs[None],m,axis=0);Cp=Cm.copy();hit=np.zeros(m,dtype=bool)
        for k in range(1,n):
            rows=np.arange(n-k,n)
            nn=rng.choice(rn,size=(m,k));dd=rng.choice(rd,size=(m,k))
            prev=Cm[:,rows,k-1]
            raw=lam[:,[k]]*E[rows]+s[:,[k]]*np.sqrt(E[rows])*nn+prev*(1-delta[:,[k-1]])-tau[:,[k-1]]*np.sqrt(prev)*dd
            hit|=(raw<0).any(axis=1);Cm[:,rows,k]=np.maximum(raw,0.)
            Cp[:,rows,k]=lam[:,[k]]*E[rows]+Cp[:,rows,k-1]*(1-delta[:,[k-1]])
        if not (np.isfinite(Cm).all() and np.isfinite(Cp).all()):raise ValueError('Simulations non finies : aucune suppression ou troncature silencieuse n’est appliquée.')
        by_origin.append(Cm[:,:,n-1]-latest);predictive.append((Cm[:,:,n-1]-latest).sum(1));param_only.append((Cp[:,:,n-1]-latest).sum(1));floored.append(hit)
    pred=np.concatenate(predictive);par=np.concatenate(param_only);hit=np.concatenate(floored)
    batches=np.array_split(pred,4)
    diag={'model':'Schnieper — bootstrap non paramétrique de résidus de Pearson (cours §6.4.1)','simulations':int(simulations),'seed':int(seed),
          'floored_simulations':int(hit.sum()),'floored_rate':float(hit.mean()),'floor':'max(·,0) sur chaque C simulé, comme pmax du cours',
          'residuals_new_claims':int(len(rn)),'residuals_revisions':int(len(rd)),'central_reserve':result.total_reserve,
          'invalid_simulations_discarded':0,'negative_reserve_simulations':int(np.sum(pred<0)),
          'q95_batches':[float(np.quantile(b,.95)) for b in batches],'tail_factor':1.,'is_mack_bootstrap':False,'includes_process_risk':True,'includes_parameter_risk':True}
    return SchnieperBootstrapResult(pred,par,np.concatenate(by_origin),diag)
