from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(source: str, needle: str, label: str) -> None:
    if needle not in source:
        raise AssertionError(f"Missing {label}: {needle}")


def reject(source: str, needle: str, label: str) -> None:
    if needle in source:
        raise AssertionError(f"Unexpected {label}: {needle}")


def main() -> None:
    executor = (ROOT / "simulator" / "action_executor.py").read_text(encoding="utf-8")
    snapshot = (ROOT / "simulator" / "action_start_snapshot.py").read_text(encoding="utf-8")
    weapon = (ROOT / "simulator" / "weapon_effects.py").read_text(encoding="utf-8")
    simulation = (ROOT / "simulator" / "simulation.py").read_text(encoding="utf-8")
    buff_system = (ROOT / "simulator" / "buff_system.py").read_text(encoding="utf-8")

    require(snapshot, "class ActionStartEffectSnapshot", "snapshot dataclass")
    require(snapshot, "capture_action_start_effect_snapshot", "snapshot capture function")
    require(executor, "action_start_snapshot = capture_action_start_effect_snapshot(state)", "snapshot creation")
    require(executor, "force_active_buff_ids: set[str] = set(action_start_snapshot.active_buff_ids)", "generic buff snapshot")
    require(executor, "action_start_snapshot.target_damage_taken_amp", "Interfered Marker snapshot amp")
    require(executor, "action_start_snapshot.havoc_bane_def_reduction", "Havoc Bane snapshot def reduction")
    require(executor, "application_time=combat_start_time", "Trailblazing Star same-action combat-time application")
    require(weapon, "action_start_snapshot: ActionStartEffectSnapshot | None = None", "weapon snapshot argument")
    require(weapon, "force_active_buff_ids=set(action_start_snapshot.active_buff_ids)", "Everbright generic buff snapshot")

    reject(executor, "get_havoc_bane_def_reduction_at_time(state, hit.time)", "Havoc Bane hit-time gate")
    reject(executor, "_active_interfered_marker_buff_damage_amp(state, buffs, time_offset=hit.time)", "old marker dedupe")
    reject(executor, "application_time=start_time", "Trailblazing Star same-action visual-time application")
    reject(executor, "application_time=state.current_time", "Trailblazing Star same-action current_time application")
    reject(weapon, "float(active.remaining_duration) - time_offset),", "Everbright hit-time remaining gate")

    require(executor, "tick_buffs(state, effective_combat_time_cost)", "combat-time buff ticking")
    require(buff_system, "_cap_combat_uptime_windows", "partial uptime cap")
    require(simulation, "weapon_effect_uptime_seconds(\n                self.state,\n                STARFIELD_CALIBRATOR_BUFF_ID,\n                self.state.combat_time,", "weapon uptime combat time")
    require(simulation, "trailblazing_star_uptime_seconds(\n                self.state,\n                self.state.combat_time,", "echo uptime combat time")
    reject(simulation, "weapon_effect_uptime_seconds(\n                self.state,\n                STARFIELD_CALIBRATOR_BUFF_ID,\n                self.state.current_time,", "weapon uptime current_time")
    reject(simulation, "trailblazing_star_uptime_seconds(\n                self.state,\n                self.state.current_time,", "echo uptime current_time")

    print("action_start_effect_snapshot_guard_smoke_test ok")


if __name__ == "__main__":
    main()
