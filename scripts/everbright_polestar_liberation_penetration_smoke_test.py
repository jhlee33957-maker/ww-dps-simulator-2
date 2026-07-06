from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.buff_system import tick_buffs
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config
from simulator.weapon_effects import apply_weapon_mechanic_event_effects


DATA_DIR = ROOT / "data"
BUFF_ID = "everbright_polestar_liberation_penetration"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def transition_config(mode: str) -> dict:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = mode
    return config


def make_sim(mode: str = "fusion_burst", rank: int = 1) -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
        transition_config=transition_config(mode),
    )
    sim.characters["aemeath"].weapon["rank"] = rank
    return sim


def active_penetration_buff(sim: Simulation):
    active = [buff for buff in sim.state.active_buffs if buff.buff_id == BUFF_ID]
    assert len(active) == 1
    return active[0]


def trigger(sim: Simulation):
    assert sim.execute_action("aemeath_basic_form_stage_3")
    return sim.timeline[-1]


def test_trigger_modes_and_refresh() -> None:
    for mode, event_tag in (("fusion_burst", "fusion_burst"), ("tune_rupture", "tune_rupture_shifting")):
        sim = make_sim(mode)
        row = trigger(sim)
        assert row.emitted_mechanic_event_tags == [event_tag]
        assert row.weapon_effect_triggered is True
        assert row.weapon_effect_logs[-1]["everbright_polestar_liberation_penetration_active"] is True
        buff = active_penetration_buff(sim)
        assert buff.stack_count == 1
        assert_close(buff.remaining_duration, 8.0, "duration")
        assert_close(buff.metadata["dynamic_def_ignore"], 0.32, "R1 DEF Ignore")
        assert_close(buff.metadata["dynamic_fusion_res_ignore"], 0.10, "R1 Fusion RES Ignore")

    sim = make_sim("fusion_burst")
    trigger(sim)
    tick_buffs(sim.state, 3.0)
    assert active_penetration_buff(sim).remaining_duration < 8.0
    log = apply_weapon_mechanic_event_effects(
        emitted_event_tags=["fusion_burst"],
        source_character_id="aemeath",
        state=sim.state,
        characters=sim.characters,
        buffs=sim.buffs,
        weapon_definitions=sim.weapon_definitions,
        application_time=sim.state.current_time + 3.0,
        event_source="test_refresh",
    )
    assert log["weapon_effect_buff_refreshed"] is True
    assert log["everbright_polestar_buff_refreshed"] is True
    assert_close(active_penetration_buff(sim).remaining_duration, 8.0, "refresh duration")


def test_qualifying_and_nonqualifying_damage() -> None:
    sim = make_sim("fusion_burst")
    trigger(sim)
    assert sim.execute_action("aemeath_heavy_aemeath_charged_1")
    liberation = sim.timeline[-1]
    assert liberation.damage_bonus_category == "resonance_liberation"
    assert liberation.everbright_polestar_liberation_penetration_active is True
    assert_close(liberation.everbright_polestar_def_ignore_bonus, 0.32, "liberation DEF Ignore")
    assert_close(liberation.everbright_polestar_fusion_res_ignore_bonus, 0.10, "liberation Fusion RES Ignore")

    assert sim.execute_action("aemeath_basic_form_stage_1")
    basic = sim.timeline[-1]
    assert basic.damage_bonus_category == "basic_attack"
    assert basic.everbright_polestar_liberation_penetration_active is False
    assert_close(basic.everbright_polestar_def_ignore_bonus, 0.0, "basic DEF Ignore")

    skill = make_sim("fusion_burst")
    trigger(skill)
    skill.state.cooldowns.clear()
    assert skill.execute_action("aemeath_resonance_skill")
    skill_row = skill.timeline[-1]
    assert skill_row.damage_bonus_category == "resonance_skill"
    assert_close(skill_row.everbright_polestar_def_ignore_bonus, 0.0, "skill DEF Ignore")

    tune = make_sim("fusion_burst")
    trigger(tune)
    tune.state.enemy_tune_break_available = True
    tune.state.enemy_mistune_active = True
    assert tune.execute_action("aemeath_tune_break")
    tune_row = tune.timeline[-1]
    assert tune_row.damage_bonus_category == "tune_break"
    assert_close(tune_row.everbright_polestar_def_ignore_bonus, 0.0, "Tune Break DEF Ignore")
    assert_close(tune_row.everbright_polestar_fusion_res_ignore_bonus, 0.0, "Tune Break Fusion RES Ignore")

    tick_buffs(tune.state, 8.1)
    assert not any(buff.buff_id == BUFF_ID for buff in tune.state.active_buffs)


def test_rank_five_values() -> None:
    sim = make_sim("fusion_burst", rank=5)
    trigger(sim)
    assert sim.execute_action("aemeath_heavy_aemeath_charged_1")
    row = sim.timeline[-1]
    assert_close(row.everbright_polestar_def_ignore_bonus, 0.64, "R5 DEF Ignore")
    assert_close(row.everbright_polestar_fusion_res_ignore_bonus, 0.30, "R5 Fusion RES Ignore")


def main() -> None:
    test_trigger_modes_and_refresh()
    test_qualifying_and_nonqualifying_damage()
    test_rank_five_values()
    print("everbright_polestar_liberation_penetration_smoke_test ok")


if __name__ == "__main__":
    main()
