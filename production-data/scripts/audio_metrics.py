"""Optional, explicitly scoped G2 audio measurements. No perceptual judgments."""
from __future__ import annotations
import math
import re
import subprocess
from pathlib import Path


def _number(pattern, text):
    matches = re.findall(pattern, text, re.IGNORECASE)
    if not matches:
        raise ValueError("ffmpeg output lacks the requested metric")
    value = float(matches[-1])
    if not math.isfinite(value):
        raise ValueError("non-finite audio measurement")
    return value


def _ffmpeg(args):
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", *args],
                          capture_output=True, text=True)
    if proc.returncode:
        raise ValueError("ffmpeg measurement failed: " + proc.stderr[-500:])
    return proc.stderr


def loudness(media, sink):
    # ebur128 summary: gated integrated LUFS and oversampled true-peak dBFS (dBTP).
    text = _ffmpeg([str(media), "-vn", "-af", "ebur128=peak=true", "-f", "null", sink])
    summary = text.rsplit("Summary:", 1)[-1]
    if summary == text:
        raise ValueError("ebur128 summary unavailable")
    integrated = _number(r"\bI:\s*([-+]?\d+(?:\.\d+)?)\s*LUFS", summary)
    peak_section = summary.split("True peak:")
    if len(peak_section) < 2:
        raise ValueError("ebur128 true peak unavailable")
    peak = _number(r"\bPeak:\s*([-+]?\d+(?:\.\d+)?)\s*dBFS", peak_section[-1])
    return {"integrated_lufs": integrated, "true_peak_dbtp": peak}


def rms_window(path, start, end, sink):
    # volumedetect mean_volume is full-window, ungated RMS in dBFS; both stems
    # are measured over the same explicit timeline window, never different times.
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(start),
                           "-t", str(end-start), "-i", str(path), "-vn", "-af",
                           "volumedetect", "-f", "null", sink], capture_output=True, text=True)
    if proc.returncode:
        raise ValueError("stem measurement failed: " + proc.stderr[-500:])
    return _number(r"mean_volume:\s*([-+]?\d+(?:\.\d+)?)\s*dB", proc.stderr)


def measure(media, cfg, duration, tool_versions, hash_file, config_path, sink):
    """Return metric checks and auditable evidence. Missing prerequisites BLOCK required checks."""
    settings = cfg.get("audio_metrics", {})
    checks, evidence = [], []
    rule = settings.get("rule_version")
    config_hash = hash_file(config_path)
    for metric in ("true_peak_dbtp", "integrated_lufs", "voice_music_rms_delta_db"):
        if metric not in settings:
            continue  # not configured is not PASS
        spec = settings[metric]
        required = spec.get("required", True)
        entry = {"check_id": metric, "status": "blocked", "measured": None,
                 "expected": spec.get("max_dbtp") if metric == "true_peak_dbtp" else
                             {k:v for k,v in spec.items() if k in ("min_lufs", "max_lufs", "min_delta_db")},
                 "required": required}
        record = {"metric": metric, "status": "blocked", "rule_version": rule,
                  "configuration_schema_version": cfg["schema_version"],
                  "configuration_sha256": config_hash, "tool_versions": tool_versions,
                  "inputs": [], "method": None, "unit": None, "threshold": entry["expected"],
                  "measured_value": None}
        try:
            if not rule:
                raise ValueError("missing audio_metrics.rule_version")
            if metric in ("true_peak_dbtp", "integrated_lufs"):
                if metric == "true_peak_dbtp" and "max_dbtp" not in spec:
                    raise ValueError("missing max_dbtp threshold")
                if metric == "integrated_lufs" and not any(k in spec for k in ("min_lufs", "max_lufs")):
                    raise ValueError("missing LUFS threshold")
                record["inputs"] = [{"path": str(media), "sha256": hash_file(media)}]
                record["method"] = "ffmpeg ebur128=peak=true; full programme; integrated gated EBU R128; true peak oversampled"
                record["unit"] = "dBTP" if metric == "true_peak_dbtp" else "LUFS"
                measured = loudness(media, sink)[metric]
                ok = measured <= spec["max_dbtp"] if metric == "true_peak_dbtp" else (
                    measured >= spec.get("min_lufs", -math.inf) and measured <= spec.get("max_lufs", math.inf))
            else:
                if "min_delta_db" not in spec:
                    raise ValueError("missing min_delta_db threshold")
                intervals = spec.get("intervals")
                if not intervals or any(x["end_seconds"] <= x["start_seconds"] or x["end_seconds"] > duration for x in intervals):
                    raise ValueError("missing or invalid simultaneous voice intervals")
                stems = []
                for key in ("voice_path", "music_path"):
                    raw = spec.get(key)
                    if not raw:
                        raise ValueError("missing separated " + key)
                    path = (config_path.parent / raw).resolve()
                    if not path.is_file():
                        raise ValueError("separated input missing: " + key)
                    stems.append(path)
                    record["inputs"].append({"path": str(path), "sha256": hash_file(path)})
                record["method"] = "ffmpeg volumedetect mean_volume (ungated RMS dBFS); same explicit intervals on aligned stems; minimum per-window voice minus music"
                record["unit"] = "dB"
                record["intervals"] = intervals
                window_values = []
                for window in intervals:
                    start, end = window["start_seconds"], window["end_seconds"]
                    voice = rms_window(stems[0], start, end, sink)
                    music = rms_window(stems[1], start, end, sink)
                    window_values.append({"start_seconds": start, "end_seconds": end,
                                          "voice_rms_dbfs": voice, "music_rms_dbfs": music,
                                          "delta_db": voice-music})
                record["windows"] = window_values
                measured = min(x["delta_db"] for x in window_values)
                ok = measured >= spec["min_delta_db"]
            entry.update(status="pass" if ok else "fail", measured=measured)
            record.update(status=entry["status"], measured_value=measured)
        except (ValueError, OSError, KeyError) as exc:
            entry["diagnostic"] = str(exc)
            record["diagnostic"] = str(exc)
        checks.append(entry)
        evidence.append(record)
    return checks, evidence
