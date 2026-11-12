import numpy as np
import pytest
from reserving.mack import mack,chain_ladder
from reserving.data import load_dataset
from reserving.reference import reference_mack
from reserving.triangle import observed_mask

@pytest.mark.parametrize('key',['course','genins','raa','cas'])
def test_independent_library_reconciliation(key):
 t=load_dataset(key);a=mack(t.cumulative);b=reference_mack(t.cumulative)
 assert a.total_reserve==pytest.approx(b['reserve'],rel=1e-12)
 assert a.total_rmsep==pytest.approx(b['rmsep'],rel=1e-12)
 np.testing.assert_allclose(np.sqrt(a.msep),b['annual_rmsep'],rtol=1e-12,atol=1e-8)
 np.testing.assert_allclose(a.factors,b['factors'],rtol=1e-12)

def test_course_reference_and_data_not_modified():
 t=load_dataset('course');before=t.cumulative.copy();r=mack(t.cumulative)
 assert r.total_reserve==pytest.approx(18_680_847.767812435,abs=1e-7)
 np.testing.assert_equal(before,t.cumulative)
 mask=observed_mask(t.n);np.testing.assert_array_equal(r.projected[mask],before[mask])

def test_covariance_is_included_and_scaling_holds():
 t=load_dataset('course');r=mack(t.cumulative);s=mack(t.cumulative*10)
 assert r.total_msep>r.msep.sum()
 np.testing.assert_allclose(r.parameter_covariance,r.parameter_covariance.T)
 assert s.total_reserve==pytest.approx(r.total_reserve*10)
 assert s.total_rmsep==pytest.approx(r.total_rmsep*10)

def test_exact_multiplicative_triangle_has_no_variance():
 values=np.full((5,5),np.nan)
 for i in range(5):
  for j in range(5-i):values[i,j]=(i+1)*100*2**j
 r=mack(values);assert r.total_rmsep==0
 np.testing.assert_allclose(r.factors,2)

def test_recoveries_are_allowed_in_mack():
 r=mack(load_dataset('raa').cumulative)
 assert r.diagnostics['negative_observed_increments']>0

def test_course_is_not_genins_alias():
 a=load_dataset('course').cumulative;b=load_dataset('genins').cumulative
 assert a[7,2]==2_864_494 and b[7,2]==2_864_498
 assert mack(a).total_reserve!=mack(b).total_reserve
