from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.full_real_cycle_integration import (
    _row_damage_attribution,
    assert_close,
    execute_strict_route,
)


EXPECTED_TOTAL_DAMAGE = 1792244.9381157316
EXPECTED_DAMAGE_BY_CHARACTER = {
    "aemeath": 1404246.4250625486,
    "lynae": 319145.0773344416,
    "mornye": 68853.43571874128,
}
EXPECTED_TUNE_RESPONSES = {
    "aemeath_starburst": ("aemeath", 37853.02353628158),
    "mornye_particle_jet": ("mornye", 18643.675744591033),
    "lynae_spectral_analysis": ("lynae", 117577.93963060687),
}
EXPECTED_TUNE_BREAK_ROW_DAMAGE = 264216.8723242778
EXPECTED_TUNE_BREAK_RESIDUAL = 90142.23341279835


def _assert_damage_by_character(actual: dict[str, float]) -> None:
    assert set(actual) == set(EXPECTED_DAMAGE_BY_CHARACTER)
    for character_id, expected in EXPECTED_DAMAGE_BY_CHARACTER.items():
        assert_close(actual[character_id], expected, f"{character_id} corrected damage", 1e-9)
    assert_close(sum(actual.values()), EXPECTED_TOTAL_DAMAGE, "damage attribution total", 1e-9)


def main() -> None:
    first = execute_strict_route()
    second = execute_strict_route()

    tune_break_row = first.simulation.timeline[30]
    assert tune_break_row.resolved_action_id == "aemeath_tune_break"
    assert_close(tune_break_row.damage, EXPECTED_TUNE_BREAK_ROW_DAMAGE, "Tune Break total row damage", 1e-9)
    assert len(tune_break_row.tune_response_events) == 3
    for event in tune_break_row.tune_response_events:
        response_id = event["response_id"]
        expected_source, expected_damage = EXPECTED_TUNE_RESPONSES[response_id]
        assert event["source_character_id"] == expected_source
        assert_close(event["damage"], expected_damage, f"{response_id} raw response damage", 1e-9)

    attribution = _row_damage_attribution(tune_break_row)
    assert_close(
        attribution["residual_actor_damage"],
        EXPECTED_TUNE_BREAK_RESIDUAL,
        "Tune Break Aemeath residual",
        1e-9,
    )
    assert attribution["actor_character_id"] == "aemeath"

    _assert_damage_by_character(first.result["totals"]["damage_by_character"])
    _assert_damage_by_character(second.result["totals"]["damage_by_character"])
    assert first.result["totals"]["damage_by_character"] == second.result["totals"]["damage_by_character"]

    sigillum_events = [
        event
        for row in first.simulation.timeline
        for event in row.scheduled_damage_events
        if event.get("source_action_id") == "aemeath_echo_sigillum"
    ]
    assert [event["source_character_id"] for event in sigillum_events] == ["aemeath", "aemeath"]
    assert all(event["damage"] > 0.0 for event in sigillum_events)

    mornye_syntony_events = [
        event
        for row in first.simulation.timeline
        for event in row.scheduled_damage_events
        if event.get("payload_action_id") in {
            "mornye_syntony_field_damage",
            "mornye_syntony_field_target_damage",
        }
    ]
    assert len(mornye_syntony_events) >= 3
    assert all(event["source_character_id"] == "mornye" for event in mornye_syntony_events)
    assert all(event["damage"] > 0.0 for event in mornye_syntony_events)

    seraphic_generated = [
        event
        for row in first.simulation.timeline
        for event in row.generated_mechanic_damage_events
        if event.get("source_action_id") in {
            "aemeath_seraphic_duet_overturn",
            "aemeath_seraphic_duet_encore",
        }
    ]
    assert len(seraphic_generated) == 2
    assert all(event["source_character_id"] == "aemeath" for event in seraphic_generated)
    assert all(event["damage"] > 0.0 for event in seraphic_generated)

    print("full_real_cycle_damage_attribution_smoke_test ok")


if __name__ == "__main__":
    main()
