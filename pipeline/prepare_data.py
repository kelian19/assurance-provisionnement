from pathlib import Path
import json
from reserving.data import prepare_course,source_manifest,library_sources

def main():
 prepare_course();root=Path(__file__).resolve().parents[1];(root/'reports').mkdir(exist_ok=True)
 m={'course':source_manifest()['course'],'library_samples':library_sources()}
 (root/'reports/data_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
 print('Source du cours téléchargée et empreintes enregistrées. Les fichiers bruts restent hors Git.')
if __name__=='__main__':main()
