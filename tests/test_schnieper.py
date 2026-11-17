import numpy as np
import pytest
from reserving.data import load_schnieper
from reserving.mack import mack
from reserving.schnieper import SchnieperData,schnieper,schnieper_bootstrap,pearson_residuals,process_variance,validate_schnieper
from reserving.triangle import observed_mask

@pytest.fixture(scope='module')
def course():return load_schnieper()

def test_course_example_5_4_reproduces_printed_values(course):
    r=schnieper(course)
    np.testing.assert_allclose(r.lam*1e3,[0.450,1.059,1.396,1.150,1.181,0.492,0.499],atol=5e-4)
    np.testing.assert_allclose(r.delta,[-0.359,0.072,-0.048,-0.054,0.070,0.033],atol=5e-4)
    np.testing.assert_allclose(np.sqrt(r.sigma2),[0.0538,0.0737,0.1089,0.0795,0.0560,0.0575,0.0],atol=5e-5)
    np.testing.assert_allclose(np.sqrt(r.tau2),[0.3874,1.2686,1.1768,3.4603,0.3034,0.0],atol=5e-5)
    np.testing.assert_allclose(r.ultimate,[79.5,64.4,101.3,79.8,113.0,106.6,123.4],atol=0.05)
    np.testing.assert_allclose(r.reserves,[0,4.4,4.8,32.9,60.3,77.2,104.3],atol=0.05)
    assert r.total_reserve==pytest.approx(283.9,abs=0.05)

def test_course_cumulative_triangle_is_rebuilt_from_n_and_d(course):
    c=course.cumulative
    np.testing.assert_allclose(c[0],[7.5,28.9,52.6,84.5,80.1,76.9,79.5],atol=1e-9)
    np.testing.assert_allclose(c[2,:5],[13.8,42.4,36.3,53.3,96.5],atol=1e-9)
    assert np.isnan(c[~observed_mask(7)]).all()

def test_mack_on_the_same_cumulative_triangle_gives_course_comparison(course):
    assert mack(course.cumulative).total_reserve==pytest.approx(464.2,abs=0.05)

def test_true_ibnr_and_ibner_sum_to_the_reserve(course):
    r=schnieper(course)
    np.testing.assert_allclose(r.ibnr+r.ibner,r.reserves,atol=1e-9)
    assert r.ibnr.sum()>r.total_reserve>0 and r.ibner.sum()<0

def test_projection_preserves_observations_and_inputs(course):
    before=(course.new_claims.copy(),course.revisions.copy(),course.exposure.copy())
    r=schnieper(course);mask=observed_mask(course.n)
    np.testing.assert_array_equal(r.projected[mask],course.cumulative[mask])
    for a,b in zip(before,(course.new_claims,course.revisions,course.exposure)):np.testing.assert_array_equal(a,b)
    assert not course.new_claims.flags.writeable

def test_unit_invariance_remark_5_10(course):
    r=schnieper(course)
    k=7.
    both=schnieper(SchnieperData(course.new_claims*k,course.revisions*k,course.exposure*k,course.origins))
    np.testing.assert_allclose(both.lam,r.lam);np.testing.assert_allclose(both.delta,r.delta)
    assert both.total_reserve==pytest.approx(r.total_reserve*k)
    exposure_only=schnieper(SchnieperData(course.new_claims,course.revisions,course.exposure*k,course.origins))
    np.testing.assert_allclose(exposure_only.lam,r.lam/k)
    assert exposure_only.total_reserve==pytest.approx(r.total_reserve)

def _counts_example():
    nan=np.nan
    N=np.array([[10,5,0,1,1],[7,6,3,1,nan],[10,3,2,nan,nan],[18,5,nan,nan,nan],[19,nan,nan,nan,nan]],dtype=float)
    D=np.array([[0,2,2,0,0],[0,5,2,1,nan],[0,5,1,nan,nan],[0,8,nan,nan,nan],[0,nan,nan,nan,nan]],dtype=float)
    return SchnieperData(N,D,np.array([20,25,32,39,42.]),tuple('12345'))

def test_course_example_5_6_counts_above_threshold():
    r=schnieper(_counts_example())
    np.testing.assert_allclose(r.lam,[0.405,0.164,0.065,0.044,0.05],atol=5e-4)
    np.testing.assert_allclose(r.delta,[0.444,0.172,0.050,0.0],atol=5e-4)
    np.testing.assert_allclose(r.ultimate,[13,10.25,11.57,17.88,20.26],atol=0.005)
    np.testing.assert_allclose(r.reserves,[0,1.25,2.57,2.88,1.26],atol=0.005)
    assert r.total_reserve==pytest.approx(7.97,abs=0.005)

def _closed_form_variance(r,E,n):
    """Lemme 5.13 du cours, forme développée (sommes et produits), indépendante de la récurrence du moteur."""
    out=np.zeros(n)
    for i in range(n):
        d=n-1-i
        out[i]=sum(np.prod([(1-r.delta[l])**2 for l in range(k+1,n-1)])*(r.sigma2[k+1]*E[i]+r.tau2[k]*r.projected[i,k]) for k in range(d,n-1))
    return out

def test_process_variance_matches_the_lemma_5_13_closed_form(course):
    r=schnieper(course);np.testing.assert_allclose(r.process_variance,_closed_form_variance(r,course.exposure,course.n),rtol=1e-12,atol=1e-12)

def test_process_variance_matches_a_gaussian_monte_carlo(course):
    # Variances réduites (÷400) : bruit faible devant C, donc cumuls simulés positifs et Var(D|C)=τ²C bien défini.
    r=schnieper(course);n=course.n;E=course.exposure;s2=r.sigma2/400;tau2=r.tau2/400
    expected=process_variance(r.projected,E,r.delta,s2,tau2)
    rng=np.random.default_rng(12345);M=200_000;ultimate=np.zeros((n,M))
    for i in range(n):
        c=np.full(M,r.cumulative[i,n-1-i])
        for j in range(n-i,n):
            c=c*(1-r.delta[j-1])+r.lam[j]*E[i]+np.sqrt(s2[j]*E[i])*rng.standard_normal(M)-np.sqrt(tau2[j-1]*c)*rng.standard_normal(M)
        ultimate[i]=c
    assert (ultimate>0).all()
    np.testing.assert_allclose(ultimate.mean(1)[2:],r.ultimate[2:],rtol=2e-3)
    np.testing.assert_allclose(ultimate.var(1,ddof=1)[2:],expected[2:],rtol=0.03)

def test_terminal_variance_convention_is_explicit(course):
    r=schnieper(course)
    assert r.sigma2[-1]==0 and r.tau2[-1]==0
    assert r.process_variance[1]==0
    assert 'non testée' in r.diagnostics['terminal_variances'] and r.diagnostics['variance_scope'].startswith('processus seul')

@pytest.mark.parametrize('mutate,message',[
    (lambda N,D,E:N.__setitem__((3,4),0.),'futures'),
    (lambda N,D,E:D.__setitem__((6,6),0.),'futures'),
    (lambda N,D,E:N.__setitem__((0,0),-1.),'positifs'),
    (lambda N,D,E:D.__setitem__((2,0),1.),'D\\[i,1\\]'),
    (lambda N,D,E:E.__setitem__(3,0.),'exposition'),
    (lambda N,D,E:D.__setitem__((0,1),1e6),'strictement positifs'),
    (lambda N,D,E:N.__setitem__((0,2),np.nan),'manquante'),
])
def test_invalid_inputs_are_refused(course,mutate,message):
    N=course.new_claims.copy();D=course.revisions.copy();E=course.exposure.copy();mutate(N,D,E)
    with pytest.raises(ValueError,match=message):validate_schnieper(N,D,E)

def test_origins_must_match_rows(course):
    with pytest.raises(ValueError):SchnieperData(course.new_claims,course.revisions,course.exposure,('a','b'))

def test_residuals_are_centered_and_complete(course):
    r=schnieper(course);rn,rd=pearson_residuals(course,r);n=course.n
    assert len(rn)==sum(n-j for j in range(n-1))
    assert len(rd)==sum(n-j-1 for j in range(n-2))
    assert abs(rn.mean())<1e-12 and abs(rd.mean())<1e-12

def test_bootstrap_is_reproducible_and_documented(course):
    a=schnieper_bootstrap(course,simulations=500,seed=7);b=schnieper_bootstrap(course,simulations=500,seed=7);c=schnieper_bootstrap(course,simulations=500,seed=8)
    np.testing.assert_array_equal(a.predictive_reserves,b.predictive_reserves)
    assert not np.array_equal(a.predictive_reserves,c.predictive_reserves)
    d=a.diagnostics
    assert d['simulations']==500 and d['seed']==7 and d['invalid_simulations_discarded']==0 and d['is_mack_bootstrap'] is False
    assert d['includes_process_risk'] and d['includes_parameter_risk'] and 0<=d['floored_rate']<=1
    assert a.by_origin.shape==(500,course.n) and np.isfinite(a.predictive_reserves).all()
    np.testing.assert_allclose(a.by_origin.sum(1),a.predictive_reserves)

def test_bootstrap_does_not_change_inputs_and_is_chunk_independent_in_shape(course):
    before=course.new_claims.copy()
    r=schnieper_bootstrap(course,simulations=2500,seed=3)
    np.testing.assert_array_equal(before,course.new_claims)
    assert len(r.predictive_reserves)==2500

def test_bootstrap_distribution_is_consistent_with_the_central_estimate_and_variance_split(course):
    central=schnieper(course);b=schnieper_bootstrap(course,simulations=20000,seed=42);s=b.summary()
    assert s['mean']==pytest.approx(central.total_reserve,rel=0.03)
    assert s['parameter_only_std']<s['std']
    split=np.sqrt(s['parameter_only_std']**2+central.total_process_variance)
    assert s['std']==pytest.approx(split,rel=0.10)
    assert 0.003<b.diagnostics['floored_rate']<0.08

def test_bootstrap_argument_validation(course):
    for kwargs in ({'simulations':50},{'simulations':200000},{'simulations':500.5},{'simulations':500,'seed':0}):
        with pytest.raises(ValueError):schnieper_bootstrap(course,**kwargs)

def test_bootstrap_refuses_zero_variance_residuals(course):
    N=course.new_claims.copy();N[:,0]=0.001*course.exposure
    data=SchnieperData(N,course.revisions,course.exposure,course.origins)
    with pytest.raises(ValueError,match='nulle'):schnieper_bootstrap(data,simulations=100,seed=1)
