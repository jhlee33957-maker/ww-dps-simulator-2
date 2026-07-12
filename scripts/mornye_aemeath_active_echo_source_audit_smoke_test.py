from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    audit = json.loads(
        (ROOT / "data" / "source" / "mornye_aemeath_active_echo_source_audit_v102.json").read_text(
            encoding="utf-8-sig"
        )
    )
    assert audit["baseline_archive"] == "ww-dps-simulator-2(102).zip"
    assert audit["baseline_archive_sha256"] == "ca2c64e2a408737f0c407a10b9c44071fe5cc01d64f538af541bdebfd525a99c"
    assert audit["workbook_sha256"] == "81604978551989b5575e2d637ad4dfeb8c3b3b34d48e00a9ea79e9008c62f1f9"
    assert audit["implemented_action_ids"] == ["mornye_echo_reactor_husk", "aemeath_echo_sigillum"]
    assert audit["implemented_payload_action_ids"] == [
        "aemeath_echo_sigillum_hit_1",
        "aemeath_echo_sigillum_hit_2",
    ]
    assert audit["policy_action_count"] == 25

    reactor = audit["echoes"]["mornye_echo_reactor_husk"]
    assert reactor["source_refs"] == ["声骸!383", "dmg!2534"]
    assert_close(reactor["action_time_seconds"], 1.1, "Reactor action time")
    assert_close(reactor["expected_final_resonance_energy_gain_with_real_profile"], 12.381488, "Reactor RE")

    sigillum = audit["echoes"]["aemeath_echo_sigillum"]
    assert sigillum["source_refs"] == ["声骸!410", "声骸!411", "dmg!2632", "dmg!2633"]
    assert_close(sigillum["activation_action_time_seconds"], 0.0, "Sigillum activation time")
    assert [hit["due_frames"] for hit in sigillum["scheduled_hits"]] == [25, 55]
    assert_close(sigillum["expected_total_final_resonance_energy_gain_with_real_profile"], 2.832, "Sigillum RE")

    report = (ROOT / "reports" / "mornye_aemeath_active_echo_source_audit.md").read_text(encoding="utf-8")
    assert "Mornye Reactor Husk" in report
    assert "Aemeath Sigillum" in report
    print("mornye_aemeath_active_echo_source_audit_smoke_test ok")


if __name__ == "__main__":
    main()
