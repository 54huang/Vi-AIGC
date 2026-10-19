from __future__ import annotations
import json, sys, tempfile, unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import yaml
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'scripts'))
from validate_video_package import validate
from evaluate_gate import evaluate
from check_media import check_media, subtitle_intervals, union_duration

class GateAndProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.pkg=Path(self.tmp.name)/'pkg'; self.pkg.mkdir()
    def tearDown(self): self.tmp.cleanup()
    def put(self,name,data): (self.pkg/name).write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False),encoding='utf-8')
    def test_gate_run_missing_evidence_rejected_by_schema(self):
        self.put('check.yaml',{'id':'gate_g0','version':'1.0.0','schema_version':'1.0.0','record_type':'GateChecklist','stage':'G0','checks':[{'check_id':'objective','rule_version':'1.0.0','description':'Objective exists','checker_type':'human','required':True,'blocking':True,'allow_not_applicable':False}]})
        self.put('profile.yaml',{'id':'profile_demo','version':'1.0.0','schema_version':'1.0.0','record_type':'ProjectProfile','project_name':'Demo','status':'active','review_requirements':{'brief':['factuality'],'shot':['creative'],'asset':['rights'],'release':['release']},'claim_ids':[],'asset_ids':[]})
        self.put('run.yaml',{'id':'gate-run_run1','version':'1.0.0','schema_version':'1.0.0','record_type':'GateRun','checklist_ref':{'id':'gate_g0','version':'1.0.0'},'check_id':'objective','rule_version':'1.0.0','target':{'type':'ProjectProfile','id':'profile_demo','version':'1.0.0'},'status':'pass','evidence':[],'owner':'producer','checked_at':'2026-10-18T10:00:00Z','checker_type':'human','tool_version':'manual-1','configuration_version':'1.0.0','dependency_refs':[]})
        _, findings=validate(self.pkg,HERE/'schemas')
        self.assertTrue(any(x['record_id']=='gate-run_run1' and 'evidence' in x['field'] for x in findings))
    def test_gate_summary_blocks_missing_required_check(self):
        self.put('check.yaml',{'id':'gate_g0','version':'1.0.0','schema_version':'1.0.0','record_type':'GateChecklist','stage':'G0','checks':[{'check_id':'objective','rule_version':'1.0.0','description':'Objective exists','checker_type':'human','required':True,'blocking':True,'allow_not_applicable':False}]})
        result=evaluate(self.pkg,'gate_g0','1.0.0','brief_demo','1.0.0')
        self.assertEqual(result['status'],'blocked')
    def test_manifest_unknown_weight_rights_and_input_rights_are_blocked(self):
        asset={'id':'asset_input','version':'1.0.0','schema_version':'1.0.0','record_type':'Asset','status':'cleared','uri':'missing.bin','usage_scope':{},'rights':{'input_media':{'status':'unknown'}}}
        out={'id':'asset_output','version':'1.0.0','schema_version':'1.0.0','record_type':'Asset','status':'cleared','uri':'missing.bin','usage_scope':{},'manifest_refs':[{'id':'manifest_run','version':'1.0.0'}],'content_hash':{'algorithm':'sha256','digest':'0'*64},'rights':{'output_use':{'status':'verified'}}}
        self.put('in.yaml',asset); self.put('out.yaml',out)
        (self.pkg/'missing.bin').write_bytes(b'actual output bytes')
        self.put('manifest.yaml',{'id':'manifest_run','version':'1.0.0','schema_version':'1.0.0','record_type':'GenerationManifest','created_at':'2026-10-18T10:00:00Z','inputs':[{'id':'asset_input','version':'1.0.0'}],'outputs':[{'id':'asset_output','version':'1.0.0'}],'model':{'provider':'local','revision':'abc123','weights_rights':{'status':'unknown'}},'workflow':{'id':'workflow','version_or_hash':'1.0.0','code_license':'MIT'},'parameters':{},'execution_status':'succeeded'})
        _, findings=validate(self.pkg,HERE/'schemas')
        errors=[x for x in findings if x['level']=='ERROR']
        self.assertTrue(any('模型权重权利' in x['message'] for x in errors))
        self.assertTrue(any('输入素材' in x['message'] for x in errors))
        self.assertTrue(any('哈希不匹配' in x['message'] for x in errors))
    def test_media_missing_config_is_blocked_not_pass(self):
        result=check_media(self.pkg/'video.mp4',self.pkg/'missing.json')
        self.assertEqual(result['status'],'blocked')
    def test_media_invalid_config_is_blocked(self):
        config=self.pkg/'bad.json'; config.write_text('{}',encoding='utf-8')
        result=check_media(self.pkg/'video.mp4',config)
        self.assertEqual(result['status'],'blocked')
        self.assertTrue(any('Schema' in x for x in result['diagnostics']))
    def test_media_mock_adapter_passes_and_returns_hash_and_evidence(self):
        media=self.pkg/'video.mp4'; media.write_bytes(b'mock media bytes')
        subtitles=self.pkg/'video.srt'; subtitles.write_text('1\n00:00:00,000 --> 00:00:08,000\nCaption\n',encoding='utf-8')
        config={'schema_version':'1.0.0','tool_versions':{'ffprobe':'mock-1','ffmpeg':'mock-1'},'expected_duration_seconds':10,'duration_tolerance_seconds':0.1,'frame_rate_tolerance':0.01,'subtitle_min_coverage':0.75,'audio_peak_dbfs_max':-1,'specification':{'width':1920,'height':1080,'frame_rate':30,'container':'mp4','video_codec':'h264','audio_codec':'aac'},'required_subtitle':True,'required_audio':True}
        cp=self.pkg/'config.json'; cp.write_text(json.dumps(config),encoding='utf-8')
        probe={'format':{'duration':'10','format_name':'mov,mp4,m4a'},'streams':[{'codec_type':'video','codec_name':'h264','width':1920,'height':1080,'avg_frame_rate':'30/1'},{'codec_type':'audio','codec_name':'aac'}]}
        def fake_run(args,**kwargs):
            if args[0] in ('ffprobe','ffmpeg') and args[1]=='-version': return SimpleNamespace(returncode=0,stdout=f'{args[0]} version mock-1\n',stderr='')
            if args[0]=='ffprobe': return SimpleNamespace(returncode=0,stdout=json.dumps(probe),stderr='')
            if args[0]=='ffmpeg': return SimpleNamespace(returncode=0,stdout='',stderr='[Parsed_volumedetect] max_volume: -2.0 dB\n')
            raise AssertionError(args)
        with patch('check_media.shutil.which',return_value='mock-binary'), patch('check_media.subprocess.run',side_effect=fake_run):
            result=check_media(media,cp,subtitles)
        self.assertEqual(result['status'],'pass')
        self.assertTrue(result['input_sha256'])
        self.assertTrue(all(x['status']=='pass' for x in result['checks']))
    def test_media_mock_adapter_fails_on_out_of_bounds_subtitle_and_peak(self):
        media=self.pkg/'video.mp4'; media.write_bytes(b'mock media bytes')
        subtitles=self.pkg/'video.srt'; subtitles.write_text('1\n00:00:09,000 --> 00:00:11,000\nCaption\n',encoding='utf-8')
        config={'schema_version':'1.0.0','tool_versions':{'ffprobe':'mock-1','ffmpeg':'mock-1'},'expected_duration_seconds':10,'duration_tolerance_seconds':0.1,'frame_rate_tolerance':0.01,'subtitle_min_coverage':0.1,'audio_peak_dbfs_max':-3,'specification':{'width':1280,'height':720,'frame_rate':24,'container':'mp4','video_codec':'h264','audio_codec':'aac'},'required_subtitle':True,'required_audio':True}
        cp=self.pkg/'config.json'; cp.write_text(json.dumps(config),encoding='utf-8')
        probe={'format':{'duration':'10','format_name':'mov,mp4'},'streams':[{'codec_type':'video','codec_name':'h264','width':1920,'height':1080,'avg_frame_rate':'30/1'},{'codec_type':'audio','codec_name':'aac'}]}
        def fake_run(args,**kwargs):
            if args[0] in ('ffprobe','ffmpeg') and args[1]=='-version': return SimpleNamespace(returncode=0,stdout=f'{args[0]} version mock-1\n',stderr='')
            if args[0]=='ffprobe': return SimpleNamespace(returncode=0,stdout=json.dumps(probe),stderr='')
            return SimpleNamespace(returncode=0,stdout='',stderr='max_volume: -2.0 dB')
        with patch('check_media.shutil.which',return_value='mock-binary'), patch('check_media.subprocess.run',side_effect=fake_run):
            result=check_media(media,cp,subtitles)
        self.assertEqual(result['status'],'fail')
        self.assertEqual({x['check_id'] for x in result['checks'] if x['status']=='fail'},{'width','height','frame_rate','subtitle_bounds','audio_peak_dbfs'})
    def test_subtitle_union_does_not_double_count_overlaps(self):
        self.assertEqual(union_duration([(0,2),(1,3),(5,6)]),4)

if __name__=='__main__': unittest.main()
