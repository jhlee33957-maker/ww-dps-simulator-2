# Lynae Source Audit

Workbook: `data\source\鸣潮动作数据汇总.xlsx`
Source name: 琳奈

## Key Findings
- `lynae_spectral_analysis`: 震谐响应 (workbook_confirmed), source dmg!2489
- `lynae_spectral_analysis_c2`: C2震谐响应 (disabled_by_default_constellation), source dmg!2490
- `static_mist`: Static Mist (user_supplied_tooltip), source user supplied weapon tooltip; weapon!65 reviewed for Lynae weapon candidate
- `lynae_user_real_01`: User real profile stats (user_profile), source user supplied stat panel
- `lynae_complex_movement_states`: Lumiflow / skating / hold movement branches (metadata_only), source 角色-女!2577:2738
- `lynae_spray_paint_scheduled_flux_application`: Spray Paint Photocromic Flux field checks (implemented_scheduled_status_application_single_target), source 角色-女!2683:2684

## Spectral Analysis
- dmg!2489 multiplier: 18.8075
- dmg!2490 C2 multiplier: 31.9727 (disabled by default)

## Scope Notes
- Static Mist, Pact of Neonlight Leap, Hyvatia, Liberation, and Outro buff values are user-supplied tooltip sources.
- Tune Strain stack limit and per-stack damage are implemented for the current single-target Endgame Matrix model only; no multi-target behavior is claimed.
- Complex Lumiflow movement recovery, skating movement speed, stamina, and air/ground branch exactness remain metadata-only/review-required in v1.
