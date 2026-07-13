# Beam Search v111 30-second calibration result

Candidate 112 ingests the completed candidate-111 calibration. This is a result-integrity and readiness record, not a new search execution or an external-verification claim.

## Completion

- Plan: `data/beam_search_plan_v111.json` (`b504def4e0c1da82ef2a6024d19ccac76fe175df51899e50d12f3bff99a17998`)
- Stage/status: `calibration_30s` / `completed_search` / `completed_search`
- Budget/actual expansions: 500,000 / 381,918
- Elapsed/throughput: 923.3255433000159 s / 413.6330926522451 expansions/s
- Completed buckets/routes: 60 / 128 retained (12,906 observed before retention)
- Pending buckets/destination accumulators: 0 / 0
- Deduplicated/pruned/zero-time expansions: 17,452 / 287,717 / 4,605
- Peak live nodes/payload/tracked memory: 4,234 / 29,382 bytes / 253,071,736 bytes
- Checkpoints/frontier writes/accumulator finalizations: 5 / 17 / 18

## Best completed 30-second route

- Route `a301f753b3ddf6e4` (completion order 6908)
- Damage/DPS: 1369674.294344379101 / 45655.8098114793029
- Combat/current time: 30.0 / 54.949999999999974
- Selected/resolved actions: 45 / 45
- Selected hash: `a301f753b3ddf6e47acc5aa4b3325ac2465f36db102974fc72bcedb64af82011`
- Resolved hash: `d476c49e7aeba150d11fee9b23ccbc9047f5a4f8c8a5c462f6f9265423702fd5`

## Replay and attribution parity

The terminal node and deterministic party-preset replay agree on route identity, damage, time, action counts, and sequence hashes. Character attribution is Aemeath 1114883.4157092454843, Lynae 211375.7841332593816, and Mornye 43415.09450187385664; scheduled damage is 56004.767902583254909 and generated mechanic damage is 123343.33773087071313. Character-sum delta is -4.66e-10; effective role-breakdown delta is 0.0.

## Horizon warning

`reference_damage_comparison_status = horizon_mismatch_not_comparable`. The 30-second calibration is **not numerically comparable** to the verified 120-second BC total, declares no project winner, and does not prove a global optimum.

## Immutable hashes

- Action data: `d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1`
- Party configuration: `bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11`
- Manual route: `c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a`
- BC NPZ: `b020a1b9309b46bd87eb3fff4837aead53035c4c84620962f47feb9fc11846ff`
- BC model: `7b5ef151b7ac9299a8134032e58f1d75919832a3823c8715653852393045461e`
- Prior PPO model: `9b62faa610c3710bf4e17603a92baf8e8c657b51e8fba22d8525a1e33a257513`
- Direct-action manifest: `ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d`
