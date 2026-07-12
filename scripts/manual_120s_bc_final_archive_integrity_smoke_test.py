from __future__ import annotations

import argparse
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import (  # noqa: E402
    DEFAULT_DEMO_PATH,
    DIRECT_ACTION_MANIFEST_SHA256,
    SOURCE_ROUTE_FILE_SHA256,
    bytes_sha256,
    file_sha256,
)


DEFAULT_ARCHIVE = ROOT.parent / "ww-dps-simulator-2-108.zip"
EXPECTED_BC_MODEL_SHA256 = "7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e"
EXPECTED_PPO_MODEL_SHA256 = "9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513"
EXPECTED_EVAL_SELECTED_SEQUENCE_SHA256 = "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
EXPECTED_EVAL_RESOLVED_SEQUENCE_SHA256 = "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
EXPECTED_EVAL_TOTAL_DAMAGE = 5165134.682363356
EXPECTED_EVAL_DPS = 43042.78901969464
EXPECTED_SCHEDULED_DAMAGE = 205987.4042873791
EXPECTED_DAMAGE_BY_CHARACTER = {
    "aemeath": 3733934.8538652016,
    "mornye": 268807.92005964793,
    "lynae": 1162391.9084385103,
}
EXPECTED_PPO_SELECTED_SEQUENCE_SHA256 = "0bba8688b3a085fde3a842901f659b24fdefd009102cc1ccba5a0d971a27c11d"
EXPECTED_PPO_RESOLVED_SEQUENCE_SHA256 = "9650b6e4d1b8f9ba616c26293f60c8cc4a5d6ea57dcf7153305aa085f84ad6e1"
EXPECTED_PPO_TOTAL_DAMAGE = 3600637.129626801
EXPECTED_PPO_DPS = 30005.309413556675
EXPECTED_PPO_SCHEDULED_DAMAGE = 140026.5111366104
EXPECTED_PPO_DAMAGE_BY_CHARACTER = {
    "aemeath": 2674131.053725695,
    "mornye": 201528.93426401448,
    "lynae": 724977.1416370921,
}
REQUIRED_FILES = (
    "PROJECT_PROGRESS_STATE.json",
    "data/manual_120s_baseline_routes_v104.json",
    "data/generated/manual_120s_bc_demonstration_v105.npz",
    "results/manual_120s_bc_demonstration_v105_summary.json",
    "results/ppo_evaluation_summary.json",
    "results/ppo_timeline.csv",
    "results/ppo_100k_evaluation_summary.json",
    "results/ppo_100k_timeline.csv",
    "results/manual_bc_ppo_comparison_v108.json",
    "results/training_metadata.json",
    "reports/manual_120s_bc_demonstration_v105.md",
    "models/maskable_ppo_bc_v105.zip",
    "models/maskable_ppo_bc_v105.zip.bc_metadata.json",
    "models/maskable_ppo_candidate_after_bc_v105.zip",
    "rl/damage_attribution.py",
    "rl/demo_contract.py",
    "rl/evaluation_report.py",
    "rl/evaluate_maskable_ppo.py",
    "rl/pretrain_maskable_ppo_bc.py",
    "scripts/manual_120s_bc_demo_contract_smoke_test.py",
    "scripts/manual_120s_bc_packaged_generation_parity_smoke_test.py",
    "scripts/manual_120s_bc_report_portability_smoke_test.py",
    "scripts/bc_pretrain_evaluator_contract_smoke_test.py",
    "scripts/evaluate_bc_sidecar_compatibility_smoke_test.py",
    "scripts/pretrain_bc_initial_active_contract_smoke_test.py",
    "scripts/project_progress_active_echo_alignment_smoke_test.py",
    "scripts/project_progress_manual_120s_baseline_alignment_smoke_test.py",
    "scripts/project_progress_bc_demo_alignment_smoke_test.py",
    "scripts/project_progress_ppo_100k_alignment_smoke_test.py",
    "scripts/evaluation_event_source_damage_attribution_smoke_test.py",
    "scripts/evaluation_scheduled_damage_role_breakdown_smoke_test.py",
    "scripts/bc_evaluation_manual_baseline_parity_smoke_test.py",
    "scripts/ppo_100k_evaluation_contract_smoke_test.py",
    "scripts/manual_bc_ppo_comparison_smoke_test.py",
    "scripts/build_candidate_archive_output_guard_smoke_test.py",
)
TEXT_SUFFIXES = (".py", ".json", ".md", ".txt")
AUTHORITATIVE_SOURCE_FILES = (
    "data/actions.json",
    "direct_action_data_patch_manifest_v61.json",
    "data/source/direct_action_data_patch_manifest_v61.json",
)
CORRECT_SHEET_NAME = "".join(chr(codepoint) for codepoint in (0x58F0, 0x9AB8))
FORBIDDEN_CORRUPTED_SHEET_NAME = "".join(chr(codepoint) for codepoint in (0x9DAF, 0xACC8, 0x3058))
ESTABLISHED_MOJIBAKE_MARKERS = (
    "".join(chr(codepoint) for codepoint in (0x00EF, 0x00BB, 0x00BF)),
    "".join(chr(codepoint) for codepoint in (0x00E9, 0x00B6, 0x00AF, 0x00EA, 0x00B3, 0x02C6, 0x00EC, 0x00A7)),
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    stats = validate_archive(args.archive)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print("manual_120s_bc_final_archive_integrity_smoke_test ok")


def validate_archive(archive: Path) -> dict[str, Any]:
    assert archive.exists(), archive
    with zipfile.ZipFile(archive) as zf:
        names = [info.filename for info in zf.infolist()]
        name_set = set(names)
        for required in REQUIRED_FILES:
            assert required in name_set, required
        cache_entries = [name for name in names if _is_cache_entry(name)]
        obsolete_bundle_entries = [
            name for name in names if name.replace("\\", "/") == "bc_eval_bundle/" or name.startswith("bc_eval_bundle/")
        ]
        assert not cache_entries, cache_entries[:20]
        assert not obsolete_bundle_entries, obsolete_bundle_entries

        route_bytes = zf.read("data/manual_120s_baseline_routes_v104.json")
        assert bytes_sha256(route_bytes) == SOURCE_ROUTE_FILE_SHA256
        _assert_json(zf.read("data/manual_120s_baseline_routes_v104.json"))

        summary = json.loads(zf.read("results/manual_120s_bc_demonstration_v105_summary.json").decode("utf-8"))
        evaluation_summary = json.loads(zf.read("results/ppo_evaluation_summary.json").decode("utf-8"))
        ppo_summary = json.loads(zf.read("results/ppo_100k_evaluation_summary.json").decode("utf-8"))
        comparison = json.loads(zf.read("results/manual_bc_ppo_comparison_v108.json").decode("utf-8"))
        progress = json.loads(zf.read("PROJECT_PROGRESS_STATE.json").decode("utf-8"))
        model_bytes = zf.read("models/maskable_ppo_bc_v105.zip")
        assert bytes_sha256(model_bytes) == EXPECTED_BC_MODEL_SHA256
        ppo_model_bytes = zf.read("models/maskable_ppo_candidate_after_bc_v105.zip")
        assert bytes_sha256(ppo_model_bytes) == EXPECTED_PPO_MODEL_SHA256
        _assert_evaluation_summary(evaluation_summary)
        _assert_ppo_evaluation_summary(ppo_summary)
        _assert_comparison(comparison)
        npz_bytes = zf.read("data/generated/manual_120s_bc_demonstration_v105.npz")
        npz_sha = bytes_sha256(npz_bytes)
        assert summary["dataset_sha256"] == npz_sha
        assert _progress_contains(progress, npz_sha)
        with np.load(io.BytesIO(npz_bytes), allow_pickle=False) as data:
            metadata = json.loads(str(np.asarray(data["metadata_json"]).item()))
        assert metadata["source_route_file_sha256"] == SOURCE_ROUTE_FILE_SHA256
        assert summary["metadata"]["source_route_file_sha256"] == SOURCE_ROUTE_FILE_SHA256

        manifest_a = zf.read("direct_action_data_patch_manifest_v61.json")
        manifest_b = zf.read("data/source/direct_action_data_patch_manifest_v61.json")
        assert manifest_a == manifest_b
        assert bytes_sha256(manifest_a) == DIRECT_ACTION_MANIFEST_SHA256

        text_stats = scan_archive_text(zf, names)
        assert text_stats["utf8_bom_count"] == 0
        assert text_stats["replacement_character_count"] == 0
        assert text_stats["forbidden_corrupted_sheet_occurrence_count"] == 0
        assert text_stats["established_mojibake_occurrence_count"] == 0
        assert text_stats["correct_sheet_occurrence_count"] > 0
        assert text_stats["authoritative_correct_sheet_occurrence_count"] > 0

    fresh_extraction_results = run_fresh_extraction_checks(archive)
    if DEFAULT_DEMO_PATH.exists():
        assert file_sha256(DEFAULT_DEMO_PATH) == npz_sha
    return {
        "archive": archive.as_posix(),
        "archive_sha256": file_sha256(archive),
        "zip_entry_count": len(names),
        "cache_entry_count": len(cache_entries),
        "obsolete_bc_eval_bundle_entry_count": len(obsolete_bundle_entries),
        "route_sha256": SOURCE_ROUTE_FILE_SHA256,
        "npz_sha256": npz_sha,
        "bc_model_sha256": EXPECTED_BC_MODEL_SHA256,
        "ppo_model_sha256": EXPECTED_PPO_MODEL_SHA256,
        "direct_action_manifest_sha256": DIRECT_ACTION_MANIFEST_SHA256,
        **text_stats,
        "fresh_extraction_checks": fresh_extraction_results,
    }


def scan_archive_text(zf: zipfile.ZipFile, names: list[str]) -> dict[str, int]:
    stats = {
        "text_entry_count": 0,
        "utf8_bom_count": 0,
        "replacement_character_count": 0,
        "forbidden_corrupted_sheet_occurrence_count": 0,
        "established_mojibake_occurrence_count": 0,
        "correct_sheet_occurrence_count": 0,
        "authoritative_correct_sheet_occurrence_count": 0,
    }
    for name in names:
        if not name.endswith(TEXT_SUFFIXES):
            continue
        data = zf.read(name)
        stats["text_entry_count"] += 1
        if data.startswith(b"\xef\xbb\xbf"):
            stats["utf8_bom_count"] += 1
        text = data.decode("utf-8")
        stats["replacement_character_count"] += text.count("\uFFFD")
        stats["forbidden_corrupted_sheet_occurrence_count"] += text.count(FORBIDDEN_CORRUPTED_SHEET_NAME)
        stats["correct_sheet_occurrence_count"] += text.count(CORRECT_SHEET_NAME)
        if name in AUTHORITATIVE_SOURCE_FILES:
            stats["authoritative_correct_sheet_occurrence_count"] += text.count(CORRECT_SHEET_NAME)
        for marker in ESTABLISHED_MOJIBAKE_MARKERS:
            stats["established_mojibake_occurrence_count"] += text.count(marker)
        if name.endswith(".json"):
            _assert_json(data)
    return stats


def run_fresh_extraction_checks(archive: Path) -> list[dict[str, Any]]:
    checks = [
        [sys.executable, "scripts/project_progress_active_echo_alignment_smoke_test.py"],
        [sys.executable, "scripts/project_progress_manual_120s_baseline_alignment_smoke_test.py"],
        [sys.executable, "scripts/project_progress_bc_demo_alignment_smoke_test.py"],
        [sys.executable, "scripts/project_progress_ppo_100k_alignment_smoke_test.py"],
        [sys.executable, "scripts/manual_120s_bc_demo_contract_smoke_test.py"],
        [sys.executable, "scripts/manual_120s_bc_packaged_generation_parity_smoke_test.py"],
        [sys.executable, "scripts/manual_120s_bc_report_portability_smoke_test.py"],
        [sys.executable, "scripts/bc_pretrain_evaluator_contract_smoke_test.py"],
        [sys.executable, "scripts/evaluation_event_source_damage_attribution_smoke_test.py"],
        [sys.executable, "scripts/evaluation_scheduled_damage_role_breakdown_smoke_test.py"],
        [sys.executable, "scripts/bc_evaluation_manual_baseline_parity_smoke_test.py"],
        [sys.executable, "scripts/ppo_100k_evaluation_contract_smoke_test.py"],
        [sys.executable, "scripts/manual_bc_ppo_comparison_smoke_test.py"],
        [sys.executable, "scripts/build_candidate_archive_output_guard_smoke_test.py"],
        [
            sys.executable,
            "rl/pretrain_maskable_ppo_bc.py",
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--initial-active-character",
            "aemeath",
            "--demo-path",
            "data/generated/manual_120s_bc_demonstration_v105.npz",
            "--model-path",
            "models/maskable_ppo_bc_v105.zip",
            "--dry-run",
        ],
        [
            sys.executable,
            "rl/evaluate_maskable_ppo.py",
            "--model-path",
            "models/maskable_ppo_candidate_after_bc_v105.zip",
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--initial-active-character",
            "aemeath",
            "--summary-path",
            "results/ppo_100k_evaluation_summary.json",
            "--timeline-path",
            "results/ppo_100k_timeline.csv",
        ],
        [
            sys.executable,
            "rl/evaluate_maskable_ppo.py",
            "--model-path",
            "models/maskable_ppo_bc_v105.zip",
            "--party",
            "aemeath_mornye_lynae_enabled_test_party",
            "--initial-active-character",
            "aemeath",
        ],
    ]
    passed: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        extract_root = Path(temp_dir) / "project"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract_root)
        for command in checks:
            result = _run(command, cwd=extract_root, timeout=120)
            passed.append(
                {
                    "command": " ".join(command[1:]),
                    "elapsed_seconds": round(result["elapsed_seconds"], 6),
                }
            )
    return passed


def _assert_json(data: bytes) -> None:
    json.loads(data.decode("utf-8"))


def _assert_evaluation_summary(summary: dict[str, Any]) -> None:
    assert summary["selected_action_count"] == 148
    assert summary["resolved_action_count"] == 148
    assert summary["selected_sequence_sha256"] == EXPECTED_EVAL_SELECTED_SEQUENCE_SHA256
    assert summary["resolved_sequence_sha256"] == EXPECTED_EVAL_RESOLVED_SEQUENCE_SHA256
    assert summary["manual_baseline_selected_sequence_match"] is True
    assert summary["manual_baseline_resolved_sequence_match"] is True
    assert summary["manual_baseline_character_damage_match"] is True
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    _assert_close(summary["total_damage"], EXPECTED_EVAL_TOTAL_DAMAGE)
    _assert_close(summary["dps"], EXPECTED_EVAL_DPS)
    for character_id, expected_damage in EXPECTED_DAMAGE_BY_CHARACTER.items():
        _assert_close(summary["damage_by_character"][character_id], expected_damage)
    role_breakdown = summary["effective_damage_role_breakdown"]
    _assert_close(role_breakdown["scheduled_damage"], EXPECTED_SCHEDULED_DAMAGE)
    _assert_close(role_breakdown["total_damage_delta"], 0.0)


def _assert_ppo_evaluation_summary(summary: dict[str, Any]) -> None:
    assert summary["selected_action_count"] == 152
    assert summary["resolved_action_count"] == 152
    assert summary["selected_sequence_sha256"] == EXPECTED_PPO_SELECTED_SEQUENCE_SHA256
    assert summary["resolved_sequence_sha256"] == EXPECTED_PPO_RESOLVED_SEQUENCE_SHA256
    assert summary["manual_baseline_selected_sequence_match"] is False
    assert summary["manual_baseline_resolved_sequence_match"] is False
    assert summary["manual_baseline_character_damage_match"] is False
    assert summary["model_metadata_mismatches"] == {}
    assert summary["model_space_mismatches"] == {}
    _assert_close(summary["total_damage"], EXPECTED_PPO_TOTAL_DAMAGE)
    _assert_close(summary["dps"], EXPECTED_PPO_DPS)
    _assert_close(summary["final_time"], 120.0)
    _assert_close(summary["manual_baseline_total_damage"], 5165134.682363359)
    _assert_close(summary["manual_baseline_damage_ratio"], 0.6971042094839032)
    _assert_close(summary["manual_baseline_damage_delta"], -1564497.5527365585)
    for character_id, expected_damage in EXPECTED_PPO_DAMAGE_BY_CHARACTER.items():
        _assert_close(summary["damage_by_character"][character_id], expected_damage)
    role_breakdown = summary["effective_damage_role_breakdown"]
    _assert_close(role_breakdown["scheduled_damage"], EXPECTED_PPO_SCHEDULED_DAMAGE)
    _assert_close(role_breakdown["total_damage_delta"], 0.0)


def _assert_comparison(comparison: dict[str, Any]) -> None:
    assert comparison["schema_version"] == "manual_bc_ppo_comparison_v108"
    assert comparison["objective"] == "final_120_second_total_damage_only"
    assert comparison["winner"] == "bc_model"
    assert comparison["winner_model"] == "models/maskable_ppo_bc_v105.zip"
    assert comparison["ppo_candidate_classification"] == "valid_but_regressed"
    assert comparison["models"]["bc_model"]["sha256"] == EXPECTED_BC_MODEL_SHA256
    assert comparison["models"]["ppo_100k_candidate"]["sha256"] == EXPECTED_PPO_MODEL_SHA256
    results = comparison["results"]
    _assert_close(results["bc_model"]["total_damage"], EXPECTED_EVAL_TOTAL_DAMAGE)
    _assert_close(results["ppo_100k"]["total_damage"], EXPECTED_PPO_TOTAL_DAMAGE)
    assert results["ppo_100k"]["first_selected_action_divergence"] == {
        "zero_based_step": 4,
        "baseline": "aemeath_resonance_skill",
        "ppo": "swap_to_mornye",
    }


def _assert_close(actual: float, expected: float, *, tolerance: float = 1e-6) -> None:
    assert abs(float(actual) - expected) <= tolerance, (actual, expected)


def _is_cache_entry(name: str) -> bool:
    normalized = name.replace("\\", "/")
    parts = normalized.split("/")
    return (
        "__pycache__" in parts
        or ".pytest_cache" in parts
        or normalized.endswith((".pyc", ".pyo"))
    )


def _progress_contains(progress: object, value: str) -> bool:
    if isinstance(progress, dict):
        return any(_progress_contains(item, value) for item in progress.values())
    if isinstance(progress, list):
        return any(_progress_contains(item, value) for item in progress)
    return progress == value


def _run(command: list[str], *, cwd: Path, timeout: float) -> dict[str, Any]:
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    label = " ".join(command[1:])
    print(f"fresh-extraction check start: {label}", flush=True)
    started = time.perf_counter()
    stdout_fd, stdout_name = tempfile.mkstemp(prefix="archive-check-stdout-", suffix=".txt")
    stderr_fd, stderr_name = tempfile.mkstemp(prefix="archive-check-stderr-", suffix=".txt")
    os.close(stdout_fd)
    os.close(stderr_fd)
    stdout_path = Path(stdout_name)
    stderr_path = Path(stderr_name)
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process_kwargs: dict[str, Any] = {
        "cwd": cwd,
        "env": env,
        "stdout": None,
        "stderr": None,
        "creationflags": creationflags,
        "text": False,
    }
    if os.name != "nt":
        process_kwargs["start_new_session"] = True
    try:
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process_kwargs["stdout"] = stdout_file
            process_kwargs["stderr"] = stderr_file
            process = subprocess.Popen(command, **process_kwargs)
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                _terminate_process_tree(process)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    _kill_process_tree(process)
                    process.wait(timeout=10)
                elapsed = time.perf_counter() - started
                stdout_file.flush()
                stderr_file.flush()
                raise AssertionError(
                    _format_process_failure(
                        command=command,
                        timeout=timeout,
                        elapsed=elapsed,
                        stdout=_read_text(stdout_path),
                        stderr=_read_text(stderr_path),
                    )
                ) from exc
            elapsed = time.perf_counter() - started
            stdout_file.flush()
            stderr_file.flush()
        stdout = _read_text(stdout_path)
        stderr = _read_text(stderr_path)
        if returncode != 0:
            raise AssertionError(
                _format_process_failure(
                    command=command,
                    timeout=timeout,
                    elapsed=elapsed,
                    stdout=stdout,
                    stderr=stderr,
                    returncode=returncode,
                )
            )
        print(f"fresh-extraction check ok: {label} ({elapsed:.3f}s)", flush=True)
        return {"elapsed_seconds": elapsed, "stdout": stdout, "stderr": stderr}
    finally:
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def _kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def _format_process_failure(
    *,
    command: list[str],
    timeout: float,
    elapsed: float,
    stdout: str,
    stderr: str,
    returncode: int | None = None,
) -> str:
    status = f"returncode={returncode}" if returncode is not None else "timeout"
    return (
        f"Fresh extraction check failed ({status})\n"
        f"command: {' '.join(command)}\n"
        f"timeout_seconds: {timeout}\n"
        f"elapsed_seconds: {elapsed:.6f}\n"
        f"stdout:\n{stdout}\n"
        f"stderr:\n{stderr}"
    )


if __name__ == "__main__":
    main()
