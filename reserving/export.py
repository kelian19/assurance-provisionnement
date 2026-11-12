"""Dossier exportable : source, hypothèses, résultats et empreintes ; aucune sauvegarde de fichiers client."""
import hashlib,json
from datetime import datetime,timezone
import numpy as np

def triangle_fingerprint(triangle):
    payload={'origins':triangle.origins,'values':np.nan_to_num(triangle.cumulative,nan=-1).tolist(),'unit':triangle.unit,'nature':triangle.nature,'valuation':triangle.valuation}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()

def build_report(triangle,result,bootstrap=None):
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'engine_version':'reserving-v1','triangle_sha256':triangle_fingerprint(triangle),
       'input':{'name':triangle.name,'origins':triangle.origins,'source':triangle.source,'unit':triangle.unit,'nature':triangle.nature,'valuation':triangle.valuation},
       'assumptions':result.diagnostics,'total_reserve':result.total_reserve,'mack_total_rmsep':result.total_rmsep,
       'annual_results':result.summary(triangle).to_dict('records'),'development_factors':result.factors.tolist(),'mack_sigma2':result.sigma2.tolist(),
       'mack_total_process_msep':float(result.process_msep.sum()),'mack_total_parameter_msep':float(result.parameter_covariance.sum()),
       'validation_status':'demonstrator_reference_checked_not_company_approved','interpretation':'remaining payments' if triangle.nature=='paid' else 'future incurred development' if triangle.nature=='incurred' else 'nature not confirmed: future development only'}
    if bootstrap is not None:report['bootstrap']={'summary':bootstrap.summary(),'diagnostics':bootstrap.diagnostics}
    return report

def report_json(triangle,result,bootstrap=None):return json.dumps(build_report(triangle,result,bootstrap),ensure_ascii=False,indent=2,allow_nan=False)
