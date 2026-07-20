from stage2c_timing_test_support import ARRAY_ID, ready_account_array_sim


def main() -> None:
    sim = ready_account_array_sim(); assert sim.execute_action(ARRAY_ID)
    result = sim.last_action_result
    assert sim.state.concerto_energy["mornye"] == 51.0
    s3 = [e for e in result.account_constellation_events if e.get("event_type") == "mornye_s3_distributed_array"]
    weapon = [e for e in result.weapon_effect_logs if e.get("weapon_effect_id") == "resonance_skill_concerto_restore"]
    assert len(s3) == len(weapon) == 1 and weapon[0]["concerto_energy_restored_by_weapon"] == 16.0
    assert s3[0]["concerto_gain"] == 25.0 and s3[0]["icd_seconds"] == 25.0 and weapon[0]["weapon_effect_cooldown_seconds"] == 20.0
    assert result.direct_action_damage == 0 and result.scheduled_damage > 0
    print("mornye_distributed_array_cast_trigger_independence_v124_smoke_test ok packets=10 starfield=16 s3=25 total=51")


if __name__ == "__main__": main()
