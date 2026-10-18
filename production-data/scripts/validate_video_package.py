#!/usr/bin/env python3
"""Offline deterministic validation for a video-production YAML record package."""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from datetime import date
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_VERSION='1.0.0'
TYPE_TO_SCHEMA={'ProjectProfile':'project-profile','VideoBrief':'video-brief','Claim':'claim','Asset':'asset','Shot':'shot','Review':'review','Release':'release'}
PREFIX={'ProjectProfile':'profile','VideoBrief':'brief','Claim':'claim','Asset':'asset','Shot':'shot','Review':'review','Release':'release'}

def validate(package: Path, schema_dir: Path):
    findings=[]; records=[]
    def add(level,record,field,message,target=None,fix=None):
        findings.append({'level':level,'record_id':record or '<package>','field':field,'target':target,'message':message,'fix':fix})
    files=sorted([*package.rglob('*.yaml'),*package.rglob('*.yml')])
    for path in files:
        try:
            data=yaml.safe_load(path.read_text(encoding='utf-8'))
            if not isinstance(data,dict): raise ValueError('YAML 顶层必须是对象')
        except Exception as e:
            add('ERROR',path.stem,'$',f'无法读取 YAML：{e}','解析失败','修复 YAML 语法并确保顶层为映射对象'); continue
        rid=data.get('id',path.stem); typ=data.get('record_type')
        if typ not in TYPE_TO_SCHEMA:
            add('ERROR',rid,'record_type',f'未知记录类型：{typ!r}',None,'使用七种已定义 record_type 之一'); continue
        sp=schema_dir/(TYPE_TO_SCHEMA[typ]+'.schema.json')
        schema=json.loads(sp.read_text(encoding='utf-8'))
        structural_errors=list(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(data))
        for error in structural_errors:
            pathstr='.'+'.'.join(str(p) for p in error.absolute_path) if error.absolute_path else '$'
            if error.validator == 'required':
                import re
                missing=re.search(r"'([^']+)' is a required property",error.message)
                if missing: pathstr += '.' + missing.group(1)
            add('ERROR',rid,pathstr,error.message,None,'按对应 JSON Schema 修正字段/类型/枚举')
        if not structural_errors: records.append(data)
    by_key={}; by_id=defaultdict(list)
    for r in records:
        key=(r['id'],r['version'])
        if key in by_key: add('ERROR',r['id'],'id',f'重复实体版本 {r["version"]}',r['id'],'保留唯一记录或使用新版本')
        else: by_key[key]=r
        by_id[r['id']].append(r)
    def resolve(rid,ver,field,expected=None,owner=None):
        rec=owner or rid
        target=by_key.get((rid,ver))
        if not target:
            add('ERROR',rec,field,f'引用不存在的 ID/版本 {rid}@{ver}',f'{rid}@{ver}','修正引用，或将缺失版本加入数据包'); return None
        if expected and target['record_type'] not in expected:
            add('ERROR',rec,field,f'引用类型应为 {expected}，实际为 {target["record_type"]}',rid,'引用正确类型的记录'); return None
        return target
    for r in records:
        typ=r['record_type']; rid=r['id']; ver=r['version']
        if typ=='ProjectProfile': continue
        profile=None; brief=None
        if typ=='VideoBrief':
            profile=resolve(r['project_profile']['id'],r['project_profile']['version'],'project_profile',['ProjectProfile'],rid)
        elif typ=='Claim':
            profile=next((x for x in by_id.get(r.get('scope',{}).get('project_id',''),[]) if x['record_type']=='ProjectProfile'),None)
            if r['status']=='expired': add('ERROR',rid,'status','Claim 已过期，不可用于当前制作',None,'更新并重新确认 Claim 或替换引用')
            elif r['status']!='confirmed': add('WARN',rid,'status','Claim 尚未人工确认为 confirmed',None,'由事实责任人确认；机器不会判断主张真假')
        elif typ=='Asset':
            scope=r.get('usage_scope',{}); pid=scope.get('project_id')
            if pid:
                profile=next((x for x in by_id.get(pid,[]) if x['record_type']=='ProjectProfile'),None)
            if r['status'] in ('expired','revoked'): add('ERROR',rid,'status',f'Asset 状态为 {r["status"]}',None,'确认当前授权状态或换用素材')
            elif r['status']=='unverified': add('WARN',rid,'status','Asset 权限未核验',None,'由责任人核验素材权利')
            if r.get('rights_ambiguity'): add('WARN',rid,'rights_ambiguity','授权依据含糊，需人工复核；字段存在不代表授权充分',None,'由权利/法务责任人审阅授权依据')
        elif typ=='Shot':
            bref=r['brief']; brief=resolve(bref['id'],bref['version'],'brief',['VideoBrief'],rid)
            if brief:
                profile=resolve(brief['project_profile']['id'],brief['project_profile']['version'],'brief.project_profile',['ProjectProfile'],rid)
                for cid in r['claim_ids']:
                    if cid not in brief['claim_ids']: add('ERROR',rid,'claim_ids',f'Claim {cid} 未被所属 Brief 声明',cid,'将 Claim 加入 Brief 或移除此处引用')
                for aidref in r['asset_refs']:
                    a=resolve(aidref['id'],aidref['version'],'asset_refs',['Asset'],rid)
                    if a and profile:
                        scope=a.get('usage_scope',{}); channel=brief['channel']; day=date.fromisoformat(brief['planned_release_date'])
                        if scope.get('project_id') not in (None,profile['id']): add('ERROR',rid,'asset_refs',f'Asset 项目范围与 Profile {profile["id"]} 不符',a['id'],'使用适用项目的素材或更新经确认的范围')
                        if scope.get('channels') and channel not in scope['channels']: add('ERROR',rid,'asset_refs',f'Asset 不适用渠道 {channel}',a['id'],'更换素材或由权利人确认适用范围')
                        if scope.get('valid_from') and day<date.fromisoformat(scope['valid_from']): add('ERROR',rid,'asset_refs','Asset 使用日期早于有效期',a['id'],'调整发布计划或更新授权')
                        if scope.get('valid_until') and day>date.fromisoformat(scope['valid_until']): add('ERROR',rid,'asset_refs','Asset 使用日期晚于有效期',a['id'],'调整发布计划或更新授权')
                for cid in r['claim_ids']:
                    c=next((x for x in by_id.get(cid,[]) if x['record_type']=='Claim'),None)
                    if c and brief and c['status']=='expired': add('ERROR',rid,'claim_ids',f'引用过期 Claim {cid}',cid,'更新 Claim 版本并重新确认')
            for refid in r['review_refs']:
                candidates=[x for x in by_id.get(refid,[]) if x['record_type']=='Review']
                if not candidates: add('ERROR',rid,'review_refs',f'Review 不存在：{refid}',refid,'添加有效且绑定当前镜头版本的 Review'); continue
                if len(candidates)>1: add('ERROR',rid,'review_refs',f'Review ID {refid} 有多个版本但引用未指定版本',refid,'将 Review ID 唯一化后再引用')
                for review in candidates:
                    if review['target']['type']!='Shot' or (review['target']['id'],review['target']['version'])!=(rid,ver): add('ERROR',rid,'review_refs',f'Review {refid} 未绑定当前 Shot 版本 {rid}@{ver}',refid,'重新审查当前镜头版本并更新 target')
        elif typ=='Release':
            brief=resolve(r['brief']['id'],r['brief']['version'],'brief',['VideoBrief'],rid)
            selected=[]; closure={}
            for sref in r['shot_versions']:
                s=resolve(sref['id'],sref['version'],'shot_versions',['Shot'],rid)
                if s:
                    selected.append(s)
                    if brief and (s['brief']['id'],s['brief']['version'])!=(brief['id'],brief['version']): add('ERROR',rid,'shot_versions',f'Shot {s["id"]} 不属于 Release 的 Brief 版本',s['id'],'选用同一 Brief 版本中的镜头')
                    for aref in s['asset_refs']: closure[(aref['id'],aref['version'])]=aref
            provided={(x['id'],x['version']) for x in r['asset_refs']}; expected=set(closure)
            if provided!=expected:
                add('ERROR',rid,'asset_refs',f'Release 素材清单与所选 Shot 素材闭包不一致；缺少 {sorted(expected-provided)}，多出 {sorted(provided-expected)}',None,'使 asset_refs 与选定 Shot 版本实际引用素材完全一致')
            for aref in r['asset_refs']: resolve(aref['id'],aref['version'],'asset_refs',['Asset'],rid)
            if brief:
                p=resolve(brief['project_profile']['id'],brief['project_profile']['version'],'brief.project_profile',['ProjectProfile'],rid)
                if p:
                    req=p['review_requirements']; required=[]
                    def collect(target_type,target_id,target_version,scope):
                        for review_type in req.get(scope,[]): required.append((review_type,target_type,target_id,target_version))
                    collect('VideoBrief',brief['id'],brief['version'],'brief')
                    collect('Release',r['id'],r['version'],'release')
                    for s in selected:
                        collect('Shot',s['id'],s['version'],'shot')
                        for ar in s['asset_refs']: collect('Asset',ar['id'],ar['version'],'asset')
                    supplied=[]
                    for refid in r['required_review_refs']:
                        rr=next((x for x in by_id.get(refid,[]) if x['record_type']=='Review'),None)
                        if not rr: add('ERROR',rid,'required_review_refs',f'Required Review 不存在：{refid}',refid,'补充有效审查记录 ID'); continue
                        if len([x for x in by_id.get(refid,[]) if x['record_type']=='Review'])>1: add('ERROR',rid,'required_review_refs',f'Review ID {refid} 多版本引用存在歧义',refid,'将 Review ID 唯一化后再引用')
                        supplied.append(rr)
                        target=rr['target']; resolved=resolve(target['id'],target['version'],'target',['VideoBrief','Claim','Asset','Shot','Release'],rr['id'])
                        if target['type'] != (resolved or {}).get('record_type'): add('ERROR',rr['id'],'target.type','Review target.type 与目标记录类型不一致',target['id'],'修正 target.type')
                        if rr['status']!='approved': add('ERROR',rid,'required_review_refs',f'必需审查 {rr["id"]} 状态为 {rr["status"]}，非 approved',rr['id'],'由指定责任人完成并记录审查；机器不得代批')
                    for rt,tid,tv,v in required:
                        match=next((x for x in supplied if x['review_type']==rt and x['target']['type']==tid and x['target']['id']==tv and x['target']['version']==v),None)
                        if not match: add('ERROR',rid,'required_review_refs',f'缺少规则要求的 {rt} Review：{tid} {tv}@{v}',f'{tid} {tv}@{v}','补充绑定精确对象版本的人工审查记录；不可由 Release 自行省略')
        # Cross-check scope dates for all Claims used by Brief or Shot.
    # Validate Brief indexes and profile-owned record indexes.
    for r in records:
        if r['record_type']=='VideoBrief':
            p=resolve(r['project_profile']['id'],r['project_profile']['version'],'project_profile',['ProjectProfile'],r['id'])
            for sid in r['shot_ids']:
                shots=[x for x in by_id.get(sid,[]) if x['record_type']=='Shot']
                if not shots: add('ERROR',r['id'],'shot_ids',f'Shot 不存在：{sid}',sid,'创建镜头记录或修正 ID')
                elif not any(x['brief']['id']==r['id'] and x['brief']['version']==r['version'] for x in shots): add('ERROR',r['id'],'shot_ids',f'Shot {sid} 未绑定此 Brief 版本',sid,'关联正确 Brief 版本')
            for cid in r['claim_ids']:
                if p and cid not in p['claim_ids']: add('ERROR',r['id'],'claim_ids',f'Claim {cid} 不在 ProjectProfile 索引中',cid,'更新档案索引或引用正确 Claim')
    # Validate Brief-level claim scope after complete lookup.
    for r in records:
        if r['record_type']!='VideoBrief': continue
        profile=resolve(r['project_profile']['id'],r['project_profile']['version'],'project_profile',['ProjectProfile'],r['id'])
        for cid in r['claim_ids']:
            c=next((x for x in by_id.get(cid,[]) if x['record_type']=='Claim'),None)
            if not c: add('ERROR',r['id'],'claim_ids',f'Claim 不存在：{cid}',cid,'创建 Claim 或修正 ID'); continue
            if c['status']=='expired': add('ERROR',r['id'],'claim_ids',f'Claim {cid} 已过期',cid,'更新并重新确认 Claim')
            elif c['status']!='confirmed': add('WARN',r['id'],'claim_ids',f'Claim {cid} 未确认，需人工复核',cid,'由事实责任人确认')
            scope=c.get('scope',{}); day=date.fromisoformat(r['planned_release_date'])
            if profile and scope.get('project_id') not in (None,profile['id']): add('ERROR',r['id'],'claim_ids',f'Claim {cid} 属于其他项目',cid,'使用当前项目 Claim')
            if scope.get('channels') and r['channel'] not in scope['channels']: add('ERROR',r['id'],'claim_ids',f'Claim {cid} 不适用渠道 {r["channel"]}',cid,'更新经确认的 Claim 适用范围')
            if scope.get('valid_from') and day<date.fromisoformat(scope['valid_from']): add('ERROR',r['id'],'claim_ids',f'Claim {cid} 尚未生效',cid,'调整发布日期或确认范围')
            if scope.get('valid_until') and day>date.fromisoformat(scope['valid_until']): add('ERROR',r['id'],'claim_ids',f'Claim {cid} 已超过有效期',cid,'更新 Claim 并重新确认')
    return records,findings

def main():
    parser=argparse.ArgumentParser(description='校验视频生产 YAML 记录包（仅确定性检查，不构成事实/权利/合规批准）')
    parser.add_argument('package',type=Path,nargs='?',default=Path(__file__).resolve().parents[1]/'examples/valid')
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    records,findings=validate(args.package,root/'schemas')
    for f in findings:
        target=f' -> {f["target"]}' if f.get('target') else ''
        print(f'{f["level"]}: {f["record_id"]} {f["field"]}{target}: {f["message"]}')
        if f.get('fix'): print(f'  修复建议：{f["fix"]}')
    errors=sum(x['level']=='ERROR' for x in findings); warns=sum(x['level']=='WARN' for x in findings)
    if errors: print(f'ERROR: {errors} 个阻断问题，{warns} 个警告，检查 {len(records)} 条记录。')
    elif warns: print(f'WARN: 无确定性阻断；{warns} 项需人工复核，检查 {len(records)} 条记录。')
    else: print(f'PASS: {len(records)} 条记录通过确定性检查；机器 PASS 不改变人工 Review 状态或发布状态。')
    print(f'检查器版本：1.0.0；Schema 版本：{SCHEMA_VERSION}；记录 schema_version: {", ".join(sorted({r.get("schema_version","?") for r in records})) or "无"}')
    print('注意：记录一致性通过不证明主张真实、素材权利充分、内容适当或符合任何法律/平台政策。')
    return 1 if errors else (2 if warns else 0)
if __name__=='__main__': raise SystemExit(main())
