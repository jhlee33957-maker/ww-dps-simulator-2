from __future__ import annotations

from final_archive_guarded_ppo_lightweight_suite import PURE_CHECKS
from final_archive_suite_utils import assert_helper_level_scripts


def main() -> None:
    assert "guarded_ppo_stage_timeout_smoke_test.py" not in PURE_CHECKS
    assert "guarded_ppo_dry_run_step0_alias_smoke_test.py" in PURE_CHECKS
    assert "guarded_ppo_state_integrity_repeatability_smoke_test.py" in PURE_CHECKS
    assert_helper_level_scripts(PURE_CHECKS)
    print("final_archive_guarded_ppo_lightweight_contract_smoke_test ok")


if __name__ == "__main__":
    main()
