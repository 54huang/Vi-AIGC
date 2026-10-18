from __future__ import annotations
import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
import yaml
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'scripts'))
from validate_video_package import validate

class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.package=Path(self.tmp.name)/'pkg'; self.package.mkdir()
        for p in (HERE/'examples/valid').glob('*.yaml'): shutil.copy2(p,self.package/p.name)
    def tearDown(self): self.tmp.cleanup()
    def records(self): return {p.name:yaml.safe_load(p.read_text(encoding='utf-8')) for p in self.package.glob('*.yaml')}
    def save(self,records):
        for n,r in records.items(): (self.package/n).write_text(yaml.safe_dump(r,allow_unicode=True,sort_keys=False),encoding='utf-8')
    def check(self): return validate(self.package,HERE/'schemas')
    def test_complete_sample_passes_and_does_not_auto_approve(self):
        records,findings=self.check(); self.assertFalse(findings)
        release=next(r for r in records if r['record_type']=='Release')
        self.assertEqual(release['status'],'draft')
    def test_schema_files_validate_as_draft_2020_12(self):
        from jsonschema import Draft202012Validator
        for p in (HERE/'schemas').glob('*.json'):
            schema=json.loads(p.read_text(encoding='utf-8')); Draft202012Validator.check_schema(schema)
    def test_missing_field_reports_record_and_path(self):
        r=self.records(); data=r['claim_demo-feature.yaml']; data.pop('text'); self.save(r)
        _,f=self.check(); errors=[x for x in f if x['level']=='ERROR']
        self.assertTrue(any(x['record_id']=='claim_demo-feature' and 'text' in x['field'] for x in errors))
    def test_invalid_enum_and_id_report(self):
        r=self.records(); d=r['claim_demo-feature.yaml']; d['status']='unknown'; d['id']='bad-id'; self.save(r)
        _,f=self.check(); self.assertTrue(any(x['field']=='.id' for x in f)); self.assertTrue(any(x['field']=='.status' for x in f))
    def test_duplicate_id_version_is_blocked(self):
        shutil.copy2(self.package/'claim_demo-feature.yaml',self.package/'duplicate.yaml')
        _,f=self.check(); self.assertTrue(any('重复实体版本' in x['message'] for x in f))
    def test_expired_claim_is_blocked_with_id_and_path(self):
        r=self.records(); r['claim_demo-feature.yaml']['status']='expired'; self.save(r)
        _,f=self.check(); self.assertTrue(any(x['record_id']=='claim_demo-feature' and x['level']=='ERROR' for x in f))
    def test_broken_reference_and_nonexistent_version_blocked(self):
        r=self.records(); r['shot_demo-opening.yaml']['asset_refs'][0]['version']='9.0.0'; self.save(r)
        _,f=self.check(); self.assertTrue(any(x['record_id']=='shot_demo-opening' and '不存在的 ID/版本' in x['message'] for x in f))
    def test_claim_expiration_by_planned_release_date_blocks(self):
        r=self.records(); r['claim_demo-feature.yaml']['scope']['valid_until']='2026-11-01'; self.save(r)
        _,f=self.check(); self.assertTrue(any('超过有效期' in x['message'] for x in f))
    def test_asset_scope_mismatch_blocks_release(self):
        r=self.records(); r['asset_demo-product.yaml']['usage_scope']['channels']=['instagram']; self.save(r)
        _,f=self.check(); self.assertTrue(any(x['level']=='ERROR' and '不适用渠道' in x['message'] for x in f))
    def test_unapproved_human_review_blocks_release_without_mutation(self):
        r=self.records(); r['review_demo-shot-creative.yaml']['status']='pending'; self.save(r)
        records,f=self.check(); self.assertTrue(any(x['level']=='ERROR' and '非 approved' in x['message'] for x in f))
        self.assertEqual(next(x for x in records if x['record_type']=='Review' and x['id']=='review_demo-shot-creative')['status'],'pending')
    def test_cli_survives_structurally_invalid_minimal_record(self):
        bad=Path(self.tmp.name)/'invalid'; bad.mkdir()
        (bad/'broken.yaml').write_text('record_type: VideoBrief\nid: brief_broken\nversion: 1.0.0\nschema_version: 1.0.0\n',encoding='utf-8')
        cp=subprocess.run([sys.executable,str(HERE/'scripts/validate_video_package.py'),str(bad)],capture_output=True,text=True)
        self.assertEqual(cp.returncode,1); self.assertIn('project_profile',cp.stdout)
    def test_ambiguous_rights_warn_not_approve(self):
        r=self.records(); r['asset_demo-product.yaml']['rights_ambiguity']=True; self.save(r)
        _,f=self.check(); self.assertTrue(any(x['level']=='WARN' and '授权依据含糊' in x['message'] for x in f))
    def test_old_review_version_fails_exact_target_coverage(self):
        r=self.records(); r['review_demo-shot-creative.yaml']['target']['version']='0.9.0'; self.save(r)
        records,f=self.check(); self.assertTrue(any('不存在的 ID/版本' in x['message'] for x in f)); self.assertTrue(any('缺少规则要求的 creative Review' in x['message'] for x in f))
        self.assertEqual(next(x for x in records if x['record_type']=='Review' and x['id']=='review_demo-brief-factuality')['status'],'approved')
    def test_release_asset_closure_is_enforced(self):
        r=self.records(); r['release_demo-launch.yaml']['asset_refs']=[]; self.save(r)
        _,f=self.check(); self.assertTrue(any('素材清单与所选 Shot 素材闭包不一致' in x['message'] for x in f))
    def test_required_review_cannot_be_omitted(self):
        r=self.records(); r['release_demo-launch.yaml']['required_review_refs'].remove('review_demo-shot-creative'); self.save(r)
        _,f=self.check(); self.assertTrue(any('缺少规则要求的 creative Review' in x['message'] for x in f))
    def test_cli_warn_contract_uses_exit_two(self):
        r=self.records(); r['asset_demo-product.yaml']['rights_ambiguity']=True; self.save(r)
        cp=subprocess.run([sys.executable,str(HERE/'scripts/validate_video_package.py'),str(self.package)],capture_output=True,text=True)
        self.assertEqual(cp.returncode,2); self.assertIn('WARN:',cp.stdout); self.assertNotIn('PASS:',cp.stdout)
    def test_cli_returns_failure_for_errors(self):
        cp=subprocess.run([sys.executable,str(HERE/'scripts/validate_video_package.py'),str(HERE/'examples/invalid')],capture_output=True,text=True)
        self.assertEqual(cp.returncode,1); self.assertIn('ERROR:',cp.stdout)

if __name__=='__main__': unittest.main()
