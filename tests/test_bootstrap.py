import numpy as np
import pytest
from reserving.bootstrap import odp_bootstrap
from reserving.data import load_dataset

def test_reproducible_and_process_is_present():
 t=load_dataset('course');a=odp_bootstrap(t.cumulative,simulations=200,seed=42);b=odp_bootstrap(t.cumulative,simulations=200,seed=42)
 np.testing.assert_equal(a.predictive_reserves,b.predictive_reserves)
 assert a.diagnostics['includes_process_risk']
 assert a.diagnostics['invalid_simulations_discarded']==0
 assert not np.array_equal(a.parameter_reserves,a.predictive_reserves)
 np.testing.assert_allclose(a.by_origin.sum(axis=1),a.predictive_reserves)
 assert np.isfinite(a.predictive_reserves).all()
 assert a.summary()['q99']>=a.summary()['q95']>=a.summary()['median']
 assert a.diagnostics['negative_future_mean_cells']>=0

def test_bootstrap_does_not_silently_accept_recoveries_or_invalid_seed():
 with pytest.raises(ValueError,match='incréments'):odp_bootstrap(load_dataset('raa').cumulative,simulations=100,seed=42)
 with pytest.raises(ValueError,match='graine'):odp_bootstrap(load_dataset('course').cumulative,simulations=100,seed=0)

def test_saturated_leverages_are_explicitly_zero():
 from reserving.bootstrap import StableBootstrapODP
 from reserving.reference import as_chainladder
 from reserving.triangle import observed_mask
 sample=StableBootstrapODP(n_sims=100,random_state=42,hat_adj=True).fit(as_chainladder(load_dataset('course').cumulative))
 assert sample.hat_[0,-1]==0 and sample.hat_[-1,0]==0
 assert np.isfinite(sample.hat_[observed_mask(10)]).all()

def test_zero_reserve_nan_is_accepted_but_other_missing_values_are_not():
 from reserving.bootstrap import _check_reserves
 reserve=np.array([[np.nan,np.nan,10.]]);ultimate=np.array([[5.,7.,15.]]);latest=np.array([[5.,7.,5.]])
 _check_reserves(reserve,ultimate,latest)
 with pytest.raises(ValueError,match='manquante'):_check_reserves(reserve,ultimate+np.array([[0,1,0]]),latest)
 with pytest.raises(ValueError,match='non fini'):_check_reserves(reserve,np.array([[5.,np.nan,15.]]),latest)

def test_course_bootstrap_with_published_settings_reproduces_published_statistics():
 import json
 from pathlib import Path
 t=load_dataset('course');summary=odp_bootstrap(t.cumulative,simulations=5000,seed=42).summary()
 published=json.loads((Path(__file__).resolve().parents[1]/'reports/calculation_course.json').read_text(encoding='utf-8'))['bootstrap']['summary']
 for key in ['mean','median','std','q95','q99']:assert summary[key]==pytest.approx(published[key],rel=1e-9)
