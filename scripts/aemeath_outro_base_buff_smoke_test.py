from __future__ import annotations

from v114_test_support import assert_close, build, outro_instances, set_concerto, value


def main() -> None:
    no_concerto = build()
    assert no_concerto.execute_action("swap_to_mornye")
    assert not outro_instances(no_concerto)
    assert_close(no_concerto.state.concerto_energy["aemeath"], 0.0)

    sim = build()
    set_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_mornye")
    row = sim.timeline[-1]
    instances = outro_instances(sim)
    assert row.aemeath_outro_applied
    assert row.outgoing_concerto_consumed
    assert_close(sim.state.concerto_energy["aemeath"], 0.0)
    assert set(instances) == {"mornye", "lynae"}
    assert "aemeath" not in instances
    assert all(value(active) == 0.1 for active in instances.values())
    assert all(0.0 < active.remaining_duration < 20.0 for active in instances.values())

    unresolved = build(party="aemeath_test_party")
    unresolved.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "unresolved"
    set_concerto(unresolved, "aemeath")
    assert unresolved.execute_action("swap_to_dummy_support")
    assert all(value(active) == 0.1 for active in outro_instances(unresolved).values())
    assert unresolved.timeline[-1].aemeath_outro_unresolved_reason
    print("aemeath_outro_base_buff_smoke_test ok")


if __name__ == "__main__":
    main()

