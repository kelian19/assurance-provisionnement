import numpy as np
import pytest
from reserving.triangle import read_csv,validate,from_incremental,to_incremental
from reserving.data import load_dataset

def test_csv_roundtrip_and_incremental_conversion():
 t=load_dataset('course');frame=t.frame().reset_index(names='origin');payload=frame.to_csv(index=False)
 parsed=read_csv(payload);np.testing.assert_equal(parsed.cumulative,t.cumulative)
 np.testing.assert_allclose(from_incremental(to_incremental(t.cumulative)),t.cumulative,equal_nan=True)

@pytest.mark.parametrize('change',[lambda x:x.__setitem__((2,0),np.nan),lambda x:x.__setitem__((9,9),0),lambda x:x.__setitem__((0,0),0),lambda x:x.__setitem__((0,0),np.inf)])
def test_invalid_triangle_rejected(change):
 x=load_dataset('course').cumulative.copy();change(x)
 with pytest.raises(ValueError):validate(x)

def test_wrong_schema_or_size_rejected():
 with pytest.raises(ValueError):read_csv('year,A,B\n2000,10,20\n2001,20,')
 with pytest.raises(ValueError):validate(np.ones((4,3)))

def test_out_of_order_numeric_origins_are_rejected():
 with pytest.raises(ValueError,match='consécutives'):read_csv('origin,D1,D2\n2021,10,20\n2020,20,')
