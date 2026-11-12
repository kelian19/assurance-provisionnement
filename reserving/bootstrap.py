"""ODP de chainladder : résidus Pearson + projection + processus Gamma signé de bibliothèque."""
from dataclasses import dataclass
import warnings
import numpy as np
import chainladder as cl
from .triangle import validate,to_incremental,observed_mask
from .reference import as_chainladder

class StableBootstrapODP(cl.BootstrapODPSample):
    """Correction ciblée : initialiser les leviers saturés à zéro.

    chainladder 0.10.1 utilise divide(where=..., sans out) dans _get_hat :
    les entrées où h=1 peuvent contenir une mémoire non initialisée. Aucun
    tirage, modèle de processus ou autre algorithme de bibliothèque n'est changé.
    """
    def _get_hat(self,X,exp_incr_triangle):
        n=exp_incr_triangle.shape[0]
        mask=observed_mask(n)
        means=exp_incr_triangle.T[mask.T]
        if not np.isfinite(means).all() or np.any(means<=0):raise ValueError('Moyennes incrémentales ODP strictement positives requises.')
        design=self.design_matrix_
        gram=design.T@(means[:,None]*design)
        solved=np.linalg.solve(gram,design.T).T
        h=means*np.sum(design*solved,axis=1)
        residual_variance=np.maximum(1.-h,0.)
        adjustment=np.zeros_like(h)
        np.divide(1.,residual_variance,out=adjustment,where=residual_variance>1e-10)
        adjustment=np.sqrt(adjustment)
        # Library design matrix uses column-major (development then origin) order.
        out=np.full((n,n),np.nan);out.T[mask.T]=adjustment
        return out

@dataclass
class BootstrapResult:
    predictive_reserves: np.ndarray
    parameter_reserves: np.ndarray
    by_origin: np.ndarray
    diagnostics: dict
    def summary(self):
        x=self.predictive_reserves
        return {'mean':float(x.mean()),'median':float(np.median(x)),'std':float(x.std(ddof=1)),
                'q75':float(np.quantile(x,.75)),'q90':float(np.quantile(x,.90)),'q95':float(np.quantile(x,.95)),
                'q99':float(np.quantile(x,.99)),'mean_monte_carlo_se':float(x.std(ddof=1)/np.sqrt(len(x))),
                'parameter_only_std':float(self.parameter_reserves.std(ddof=1))}

def odp_bootstrap(cumulative, *, simulations=5000,seed=42):
    c=validate(cumulative);n=len(c)
    if n<4:raise ValueError('Bootstrap : au moins 4 années sont requises.')
    if not isinstance(simulations,(int,np.integer)) or not 100<=simulations<=20000:raise ValueError('Choisir entre 100 et 20 000 simulations.')
    if not isinstance(seed,(int,np.integer)) or not 1<=seed<=2**32-2:raise ValueError('La graine doit être comprise entre 1 et 2³²−2.')
    increments=to_incremental(c)
    if np.any(increments[observed_mask(n)]<0):raise ValueError('Bootstrap ODP de cette V1 réservé aux incréments observés non négatifs. Mack reste disponible pour des reprises de paiements.')
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        sampler=StableBootstrapODP(n_sims=int(simulations),random_state=int(seed),hat_adj=True)
        samples=sampler.fit_transform(as_chainladder(c))
        if not np.isfinite(float(sampler.scale_)) or float(sampler.scale_)<=0:raise ValueError('Dispersion ODP nulle ou invalide : bootstrap non identifiable.')
        parameters=samples.copy();delattr(parameters,'_get_process_variance')
        parameter_model=cl.Chainladder().fit(parameters)
        predictive_model=cl.Chainladder().fit(samples)
        parameter_raw=parameter_model.ibnr_.values[:,0,:,0]
        predictive_raw=predictive_model.ibnr_.values[:,0,:,0]
        for raw in [parameter_raw,predictive_raw]:
            if np.isinf(raw).any() or not np.isfinite(raw[:,1:]).all():raise ValueError('Simulation invalide : aucune valeur manquante hors année complètement développée n’est tolérée.')
        parameter_reserves=np.sum(np.nan_to_num(parameter_raw,nan=0.),axis=1)
        by_origin=np.nan_to_num(predictive_raw,nan=0.)
        predictive=np.sum(by_origin,axis=1)
        future=parameter_model.full_triangle_.cum_to_incr().values[:,0,:,:n]
        lower=np.add.outer(np.arange(n),np.arange(n))>=n
        negative_future_means=int(np.sum(future[:,lower]<0))
        negative_mean_simulations=int(np.sum(np.any(future[:,lower]<0,axis=1)))
    if not np.isfinite(predictive).all() or not np.isfinite(parameter_reserves).all():raise ValueError('Simulations non finies : aucune suppression ou troncature silencieuse n’est appliquée.')
    # Quantile Monte Carlo stability: four disjoint simulation batches (diagnostic, not a confidence interval).
    batches=np.array_split(predictive,4)
    diagnostics={'model':'ODP bootstrap, Pearson leverage correction, library signed Gamma process',
       'leverage_fix':'Explicit zero for saturated h=1; no uninitialized divide output','library':'chainladder','version':cl.__version__,'simulations':int(simulations),'seed':int(seed),'process_seed':int(seed)+1,
       'scale':float(sampler.scale_),'includes_process_risk':predictive_model.process_variance_ is not None,
       'negative_future_mean_cells':negative_future_means,'negative_mean_simulations':negative_mean_simulations,'negative_reserve_simulations':int(np.sum(predictive<0)),
       'invalid_simulations_discarded':0,'warnings':sorted(set(str(w.message) for w in captured)),
       'q95_batches':[float(np.quantile(b,.95)) for b in batches],'tail_factor':1.,'is_mack_bootstrap':False}
    return BootstrapResult(predictive,parameter_reserves,by_origin,diagnostics)
