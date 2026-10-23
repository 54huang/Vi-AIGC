"""Synthetic, rights-free diagnostic regression tests."""
import copy, importlib.util, json, shutil, subprocess, tempfile, unittest, yaml
from pathlib import Path
from unittest.mock import patch
try:
 import imageio_ffmpeg
 FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
 FFMPEG=shutil.which('ffmpeg')
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('check_visual',ROOT/'scripts/check_visual.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class VisualTest(unittest.TestCase):
 def setUp(self):
  self.config=json.loads((ROOT/'examples/visual-check-config.example.json').read_text(encoding='utf-8'))
  self.schema=json.loads((ROOT/'schemas/visual-check-config.schema.json').read_text(encoding='utf-8'))
 def test_schema_positive_negative_and_old_config(self):
  Draft202012Validator(self.schema).validate(self.config)
  for f in (ROOT/'examples/invalid').glob('visual-*.json'):
   with self.subTest(f=f):self.assertFalse(Draft202012Validator(self.schema).is_valid(json.loads(f.read_text(encoding='utf-8'))))
  old=json.loads((ROOT/'examples/media-check-config.example.json').read_text(encoding='utf-8'))
  Draft202012Validator(json.loads((ROOT/'schemas/media-check-config.schema.json').read_text(encoding='utf-8'))).validate(old)
 def test_missing_video_or_tool_blocks_gate_and_human_is_separate(self):
  import sys
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);config=d/'config.json';config.write_text(json.dumps(self.config),encoding='utf-8')
   ctx={'rule':'max_static_frames','id':'gate-run_visual-missing','version':'1.0.0','checklist_ref':{'id':'gate_g2-demo','version':'1.0.0'},'check_id':'visual-static','rule_version':'1.0.0','target':{'type':'Shot','id':'shot_demo-opening','version':'1.0.0'},'owner':'test','configuration_version':'1.0.0'}
   context=d/'context.json';context.write_text(json.dumps(ctx),encoding='utf-8')
   with patch.object(sys,'argv',['check_visual.py',str(d/'absent.mp4'),str(config),'--output',str(d/'out.json'),'--gate-context',str(context),'--gate-output',str(d/'gate.json')]):
    self.assertEqual(mod.main(),2)
   result=json.loads((d/'out.json').read_text(encoding='utf-8'))
   run=json.loads((d/'gate.json').read_text(encoding='utf-8'))
   Draft202012Validator(json.loads((ROOT/'schemas/visual-result.schema.json').read_text(encoding='utf-8'))).validate(result)
   self.assertEqual(result['status'],'blocked');self.assertEqual(run['status'],'blocked')
   self.assertNotIn('sha256',run['evidence'][0])
   video=d/'exists.mp4';video.write_bytes(b'synthetic bytes')
   config_data=dict(self.config,video_sha256=mod.sha256(video))
   config.write_text(json.dumps(config_data),encoding='utf-8')
   with patch.object(mod,'probe',side_effect=FileNotFoundError('ffprobe missing')), patch.object(sys,'argv',['check_visual.py',str(video),str(config),'--output',str(d/'out.json'),'--gate-context',str(context),'--gate-output',str(d/'gate.json')]):
    self.assertEqual(mod.main(),2)
   self.assertIn('ffprobe missing',json.loads((d/'out.json').read_text(encoding='utf-8'))['diagnostic'])
   checklist={'id':'gate_g2-demo','version':'1.0.0','stage':'G2','checks':[{'check_id':'visual-static','rule_version':'1.0.0','required':True,'blocking':True},{'check_id':'human-readability','rule_version':'1.0.0','required':True,'blocking':True}]}
   runs=[run]
   self.assertFalse(any(r['check_id']=='human-readability' for r in runs))
   self.assertEqual(checklist['checks'][1]['check_id'],'human-readability')
   pkg=d/'package';pkg.mkdir()
   (pkg/'checklist.yaml').write_text(yaml.safe_dump({'record_type':'GateChecklist',**checklist}),encoding='utf-8')
   (pkg/'machine.yaml').write_text(yaml.safe_dump(run),encoding='utf-8')
   gate_spec=importlib.util.spec_from_file_location('evaluate_gate',ROOT/'scripts/evaluate_gate.py')
   gate=importlib.util.module_from_spec(gate_spec);gate_spec.loader.exec_module(gate)
   self.assertEqual(gate.evaluate(pkg,'gate_g2-demo','1.0.0','shot_demo-opening','1.0.0')['status'],'blocked')
   # Even if the objective check passes, missing human readability review blocks G2.
   run['status']='pass';(pkg/'machine.yaml').write_text(yaml.safe_dump(run),encoding='utf-8')
   self.assertEqual(gate.evaluate(pkg,'gate_g2-demo','1.0.0','shot_demo-opening','1.0.0')['status'],'blocked')
 def test_missing_scene_version_and_range(self):
  for key in ('scenes','video_sha256','motion_threshold'):
   c=copy.deepcopy(self.config);del c[key]
   with self.assertRaises(ValueError):mod.validate_config(c)
  c=copy.deepcopy(self.config);c['scenes'][0]['end_frame']=0
  with self.assertRaises(ValueError):mod.validate_config(c)
 @unittest.skipUnless(FFMPEG,'ffmpeg unavailable')
 def test_synthetic_static_motion_cut_overlap_and_gate(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); raw=d/'rgb.raw';video=d/'synthetic.mkv'
   # 10 still frames, 10 translated pattern frames, then 10 abrupt bright frames.
   data=bytearray()
   for frame in range(30):
    for y in range(8):
     for x in range(8):
      level=20 if frame<10 else (220 if frame>=20 else (170 if (x+frame)%8<4 else 30))
      data.extend((level,level,level))
   raw.write_bytes(data)
   subprocess.run([FFMPEG,'-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size','8x8','-framerate','10','-i',str(raw),'-c:v','ffv1',str(video)],check=True)
   c=copy.deepcopy(self.config);c.update(video_sha256=mod.sha256(video),width=8,height=8,scenes=[{'label':'a','start_frame':0,'end_frame':12},{'label':'b','start_frame':10,'end_frame':30}],sample_every_frames=5,rules={'max_static_frames':5})
   real_popen=subprocess.Popen
   def popen(args,**kw): return real_popen([FFMPEG,*args[1:]],**kw)
   def check(args,**kw): return b'ffmpeg test 7.1\n'
   with patch.object(mod,'probe',return_value={'fps':10,'container_duration_seconds':3.06,'codec':'ffv1'}), patch.object(mod.subprocess,'Popen',side_effect=popen), patch.object(mod.subprocess,'check_output',side_effect=check):
    result=mod.analyze(video,c)
   Draft202012Validator(json.loads((ROOT/'schemas/visual-result.schema.json').read_text(encoding='utf-8'))).validate(result)
   self.assertEqual(result['video']['frame_count'],30)
   self.assertEqual(result['overlaps'],[{'start_frame':10,'end_frame':12}])
   self.assertEqual(sum(x['frames'] for x in result['scenes']),32)
   self.assertEqual(result['whole_video']['frames'],30)
   self.assertEqual(result['per_second'][0]['static_frames'],9)
   self.assertEqual(result['scenes'][0]['brand_fraction']['example-blue'],0)
   self.assertEqual(990-5*18,900)
   self.assertEqual(900/30,30.0)
   self.assertNotEqual(result['video']['container_duration_seconds'],result['video']['video_duration_seconds'])
   self.assertTrue(any(x['end_frame']-x['start_frame']>=8 for x in result['static_intervals']))
   self.assertTrue(any(e['kind']=='within-scene' for e in result['events']))
   self.assertTrue(any(e['kind']=='cut-boundary' for e in result['events']))
   self.assertEqual(result['rules']['max_static_frames']['status'],'fail')
   self.assertEqual(mod.compare(result,{**result,'analysis_profile':'other'})['comparable'],False)
   ctx={'rule':'max_static_frames','id':'gate-run_visual-test','version':'1.0.0','checklist_ref':{'id':'gate_g2-demo','version':'1.0.0'},'check_id':'visual-static','rule_version':'1.0.0','target':{'type':'Shot','id':'shot_demo-opening','version':'1.0.0'},'owner':'test','configuration_version':'1.0.0'}
   run=mod.gate_run(result,ctx,'diagnostic.json')
   Draft202012Validator(json.loads((ROOT/'schemas/gate-run.schema.json').read_text(encoding='utf-8'))).validate(run)
   self.assertEqual(run['status'],'fail')
   ctx['rule']='absent';self.assertEqual(mod.gate_run(result,ctx,'diagnostic.json')['status'],'blocked')
   c['video_sha256']='0'*64
   with self.assertRaisesRegex(ValueError,'version'):mod.analyze(video,c)
if __name__=='__main__':unittest.main()
