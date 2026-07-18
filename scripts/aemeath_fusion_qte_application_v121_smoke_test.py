from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import make_account_sim
from aemeath_qte_enabled_transition_smoke_test import set_concerto, set_qte_mode


def main() -> None:
    for form, expected in (("aemeath", "aemeath_qte_intro_human"), ("mech", "aemeath_qte_intro_mech")):
        sim = make_account_sim("lynae", aemeath_resonance_mode="fusion_burst")
        sim.state.character_states["aemeath"]["form"] = form
        set_concerto(sim, "lynae", 100.0)
        set_qte_mode(sim, "enabled")
        assert sim.execute_action("swap_to_aemeath")
        state = sim.state.character_mechanics_state["aemeath"]
        assert sim.last_action_result.resolved_action_id == f"transition:{expected}"
        assert state["fusion_effect_stacks"] == 2
        assert state["fusion_trail_stacks"] == 2
        assert state["fusion_trail_event_log"][-1]["source_event_id"] == f"transition:{expected}"
    print("aemeath_fusion_qte_application_v121_smoke_test ok")


if __name__ == "__main__":
    main()
