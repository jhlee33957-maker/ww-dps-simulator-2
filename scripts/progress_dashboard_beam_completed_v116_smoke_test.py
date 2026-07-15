from __future__ import annotations

import copy
import importlib.util
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_dashboard():
    fake_streamlit = types.SimpleNamespace(cache_data=lambda **_kwargs: (lambda function: function))
    original = sys.modules.get("streamlit")
    sys.modules["streamlit"] = fake_streamlit
    try:
        spec = importlib.util.spec_from_file_location("progress_dashboard_v116_under_test", ROOT / "progress_dashboard.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if original is None:
            del sys.modules["streamlit"]
        else:
            sys.modules["streamlit"] = original


def main() -> None:
    dashboard = load_dashboard()
    progress = json.loads((ROOT / "PROJECT_PROGRESS_STATE.json").read_text(encoding="utf-8"))
    plan = json.loads((ROOT / "data/beam_search_plan_v111.json").read_text(encoding="utf-8"))
    merged, _ = dashboard.merge_progress_data(
        copy.deepcopy(dashboard.EMBEDDED_PROGRESS_SNAPSHOT),
        {
            "PROJECT_PROGRESS_STATE.json": {"data": progress},
            "data/beam_search_plan_v111.json": {"data": plan},
        },
    )
    beam = merged["beam_search"]
    assert merged["best_method"] == "Completed Beam route"
    assert merged["best_total_damage"] == 5651892.274552992
    assert merged["best_dps"] == 47099.1022879416
    assert beam["full_120s_status"] == "Completed"
    assert beam["winner_route_id"] == "67a4250b3b8d0de9"
    assert beam["completed_route_count"] == 128
    assert beam["expansions"] == 4908270 < beam["safety_cap"] == 6500000
    assert beam["damage_gain_over_best_trained_model"] == 375047.9158609472
    assert beam["dps_gain_over_best_trained_model"] == 3125.3992988412283
    assert beam["global_optimum_proven"] is False
    assert merged["mcts"]["status"] == "Infrastructure ready; 20k calibration pending"
    assert merged["mcts"]["infrastructure_ready"] is True
    assert merged["mcts"]["calibration_20k_executed"] is False
    assert merged["mcts"]["production_search_executed"] is False
    assert "completed Beam route remains the current winner" in merged["mcts"]["summary"]
    print("progress_dashboard_beam_completed_v116_smoke_test ok")


if __name__ == "__main__":
    main()
