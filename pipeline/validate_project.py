"""Mesure les résultats effectivement obtenus ; n’entraîne aucun modèle sur les diagonales masquées."""
import hashlib,json,platform,sys
from pathlib import Path
import importlib.metadata as md
import numpy as np
import pandas as pd
from reserving.data import load_dataset
from reserving.mack import mack
from reserving.reference import reference_mack
from reserving.bootstrap import odp_bootstrap
from reserving.backtest import diagonal_backtest,backtest_summary
from reserving.export import build_report
ROOT=Path(__file__).resolve().parents[1]

def main():
 comparisons=[];backtests={};boots={}
 for key in ['course','genins','raa','cas']:
  t=load_dataset(key);m=mack(t.cumulative);ref=reference_mack(t.cumulative)
  assert abs(m.total_reserve-ref['reserve'])<1e-6
  assert abs(m.total_rmsep-ref['rmsep'])<1e-6
  comparisons.append({'dataset':key,'reserve':m.total_reserve,'mack_rmsep':m.total_rmsep,'library_reserve':ref['reserve'],'library_rmsep':ref['rmsep'],'absolute_reserve_gap':abs(m.total_reserve-ref['reserve']),'absolute_rmsep_gap':abs(m.total_rmsep-ref['rmsep'])})
  bt=diagonal_backtest(t.cumulative);bt.to_csv(ROOT/f'reports/backtest_{key}.csv',index=False)
  backtests[key]=backtest_summary(bt).to_dict('records')
  if key in ['course','cas']:
   b=odp_bootstrap(t.cumulative,simulations=5000,seed=42)
   boots[key]={'summary':b.summary(),'diagnostics':b.diagnostics}
   (ROOT/f'reports/calculation_{key}.json').write_text(json.dumps(build_report(t,m,b),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
   # Simulation values are generated outputs, not raw source observations.
   pd.DataFrame({'scenario':np.arange(1,5001),'reserve':b.predictive_reserves}).to_csv(ROOT/f'reports/scenarios_{key}.csv',index=False)
 versions={name:md.version(name) for name in ['numpy','pandas','scipy','chainladder','streamlit','plotly','pytest','scikit-learn','sparse','numba']}
 report={'engine_version':'reserving-v1','python':platform.python_version(),'versions':versions,
 'deterministic_comparisons':comparisons,'course_reference':18_680_847.767812435,'course_reference_matched':abs(comparisons[0]['reserve']-18_680_847.767812435)<1e-7,
 'backtests':backtests,'bootstrap':boots,
 'reference_configuration':{'average':'volume','sigma_interpolation':'mack','tail':1.,'reference_library':'chainladder','reference_version':versions['chainladder']},
 'data_difference':{'course_origin_index_7_development_index_2':2864494,'genins_same_cell':2864498,'datasets_kept_distinct':True},
 'R_reference_executed':False,'R_reference_reason':'Rscript absent in execution environment; optional R validation script supplied',
 'limits':['Fixed tail factor 1','No inflation or discounting','No one-year capital interpretation','Only three known calendar diagonals, not validation of ultimate tails','Bootstrap uses signed Gamma library extension for negative fitted future increments','Deterministic h=1 correction supplied to avoid undefined memory in chainladder 0.10.1','Units of source files preserved, not automatically interpreted as EUR or USD'],
 'publication':'local only; no Site registration or hosting deployment'}
 (ROOT/'reports/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
 direct=['numpy','pandas','scipy','chainladder','streamlit','plotly','pytest','scikit-learn','sparse','numba']
 (ROOT/'requirements.txt').write_text('\n'.join(f'{name}=={versions[name]}' for name in direct)+'\n')
 print(json.dumps({'comparisons':comparisons,'bootstrap':boots,'backtests':backtests},indent=2))
if __name__=='__main__':main()
