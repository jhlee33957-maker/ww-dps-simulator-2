from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_result_role import resolve_mcts_result_role, result_role_fields
from search.mcts_reporting import write_mcts_results


def fails(callable_, text: str) -> None:
    try: callable_()
    except ValueError as error: assert text in str(error), str(error)
    else: raise AssertionError("expected role resolution failure")


def main() -> None:
    plans = [
        (Path("data/mcts_plan_v117_32gb.json"), "4d69880283f7a2fe837631fece76cd5eb06e62af544b31e9ea6c96f1a82f11bb", "calibration"),
        (Path("data/mcts_plan_v118_32gb_3x50k.json"), "2f5cb64f0a5b71a3957dadfbeff8f2c9ac7923b76e52ab410bcb805dc2f38562", "production"),
    ]
    resolved = []
    for path, digest, expected_role in plans:
        plan = json.loads((ROOT / path).read_text(encoding="utf-8"))
        stages = plan["stages"]
        for stage in stages:
            before = hashlib.sha256(json.dumps(stage, sort_keys=True).encode()).hexdigest()
            role = resolve_mcts_result_role(path, digest, stage["stage_id"], copy.deepcopy(stage), root=ROOT)
            after = hashlib.sha256(json.dumps(stage, sort_keys=True).encode()).hexdigest()
            assert role == expected_role and before == after
            flags = result_role_fields(role)
            assert flags["calibration_only"] is (role == "calibration")
            assert flags["production_search_result"] is (role == "production")
            resolved.append(role)
    prod_plan = json.loads((ROOT / plans[1][0]).read_text(encoding="utf-8"))
    stage = prod_plan["stages"][0]
    fails(lambda: resolve_mcts_result_role(plans[1][0], "0" * 64, stage["stage_id"], stage, root=ROOT), "SHA mismatch")
    fails(lambda: resolve_mcts_result_role(plans[1][0], plans[1][1], "wrong_stage", stage, root=ROOT), "Unknown hash-pinned")
    bad = dict(stage, result_role="unknown")
    fails(lambda: resolve_mcts_result_role(plans[1][0], plans[1][1], stage["stage_id"], bad, root=ROOT), "Unknown explicit")
    source = (ROOT / "search/mcts_reporting.py").read_text(encoding="utf-8")
    assert '"calibration_only": True' not in source
    with tempfile.TemporaryDirectory(prefix="mcts-role-reporting-") as temporary:
        output = Path(temporary)
        written = write_mcts_results(
            output,
            {
                "stage_id": stage["stage_id"], "termination_status": "fixture",
                "simulations_completed": 0, "completed_rollout_count": 0, "_completed_routes": [],
                "logical_result_sha256": "a" * 64, "rng_final_state_sha256": "b" * 64,
            },
            plan_path=plans[1][0], plan_sha256=plans[1][1], stage=stage, root=ROOT,
        )
        final = written["final_summary"]
        assert final["result_role"] == "production" and final["calibration_only"] is False
        assert final["production_search_result"] is True and final["global_optimum_proven"] is False
        assert written["result"]["logical_result_sha256"] == "a" * 64
        assert written["result"]["rng_final_state_sha256"] == "b" * 64
    print(f"mcts_result_role_reporting_smoke_test ok calibration={resolved.count('calibration')} production={resolved.count('production')}")


if __name__ == "__main__": main()
