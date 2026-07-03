# Aemeath Timing Review

## Summary

- Workbook path: `data\\source\\\u9e23\u6f6e\u52a8\u4f5c\u6570\u636e\u6c47\u603b.xlsx`
- Candidate rows scanned: 229
- Timing candidates created: 8
- High confidence: 2
- Medium confidence: 5
- Low confidence: 1
- safe_to_patch count: 2
- Unresolved count: 112
- Heavy candidates count: 4
- Form Switch candidates count: 2
- Sync Strike candidates count: 2
- Excluded QTE rows count: 9

This report is review-only and does not modify `data/actions.json`.

## Heavy Attack Timing Candidates

| action_id | character | source rows | charge rows included | attack rows included | action_time_seconds | combat_time_cost_seconds | max_hit_time | current action_time | confidence | safe_to_patch | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aemeath_heavy_aemeath_charged_1 | aemeath | ["2761:重击-1"] | False | True | 1.8333 | 1.8333 | 0.0333 | 1.8333 | medium | False | ["Heavy candidate lacks explicit charge/preparation rows."] |
| aemeath_heavy_aemeath_charged_2 | aemeath | ["2762:重击-2", "2763:强化重击-前置", "2765:强化重击-1", "2766:强化重击-2", "2767:强化重击-3"] | True | True | 1.8333 | 1.8333 | 0.5667 | 3.6667 | medium | False | ["Heavy candidate includes charge and release rows; sum-vs-max frame interpretation requires manual review."] |
| aemeath_heavy_mech_charged_1 | aemeath_mech | ["2904:重击"] | False | True | 1.0333 | 1.0333 | 0.0167 | 1.0333 | medium | False | ["Heavy candidate lacks explicit charge/preparation rows."] |
| aemeath_heavy_mech_charged_2 | aemeath_mech | ["2905:强化重击-前置", "2907:强化重击"] | True | True | 1.0333 | 1.0333 | 0.0167 | 2.0667 | medium | False | ["Heavy candidate includes charge and release rows; sum-vs-max frame interpretation requires manual review."] |

## Form Switch Timing Candidates

| action_id | character | source rows | charge rows included | attack rows included | action_time_seconds | combat_time_cost_seconds | max_hit_time | current action_time | confidence | safe_to_patch | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aemeath_form_switch_to_aemeath_normal | aemeath_mech | ["2913:E1-常规切换爱弥斯"] | False | True |  |  |  | 0.45 | low | False | ["Normal Form Switch row has no derivation/end/action timing field."] |
| aemeath_form_switch_to_mech_normal | aemeath | ["2770:E1-常规切换机兵"] | False | True | 1.0 | 1.0 |  | 0.55 | medium | False | ["Used explicit state conversion time because no derivation/end frame was present."] |

## Sync Strike Timing Candidates

| action_id | character | source rows | charge rows included | attack rows included | action_time_seconds | combat_time_cost_seconds | max_hit_time | current action_time | confidence | safe_to_patch | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aemeath_sync_strike_armament_merge | aemeath | ["2772:E2-合击", "2773:E2-1", "2774:E2-2", "2775:E2-3"] | False | True | 1.1667 | 1.1667 | 1.0 | 1.1667 | high | True |  |
| aemeath_sync_strike_call_of_dawn | aemeath_mech | ["2916:E2-合击", "2917:E2-1", "2918:E2-2", "2919:E2-3", "2920:E2-4"] | False | True | 0.9667 | 0.9667 | 0.9333 | 0.9667 | high | True |  |

## Unresolved / Excluded Rows

- ambiguous_group_context: 29
- basic_attack_out_of_scope: 21
- dodge_counter_out_of_scope: 15
- instant_response_or_sequence_review_only: 2
- qte_intro_excluded: 9
- resonance_liberation_already_handled: 10
- seraphic_duet_already_handled: 26

## Critical Warnings

- `aemeath_heavy_aemeath_charged_1`: heavy_candidate_without_charge_rows
- `aemeath_heavy_aemeath_charged_2`: ambiguous_frame_coordinate_interpretation
- `aemeath_heavy_mech_charged_1`: heavy_candidate_without_charge_rows
- `aemeath_heavy_mech_charged_2`: ambiguous_frame_coordinate_interpretation

## Patch recommendation

- `aemeath_sync_strike_armament_merge`: action_time=1.1667s, combat_time_cost=1.1667s
- `aemeath_sync_strike_call_of_dawn`: action_time=0.9667s, combat_time_cost=0.9667s

This report does not modify `data/actions.json`.
A future whitelist patch should apply only manually reviewed values.
