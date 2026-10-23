#!/usr/bin/env python3
"""Optional, descriptive visual diagnostics. Numeric rules never replace human review."""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

VERSION = '1.0.0'

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def probe(video):
    raw = subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)], stderr=subprocess.PIPE)
    data = json.loads(raw)
    stream = next(s for s in data['streams'] if s['codec_type'] == 'video')
    return {'fps': float(Fraction(stream['avg_frame_rate'])), 'container_duration_seconds': float(data['format'].get('duration',0)), 'width':stream['width'], 'height':stream['height'], 'codec':stream.get('codec_name')}

def validate_config(c):
    from jsonschema import Draft202012Validator
    schema = json.loads((Path(__file__).resolve().parents[1] / 'schemas/visual-check-config.schema.json').read_text(encoding='utf-8'))
    errors = sorted(Draft202012Validator(schema).iter_errors(c), key=lambda e:str(e.path))
    if errors: raise ValueError('; '.join(f'{list(e.path)}: {e.message}' for e in errors))
    for s in c['scenes']:
        if s['end_frame'] <= s['start_frame']: raise ValueError('scene [start,end) must have end > start')
    return c

def _read_exact(stream, n):
    pieces=[]; remaining=n
    while remaining:
        chunk=stream.read(remaining)
        if not chunk: break
        pieces.append(chunk);remaining-=len(chunk)
    return b''.join(pieces)

def analyze(video, config, max_frames=18000):
    c=validate_config(config)
    digest=sha256(video)
    if digest != c['video_sha256']: raise ValueError('video_sha256 mismatch: wrong video version')
    meta=probe(video)
    scale=f"{c['width']}:{c['height']}"
    cmd=['ffmpeg','-v','error','-i',str(video),'-map','0:v:0','-vf',f'scale={scale}:flags=bicubic','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','-']
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    nbytes=c['width']*c['height']*3
    if max_frames<1 or c['width']*c['height']*max_frames>300_000_000:
        proc.kill();proc.stdout.close();proc.stderr.close();proc.wait()
        raise ValueError('analysis pixel budget exceeded; lower --max-frames or configured scale')
    frames=[]; prev=None
    try:
        while True:
            raw=_read_exact(proc.stdout,nbytes)
            if not raw: break
            if len(raw)!=nbytes: raise ValueError('truncated decoded frame')
            if len(frames)>=max_frames: raise ValueError('max_frames exceeded; limit analysis to a shorter clip')
            # ITU-R BT.709 luma, full-range RGB; no temporal/spatial smoothing.
            luma=[.2126*raw[i]+.7152*raw[i+1]+.0722*raw[i+2] for i in range(0,nbytes,3)]
            mean=sum(luma)/len(luma)
            contrast=math.sqrt(sum((v-mean)**2 for v in luma)/len(luma))
            motion=None if prev is None else sum(abs(a-b) for a,b in zip(prev,luma))/len(luma)
            brand={color['label']:sum(math.dist(raw[i:i+3],color['rgb'])<=color['tolerance'] for i in range(0,nbytes,3))/len(luma) for color in c.get('brand_colors',[])}
            frames.append({'frame':len(frames),'second':len(frames)/meta['fps'],'motion_mad':motion,'mean_luma':mean,'luma_stddev':contrast,'brand_fraction':brand})
            prev=luma
    finally:
        if sys.exc_info()[0] is not None: proc.kill()
        proc.stdout.close()
        stderr=proc.stderr.read().decode('utf-8',errors='replace')
        proc.stderr.close()
        returncode=proc.wait()
    if returncode: raise ValueError(f'ffmpeg decode failed: {stderr[-500:]}')
    if not frames: raise ValueError('video has no decoded frames')
    if any(s['end_frame']>len(frames) for s in c['scenes']): raise ValueError('scene exceeds decoded video frames')
    scene_starts={s['start_frame'] for s in c['scenes']}
    events=[{'frame':f['frame'],'kind':'cut-boundary' if f['frame'] in scene_starts else 'within-scene','motion_mad':f['motion_mad']} for f in frames if f['frame'] in scene_starts and f['frame']>0 or f['motion_mad'] is not None and f['motion_mad']>=c['cut_threshold']]
    static=[];begin=None
    for i,f in enumerate(frames):
        quiet=f['motion_mad'] is not None and f['motion_mad']<=c['motion_threshold']
        if quiet and begin is None:begin=i
        if not quiet and begin is not None:static.append({'start_frame':begin,'end_frame':i});begin=None
    if begin is not None:static.append({'start_frame':begin,'end_frame':len(frames)})
    per_second=defaultdict(list)
    for f in frames:per_second[int(f['second'])].append(f)
    def aggregate(items):
        static_count=sum(f['motion_mad'] is not None and f['motion_mad']<=c['motion_threshold'] for f in items)
        brands={color['label']:sum(f['brand_fraction'][color['label']] for f in items)/len(items) for color in c.get('brand_colors',[])}
        return {'frames':len(items),'static_frames':static_count,'static_fraction':static_count/len(items),'brand_fraction':brands,'mean_motion_mad':sum(f['motion_mad'] for f in items if f['motion_mad'] is not None)/max(1,sum(f['motion_mad'] is not None for f in items)),'mean_luma':sum(f['mean_luma'] for f in items)/len(items),'mean_contrast':sum(f['luma_stddev'] for f in items)/len(items)}
    scenes=[{**s,**aggregate(frames[s['start_frame']:s['end_frame']]),'events':[e for e in events if s['start_frame']<=e['frame']<s['end_frame']]} for s in c['scenes']]
    coverage=[0]*len(frames)
    for s in c['scenes']:
        for i in range(s['start_frame'],s['end_frame']):coverage[i]+=1
    overlaps=[{'start_frame':start,'end_frame':end} for start,end in _ranges([x>1 for x in coverage])]
    samples=[{'frame':f['frame'],'second':f['second'],'mean_luma':f['mean_luma'],'luma_stddev':f['luma_stddev']} for f in frames if f['frame']%c['sample_every_frames']==0]
    rules={}
    for name in ('max_static_frames','min_mean_luma'):
        if name not in c.get('rules',{}):continue
        value=max((x['end_frame']-x['start_frame'] for x in static),default=0) if name=='max_static_frames' else aggregate(frames)['mean_luma']
        threshold=c['rules'][name]
        rules[name]={'status':'pass' if (value<=threshold if name=='max_static_frames' else value>=threshold) else 'fail','measured_value':value,'expected_value':threshold}
    return {'schema_version':'1.0.0','status':'informational','video_sha256':digest,'analysis_profile':c['analysis_profile'],'method':{'tool_version':VERSION,'ffmpeg_version':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0],'ffprobe_version':subprocess.check_output(['ffprobe','-version'],text=True).splitlines()[0],'fps':meta['fps'],'scale':scale,'color':'rgb24 full-range; BT.709 luma','filter':'bicubic scale; no blur','motion':'mean absolute difference of consecutive scaled luma frames','contrast':'population stddev of scaled luma','sample_every_frames':c['sample_every_frames'],'scene_bounds':'explicit [start,end); source config','overlap_policy':'per-scene independent; whole-video frames counted once'},'video':{'frame_count':len(frames),'video_duration_seconds':len(frames)/meta['fps'],'container_duration_seconds':meta['container_duration_seconds'], 'codec':meta['codec']},'whole_video':aggregate(frames),'frames':frames,'per_second':[{'second':k,**aggregate(v)} for k,v in sorted(per_second.items())],'scenes':scenes,'overlaps':overlaps,'unassigned_frames':sum(x==0 for x in coverage),'static_intervals':static,'events':events,'sample_index':samples,'rules':rules,'human_review':'pending; metrics do not approve creative quality, readability, rights or release'}

def _ranges(flags):
    start=None
    for i,v in enumerate([*flags,False]):
        if v and start is None:start=i
        if not v and start is not None:yield start,i;start=None

def compare(a,b):
    keys=('analysis_profile','method')
    if any(a[k]!=b[k] for k in keys):return {'comparable':False,'reason':'analysis profile/method mismatch; no numeric improvement conclusion'}
    return {'comparable':True,'motion_delta':b['whole_video']['mean_motion_mad']-a['whole_video']['mean_motion_mad']}

def gate_run(result, context, output_uri):
    rule=context['rule']
    selected=result.get('rules',{}).get(rule)
    status=selected['status'] if selected else 'blocked'
    evidence=[{'description':f'视觉诊断 {rule}; 有效视频哈希与分析口径见独立 JSON；不代表人工签认','uri':output_uri}]
    if result.get('video_sha256'):evidence[0]['sha256']=result['video_sha256']
    if selected:evidence[0].update(measured_value=selected['measured_value'],expected_value=selected['expected_value'])
    return {'id':context['id'],'version':context['version'],'schema_version':'1.0.0','record_type':'GateRun','checklist_ref':context['checklist_ref'],'check_id':context['check_id'],'rule_version':context['rule_version'],'target':context['target'],'status':status,'evidence':evidence,'owner':context['owner'],'checked_at':datetime.now(timezone.utc).isoformat(),'checker_type':'automated','tool_version':VERSION,'configuration_version':context['configuration_version'],'dependency_refs':context.get('dependency_refs',[]),'diagnostic': '缺少项目显式规则阈值' if not selected else '客观配置规则；人工审片仍需独立 GateRun'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);p.add_argument('config',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--max-frames',type=int,default=18000);p.add_argument('--gate-context',type=Path,help='JSON with exact checklist/target/rule metadata');p.add_argument('--gate-output',type=Path);a=p.parse_args()
    if a.gate_context and not a.gate_output:p.error('--gate-context requires --gate-output')
    if a.gate_output and not a.gate_context:p.error('--gate-output requires --gate-context')
    config={}
    try:
        config=json.loads(a.config.read_text(encoding='utf-8'))
        result=analyze(a.video,config,a.max_frames)
    except (OSError,ValueError,KeyError,ImportError,subprocess.SubprocessError) as e:
        result={'schema_version':'1.0.0','status':'blocked','diagnostic':str(e),'human_review':'pending'}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    gate_status=None
    if a.gate_context:
        context=json.loads(a.gate_context.read_text(encoding='utf-8'))
        blocked=result['status']=='blocked'
        if blocked:
            result={'rules':{}}
        run=gate_run(result,context,str(a.output))
        if blocked:run['diagnostic']='必需视频、解码工具或配置不可用；见诊断 JSON'
        gate_status=run['status']
        a.gate_output.write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status': 'blocked' if a.gate_context and blocked else result['status'],'output':str(a.output),'gate_status':gate_status},ensure_ascii=False))
    return 2 if result.get('status')=='blocked' or gate_status=='blocked' else (1 if gate_status=='fail' else 0)
if __name__=='__main__':raise SystemExit(main())
