"""Chargement explicite des sources, aucune donnée brute embarquée dans Git."""
import hashlib,json,urllib.request
from pathlib import Path
import numpy as np
import chainladder as cl
from .triangle import Triangle
ROOT=Path(__file__).resolve().parents[1]
COURSE_URL='https://nicolasbaradel.fr/enseignement/ressources/R/donneesMACK.txt'
DATASETS={'course':'Mack — triangle du cours','genins':'GenIns — bibliothèque','raa':'RAA — bibliothèque','cas':'CAS/NAIC — State Farm, auto particuliers'}

def source_manifest():
 path=ROOT/'data/raw/manifest.json'
 return json.loads(path.read_text()) if path.exists() else {}

def prepare_course():
 folder=ROOT/'data/raw';folder.mkdir(parents=True,exist_ok=True)
 path=folder/'donneesMACK.txt';manifest=folder/'manifest.json'
 if not path.exists():path.write_bytes(urllib.request.urlopen(COURSE_URL,timeout=30).read())
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 m=source_manifest()
 published=ROOT/'reports/data_manifest.json'
 if published.exists():
  expected=json.loads(published.read_text()).get('course',{}).get('sha256')
  if expected and expected!=digest:raise ValueError('La source distante diffère de la version documentée. Revue de version requise.')
 if m.get('course',{}).get('sha256',digest)!=digest:raise ValueError('L’empreinte locale du triangle du cours a changé.')
 m['course']={'url':COURSE_URL,'sha256':digest,'bytes':path.stat().st_size,'unit':'unités non précisées dans le fichier','calendar':'non précisé dans le fichier'}
 manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2))
 return path

def load_dataset(key):
 if key=='course':
  path=ROOT/'data/raw/donneesMACK.txt'
  if not path.exists():raise FileNotFoundError('Données du cours absentes. Exécuter python -m pipeline.prepare_data avant de lancer l’interface.')
  metadata=source_manifest().get('course',{})
  if metadata.get('sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('Empreinte du fichier source invalide.')
  rows=[[float(v.strip()) if v.strip() else np.nan for v in line.split('&')] for line in path.read_text().splitlines()]
  return Triangle(np.array(rows),tuple(f'Année {i+1}' for i in range(len(rows))),DATASETS[key],'unités du cours','unspecified',COURSE_URL)
 if key in ('genins','raa'):
  t=cl.load_sample(key)
  return Triangle(t.values[0,0],tuple(str(v) for v in t.origin),DATASETS[key],'unités de la source','unspecified',f'chainladder {cl.__version__} / {key}',str(t.valuation_date.date()))
 if key=='cas':
  data=cl.load_sample('clrd');t=data[(data['LOB']=='ppauto')&(data['GRNAME']=='State Farm Mut Grp')]['CumPaidLoss']
  return Triangle(t.values[0,0],tuple(str(v) for v in t.origin),DATASETS[key],'unités CAS/NAIC non converties','paid',f'CAS Loss Reserve Database via chainladder {cl.__version__}, clrd.csv ; un seul groupe, une seule branche',str(t.valuation_date.date()))
 raise ValueError('Jeu de données inconnu.')

def library_sources():
 folder=Path(cl.__file__).parent/'utils/data'
 return {name:{'version':cl.__version__,'sha256':hashlib.sha256((folder/f'{name}.csv').read_bytes()).hexdigest(),
 'source':f'https://github.com/casact/chainladder-python/tree/v{cl.__version__}/chainladder/utils/data','redistributed':False} for name in ['genins','raa','clrd']}
