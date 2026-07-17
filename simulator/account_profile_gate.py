from __future__ import annotations

from typing import Any


CHARACTER_DISPLAY_NAMES = {
    "aemeath": "Aemeath",
    "lynae": "Lynae",
    "mornye": "Mornye",
}


class AccountProfileSimulationBlocked(RuntimeError):
    """Raised when a stored account profile is used for combat execution."""


def validate_profile_simulation_readiness(
    profile: Any,
    character_contracts: dict[str, Any] | None = None,
) -> None:
    del character_contracts
    get = profile.get if isinstance(profile, dict) else lambda key, default=None: getattr(profile, key, default)
    if not bool(get("account_profile", False)):
        return
    if bool(get("simulation_ready", False)):
        return

    character_id = str(get("id", get("character_id", "unknown")))
    profile_id = str(get("build_profile_id", get("profile_id", "unknown_profile")))
    constellation = get("constellation", {}) or {}
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


def blocked_account_profile_messages(characters: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    for character in characters.values():
        try:
            validate_profile_simulation_readiness(character)
        except AccountProfileSimulationBlocked as exc:
            messages.append(str(exc))
    return messages


def validate_simulation_readiness_for_characters(
    characters: dict[str, Any],
    *,
    entry_point: str = "simulator execution",
) -> None:
    messages = blocked_account_profile_messages(characters)
    if not messages:
        return
    raise AccountProfileSimulationBlocked(f"{entry_point} rejected:\n" + "\n".join(messages))
