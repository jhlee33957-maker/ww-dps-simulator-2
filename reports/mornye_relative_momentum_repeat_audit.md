# Mornye Relative Momentum Repeat Audit

| Action | Relative Momentum delta | Source rows | Source status | Calculation |
| --- | ---: | --- | --- | --- |
| mornye_wfo_basic_stage_1 | 10 | [4128] | workbook_confirmed_repeat_aware | 2.5 x 4 |
| mornye_wfo_basic_stage_2 | 12 | [4129] | workbook_confirmed_repeat_aware | 3 x 4 |
| mornye_wfo_basic_stage_3 | 18 | [4132, 4133] | workbook_confirmed | 9 + 9 |
| mornye_skill_distributed_array | 60 | [4144, 4145, 4146, 4147] | workbook_confirmed | 15 x 4 |
| mornye_heavy_inversion | -100 | [4135, 4136] | not_source_confirmed_direct_interfered | consume 100 |

## Route Implication

Distributed Array + WFO A1 + WFO A2 + WFO A3 now reaches 100 Relative Momentum: 60 + 10 + 12 + 18.
Heavy Inversion still consumes 100 Relative Momentum and applies Observation Marker.
