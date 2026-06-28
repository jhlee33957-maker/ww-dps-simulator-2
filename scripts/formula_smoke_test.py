from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.damage_formula import (
    calculate_anomaly_damage,
    calculate_havoc_bane_def_reduction,
    calculate_normal_damage,
    calculate_tune_break_damage,
)


def main() -> None:
    common = {
        "enemy_res": 0.1,
        "res_pen": 0.0,
        "attacker_level": 90,
        "enemy_level": 90,
        "def_ignore": 0.0,
        "def_reduction": 0.0,
    }
    normal = calculate_normal_damage(
        skill_multiplier=3.2,
        character_base_atk=880.0,
        weapon_base_atk=588.0,
        atk_percent=0.52,
        flat_atk=320.0,
        dmg_bonus=0.42,
        crit_rate=0.7,
        crit_damage=2.5,
        boost=0.08,
        dmg_taken=0.0,
        final_dmg_bonus=0.0,
        **common,
    )
    tune_break = calculate_tune_break_damage(
        tune_break_multiplier=0.45,
        tune_break_boost_points=20.0,
        tune_dmg_bonus=0.0,
        **common,
    )
    print(f"Normal damage sample: {normal:.2f}")
    print(f"Tune break damage sample: {tune_break:.2f}")
    for anomaly_type, stacks in [
        ("aero_erosion", 3),
        ("spectro_frazzle", 2),
        ("electro_flare", 12),
    ]:
        damage = calculate_anomaly_damage(anomaly_type=anomaly_type, stacks=stacks, **common)
        print(f"{anomaly_type} sample: {damage:.2f}")
    print(f"havoc_bane def reduction at 5 stacks: {calculate_havoc_bane_def_reduction(5):.2f}")


if __name__ == "__main__":
    main()
