"""Conditional, version-bound G1 voice selection examples."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_gate import evaluate
from validate_video_package import validate

CHECKLIST = {
    "id": "gate_g1-voice", "version": "1.0.0", "schema_version": "1.0.0",
    "record_type": "GateChecklist", "stage": "G1",
    "checks": [{"check_id": "voice-selection", "rule_version": "1.0.0",
                "description": "Representative listening approval before full-track production, or authorized no-voice N/A",
                "checker_type": "human", "required": True, "blocking": True,
                "allow_not_applicable": True,
                "dependency_refs": [{"id": "brief_demo", "version": "1.0.0"},
                                    {"id": "asset_voice-plan", "version": "1.0.0"}]}],
}
RUN = {
    "id": "gate-run_voice", "version": "1.0.0", "schema_version": "1.0.0",
    "record_type": "GateRun", "checklist_ref": {"id": "gate_g1-voice", "version": "1.0.0"},
    "check_id": "voice-selection", "rule_version": "1.0.0",
    "target": {"type": "VideoBrief", "id": "brief_demo", "version": "1.0.0"},
    "status": "pass", "evidence": [{"description": "Sample URI, script and voice-plan versions, relevant settings and listening decision", "uri": "local-review://voice-approval"}],
    "owner": "voice director", "checked_at": "2026-10-19T10:00:00Z",
    "checker_type": "human", "tool_version": "manual-1",
    "configuration_version": "1.0.0",
    "dependency_refs": [{"id": "brief_demo", "version": "1.0.0"},
                        {"id": "asset_voice-plan", "version": "1.0.0"}],
}

class G1VoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.put("check.yaml", CHECKLIST)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, record):
        (self.path / name).write_text(yaml.safe_dump(record, allow_unicode=True), encoding="utf-8")

    def summary(self, version="1.0.0"):
        return evaluate(self.path, "gate_g1-voice", "1.0.0", "brief_demo", version)

    def test_selected_and_not_selected(self):
        self.assertEqual(self.summary()["status"], "blocked")
        self.put("run.yaml", RUN)
        self.assertEqual(self.summary()["status"], "pass")

    def test_new_script_or_voice_plan_must_be_reviewed(self):
        self.put("run.yaml", RUN)
        self.assertEqual(self.summary("1.0.1")["status"], "blocked")
        changed = copy.deepcopy(CHECKLIST)
        changed["checks"][0]["dependency_refs"] = [{"id": "brief_demo", "version": "1.0.0"},
                                                 {"id": "asset_voice-plan", "version": "1.0.1"}]
        self.put("check.yaml", changed)
        self.assertEqual(self.summary()["status"], "blocked")

    def test_validation_success_does_not_approve_final_gate(self):
        self.put("run.yaml", RUN)
        self.assertEqual(self.summary()["status"], "pass")
        final = copy.deepcopy(CHECKLIST)
        final.update(id="gate_g3-final", stage="G3")
        final["checks"][0].update(check_id="release-approval", description="Final version and rights approved",
                                    allow_not_applicable=False)
        self.put("final.yaml", final)
        self.assertEqual(evaluate(self.path, "gate_g3-final", "1.0.0", "brief_demo", "1.0.0")["status"], "blocked")

    def test_no_voice_authorized_na(self):
        run = copy.deepcopy(RUN)
        run.update(status="not-applicable", na_reason="No narration in this brief", na_authorized_by="producer")
        self.put("run.yaml", run)
        self.assertEqual(self.summary()["status"], "pass")
        run.pop("na_authorized_by")
        self.put("run.yaml", run)
        self.assertEqual(self.summary()["status"], "blocked")
        _, findings = validate(self.path, ROOT / "schemas")
        self.assertTrue(any("na_authorized_by" in str(f) for f in findings))

if __name__ == "__main__":
    unittest.main()
