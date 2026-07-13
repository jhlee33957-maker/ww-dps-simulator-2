from __future__ import annotations

from mornye_high_syntony_field_runtime_buff_smoke_test import (
    test_data_buff_definition,
    test_field_creation_only_heal_proxy,
    test_high_def_does_not_add_atk_or_hp_and_expiry,
    test_high_syntony_runtime_support_and_damage_formula,
    test_requires_active_syntony_field,
)


def main() -> None:
    test_data_buff_definition()
    test_requires_active_syntony_field()
    test_high_syntony_runtime_support_and_damage_formula()
    test_high_def_does_not_add_atk_or_hp_and_expiry()
    test_field_creation_only_heal_proxy()


if __name__ == "__main__":
    main()
