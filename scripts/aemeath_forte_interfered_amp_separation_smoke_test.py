from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from characters.aemeath import AemeathMechanic
from simulator.action_executor import execute_action
from simulator.models import ActionData, CharacterData, CombatState


def load_action(action_id: str) -> ActionData:
    with (ROOT / "data" / "actions.json").open("r", encoding="utf-8-sig") as file:
        for raw in json.load(file):
            if raw["id"] == action_id:
                return ActionData(**raw)
    raise AssertionError(f"missing action {action_id}")


def load_character(character_id: str) -> CharacterData:
    with (ROOT / "data" / "characters.json").open("r", encoding="utf-8-sig") as file:
        for raw in json.load(file):
            if raw["id"] == character_id:
                return CharacterData(**raw)
    raise AssertionError(f"missing character {character_id}")


def run_with_amp(amp: float):
    state = CombatState(
        active_character_id="aemeath",
        party_members=["aemeath"],
        resonance_energy={"aemeath": 125.0},
        concerto_energy={"aemeath": 0.0},
        mechanics_config={"aemeath": {"aemeath_resonance_mode": "tune_rupture"}},
        interfered_marker_damage_taken_amp=amp,
        interfered_marker_remaining=8.0 if amp else 0.0,
    )
    mechanic = AemeathMechanic()
    mechanic.initialize_state(state)
    data = state.character_mechanics_state["aemeath"]
    data["form"] = "aemeath"
    data["synchronization_rate"] = 100.0
    data["seraphic_duo_remaining"] = 5.0
    result = execute_action(
        load_action("aemeath_seraphic_duet_overturn"),
        state,
        {"aemeath": load_character("aemeath")},
        {},
        mechanic=mechanic,
        weapon_definitions={},
    )
    generated_hits = [hit for hit in result.hit_details if hit.get("is_generated_mechanic_damage")]
    assert generated_hits
    return result, generated_hits


def main() -> None:
    with (ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json").open(
        "r", encoding="utf-8-sig"
    ) as file:
        config_text = json.dumps(json.load(file), ensure_ascii=False)
    assert "1.0935" in config_text
    assert "1.531" not in config_text
    assert "1.5309" not in config_text

    base_result, base_hits = run_with_amp(0.0)
    amp_result, amp_hits = run_with_amp(0.4)
    assert base_result.aemeath_seraphic_duet_followup_multiplier == 1.0935
    assert amp_result.aemeath_seraphic_duet_followup_multiplier == 1.0935
    assert amp_result.generated_mechanic_damage > base_result.generated_mechanic_damage * 1.39
    assert amp_result.generated_mechanic_damage < base_result.generated_mechanic_damage * 1.41
    assert all(hit["source_multiplier"] == 1.0935 for hit in amp_hits)
    assert all(hit["applied_damage_taken_amp"] == 0.4 for hit in amp_hits)
    assert all(hit["effective_damage_taken_amp"] == 0.4 for hit in amp_hits)
    assert all(hit["applied_damage_taken_amp"] == 0.0 for hit in base_hits)
    print("aemeath_forte_interfered_amp_separation_smoke_test ok")


if __name__ == "__main__":
    main()
