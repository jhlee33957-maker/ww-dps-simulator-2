from __future__ import annotations


def calculate_reward(damage_this_action: float) -> float:
    return damage_this_action / 10000.0


def reward_from_damage(damage_this_action: float) -> float:
    return calculate_reward(damage_this_action)
