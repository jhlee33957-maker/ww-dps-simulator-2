from __future__ import annotations

from v124_timing_test_support import make_sim
from account_constellation_v121_runtime_test_utils import make_account_sim, ready_mornye_distributed_array


HEAVY_ID = "mornye_heavy_inversion"
ARRAY_ID = "mornye_skill_distributed_array"


def ready_heavy_sim():
    sim = make_sim("mornye")
    state = sim.state.character_mechanics_state["mornye"]
    state.update({"mode": "wide_field_observation", "wide_field_observation_remaining": 10.0, "relative_momentum": 100.0})
    return sim


def packet_events(sim, action_id: str):
    return [event for event in sim.state.chronological_event_log if event.get("source_action_id") == action_id and "packet_group_id" in event]


def ready_account_array_sim():
    sim = make_account_sim("mornye")
    ready_mornye_distributed_array(sim)
    return sim
