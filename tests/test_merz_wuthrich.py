"""Incertitude à un an (Merz-Wüthrich 2008) : valeurs publiées, cas limites exacts, cohérence avec Mack."""
import numpy as np
import pytest
import chainladder as cl
from reserving.merz_wuthrich import merz_wuthrich
from reserving.mack import mack

@pytest.fixture(scope='module')
def mw2008():
    return cl.load_sample('mw2008').values[0,0]

def test_reproduces_published_totals(mw2008):
    """Merz et Wüthrich (2008) publient, pour leur triangle, √msep CDR = 81 080 et √msep Mack = 108 401."""
    r=merz_wuthrich(mw2008)
    assert abs(r.reserves.sum()-2237826)<1
    assert abs(r.total_rmsep_cdr-81080)<1
    assert abs(r.total_rmsep_mack-108401)<1

def test_one_remaining_period_equals_mack(mw2008):
    """Pour l'origine à qui il ne reste qu'une période, tout le run-off se révèle en un an : msep CDR = msep Mack."""
    r=merz_wuthrich(mw2008)
    assert r.msep_cdr[1]==pytest.approx(r.mack_msep[1],rel=1e-12)
    assert r.msep_cdr[0]==0 and r.mack_msep[0]==0

@pytest.mark.parametrize('key',['raa','genins'])
def test_one_year_below_ultimate(key):
    c=cl.load_sample(key).values[0,0];r=merz_wuthrich(c)
    assert np.all(r.msep_cdr<=r.mack_msep*(1+1e-12))
    assert 0<r.one_year_share<=1
    assert np.allclose(r.msep_cdr,r.process+r.estimation)

def test_deterministic_triangle_has_no_uncertainty():
    """Facteurs exactement constants : σ² = 0, donc aucun CDR attendu."""
    n=6;f=np.array([1.8,1.3,1.1,1.05,1.02]);c=np.full((n,n),np.nan)
    for i in range(n):
        c[i,0]=100+10*i
        for j in range(n-1-i):c[i,j+1]=c[i,j]*f[j]
    r=merz_wuthrich(c)
    assert r.total_msep_cdr==pytest.approx(0,abs=1e-9) and r.total_rmsep_mack==pytest.approx(0,abs=1e-6)

def test_parameters_shared_with_mack(mw2008):
    r=merz_wuthrich(mw2008);m=mack(mw2008)
    assert np.allclose(r.ultimate,m.ultimate) and r.mack_total_msep==pytest.approx(m.total_msep)
