# MCTS v118 3x50k production result (candidate 119)

Candidate 119 ingests the three independently completed production seeds. It is pending external review.

## Ranking

1. seed 118003 — `d3dcc3f4b372ac5d`, 4,647,724.703247974 damage (38,731.039193733115 DPS)
2. seed 118002 — `33330b882697c345`, 4,456,165.094682989 damage (37,134.70912235824 DPS)
3. seed 118001 — `4d32f291ea1bbe80`, 3,957,306.530795142 damage (32,977.55442329285 DPS)

All winners replayed through the normal diagnostic simulator with exact selected/resolved hashes, exact damage, and 120.0 seconds of combat time. All 384 retained routes were completed 120-second routes.

## Aggregate

- 150,000 simulations and completed rollouts; 0 invalid rollouts; 150,003 nodes
- Mean damage: 4353732.109575368
- Median damage: 4456165.094682989
- Population standard deviation: 291019.70213007974
- Range: 690418.1724528316
- Runtime: 22403.5677768 seconds
- Total action executions: 26652751
- Combined throughput: 1189.6654704970804 actions/s
- Highest observed RSS: 118767616 bytes

## Plateaus and comparison

- seed 118001: best at simulation 30,820; 19,180 simulations without improvement
- seed 118002: best at simulation 38,749; 11,251 simulations without improvement
- seed 118003: best at simulation 11,285; 38,715 simulations without improvement
- Best MCTS versus Beam: -1004167.5713050179 damage (-17.76692694278993%)
- Best MCTS versus guarded PPO 90k: -629119.6554440707 damage (-11.92227044574058%)

The completed Beam route remains the overall project winner and guarded PPO 90k remains the best trained model. No 100k/200k MCTS extension is recommended: every seed had a long post-best plateau and the best seed still trails Beam by more than one million damage. This is stopping evidence, not proof that more MCTS could never improve. No global optimum is claimed.
