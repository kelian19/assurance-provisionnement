"""Chain-Ladder et MSEP Mack, alpha=1, toutes années, variance finale Mack, tail=1."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .triangle import Triangle,validate,observed_mask,to_incremental

@dataclass
class MackResult:
    projected: np.ndarray
    factors: np.ndarray
    sigma2: np.ndarray
    latest: np.ndarray
    ultimate: np.ndarray
    reserves: np.ndarray
    process_msep: np.ndarray
    parameter_covariance: np.ndarray
    diagnostics: dict
    @property
    def total_reserve(self):return float(self.reserves.sum())
    @property
    def msep(self):return self.process_msep+np.diag(self.parameter_covariance)
    @property
    def total_msep(self):return float(self.process_msep.sum()+self.parameter_covariance.sum())
    @property
    def total_rmsep(self):return float(np.sqrt(max(self.total_msep,0)))
    def summary(self,triangle):
        return pd.DataFrame({'origin':triangle.origins,'latest':self.latest,'ultimate':self.ultimate,'reserve':self.reserves,'mack_rmsep':np.sqrt(self.msep)})

def chain_ladder(cumulative):
    c=validate(cumulative);n=len(c)
    f=np.array([c[:n-j-1,j+1].sum()/c[:n-j-1,j].sum() for j in range(n-1)])
    if not np.isfinite(f).all() or (f<=0).any():raise ValueError('Facteur de développement non positif ou non fini.')
    projected=c.copy()
    for i in range(1,n):
        age=n-i-1
        for j in range(age,n-1):projected[i,j+1]=projected[i,j]*f[j]
    latest=c[np.arange(n),n-np.arange(n)-1]
    return f,projected,latest,projected[:,-1]-latest

def mack(cumulative):
    c=validate(cumulative);n=len(c)
    if n<4:raise ValueError('Mack avec approximation de variance finale exige au moins 4 années.')
    f,projected,latest,reserves=chain_ladder(c);u=projected[:,-1]
    sigma2=np.zeros(n-1);denom=np.array([c[:n-j-1,j].sum() for j in range(n-1)])
    for j in range(n-2):
        x=c[:n-j-1,j];y=c[:n-j-1,j+1]
        sigma2[j]=np.sum((y-f[j]*x)**2/x)/(len(x)-1)
    a,b=sigma2[-2],sigma2[-3]
    sigma2[-1]=min(a*a/b,a,b) if b>0 else 0.
    process=np.zeros(n);cov=np.zeros((n,n));scaled=sigma2/f**2
    for i in range(1,n):
        j=np.arange(n-i-1,n-1)
        process[i]=u[i]**2*np.sum(scaled[j]/projected[i,j])
        for k in range(1,n):
            overlap=np.arange(max(n-i-1,n-k-1),n-1)
            cov[i,k]=u[i]*u[k]*np.sum(scaled[overlap]/denom[overlap])
    inc=to_incremental(c);negative=int(np.sum(inc[observed_mask(n)]<0))
    diag={'tail_factor':1.,'final_sigma_method':'Mack minimum approximation','negative_observed_increments':negative,
          'factors_below_one':int(np.sum(f<1)),'positive_cumulative_required':True,'independent_origins_assumed':True,
          'calendar_effects_tested':False,'currency_inflation_adjusted':False,'sample_size_by_factor':list(range(n-1,0,-1))}
    return MackResult(projected,f,sigma2,latest,u,reserves,process,cov,diag)
