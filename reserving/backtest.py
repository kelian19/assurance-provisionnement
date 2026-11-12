"""Diagonales calendaires connues masquées, sans utilisation des facteurs futurs."""
import numpy as np
import pandas as pd
from .triangle import validate,observed_mask
from .mack import chain_ladder

def diagonal_backtest(cumulative,max_diagonals=3):
 c=validate(cumulative);n=len(c);rows=[]
 for hidden in range(1,min(max_diagonals,n-4)+1):
  size=n-hidden
  train=c[:size,:size].copy();train[~observed_mask(size)]=np.nan
  f,projected,latest,reserves=chain_ladder(train)
  # Existing origins only, excluding the oldest beyond the fitted maturity and the new origin.
  for i in range(1,size):
   j=size-i;prev=c[i,j-1];actual=c[i,j];predicted=prev*f[j-1]
   rows.append({'hidden_diagonals':hidden,'origin_index':i,'development_index':j,'observed_cumulative':actual,
      'predicted_cumulative':predicted,'observed_increment':actual-prev,'predicted_increment':predicted-prev,'error':predicted-actual})
 return pd.DataFrame(rows)

def backtest_summary(rows):
 if rows.empty:return pd.DataFrame()
 grouped=rows.groupby('hidden_diagonals').agg(cells=('error','size'),observed_increment=('observed_increment','sum'),predicted_increment=('predicted_increment','sum'),mean_error=('error','mean'),mae=('error',lambda x:float(np.abs(x).mean())))
 grouped['observed_predicted']=np.where(grouped.predicted_increment!=0,grouped.observed_increment/grouped.predicted_increment,np.nan)
 return grouped.reset_index()
