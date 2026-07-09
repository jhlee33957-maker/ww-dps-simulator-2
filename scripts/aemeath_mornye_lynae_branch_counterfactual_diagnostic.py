from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare short-horizon Aemeath/Mornye/Lynae branch returns.")
    parser.add_argument("--party", type=str, default=PARTY_ID)
    parser.add_argument("--write-json", type=Path, default=None)
    return parser


def run_branch_counterfactual_diagnostic(
    party: str = PARTY_ID,
    write_json: Path | None = None,
) -> dict[str, Any]:
    routes = [
        _execute_route(
            "aemeath_route",
            setup=_setup_aemeath_ready,
            actions=["aemeath_resonance_skill", "aemeath_basic_attack", "aemeath_heavy_attack", "aemeath_resonance_skill"],
            party=party,
        ),
        _execute_route(
            "swap_to_mornye_route",
            setup=_setup_aemeath_ready,
            actions=["swap_to_mornye", "mornye_resonance_skill", "mornye_basic_attack"],
            party=party,
        ),
        _execute_route(
            "swap_to_lynae_route",
            setup=_setup_aemeath_ready,
            actions=["swap_to_lynae"],
            party=party,
        ),
        _execute_route(
            "lynae_core_route",
            setup=_setup_aemeath_ready,
            actions=[
                "swap_to_lynae",
                "lynae_resonance_skill",
                "lynae_spark_collision",
                "lynae_polychrome_leap",
                "lynae_polychrome_leap",
                "lynae_polychrome_leap",
                "lynae_visual_impact",
            ],
            party=party,
        ),
        _execute_lynae_outro_route(party),
    ]
    report = {
        "party_id": party,
        "diagnostic": "aemeath_mornye_lynae_branch_counterfactual",
        "note": "Diagnostic only: routes are deterministic short-horizon probes and do not assert Lynae must be better.",
        "routes": routes,
    }
    if write_json is not None:
        write_json.parent.mkdir(parents=True, exist_ok=True)
        write_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _new_sim(party: str) -> Simulation:
    return Simulation.from_json(ROOT / "data", party=party)


def _setup_aemeath_ready(sim: Simulation) -> None:
    sim.state.active_character_id = "aemeath"
    _set_full_concerto(sim, "aemeath")


def _set_full_concerto(sim: Simulation, character_id: str) -> None:
    state = sim.state.character_states[character_id]
    cap = float(state.get("concerto_energy_cap", 100.0) or 100.0)
    state["concerto_energy"] = cap
    state["concerto_ready"] = True
    sim.state.concerto_energy[character_id] = cap


def _execute_route(
    name: str,
    setup: Callable[[Simulation], None],
    actions: list[str],
    party: str,
) -> dict[str, Any]:
    sim = _new_sim(party)
    setup(sim)
    attempted_actions: list[dict[str, Any]] = []
    trajectory = [_lynae_state_point(sim, "initial")]
    for action_id in actions:
        valid_before = action_id in sim.actions and sim.is_action_available(sim.actions[action_id])
        executed = bool(action_id in sim.actions and sim.execute_action(action_id))
        row = sim.timeline[-1].model_dump(mode="json") if executed and sim.timeline else None
        attempted_actions.append(
            {
                "selected_action_id": action_id,
                "valid_before": valid_before,
                "executed": executed,
                "resolved_action_id": row.get("resolved_action_id") if row else None,
            }
        )
        trajectory.append(_lynae_state_point(sim, action_id))
    return _route_report(name, sim, attempted_actions, trajectory)


def _execute_lynae_outro_route(party: str) -> dict[str, Any]:
    sim = _new_sim(party)
    _setup_aemeath_ready(sim)
    attempted_actions: list[dict[str, Any]] = []
    trajectory = [_lynae_state_point(sim, "initial")]
    opening = [
        "swap_to_lynae",
        "lynae_resonance_skill",
        "lynae_spark_collision",
        "lynae_polychrome_leap",
        "lynae_polychrome_leap",
        "lynae_polychrome_leap",
        "lynae_visual_impact",
    ]
    for action_id in opening:
        _try_action(sim, action_id, attempted_actions, trajectory)

    priority = [
        "lynae_resonance_liberation",
        "lynae_resonance_skill",
        "lynae_basic_attack",
        "lynae_heavy_attack",
        "lynae_mid_air_attack",
        "lynae_dodge_counter",
        "lynae_spark_collision",
        "lynae_polychrome_leap",
        "lynae_visual_impact",
        "short_wait",
    ]
    for _ in range(60):
        if _concerto_ready(sim, "lynae"):
            break
        action_id = next((item for item in priority if item in sim.actions and sim.is_action_available(sim.actions[item])), None)
        if action_id is None:
            break
        _try_action(sim, action_id, attempted_actions, trajectory)

    _try_action(sim, "swap_to_aemeath", attempted_actions, trajectory)
    return _route_report("lynae_outro_route", sim, attempted_actions, trajectory)


def _try_action(
    sim: Simulation,
    action_id: str,
    attempted_actions: list[dict[str, Any]],
    trajectory: list[dict[str, Any]],
) -> None:
    valid_before = action_id in sim.actions and sim.is_action_available(sim.actions[action_id])
    executed = bool(action_id in sim.actions and sim.execute_action(action_id))
    row = sim.timeline[-1].model_dump(mode="json") if executed and sim.timeline else None
    attempted_actions.append(
        {
            "selected_action_id": action_id,
            "valid_before": valid_before,
            "executed": executed,
            "resolved_action_id": row.get("resolved_action_id") if row else None,
        }
    )
    trajectory.append(_lynae_state_point(sim, action_id))


def _route_report(
    name: str,
    sim: Simulation,
    attempted_actions: list[dict[str, Any]],
    trajectory: list[dict[str, Any]],
) -> dict[str, Any]:
    total_damage = float(sim.state.total_damage)
    combat_time_cost = float(sim.state.combat_time)
    selected_actions = [item["selected_action_id"] for item in attempted_actions if item["executed"]]
    resolved_actions = [row.resolved_action_id or row.selected_action_id for row in sim.timeline]
    final_row = sim.timeline[-1].model_dump(mode="json") if sim.timeline else {}
    lynae_outro_became_available = any(point["concerto_ready"] for point in trajectory)
    return {
        "route_id": name,
        "route_label": name.replace("_", " "),
        "total_damage": total_damage,
        "combat_time_cost": combat_time_cost,
        "damage_per_combat_second": total_damage / combat_time_cost if combat_time_cost > 0.0 else 0.0,
        "action_time": float(sim.state.current_time),
        "attempted_actions": attempted_actions,
        "selected_actions": selected_actions,
        "resolved_actions": resolved_actions,
        "lynae_resource_trajectory": trajectory,
        "lynae_outro_available": lynae_outro_became_available,
        "lynae_outro_ready_at_end": _concerto_ready(sim, "lynae"),
        "buffs_applied_after_lynae_outro": final_row.get("applied_buffs", []) if selected_actions[-1:] == ["swap_to_aemeath"] else [],
        "active_character": sim.state.active_character_id,
    }


def _lynae_state_point(sim: Simulation, label: str) -> dict[str, Any]:
    state = sim.state.character_mechanics_state.get("lynae", {})
    return {
        "after_action": label,
        "overflow": float(state.get("overflow", 0.0) or 0.0),
        "lumiflow": float(state.get("lumiflow", 0.0) or 0.0),
        "true_color": float(state.get("true_color", 0.0) or 0.0),
        "kaleidoscopic_parade_remaining": float(state.get("kaleidoscopic_parade_remaining", 0.0) or 0.0),
        "photocromic_flux_active": bool(state.get("photocromic_flux_active", False)),
        "concerto_energy": float(sim.state.concerto_energy.get("lynae", 0.0) or 0.0),
        "concerto_ready": _concerto_ready(sim, "lynae"),
    }


def _concerto_ready(sim: Simulation, character_id: str) -> bool:
    return bool(sim.state.character_states.get(character_id, {}).get("concerto_ready", False))


def main() -> None:
    args = build_arg_parser().parse_args()
    report = run_branch_counterfactual_diagnostic(party=args.party, write_json=args.write_json)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
