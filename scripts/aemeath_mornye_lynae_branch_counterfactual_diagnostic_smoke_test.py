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
    ):
        assert route_id in routes
        assert "total_damage" in routes[route_id]
        assert "lynae_resource_trajectory" in routes[route_id]
    assert routes["lynae_core_route"]["selected_actions"]
    print("aemeath_mornye_lynae_branch_counterfactual_diagnostic_smoke_test ok")


if __name__ == "__main__":
    main()
