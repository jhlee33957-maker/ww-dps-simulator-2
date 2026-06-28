from __future__ import annotations


def reward_from_damage(damage_this_action: float) -> float:
    return damage_this_action / 10000.0
