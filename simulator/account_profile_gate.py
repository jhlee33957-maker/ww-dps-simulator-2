from __future__ import annotations

from typing import Any

from simulator.account_constellation_effects import (
    ACCOUNT_SCOPE_ID,
    AccountScopeValidationError,
    validate_account_single_boss_scope,
)


CHARACTER_DISPLAY_NAMES = {
    "aemeath": "Aemeath",
    "lynae": "Lynae",
    "mornye": "Mornye",
}


class AccountProfileSimulationBlocked(RuntimeError):
    """Raised when a stored account profile is used for combat execution."""


_MISSING = object()
ACCOUNT_CONSTELLATION_READY_MESSAGE = (
    "Constellation mechanics implemented for single boss. Account party and baseline are not configured. "
    "Kill, wave, and survival effects are unsupported."
)


def validate_profile_simulation_readiness(
    profile: Any,
    character_contracts: dict[str, Any] | None = None,
    *,
    account_scope: Any = None,
    precombat_elapsed_seconds: Any = _MISSING,
) -> None:
    del character_contracts
    get = profile.get if isinstance(profile, dict) else lambda key, default=None: getattr(profile, key, default)
    if not bool(get("account_profile", False)):
        return
    constellation = get("constellation", {}) or {}
    mechanics_implemented = bool(isinstance(constellation, dict) and constellation.get("mechanics_implemented", False))
    if mechanics_implemented:
        _validate_account_mechanics_runtime_requirements(
            profile,
            account_scope=account_scope,
            precombat_elapsed_seconds=precombat_elapsed_seconds,
        )
        return

    character_id = str(get("id", get("character_id", "unknown")))
    profile_id = str(get("build_profile_id", get("profile_id", "unknown_profile")))
    sequence = get("sequence", None)
    if sequence is None and isinstance(constellation, dict):
        sequence = constellation.get("sequence")
    sequence = int(sequence or 0)
    display_name = CHARACTER_DISPLAY_NAMES.get(character_id, character_id)
    required_range = f"S1-S{sequence}" if sequence > 0 else "constellation"
    reason = str(get("simulation_block_reason", "pending_constellation_mechanics"))
    message = (
        f"{profile_id} cannot be simulated: "
        f"{display_name} Sequence {sequence} account profile requires validated {required_range} mechanics. "
        f"Missing constellation-mechanics contract ({reason})."
    )
    raise AccountProfileSimulationBlocked(message)


def _validate_account_mechanics_runtime_requirements(
    profile: Any,
    *,
    account_scope: Any,
    precombat_elapsed_seconds: Any,
) -> None:
    get = profile.get if isinstance(profile, dict) else lambda key, default=None: getattr(profile, key, default)
    character_id = str(get("id", get("character_id", "unknown")))
    profile_id = str(get("build_profile_id", get("profile_id", "unknown_profile")))
    sequence = int(get("sequence", 0) or ((get("constellation", {}) or {}).get("sequence", 0) if isinstance(get("constellation", {}), dict) else 0))
    display_name = CHARACTER_DISPLAY_NAMES.get(character_id, character_id)
    try:
        validate_account_single_boss_scope(account_scope)
    except AccountScopeValidationError as exc:
        raise AccountProfileSimulationBlocked(
            f"{profile_id} cannot be simulated: {display_name} Sequence {sequence} account profile requires "
            f"explicit account scope {ACCOUNT_SCOPE_ID!r}; {exc}. {ACCOUNT_CONSTELLATION_READY_MESSAGE}"
        ) from exc
    if precombat_elapsed_seconds is _MISSING or precombat_elapsed_seconds is None:
        raise AccountProfileSimulationBlocked(
            f"{profile_id} cannot be simulated: {display_name} Sequence {sequence} account profile requires "
            f"explicit precombat_elapsed_seconds; use 0 for no precombat elapsed time. "
            f"{ACCOUNT_CONSTELLATION_READY_MESSAGE}"
        )


def blocked_account_profile_messages(
    characters: dict[str, Any],
    *,
    account_scope: Any = None,
    precombat_elapsed_seconds: Any = _MISSING,
) -> list[str]:
    messages: list[str] = []
    for character in characters.values():
        try:
            validate_profile_simulation_readiness(
                character,
                account_scope=account_scope,
                precombat_elapsed_seconds=precombat_elapsed_seconds,
            )
        except AccountProfileSimulationBlocked as exc:
            messages.append(str(exc))
    return messages


def validate_simulation_readiness_for_characters(
    characters: dict[str, Any],
    *,
    entry_point: str = "simulator execution",
    account_scope: Any = None,
    precombat_elapsed_seconds: Any = _MISSING,
) -> None:
    messages = blocked_account_profile_messages(
        characters,
        account_scope=account_scope,
        precombat_elapsed_seconds=precombat_elapsed_seconds,
    )
    if not messages:
        return
    raise AccountProfileSimulationBlocked(f"{entry_point} rejected:\n" + "\n".join(messages))
