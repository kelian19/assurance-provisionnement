"""Adaptateur de comparaison externe ; dates techniques pour les triangles sans calendrier."""
import numpy as np
import pandas as pd
import chainladder as cl
from .triangle import validate,observed_mask

def as_chainladder(cumulative):
    c=validate(cumulative);n=len(c);i,j=np.where(observed_mask(n))
    # Calendar labels serve only to preserve origin/development geometry.
    data=pd.DataFrame({'origin':pd.to_datetime(pd.Series(2000+i).astype(str)+'-01-01'),'valuation':pd.to_datetime(pd.Series(2000+i+j).astype(str)+'-12-31'),'value':c[i,j]})
    return cl.Triangle(data,origin='origin',development='valuation',columns='value',cumulative=True)

def reference_mack(cumulative):
    triangle=as_chainladder(cumulative)
    developed=cl.Development(average='volume',sigma_interpolation='mack').fit_transform(triangle)
    model=cl.MackChainladder().fit(developed)
    return {'reserve':float(model.ibnr_.sum()),'rmsep':float(np.asarray(model.total_mack_std_err_).ravel()[0]),
            'annual_rmsep':np.nan_to_num(model.mack_std_err_.values[0,0,:,-1]),'factors':developed.ldf_.values[0,0,0,:len(cumulative)-1],
            'version':cl.__version__}
