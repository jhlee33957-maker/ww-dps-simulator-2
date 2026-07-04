# Mornye Source-backed Cycle Candidates

## A_current_simulator_route
- Description: Current implemented path to WFO / Inversion / Interfered / Outro.
- Actions: ['Basic A1', 'Basic A2', 'Basic A3', 'Heavy Geopotential Shift', 'WFO actions / Distributed Array until 100 Relative Momentum', 'Heavy Inversion', 'optional simplified Interfered Marker', 'Outro when Concerto full']
- Estimated combat time: around 20s in current route diagnostics
- Source confidence: `source_partial`
## B_source_backed_shortest_wfo
- Description: Shortest source-backed route to WFO using baseline core.
- Actions: ['A1 (+20 core)', 'A2 (+43 core)', 'A3 (+37 core)', '强化重击 (enter 30s 观测状态, clear core)']
- Estimated combat time: under 10s based on source action end frames
- Source confidence: `source_confirmed_for_core_and_wfo`
## C_source_backed_shortest_inversion_or_observation_marker
- Description: Shortest source-backed route to Observation Marker.
- Actions: ['Reach WFO', 'Generate enough special resource / 相对动能', '观测重击']
- Estimated combat time: not fully provable under 10s from source without resolving WFO resource interpretation and route constraints
- Source confidence: `source_partial`
## D_source_backed_shortest_interfered_marker
- Description: Shortest source-backed route to Interfered Marker.
- Actions: []
- Estimated combat time: not provable
- Source confidence: `source_unresolved`
- Unresolved: ['Requires 观测标记 + 偏移状态 + 谐度破坏伤害; current audit does not prove a complete deterministic route.']
## E_source_backed_shortest_outro
- Description: Shortest source-backed route to full Concerto / Outro.
- Actions: ['unresolved']
- Estimated combat time: not fully provable
- Source confidence: `source_conflict_for_qte_concerto`
- Unresolved: ['QTE row and passive text disagree on Concerto amount; full Concerto route needs reviewed source calculation.']
## Direct Answers
- excel_supports_under_10s_mornye_cycle: WFO entry under 10s appears source-backed. Full Interfered Marker or Outro cycle under 10s is not proven by this audit.
- why_current_route_takes_around_20s: Current route requires accumulating 100 Relative Momentum after WFO through implemented WFO gains and Distributed Array, and optional Interfered Marker is tied to Inversion. Conservative Expectation Error routing does not shortcut to Optimal Solution.
- current_20s_source_supported: source_partial for current implemented route; likely incomplete for full Mornye mechanics because Interfered Marker/Tune routes are unresolved.
- sub_10s_source_backed_route_found: Yes for WFO entry only; no for full Interfered Marker or Outro route.
