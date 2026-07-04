# Mornye Source vs Current Code Diff

| Current action | Verdict | Impact | Recommendation | Notes |
| --- | --- | --- | --- | --- |
| `mornye_basic_stage_1` | mismatch | medium | needs_human_review | action_time differs from source display action-end frame / 60 |
| `mornye_basic_stage_2` | mismatch | medium | needs_human_review | action_time differs from source display action-end frame / 60 |
| `mornye_basic_stage_3` | mismatch | high | needs_human_review | damage coefficients differ |
| `mornye_basic_stage_4` | mismatch | high | needs_human_review | damage coefficients differ |
| `mornye_wfo_basic_stage_1` | mismatch | high | needs_human_review | damage coefficients differ |
| `mornye_wfo_basic_stage_2` | mismatch | high | needs_human_review | damage coefficients differ |
| `mornye_wfo_basic_stage_3` | mismatch | high | needs_human_review | damage coefficients differ |
| `mornye_heavy_attack_normal` | mismatch | medium | needs_human_review | action_time differs from source display action-end frame / 60 |
| `mornye_heavy_geopotential_shift` | mismatch | medium | needs_human_review | action_time differs from source display action-end frame / 60 |
| `mornye_heavy_inversion` | match | low | needs_human_review | Current optional Interfered Marker amp is simplified_on_inversion; source says Interfered Marker needs Observation Marker + 偏移状态 + 谐度破坏伤害. |
| `mornye_skill_optimal_solution` | mismatch | high | needs_human_review | damage coefficients differ |
| `mornye_skill_distributed_array` | mismatch | medium | needs_human_review | action_time differs from source display action-end frame / 60 |
| `mornye_liberation_critical_protocol` | mismatch | medium | needs_human_review | action_time differs from source display action-end frame / 60 |
| `mornye_syntony_field_damage` | code_simplification | medium | leave_as_simplified | damage coefficients differ; automatic Syntony Field scheduling is not implemented |
| `mornye_intro_convergence` | mismatch | medium | needs_human_review | action_time differs from source display action-end frame / 60; Source has QTE row 协奏回收=10 and passive text saying QTE/观测A3 grants 20 Concerto; mark source conflict before patching. |
| `mornye_outro_recursion` | match | low | no_change |  |
| `Syntony Field / 谐振场` | code_simplification | high | needs_human_review | Syntony Field exists in current state as metadata but not as full source mechanics. |
| `High Syntony Field / 强谐振场` | code_simplification | medium | needs_human_review | High Syntony Field details are not fully modeled. |
| `谐度破坏` | missing_in_code | high | needs_human_review | Required for source Interfered Marker condition. |
| `震谐响应` | missing_in_code | high | needs_human_review | Resource/marker effects are unresolved in this audit. |
