from __future__ import annotations

from v114_test_support import add_event_action, build, outro_instances, set_concerto, value


def main() -> None:
    sim = build()
    set_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_mornye")
    assert sim.execute_action(add_event_action(sim, "mornye", "tune_rupture_shifting"))
    assert value(outro_instances(sim)["mornye"]) == 0.2
    assert sim.execute_action("swap_to_aemeath")
    set_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_lynae")
    row = sim.timeline[-1]
    event = next(e for e in row.transition_events if e.get("action_id") == "aemeath_outro_unseen_guard")
    assert event["recipient_values_after"] == {"mornye": 0.1, "lynae": 0.1}
    instances = outro_instances(sim)
    assert value(instances["mornye"]) == 0.1
    assert value(instances["lynae"]) == 0.2  # matching timed Intro upgrades after reset
    print("aemeath_outro_recast_reset_smoke_test ok")


if __name__ == "__main__":
    main()

