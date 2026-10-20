"""Synthetic audio fixtures and deterministic metric-boundary tests."""
import json
import math
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audio_metrics import loudness, measure, rms_window
from check_media import check_media, file_sha256


def tone(path, amplitude=0.1):
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(8000)
        samples = [int(32767 * amplitude * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(8000)]
        stream.writeframes(struct.pack("<" + "h" * len(samples), *samples))


class AudioMetricsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.video = self.folder / "video.mp4"; self.video.write_bytes(b"synthetic media placeholder")
        tone(self.folder / "voice.wav", .2); tone(self.folder / "music.wav", .1)
        self.cfg = {"schema_version": "1.1.0", "audio_metrics": {"rule_version": "1.0.0",
            "true_peak_dbtp": {"max_dbtp": -1},
            "integrated_lufs": {"min_lufs": -25, "max_lufs": -15},
            "voice_music_rms_delta_db": {"min_delta_db": 3, "voice_path": "voice.wav",
                                          "music_path": "music.wav", "intervals": [{"start_seconds": 0, "end_seconds": 1}]}}}
        self.path = self.folder / "config.json"; self.save()

    def tearDown(self): self.tmp.cleanup()
    def save(self): self.path.write_text(json.dumps(self.cfg), encoding="utf-8")
    def run_metrics(self):
        return measure(self.video, self.cfg, 1, {"ffmpeg": "ffmpeg version mock"}, file_sha256, self.path, "NUL")

    def test_old_config_schema_and_new_config_schema(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / "schemas/media-check-config.schema.json").read_text(encoding="utf-8"))
        old = {"schema_version": "1.0.0", "tool_versions": {"ffprobe": "mock", "ffmpeg": "mock"},
               "duration_tolerance_seconds": 0, "subtitle_min_coverage": 0,
               "audio_peak_dbfs_max": -1, "specification": {"width": 10, "height": 10, "frame_rate": 24},
               "expected_duration_seconds": 1, "frame_rate_tolerance": 0}
        self.assertFalse(list(Draft202012Validator(schema).iter_errors(old)))
        new = dict(old, schema_version="1.1.0", audio_metrics=self.cfg["audio_metrics"])
        self.assertFalse(list(Draft202012Validator(schema).iter_errors(new)))
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(dict(old, audio_metrics={}))))

    def test_distinct_measurement_parsers(self):
        summary = "Summary:\n  Integrated loudness:\n    I: -20.0 LUFS\n  True peak:\n    Peak: -1.5 dBFS\n"
        with patch("audio_metrics.subprocess.run", return_value=SimpleNamespace(returncode=0, stderr=summary)):
            self.assertEqual(loudness(self.video, "NUL"), {"integrated_lufs": -20.0, "true_peak_dbtp": -1.5})
        with patch("audio_metrics.subprocess.run", return_value=SimpleNamespace(returncode=0, stderr="mean_volume: -16.2 dB")):
            self.assertEqual(rms_window(self.folder / "voice.wav", 0, 1, "NUL"), -16.2)

    def test_pass_fail_block_and_audit_evidence(self):
        with patch("audio_metrics.loudness", return_value={"integrated_lufs": -20, "true_peak_dbtp": -1.5}), \
             patch("audio_metrics.rms_window", side_effect=[-14, -20]):
            checks, evidence = self.run_metrics()
        self.assertEqual([x["status"] for x in checks], ["pass"] * 3)
        self.assertEqual(evidence[2]["measured_value"], 6)
        self.assertEqual(evidence[2]["inputs"][0]["sha256"], file_sha256(self.folder / "voice.wav"))
        self.assertIn("ungated RMS", evidence[2]["method"])
        self.cfg["audio_metrics"]["true_peak_dbtp"]["max_dbtp"] = -2
        self.cfg["audio_metrics"]["integrated_lufs"]["min_lufs"] = -18
        self.cfg["audio_metrics"]["voice_music_rms_delta_db"]["min_delta_db"] = 8
        self.save()
        with patch("audio_metrics.loudness", return_value={"integrated_lufs": -20, "true_peak_dbtp": -1.5}), \
             patch("audio_metrics.rms_window", side_effect=[-14, -20]):
            checks, _ = self.run_metrics()
        self.assertEqual([x["status"] for x in checks], ["fail"] * 3)
        self.cfg["audio_metrics"]["true_peak_dbtp"].pop("max_dbtp")
        self.cfg["audio_metrics"]["voice_music_rms_delta_db"].pop("music_path")
        self.save()
        with patch("audio_metrics.loudness", return_value={"integrated_lufs": -20, "true_peak_dbtp": -1.5}):
            checks, _ = self.run_metrics()
        self.assertEqual(checks[0]["status"], "blocked")
        self.assertEqual(checks[2]["status"], "blocked")
        self.cfg["audio_metrics"]["voice_music_rms_delta_db"].update(music_path="music.wav", intervals=[])
        self.save()
        checks, _ = self.run_metrics()
        self.assertEqual(checks[2]["status"], "blocked")

    def test_missing_tool_does_not_fake_measurement(self):
        with patch("audio_metrics.subprocess.run", side_effect=OSError("ffmpeg absent")):
            checks, _ = self.run_metrics()
        self.assertEqual(checks[0]["status"], "blocked")
        self.assertEqual(checks[1]["status"], "blocked")

    def test_new_media_gate_propagates_required_metric_status(self):
        self.cfg.update(tool_versions={"ffprobe":"mock", "ffmpeg":"mock"},
                        expected_duration_seconds=1, duration_tolerance_seconds=0,
                        frame_rate_tolerance=0, subtitle_min_coverage=0,
                        audio_peak_dbfs_max=-1, required_subtitle=False,
                        specification={"width":10,"height":10,"frame_rate":24})
        self.save()
        probe={"format":{"duration":"1"},"streams":[{"codec_type":"video","width":10,"height":10,"avg_frame_rate":"24/1"},{"codec_type":"audio"}]}
        def fake(args, **kwargs):
            if args[1] == "-version": return SimpleNamespace(returncode=0,stdout=args[0]+" version mock",stderr="")
            if args[0] == "ffprobe": return SimpleNamespace(returncode=0,stdout=json.dumps(probe),stderr="")
            return SimpleNamespace(returncode=0,stdout="",stderr="max_volume: -2.0 dB")
        with patch("check_media.shutil.which", return_value="mock"), patch("check_media.subprocess.run", side_effect=fake), \
             patch("audio_metrics.loudness", return_value={"integrated_lufs":-20,"true_peak_dbtp":-1.5}), \
             patch("audio_metrics.rms_window", side_effect=[-14,-20]):
            result=check_media(self.video,self.path)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(len(result["audio_evidence"]), 3)
        self.cfg["audio_metrics"]["voice_music_rms_delta_db"].pop("music_path")
        self.save()
        with patch("check_media.shutil.which", return_value="mock"), patch("check_media.subprocess.run", side_effect=fake), \
             patch("audio_metrics.loudness", return_value={"integrated_lufs":-20,"true_peak_dbtp":-1.5}):
            result=check_media(self.video,self.path)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["audio_evidence"][2]["status"], "blocked")

    def test_legacy_media_path_keeps_sample_peak(self):
        cfg = {"schema_version":"1.0.0", "tool_versions":{"ffprobe":"mock", "ffmpeg":"mock"},
               "expected_duration_seconds":1, "duration_tolerance_seconds":0,
               "frame_rate_tolerance":0, "subtitle_min_coverage":0, "audio_peak_dbfs_max":-1,
               "specification":{"width":10,"height":10,"frame_rate":24}, "required_subtitle":False}
        self.path.write_text(json.dumps(cfg), encoding="utf-8")
        probe={"format":{"duration":"1"},"streams":[{"codec_type":"video","width":10,"height":10,"avg_frame_rate":"24/1"},{"codec_type":"audio"}]}
        def fake(args, **kwargs):
            if args[1] == "-version": return SimpleNamespace(returncode=0,stdout=args[0]+" version mock",stderr="")
            if args[0] == "ffprobe": return SimpleNamespace(returncode=0,stdout=json.dumps(probe),stderr="")
            return SimpleNamespace(returncode=0,stdout="",stderr="max_volume: -2.0 dB")
        with patch("check_media.shutil.which", return_value="mock"), patch("check_media.subprocess.run", side_effect=fake):
            result=check_media(self.video,self.path)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(next(x for x in result["checks"] if x["check_id"] == "audio_peak_dbfs")["measured"], -2)
        self.assertNotIn("audio_evidence", result)

if __name__ == "__main__": unittest.main()
