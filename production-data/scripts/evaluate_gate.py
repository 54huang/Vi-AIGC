#!/usr/bin/env python3
"""Summarize version-matched GateRun records for a checklist target."""
import argparse, json
from pathlib import Path
import yaml

def evaluate(package: Path, checklist_id: str, checklist_version: str, target_id: str, target_version: str):
    records=[]
    for path in [*package.rglob('*.yaml'),*package.rglob('*.yml')]:
        try:
            x=yaml.safe_load(path.read_text(encoding='utf-8'))
            if isinstance(x,dict): records.append(x)
        except Exception: continue
    checklist=next((r for r in records if r.get('record_type')=='GateChecklist' and (r.get('id'),r.get('version'))==(checklist_id,checklist_version)),None)
    if not checklist: return {'status':'blocked','diagnostics':['指定 GateChecklist 不存在']}
    results=[]; blocking=False
    for check in checklist['checks']:
        runs=[r for r in records if r.get('record_type')=='GateRun' and r.get('checklist_ref')=={'id':checklist_id,'version':checklist_version} and r.get('check_id')==check['check_id'] and r.get('rule_version')==check['rule_version'] and (not check.get('configuration_ref') or r.get('configuration_version')==check['configuration_ref']) and (not check.get('dependency_refs') or {(x['id'],x['version']) for x in r.get('dependency_refs',[])}=={(x['id'],x['version']) for x in check['dependency_refs']}) and r.get('target',{}).get('id')==target_id and r.get('target',{}).get('version')==target_version]
        runs.sort(key=lambda r:r.get('checked_at',''))
        current=runs[-1] if runs else None
        status=current.get('status') if current else 'blocked'
        if status in ('fail','blocked') and check.get('blocking',True): blocking=True
        if status=='not-applicable' and (not check.get('allow_not_applicable') or not current or not current.get('na_reason') or not current.get('na_authorized_by')):
            blocking=True
        results.append({'check_id':check['check_id'],'status':status,'gate_run_id':current.get('id') if current else None,'evidence':current.get('evidence',[]) if current else [],'required':check.get('required',True),'blocking':check.get('blocking',True)})
    if blocking or any(x['status']=='blocked' and x['required'] for x in results): status='blocked'
    elif any(x['status']=='fail' and x['required'] for x in results): status='fail'
    else: status='pass'
    return {'checklist_ref':{'id':checklist_id,'version':checklist_version},'stage':checklist['stage'],'target':{'id':target_id,'version':target_version},'status':status,'checks':results}

def main():
    p=argparse.ArgumentParser(); p.add_argument('package',type=Path); p.add_argument('--checklist-id',required=True); p.add_argument('--checklist-version',required=True); p.add_argument('--target-id',required=True); p.add_argument('--target-version',required=True); a=p.parse_args()
    result=evaluate(a.package,a.checklist_id,a.checklist_version,a.target_id,a.target_version); print(json.dumps(result,ensure_ascii=False,indent=2)); return {'pass':0,'fail':1,'blocked':2}[result['status']]
if __name__=='__main__': raise SystemExit(main())
