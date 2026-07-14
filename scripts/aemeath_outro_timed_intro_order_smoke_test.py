from __future__ import annotations

from v114_test_support import build, outro_instances, set_concerto, value


def main() -> None:
    sim = build()
    set_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_lynae")
    row = sim.timeline[-1]
    assert row.damage > 0.0
    assert all(detail["applied_damage_amp"] == 0.1 for detail in row.hit_details)
    assert row.aemeath_outro_recipient_values_before["lynae"] == 0.1
    assert row.aemeath_outro_recipient_values_after["lynae"] == 0.2
    assert value(outro_instances(sim)["lynae"]) == 0.2
    assert row.aemeath_outro_upgraded_character_ids == ["lynae"]
    assert not row.aemeath_outro_upgrade_duration_refreshed
    print("aemeath_outro_timed_intro_order_smoke_test ok")


if __name__ == "__main__":
    main()
