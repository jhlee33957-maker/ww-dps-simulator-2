# Mornye Resource Flow Audit

## rest_mass_core
- Verdict: `source_confirmed`
- Answer: Current rest_mass_energy corresponds to 静质量能 / core-like special energy. Source text states 静质量能=相对动能，上限100点; baseline rows use 核心回收1 for gains.
## relative_momentum
- Verdict: `source_partial`
- Answer: Current relative_momentum likely corresponds to 相对动能 during 观测状态. Source text states 静质量能=相对动能, and WFO rows place values under 核心回收1. The workbook does not rename the column, so this remains source_partial.
## concerto
- Verdict: `source_conflict_for_qte`
- Answer: Distributed Array setup row proves 协奏回收=10. Passive text proves QTE/观测A3 grants 20 Concerto, but QTE row itself has 协奏回收=10. Do not patch QTE Concerto until reviewed.
## resonance_energy
- Verdict: `source_confirmed_for_row_gains_cost_requires_current_code_review`
- Answer: Frame/skill rows expose 大招回收 values; current simulator separately scales Resonance Energy gain by Energy Regen. Liberation cost 175 is current code behavior and should be checked against workbook/resource system before changing.
## distributed_array
- Verdict: `source_partial`
- Answer: E2-分布式阵列 has 协奏回收=10. E2-1..E2-4 each have 核心回收1=15. Current implementation Distributed Array = concerto +10 and relative_momentum +60 is partially source-backed, but the repeated 15 values are not literally labeled Relative Momentum.
## qte_intro
- Verdict: `source_conflict`
- Answer: QTE enters observation state and clears core. Concerto amount conflicts between QTE row 10 and passive text 20.
## wfo
- Verdict: `source_confirmed`
- Answer: WFO/观测状态 is entered by 强化重击 and QTE for 30 seconds. Source text says it clears special energy when it naturally ends and is removed by listed movement/background conditions.
## inversion
- Verdict: `source_confirmed_marker_only`
- Answer: 观测重击 consumes special energy on its time-stop row and applies 30s 观测标记 on hit. It is not source-proven to directly apply 干涉标记.
