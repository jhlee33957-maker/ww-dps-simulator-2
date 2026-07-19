from __future__ import annotations

from v124_timing_test_support import ROOT  # noqa: F401
from simulator.timing_training_gate import TimingObservationAuditRequired, assert_timing_runtime_workload_allowed, load_timing_runtime_gate


def main() -> None:
    gate = load_timing_runtime_gate()
    assert gate["markov_state_observation_audit_completed"] is True
    assert gate["observation_v7_required"] is True
    assert gate["observation_v7_implemented"] is False
    for workload in ("BC", "PPO", "Beam", "MCTS"):
        try:
            assert_timing_runtime_workload_allowed(workload)
        except TimingObservationAuditRequired:
            pass
        else:
            raise AssertionError(f"{workload} was not blocked")
    guarded_source = (ROOT / "rl" / "guarded_ppo.py").read_text(encoding="utf-8")
    refresh_source = (ROOT / "rl" / "train_maskable_ppo_bc_refresh_plan.py").read_text(encoding="utf-8")
    assert "assert_timing_runtime_workload_allowed" in guarded_source
    assert "assert_timing_runtime_workload_allowed" in refresh_source
    print("training_blocked_until_observation_audit_v124_smoke_test ok")


if __name__ == "__main__":
    main()
