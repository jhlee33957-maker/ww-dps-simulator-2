from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.aemeath_mornye_lynae_branch_counterfactual_diagnostic import run_branch_counterfactual_diagnostic


def main() -> None:
    report = run_branch_counterfactual_diagnostic()
    routes = {route["route_id"]: route for route in report["routes"]}
    for route_id in (
        "aemeath_route",
        "swap_to_mornye_route",
        "swap_to_lynae_route",
        "lynae_core_route",
        "lynae_outro_route",
        "lynae_after_intro_liberation_used_route",
        "lynae_kaleidoscopic_after_liberation_route",
        "aemeath_post_liberation_ready_for_lynae_route",
    ):
        assert route_id in routes
        assert "total_damage" in routes[route_id]
        assert "lynae_resource_trajectory" in routes[route_id]
        assert "liberation_already_consumed" in routes[route_id]
    assert routes["lynae_core_route"]["selected_actions"]
    assert routes["lynae_after_intro_liberation_used_route"]["liberation_already_consumed"] is True
    assert routes["lynae_kaleidoscopic_after_liberation_route"]["visual_impact_reached"] is True
    print("aemeath_mornye_lynae_branch_counterfactual_diagnostic_smoke_test ok")


if __name__ == "__main__":
    main()
