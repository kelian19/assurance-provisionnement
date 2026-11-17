"""Chargement explicite des sources, aucune donnée brute embarquée dans Git."""
import hashlib,json,urllib.request
from pathlib import Path
import numpy as np
import chainladder as cl
from .triangle import Triangle
from .schnieper import SchnieperData
ROOT=Path(__file__).resolve().parents[1]
COURSE_URL='https://nicolasbaradel.fr/enseignement/ressources/R/donneesMACK.txt'
SCHNIEPER_URLS={k:f'https://nicolasbaradel.fr/enseignement/ressources/R/donneesSCHNIEPER_{k}.txt' for k in 'NDE'}
DATASETS={'course':'Mack — triangle du cours','genins':'GenIns — bibliothèque','raa':'RAA — bibliothèque','cas':'CAS/NAIC — State Farm, auto particuliers'}

def source_manifest():
 path=ROOT/'data/raw/manifest.json'
 return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def prepare_course():
 folder=ROOT/'data/raw';folder.mkdir(parents=True,exist_ok=True)
 path=folder/'donneesMACK.txt';manifest=folder/'manifest.json'
 if not path.exists():path.write_bytes(urllib.request.urlopen(COURSE_URL,timeout=30).read())
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 m=source_manifest()
 published=ROOT/'reports/data_manifest.json'
 if published.exists():
  expected=json.loads(published.read_text(encoding='utf-8')).get('course',{}).get('sha256')
  if expected and expected!=digest:raise ValueError('La source distante diffère de la version documentée. Revue de version requise.')
 if m.get('course',{}).get('sha256',digest)!=digest:raise ValueError('L’empreinte locale du triangle du cours a changé.')
 m['course']={'url':COURSE_URL,'sha256':digest,'bytes':path.stat().st_size,'unit':'unités non précisées dans le fichier','calendar':'non précisé dans le fichier'}
 manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
 return path

def load_dataset(key):
 if key=='course':
  path=ROOT/'data/raw/donneesMACK.txt'
  if not path.exists():raise FileNotFoundError('Données du cours absentes. Exécuter python -m pipeline.prepare_data avant de lancer l’interface.')
  metadata=source_manifest().get('course',{})
  if metadata.get('sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('Empreinte du fichier source invalide.')
  rows=[[float(v.strip()) if v.strip() else np.nan for v in line.split('&')] for line in path.read_text(encoding='utf-8').splitlines()]
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

def prepare_schnieper():
 """Télécharge N, D, E du cours (empreintes vérifiées contre le manifeste publié)."""
 folder=ROOT/'data/raw';folder.mkdir(parents=True,exist_ok=True)
 published=ROOT/'reports/data_manifest.json';expected=json.loads(published.read_text(encoding='utf-8')).get('schnieper',{}) if published.exists() else {}
 m=source_manifest();entry={}
 for key,url in SCHNIEPER_URLS.items():
  path=folder/f'donneesSCHNIEPER_{key}.txt'
  if not path.exists():path.write_bytes(urllib.request.urlopen(url,timeout=30).read())
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  if expected.get(key,{}).get('sha256',digest)!=digest:raise ValueError(f'La source Schnieper {key} diffère de la version documentée. Revue de version requise.')
  entry[key]={'url':url,'sha256':digest,'bytes':path.stat().st_size}
 m['schnieper']=entry;(folder/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
 return entry

def load_schnieper():
 """Triangles N, D et expositions E de l'exemple 5.4 du cours (Schnieper 1991)."""
 folder=ROOT/'data/raw';metadata=source_manifest().get('schnieper',{})
 raw={}
 for key in 'NDE':
  path=folder/f'donneesSCHNIEPER_{key}.txt'
  if not path.exists():raise FileNotFoundError('Données Schnieper absentes. Exécuter python -m pipeline.prepare_data avant de lancer l’interface.')
  if metadata.get(key,{}).get('sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('Empreinte du fichier source Schnieper invalide.')
  raw[key]=[line for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
 grid=lambda lines:np.array([[float(v.strip()) if v.strip() else np.nan for v in line.split('&')] for line in lines])
 E=np.array([float(v) for v in raw['E']])
 return SchnieperData(grid(raw['N']),grid(raw['D']),E,tuple(f'Année {i+1}' for i in range(len(E))),'Schnieper — exemple 5.4 du cours','unités du cours','/'.join(SCHNIEPER_URLS['N'].split('/')[:-1])+'/donneesSCHNIEPER_{N,D,E}.txt')
