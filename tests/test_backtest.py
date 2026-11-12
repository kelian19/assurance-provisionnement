import numpy as np
from reserving.backtest import diagonal_backtest
from reserving.data import load_dataset

def test_withheld_diagonal_cannot_change_its_own_prediction():
 c=load_dataset('course').cumulative.copy();a=diagonal_backtest(c,max_diagonals=1)
 n=len(c)
 for i in range(1,n-1):c[i,n-1-i]*=1.2
 b=diagonal_backtest(c,max_diagonals=1)
 np.testing.assert_allclose(a.predicted_cumulative,b.predicted_cumulative)
 assert not np.allclose(a.observed_cumulative,b.observed_cumulative)

def test_only_observed_future_cells_are_scored():
 c=load_dataset('course').cumulative;b=diagonal_backtest(c)
 assert len(b)==8+7+6
 assert np.isfinite(b.observed_cumulative).all()
