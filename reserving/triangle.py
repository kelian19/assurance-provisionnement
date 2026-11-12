"""Contrat d'entrée : triangle carré annuel, NA futurs et cumuls strictement positifs."""
from dataclasses import dataclass
from io import StringIO
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class Triangle:
    cumulative: np.ndarray
    origins: tuple[str,...]
    name: str = 'Triangle importé'
    unit: str = 'unités'
    nature: str = 'unspecified'
    source: str = ''
    valuation: str = 'non renseignée'

    def __post_init__(self):
        c=validate(self.cumulative)
        if len(self.origins)!=len(c) or len(set(self.origins))!=len(c):raise ValueError('Les origines doivent être uniques et correspondre aux lignes.')
        if self.nature not in ('paid','incurred','unspecified'):raise ValueError('Nature de triangle inconnue.')
        c.setflags(write=False);object.__setattr__(self,'cumulative',c)

    @property
    def n(self):return len(self.cumulative)
    def frame(self):return pd.DataFrame(self.cumulative,index=self.origins,columns=[f'D{j+1}' for j in range(self.n)])

def observed_mask(n):return np.add.outer(np.arange(n),np.arange(n))<n

def validate(values):
    c=np.array(values,dtype=float,copy=True)
    if c.ndim!=2 or c.shape[0]!=c.shape[1] or not 2<=len(c)<=30:raise ValueError('Triangle carré requis : 2 à 30 années de survenance et de développement.')
    mask=observed_mask(len(c))
    if not np.isfinite(c[mask]).all():raise ValueError('Une cellule observée est manquante ou non finie. Les trous internes ne sont pas acceptés.')
    if not np.isnan(c[~mask]).all():raise ValueError('Les cellules futures doivent être vides/NA. Un zéro futur ne signifie pas une valeur inconnue.')
    if (c[mask]<=0).any():raise ValueError('Cette V1 exige des cumuls observés strictement positifs. Ne pas remplacer les zéros par une petite constante.')
    return c

def to_incremental(cumulative):
    c=validate(cumulative);return np.concatenate([c[:,:1],np.diff(c,axis=1)],axis=1)

def from_incremental(incremental):
    a=np.asarray(incremental,dtype=float)
    if a.ndim!=2 or a.shape[0]!=a.shape[1]:raise ValueError('Triangle incrémental carré requis.')
    return validate(np.cumsum(a,axis=1))

def read_csv(payload, *, representation='cumulative',unit='unités',nature='unspecified',name='Triangle importé',valuation='non renseignée'):
    text=payload.decode('utf-8-sig') if isinstance(payload,bytes) else str(payload)
    if len(text)>2_000_000:raise ValueError('Fichier trop volumineux : maximum 2 Mo.')
    table=pd.read_csv(StringIO(text),sep=None,engine='python',dtype=str)
    if len(table.columns)<3 or table.columns[0]!='origin':raise ValueError('La première colonne doit être origin, suivie de D1, D2, …, Dn.')
    if list(table.columns[1:])!=[f'D{j+1}' for j in range(len(table.columns)-1)]:raise ValueError('Colonnes attendues : origin,D1,D2,…,Dn, dans cet ordre.')
    origins=tuple(table['origin'].astype(str))
    if table.origin.isna().any():raise ValueError('Une origine est manquante.')
    numeric_origins=pd.to_numeric(table.origin,errors='coerce')
    if numeric_origins.notna().all() and not np.all(np.diff(numeric_origins)==1):raise ValueError('Les années numériques doivent être croissantes et consécutives.')
    try:a=table.iloc[:,1:].apply(pd.to_numeric,errors='raise').to_numpy(dtype=float)
    except (ValueError,TypeError) as exc:raise ValueError('Montants numériques attendus ; décimales avec point, sans séparateur de milliers.') from exc
    if representation=='incremental':a=from_incremental(a)
    elif representation!='cumulative':raise ValueError('Représentation inconnue.')
    return Triangle(a,origins,name,unit,nature,'Fichier fourni par l’utilisateur',valuation)
