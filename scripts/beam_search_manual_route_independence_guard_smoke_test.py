from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_FILES = [
    ROOT / "search" / "beam_search.py",
    ROOT / "search" / "beam_state.py",
]
FORBIDDEN = [
    "manual_120s_baseline_routes",
    "ROUTE_PATH",
    "SELECTED_ROUTE",
    "EXPECTED_RESOLVED_ROUTE",
    "maskable_ppo_bc_v105",
    "maskable_ppo_candidate_after_bc_v105",
    "manual_120s_bc_demonstration_v105.npz",
    "stable_baselines",
    "MaskablePPO",
    "predict(",
    "probabilities",
    "policy_probability",
]


def main() -> None:
    for path in CORE_FILES:
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN:
            assert forbidden not in text, (path, forbidden)
    reporting = (ROOT / "search" / "beam_reporting.py").read_text(encoding="utf-8")
    assert "BC_TOTAL_DAMAGE" in reporting
    plan = (ROOT / "search" / "beam_plan.py").read_text(encoding="utf-8")
    assert "manual_120s_baseline_routes_v104.json" in plan
    assert "selected_policy_actions" not in plan
    print("beam_search_manual_route_independence_guard_smoke_test ok")


if __name__ == "__main__":
    main()
