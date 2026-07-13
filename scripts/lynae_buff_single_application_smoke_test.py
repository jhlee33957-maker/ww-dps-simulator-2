from __future__ import annotations

import math
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def install_gymnasium_stub() -> None:
    try:
        import gymnasium  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    class Env:
        def reset(self, seed=None, options=None):
            return None

    class Discrete:
        def __init__(self, n):
            self.n = n

    class Box:
        def __init__(self, low, high, shape, dtype):
            self.low = low
            self.high = high
            self.shape = shape
            self.dtype = dtype

    spaces = types.SimpleNamespace(Discrete=Discrete, Box=Box)
    sys.modules["gymnasium"] = types.SimpleNamespace(Env=Env, spaces=spaces)
    sys.modules["gymnasium.spaces"] = spaces


install_gymnasium_stub()

from env.wuwa_env import WuwaDpsEnv
from simulator.buff_system import (
    apply_buff,
    buffed_combat_stats,
    damage_amp_for_action,
    effective_atk_percent_contribution,
    effective_damage_amp_contribution,
    get_active_buffs_for_action,
)
from simulator.models import ActiveBuff
from simulator.simulation import Simulation


PARTY_ID = "aemeath_lynae_enabled_test_party"


def assert_close(actual: float, expected: float, label: str) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6), f"{label}: {actual} != {expected}"


def make_env() -> WuwaDpsEnv:
    env = WuwaDpsEnv(ROOT / "data", party=PARTY_ID)
    env.reset()
    return env


def execute_lynae_outro_to_aemeath(sim: Simulation) -> None:
    sim.state.active_character_id = "lynae"
    sim.state.concerto_energy["lynae"] = 100.0
    assert sim.execute_action("swap_to_aemeath")


def observation(env: WuwaDpsEnv) -> dict[str, float]:
    return dict(zip(env.observation_labels(), [float(value) for value in env._get_observation()], strict=True))


def slot_for_character(env: WuwaDpsEnv, character_id: str) -> int:
    reverse = {character: slot for slot, character in env.observation_slot_mapping().items() if character is not None}
    return int(reverse[character_id].rsplit("_", 1)[1])


def active_buff(sim: Simulation, buff_id: str) -> ActiveBuff:
    return next(buff for buff in sim.state.active_buffs if buff.buff_id == buff_id)


def test_real_lynae_outro_single_application() -> dict[str, float]:
    env = make_env()
    sim = env.simulation
    execute_lynae_outro_to_aemeath(sim)

    assert active_buff(sim, "static_mist_incoming_atk")
    assert active_buff(sim, "pact_neonlight_incoming_atk")

    aemeath = sim.characters["aemeath"]
    stats = buffed_combat_stats(aemeath, sim.state, sim.buffs)
    assert_close(stats["static_mist_incoming_atk_percent_bonus"], 0.10, "Static Mist ATK")
    assert_close(stats["pact_neonlight_incoming_atk_percent_bonus"], 0.15, "Pact ATK at zero Tune Break Boost")
    assert_close(stats["runtime_atk_percent_bonus"], 0.25, "Static Mist plus Pact ATK")
    assert stats["runtime_atk_percent_bonus"] not in {0.35, 0.50}

    normal_action = sim.resolve_action_for_character(sim.actions["aemeath_basic_attack"], "aemeath")
    liberation_action = sim.resolve_action_for_character(sim.actions["aemeath_resonance_liberation"], "aemeath")
    assert_close(damage_amp_for_action("aemeath", normal_action, sim.state, sim.buffs), 0.15, "Outro normal amp")

    active_pairs = get_active_buffs_for_action("aemeath", liberation_action, sim.state, sim.buffs)
    generic_amp = sum(effective_damage_amp_contribution(active, buff, category="all") for active, buff in active_pairs)
    liberation_amp = sum(
        effective_damage_amp_contribution(active, buff, category="resonance_liberation")
        for active, buff in active_pairs
    )
    assert_close(generic_amp, 0.15, "Outro generic amp")
    assert_close(liberation_amp, 0.25, "Outro Liberation amp")
    assert_close(
        damage_amp_for_action("aemeath", liberation_action, sim.state, sim.buffs),
        0.40,
        "Outro Liberation total amp",
    )

    obs = observation(env)
    aemeath_slot = slot_for_character(env, "aemeath")
    lynae_slot = slot_for_character(env, "lynae")
    assert_close(obs[f"slot_{aemeath_slot}.runtime_all_damage_amp_scaled"], 0.15, "Aemeath observed all amp")
    assert_close(
        obs[f"slot_{aemeath_slot}.runtime_liberation_damage_amp_scaled"],
        0.25,
        "Aemeath observed Liberation amp",
    )
    assert_close(
        obs[f"slot_{aemeath_slot}.runtime_atk_percent_bonus_scaled"],
        0.50,
        "Aemeath observed ATK percent",
    )
    assert_close(obs[f"slot_{lynae_slot}.runtime_all_damage_amp_scaled"], 0.0, "Lynae unrelated all amp")
    assert_close(obs[f"slot_{lynae_slot}.runtime_liberation_damage_amp_scaled"], 0.0, "Lynae unrelated Liberation amp")

    return {
        "static_mist": stats["static_mist_incoming_atk_percent_bonus"],
        "pact": stats["pact_neonlight_incoming_atk_percent_bonus"],
        "combined_atk": stats["runtime_atk_percent_bonus"],
        "normal_amp": damage_amp_for_action("aemeath", normal_action, sim.state, sim.buffs),
        "liberation_total_amp": damage_amp_for_action("aemeath", liberation_action, sim.state, sim.buffs),
        "observed_atk_scaled": obs[f"slot_{aemeath_slot}.runtime_atk_percent_bonus_scaled"],
    }


def test_liberation_party_amp_remains_single() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    apply_buff(sim.state, sim.buffs["lynae_liberation_party_damage_amp"], "lynae")
    action = sim.resolve_action_for_character(sim.actions["aemeath_basic_attack"], "aemeath")
    assert_close(damage_amp_for_action("aemeath", action, sim.state, sim.buffs), 0.24, "Lynae Liberation party amp")


def test_generic_attack_precedence_regressions() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    apply_buff(sim.state, sim.buffs["support_attack_boost"], "lynae")
    stats = buffed_combat_stats(sim.characters["aemeath"], sim.state, sim.buffs)
    assert_close(stats["runtime_atk_percent_bonus"], 0.18, "support_attack_boost")

    for value in (0.15, 0.27, 0.30):
        sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
        sim.state.active_buffs.append(
            ActiveBuff(
                buff_id="pact_neonlight_incoming_atk",
                source_character_id="lynae",
                target_character_id="aemeath",
                remaining_duration=15.0,
                metadata={"dynamic_value": value},
            )
        )
        active = active_buff(sim, "pact_neonlight_incoming_atk")
        assert_close(
            effective_atk_percent_contribution(active, sim.buffs["pact_neonlight_incoming_atk"]),
            value,
            f"Pact dynamic {value}",
        )
        stats = buffed_combat_stats(sim.characters["aemeath"], sim.state, sim.buffs)
        assert_close(stats["runtime_atk_percent_bonus"], value, f"Pact runtime {value}")

    sim = Simulation.from_json(ROOT / "data", party="aemeath_mornye_lynae_enabled_test_party")
    sim.state.active_buffs.append(
        ActiveBuff(
            buff_id="mornye_halo_of_starry_radiance_5set",
            source_character_id="mornye",
            remaining_duration=4.0,
            metadata={"dynamic_value": 0.25},
        )
    )
    stats = buffed_combat_stats(sim.characters["aemeath"], sim.state, sim.buffs)
    assert_close(stats["halo_of_starry_radiance_5set_atk_percent_bonus"], 0.25, "Halo detail")
    assert_close(stats["runtime_atk_percent_bonus"], 0.25, "Halo runtime")


def test_category_damage_amp_combines_once() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID)
    sim._apply_specific_character_buff(
        buff_id="lynae_outro_all_damage_amp",
        source_character_id="lynae",
        target_character_id="aemeath",
        application_time=sim.state.current_time,
        metadata={"event_source": "test"},
    )
    sim._apply_specific_character_buff(
        buff_id="lynae_outro_liberation_damage_amp",
        source_character_id="lynae",
        target_character_id="aemeath",
        application_time=sim.state.current_time,
        metadata={"event_source": "test"},
    )
    action = sim.resolve_action_for_character(sim.actions["aemeath_resonance_liberation"], "aemeath")
    assert_close(damage_amp_for_action("aemeath", action, sim.state, sim.buffs), 0.40, "all plus category amp")


def main() -> None:
    values = test_real_lynae_outro_single_application()
    test_liberation_party_amp_remains_single()
    test_generic_attack_precedence_regressions()
    test_category_damage_amp_combines_once()
    print(
        "lynae_buff_single_application_smoke_test ok "
        f"static_mist={values['static_mist']:.2f} "
        f"pact={values['pact']:.2f} "
        f"combined_atk={values['combined_atk']:.2f} "
        f"normal_amp={values['normal_amp']:.2f} "
        f"liberation_total_amp={values['liberation_total_amp']:.2f}"
    )


if __name__ == "__main__":
    main()
