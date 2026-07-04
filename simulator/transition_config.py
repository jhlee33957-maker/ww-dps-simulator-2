from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from simulator.party_transition import load_transition_config as load_base_transition_config


VALID_TRANSITION_MODES = {"disabled", "dry_run", "enabled"}
SUPPORTED_CHARACTER_TRANSITIONS = (
    ("aemeath", "intro_qte"),
    ("mornye", "intro_qte"),
    ("mornye", "outro"),
)


def load_transition_config(data_dir: Path | str) -> dict[str, Any]:
    return load_base_transition_config(data_dir)


def build_transition_mode_overrides(
    *,
    transition_mode: str | None = None,
    aemeath_qte_mode: str | None = None,
    mornye_intro_mode: str | None = None,
) -> dict[str, Any]:
    overrides: dict[str, Any] = {"characters": {}}
    if transition_mode:
        _validate_mode(transition_mode)
        set_character_transition_mode(overrides, "aemeath", "intro_qte", transition_mode)
        set_character_transition_mode(overrides, "mornye", "intro_qte", transition_mode)
    if aemeath_qte_mode:
        _validate_mode(aemeath_qte_mode)
        set_character_transition_mode(overrides, "aemeath", "intro_qte", aemeath_qte_mode)
    if mornye_intro_mode:
        _validate_mode(mornye_intro_mode)
        set_character_transition_mode(overrides, "mornye", "intro_qte", mornye_intro_mode)
    return overrides


def build_effective_transition_config(
    base_config: dict[str, Any],
    party_preset: dict[str, Any] | None = None,
    *,
    cli_overrides: dict[str, Any] | None = None,
    ui_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    effective = deepcopy(base_config)
    sources = ["default"]
    preset_overrides = (party_preset or {}).get("transition_overrides")
    if preset_overrides:
        _deep_update(effective, preset_overrides)
        sources.append("party_preset")
    mechanic_overrides = (party_preset or {}).get("mechanic_overrides")
    if mechanic_overrides:
        effective.setdefault("mechanics", {})
        _deep_update(effective["mechanics"], mechanic_overrides)
        sources.append("party_preset_mechanics")
    if ui_overrides:
        _deep_update(effective, ui_overrides)
        sources.append("ui_override")
    if cli_overrides:
        _deep_update(effective, cli_overrides)
        sources.append("cli_override")
    effective["_transition_config_source"] = sources
    return effective


def get_character_transition_mode(
    config: dict[str, Any],
    character_id: str,
    transition_type: str,
) -> str | bool | None:
    event_config = (
        (config.get("characters") or {})
        .get(character_id, {})
        .get(transition_type, {})
    )
    if transition_type == "outro":
        return bool(event_config.get("enabled", False))
    mode = str(event_config.get("mode", "disabled"))
    return mode if mode in VALID_TRANSITION_MODES else "disabled"


def set_character_transition_mode(
    config: dict[str, Any],
    character_id: str,
    transition_type: str,
    mode: str,
) -> None:
    _validate_mode(mode)
    character_config = config.setdefault("characters", {}).setdefault(character_id, {})
    transition_config = character_config.setdefault(transition_type, {})
    transition_config["mode"] = mode
    transition_config["mode_override"] = True
    if transition_type != "outro":
        transition_config["enabled"] = mode == "enabled"


def transition_mode_summary(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "aemeath": {
            "intro_qte": get_character_transition_mode(config, "aemeath", "intro_qte"),
        },
        "mornye": {
            "intro_qte": get_character_transition_mode(config, "mornye", "intro_qte"),
            "outro": get_character_transition_mode(config, "mornye", "outro"),
        },
    }


def transition_event_counts(timeline_rows: list[Any]) -> dict[str, int]:
    counts = {
        "transition_events_applied_count": 0,
        "qte_events_applied_count": 0,
        "intro_events_applied_count": 0,
        "outro_events_applied_count": 0,
        "fallback_swap_count": 0,
        "placeholder_swap_count": 0,
    }
    for row in timeline_rows:
        get = row.get if isinstance(row, dict) else lambda key, default=None: getattr(row, key, default)
        if get("fallback_swap_used", False):
            counts["fallback_swap_count"] += 1
        if get("swap_timing_is_placeholder", False):
            counts["placeholder_swap_count"] += 1
        for event in get("transition_events", []) or []:
            if not event.get("applied", False):
                continue
            counts["transition_events_applied_count"] += 1
            event_type = str(event.get("event_type", ""))
            trigger = str(event.get("trigger_classification", ""))
            if "qte" in trigger:
                counts["qte_events_applied_count"] += 1
            if "intro" in event_type or trigger == "intro":
                counts["intro_events_applied_count"] += 1
            if "outro" in event_type:
                counts["outro_events_applied_count"] += 1
    return counts


def _deep_update(target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = deepcopy(value)
    return target


def _validate_mode(mode: str) -> None:
    if mode not in VALID_TRANSITION_MODES:
        raise ValueError(f"Unsupported transition mode {mode!r}; expected one of {sorted(VALID_TRANSITION_MODES)}.")
