"""Guard combat-effect duration progression against action-time regressions.

Duration-based combat effects must tick by resolved combat elapsed time, while
action-local clocks such as timeline time and cooldowns can keep their existing
semantics. This smoke test intentionally checks only the central effect ticking
paths so action-time uses elsewhere do not become false positives.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def assert_contains(source: str, needle: str, label: str) -> None:
    if needle not in source:
        raise AssertionError(f"Missing {label}: {needle}")


def assert_not_contains(source: str, needle: str, label: str) -> None:
    if needle in source:
        raise AssertionError(f"Unexpected {label}: {needle}")


def main() -> None:
    executor_source = (ROOT / "simulator" / "action_executor.py").read_text(encoding="utf-8")
    simulation_source = (ROOT / "simulator" / "simulation.py").read_text(encoding="utf-8")

    assert_contains(
        executor_source,
        "tick_buffs(state, effective_combat_time_cost)",
        "active buff combat-time tick",
    )
    assert_contains(
        executor_source,
        "advance_anomalies(state, effective_combat_time_cost)",
        "anomaly combat-time tick",
    )
    assert_not_contains(
        executor_source,
        "tick_buffs(state, action_time)",
        "active buff action-time tick",
    )
    assert_not_contains(
        executor_source,
        "advance_anomalies(state, action_time)",
        "anomaly action-time tick",
    )

    assert_contains(
        simulation_source,
        "combat_elapsed=result.effective_combat_time_cost",
        "character mechanic combat elapsed argument",
    )
    assert_contains(
        simulation_source,
        "action_elapsed=result.action_time",
        "character mechanic action elapsed argument",
    )
    assert_not_contains(
        simulation_source,
        "mechanic.advance_time(self.state, result.action_time)",
        "old mechanic action-time-only call",
    )
    assert_contains(
        simulation_source,
        "self._advance_tune_break_runtime(\n"
        "            action_elapsed=result.action_time,\n"
        "            combat_elapsed=result.effective_combat_time_cost,\n"
        "        )",
        "Tune Break runtime split elapsed call",
    )

    print("combat-time effect duration guard ok")


if __name__ == "__main__":
    main()
