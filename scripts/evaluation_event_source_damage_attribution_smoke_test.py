from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.damage_attribution import (  # noqa: E402
    DamageAttributionError,
    damage_by_character,
    damage_by_character_and_source,
    row_damage_attribution,
)


def main() -> None:
    shared_event = {
        "event_id": "shared-generated",
        "source_character_id": "lynae",
        "source_action_id": "lynae_spectral_analysis",
        "damage": 13.0,
    }
    row = {
        "selected_action_id": "aemeath_tune_break",
        "resolved_action_id": "aemeath_tune_break",
        "actor_character_id": "aemeath",
        "total_action_damage": 100.0,
        "scheduled_damage_events": [
            {"event_id": "scheduled-1", "source_character_id": "mornye", "damage": 20.0}
        ],
        "tune_response_events": [
            {"event_id": "response-1", "response_id": "aemeath_starburst", "source_character_id": "aemeath", "damage": 30.0}
        ],
        "generated_mechanic_damage_events": [
            shared_event,
            dict(shared_event),
        ],
    }
    attribution = row_damage_attribution(row)
    assert attribution["residual_actor_damage"] == 37.0
    assert attribution["damage_by_character"] == {
        "aemeath": 67.0,
        "lynae": 13.0,
        "mornye": 20.0,
    }
    assert attribution["explicit_event_damage_by_role"] == {
        "generated_mechanic_damage": 13.0,
        "scheduled_damage": 20.0,
        "tune_response_damage": 30.0,
    }

    character_totals = damage_by_character([row], total_damage=100.0)
    assert character_totals == attribution["damage_by_character"]

    by_source = damage_by_character_and_source([row], total_damage=100.0)
    assert by_source["Aemeath direct action residual"] == 37.0
    assert by_source["Aemeath Tune Break response damage"] == 30.0
    assert by_source["Mornye scheduled damage"] == 20.0
    assert by_source["Lynae generated mechanic event damage"] == 13.0
    assert abs(sum(by_source.values()) - 100.0) <= 1e-9

    negative = dict(row, total_action_damage=10.0)
    try:
        row_damage_attribution(negative)
    except DamageAttributionError as exc:
        assert "negative residual" in str(exc)
    else:
        raise AssertionError("negative residual attribution did not fail")
    print("evaluation_event_source_damage_attribution_smoke_test ok")


if __name__ == "__main__":
    main()
