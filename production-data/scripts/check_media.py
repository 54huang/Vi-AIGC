#!/usr/bin/env python3
"""Reproducible, local media checks; missing tools/config produce BLOCKED, never PASS."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

VERSION='1.1.0'
from audio_metrics import measure as measure_audio

def run(cmd):
    try:
        return subprocess.run(cmd,capture_output=True,text=True,check=False)
    except OSError as exc:
        return None, str(exc)

def subtitle_intervals(path: Path):
    text=path.read_text(encoding='utf-8-sig')
    pattern=r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})'
    def sec(value):
        h,m,s=value.replace(',', '.').split(':'); return int(h)*3600+int(m)*60+float(s)
    return [(sec(a),sec(b)) for a,b in re.findall(pattern,text)]

def file_sha256(path: Path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def union_duration(intervals):
    end=total=0.0
    for start,stop in sorted(intervals):
        start=max(0.0,start); stop=max(start,stop)
        if stop<=end: continue
        total += stop-max(start,end); end=stop
    return total

def check_media(media: Path, config_path: Path, subtitles: Path|None=None):
    result={'checker':'media-check','checker_version':VERSION,'status':'blocked','media':str(media),'measurements':{},'checks':[],'diagnostics':[]}
    if not config_path.is_file(): result['diagnostics'].append('检查配置文件缺失'); return result
    try: cfg=json.loads(config_path.read_text(encoding='utf-8'))
    except Exception as exc: result['diagnostics'].append(f'配置无法解析：{exc}'); return result
    try:
        from jsonschema import Draft202012Validator
        schema=json.loads((Path(__file__).resolve().parents[1]/'schemas/media-check-config.schema.json').read_text(encoding='utf-8'))
        errors=list(Draft202012Validator(schema).iter_errors(cfg))
        if errors:
            result['diagnostics'].append('配置不符合 Schema：'+'; '.join(e.message for e in errors)); return result
    except Exception as exc:
        result['diagnostics'].append(f'无法验证媒体配置 Schema：{exc}'); return result
    required=('duration_tolerance_seconds','subtitle_min_coverage','audio_peak_dbfs_max','specification','tool_versions')
    missing=[x for x in required if x not in cfg]
    if missing: result['diagnostics'].append('配置缺少字段：'+', '.join(missing)); return result
    if not media.is_file(): result['diagnostics'].append('媒体文件不存在'); return result
    for binary in ('ffprobe','ffmpeg'):
        if not shutil.which(binary): result['diagnostics'].append(f'缺少检查工具 {binary}'); return result
    ver={}
    for binary in ('ffprobe','ffmpeg'):
        p=subprocess.run([binary,'-version'],capture_output=True,text=True)
        actual=(p.stdout or p.stderr).splitlines()[0] if p.returncode==0 else ''
        expected=cfg['tool_versions'].get(binary)
        if not actual or expected not in actual:
            result['diagnostics'].append(f'{binary} 版本与配置不符或不可读：期望包含 {expected!r}，实测 {actual!r}'); return result
        ver[binary]=actual
    probe=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(media)],capture_output=True,text=True)
    if probe.returncode: result['diagnostics'].append('媒体不可读取：'+probe.stderr.strip()); return result
    try: info=json.loads(probe.stdout)
    except Exception as exc: result['diagnostics'].append(f'ffprobe 返回无效数据：{exc}'); return result
    streams=info.get('streams',[]); video=next((x for x in streams if x.get('codec_type')=='video'),None); audio=next((x for x in streams if x.get('codec_type')=='audio'),None)
    if not video: result['diagnostics'].append('媒体中缺少视频流'); return result
    duration=float(info.get('format',{}).get('duration',video.get('duration',0)) or 0)
    spec=cfg['specification']; checks=[]
    def emit(name,ok,measured,expected): checks.append({'check_id':name,'status':'pass' if ok else 'fail','measured':measured,'expected':expected})
    emit('width',video.get('width')==spec['width'],video.get('width'),spec['width'])
    emit('height',video.get('height')==spec['height'],video.get('height'),spec['height'])
    fps=video.get('avg_frame_rate','0/1').split('/'); actual_fps=float(fps[0])/float(fps[1]) if len(fps)==2 and float(fps[1]) else 0
    emit('frame_rate',abs(actual_fps-float(spec['frame_rate']))<=float(cfg['frame_rate_tolerance']),actual_fps,spec['frame_rate'])
    if spec.get('video_codec'): emit('video_codec',video.get('codec_name')==spec['video_codec'],video.get('codec_name'),spec['video_codec'])
    if spec.get('container'): emit('container',spec['container'] in info.get('format',{}).get('format_name',''),info.get('format',{}).get('format_name'),spec['container'])
    if spec.get('audio_codec') and audio: emit('audio_codec',audio.get('codec_name')==spec['audio_codec'],audio.get('codec_name'),spec['audio_codec'])
    if 'expected_duration_seconds' not in cfg: result['diagnostics'].append('缺少 expected_duration_seconds，无法检查时长'); return result
    expected_duration=float(cfg['expected_duration_seconds']); tolerance=float(cfg['duration_tolerance_seconds'])
    emit('duration',abs(duration-expected_duration)<=tolerance,duration,{'seconds':expected_duration,'tolerance':tolerance})
    if cfg.get('required_subtitle',True):
        if not subtitles or not subtitles.is_file(): result['diagnostics'].append('必需字幕文件缺失'); return result
        intervals=subtitle_intervals(subtitles)
        if not intervals: result['diagnostics'].append('字幕没有可识别的 SRT/VTT 时间码'); return result
        outside=[x for x in intervals if x[0]<0 or x[1]>duration or x[1]<=x[0]]
        if outside: emit('subtitle_bounds',False,outside,f'0..{duration:.3f}s with end > start')
        else: emit('subtitle_bounds',True,'all cues within media duration',f'0..{duration:.3f}s')
        coverage=min(1.0,union_duration(intervals)/duration) if duration else 0
        emit('subtitle_coverage',coverage>=float(cfg['subtitle_min_coverage']),coverage,cfg['subtitle_min_coverage'])
    if cfg.get('required_audio',True):
        if not audio: result['diagnostics'].append('必需音频流缺失'); return result
        peak=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(media),'-vn','-af','volumedetect','-f','null','NUL' if sys.platform=='win32' else '/dev/null'],capture_output=True,text=True)
        if peak.returncode: result['diagnostics'].append('ffmpeg sample peak 检查失败：'+peak.stderr.strip()[-500:]); return result
        match=re.search(r'max_volume:\s*(-?inf|[-\d.]+) dB',peak.stderr)
        if not match: result['diagnostics'].append('无法从 ffmpeg volumedetect 取得音频峰值'); return result
        peak_db=-120.0 if match.group(1)=='-inf' else float(match.group(1))
        emit('audio_peak_dbfs',peak_db<=float(cfg['audio_peak_dbfs_max']),peak_db,cfg['audio_peak_dbfs_max'])
    if cfg.get('audio_metrics'):
        extras, evidence=measure_audio(media,cfg,duration,ver,file_sha256,config_path,'NUL' if sys.platform=='win32' else '/dev/null')
        checks.extend(extras); result['audio_evidence']=evidence
        for check in extras:
            if check['status']=='blocked' and check.get('required',True):
                result['diagnostics'].append(check['check_id']+': '+check.get('diagnostic','measurement blocked'))
    result['tool_versions']=ver; result['input_size_bytes']=media.stat().st_size; result['input_sha256']=file_sha256(media); result['measurements']={'duration_seconds':duration,'video_codec':video.get('codec_name'),'width':video.get('width'),'height':video.get('height'),'frame_rate':actual_fps,'audio_present':audio is not None}; result['checks']=checks
    result['status']='blocked' if any(x['status']=='blocked' and x.get('required',True) for x in checks) else ('fail' if any(x['status']=='fail' and x.get('required',True) for x in checks) else 'pass'); return result

def main():
    ap=argparse.ArgumentParser(description='Local media gate checks; no semantic or rights sufficiency judgments.')
    ap.add_argument('media',type=Path); ap.add_argument('--config',required=True,type=Path); ap.add_argument('--subtitles',type=Path)
    args=ap.parse_args(); result=check_media(args.media,args.config,args.subtitles); print(json.dumps(result,ensure_ascii=False,indent=2)); return {'pass':0,'fail':1,'blocked':2}[result['status']]
if __name__=='__main__': raise SystemExit(main())
