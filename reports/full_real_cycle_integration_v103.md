# Full Real-Cycle Integration Candidate 104

This is a deterministic integration route through the verified active-Echo mechanics. It is not the 120-second manual baseline and is not claimed globally optimal.

- Baseline source: ww-dps-simulator-2(103).zip / label 103
- Candidate status: pending external review
- Final combat time: 32.949999999999996s / 1977F
- Total damage: 1792244.9381157316
- Route-duration DPS: 54392.86610366409
- Damage by character: {"aemeath": 1404246.4250625486, "lynae": 319145.0773344416, "mornye": 68853.43571874128}
- Placeholder/fallback swaps: 1 at [{"step": 6, "selected_action_id": "swap_to_mornye", "resolved_action_id": "swap_to_mornye", "fallback_swap_used": true, "swap_timing_is_placeholder": true, "transition_type": "normal_swap"}]

The opening Aemeath -> Mornye normal swap uses the known generic 0.50-second placeholder. Mornye -> Lynae and Lynae -> Aemeath use real enabled transition actions.

## Major Checkpoints

- Aemeath opening Off-Tune after action 5: 263.25
- Mornye Off-Tune after action 18: 1926.27
- Mornye Concerto after action 18: 100.0
- Tune Break Rupturous Trail stacks after action 31: 30
- First Seraphic Trail preserved: True
- Second Seraphic Trail consumed: True
- Final Interfered Marker remaining: 0.11666666666666603

## Remaining Unresolved Limits

- Opening Aemeath -> Mornye normal-swap exact timing is unresolved; current route uses the known 0.50s placeholder.
- Mornye exact dodge-cancel next-input frame remains unresolved; Reactor Husk uses the verified uncancelled 66F route.
- Mornye/Aemeath/Lynae active Echo Off-Tune values are source-unconfirmed and remain runtime zero where unresolved.
