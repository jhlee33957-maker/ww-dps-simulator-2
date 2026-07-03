# Aemeath QTE Action Candidate Review

## A. Summary

- Raw source rows: 24
- Action candidates: 1
- Executable candidates: 0
- simulation applied: false
- review only: true
- simulation executable: false

## B. Action Candidate Table

| candidate_id | proposed_action_id | character | action_time | combat_time_cost | hit count | parsed multipliers | skill category | damage type | previous Outro trigger frame | implementation status | safe_to_implement_later |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aemeath_qte_intro | aemeath_qte_intro | aemeath | `None` | `None` | `5` | `[0.1346, 0.1346, 1.0766, 0.653, 0.9795]` | `变奏` | `变奏伤害` | `[40.0, 48.0]` | action_ready_review_candidate | false |

## C. Candidate Details

### aemeath_qte_intro

- Executable rows used: `[('QTE', 2789), ('QTE-1', 2790), ('QTE-2', 2791), ('QTE-3', 2792), ('QTE', 2934), ('QTE-1', 2935), ('QTE-2', 2936), ('QTE-1', 2726), ('QTE-2', 2727), ('QTE-3', 2728), ('QTE-1', 2781), ('QTE-2', 2782)]`
- Metadata rows used: `[('E1-QTE切换机兵', 2771), ('QTE', 2789), ('特殊能量', 2806), ('E1-QTE切换爱弥斯', 2915), ('QTE', 2934), ('E1-QTE切换机兵', 2712), ('E1-QTE切换爱弥斯', 2764)]`
- Excluded rows: `[('E2-合击', 2772, 'qte_followup_form_switch_note'), ('强化E-降临', 2776, 'seraphic_duet_notice'), ('大招1-前置', 2793, 'overdrive_notice'), ('大招2-前置', 2798, 'finale_notice'), ('谐度破坏-时停', 2802, 'tune_break_notice'), ('强化E-登台', 2921, 'seraphic_duet_notice'), ('谐度破坏-时停', 2937, 'tune_break_notice')]`
- Timing candidate: `{'action_time_frames': None, 'action_time_seconds': None, 'action_time_frame_candidates': [60.0, 72.0], 'combat_time_cost_frames': None, 'combat_time_cost_seconds': None, 'confirmed_time_stop_frame_candidates': [46.0, 50.0], 'hit_frames': [52.0, 54.0, 56.0, 42.0, 60.0], 'hit_times_seconds': [0.8667, 0.9, 0.9333, 0.7, 1.0], 'previous_outro_trigger_frame': None, 'previous_outro_trigger_frames': [40.0, 48.0], 'confidence': 'low', 'warnings': ['Multiple parent QTE action-time candidates found; selected action_time left unresolved.', 'Previous-character Outro trigger frame is ambiguous or unresolved.', 'Confirmed time-stop metadata exists; combat_time_cost requires manual review.']}`
- Damage candidate: `{'skill_category': '变奏', 'damage_type': '变奏伤害', 'raw_coefficients': [0.1346, 0.1346, 1.0766, 0.653, 0.9795], 'parsed_multipliers': [0.1346, 0.1346, 1.0766, 0.653, 0.9795], 'hit_count': 5, 'confidence': 'high', 'warnings': []}`
- Notice metadata: `{'previous_character_outro_trigger_frame': None, 'previous_outro_trigger_frames': [40.0, 48.0], 'previous_character_outro_trigger_source': ['13 | QTE | 无敌期间不能切人\n第48F触发上一角色延奏\n第1F获得流光增幅状态，持续15秒\n流光增幅状态期间施放大招1，可额外获得1点共鸣率 | 1 | 60 | 10 | 40 | 0.3164 | 11 | 地面 | 时停 | 0 | 1 | 50 | 0 | 1 | 50', '13 | QTE | 无敌期间不能切人，第40F触发上一角色延奏\n第1F获得流光增幅状态，持续15秒\n流光增幅状态期间施放大招1，可额外获得1点共鸣率 | 1 | 72 | 10 | 40 | 0.3164 | 11 | 地面 | 时停 | 0 | 1 | 46 | 0 | 1 | 46'], 'cannot_switch_during_invulnerable': True, 'cannot_switch_source': ['13 | QTE | 无敌期间不能切人\n第48F触发上一角色延奏\n第1F获得流光增幅状态，持续15秒\n流光增幅状态期间施放大招1，可额外获得1点共鸣率 | 1 | 60 | 10 | 40 | 0.3164 | 11 | 地面 | 时停 | 0 | 1 | 50 | 0 | 1 | 50', '13 | QTE | 无敌期间不能切人，第40F触发上一角色延奏\n第1F获得流光增幅状态，持续15秒\n流光增幅状态期间施放大招1，可额外获得1点共鸣率 | 1 | 72 | 10 | 40 | 0.3164 | 11 | 地面 | 时停 | 0 | 1 | 46 | 0 | 1 | 46'], 'state_grants': [{'state_name_raw': '流光增幅', 'start_frame': 1.0, 'duration_seconds': 15.0, 'source_text': '第1F获得流光增幅状态，持续15秒'}], 'qte_followup_form_switch_notes': [{'sheet': '角色-女', 'sheet_role': 'frame_sheet', 'row_number': 2771, 'character': 'aemeath', 'category': 'intro_candidate', 'source_action_name': 'E1-QTE切换机兵', 'raw_row_text': '10* | E1-QTE切换机兵 | 切换形态共享冷却1秒，立即施放机兵A3 | 0.75 | 2 | 地转漂浮 | 1'}, {'sheet': '角色-女', 'sheet_role': 'frame_sheet', 'row_number': 2915, 'character': 'aemeath_mech', 'category': 'intro_candidate', 'source_action_name': 'E1-QTE切换爱弥斯', 'raw_row_text': '10* | E1-QTE切换爱弥斯 | 切换形态共享冷却1秒，立即施放爱弥斯A3 | 0.75 | 2 | 地面'}, {'sheet': '角色技能类型', 'sheet_role': 'skill_type_sheet', 'row_number': 2712, 'character': 'aemeath', 'category': 'intro_candidate', 'source_action_name': 'E1-QTE切换机兵', 'raw_row_text': 'E1-QTE切换机兵 | - | - | 共鸣技能 | -'}, {'sheet': '角色技能类型', 'sheet_role': 'skill_type_sheet', 'row_number': 2764, 'character': 'aemeath_mech', 'category': 'intro_candidate', 'source_action_name': 'E1-QTE切换爱弥斯', 'raw_row_text': 'E1-QTE切换爱弥斯 | - | - | 共鸣技能 | -'}], 'raw_notice_text': ['13 | QTE | 无敌期间不能切人\n第48F触发上一角色延奏\n第1F获得流光增幅状态，持续15秒\n流光增幅状态期间施放大招1，可额外获得1点共鸣率 | 1 | 60 | 10 | 40 | 0.3164 | 11 | 地面 | 时停 | 0 | 1 | 50 | 0 | 1 | 50', '13 | QTE | 无敌期间不能切人，第40F触发上一角色延奏\n第1F获得流光增幅状态，持续15秒\n流光增幅状态期间施放大招1，可额外获得1点共鸣率 | 1 | 72 | 10 | 40 | 0.3164 | 11 | 地面 | 时停 | 0 | 1 | 46 | 0 | 1 | 46', '10* | E1-QTE切换机兵 | 切换形态共享冷却1秒，立即施放机兵A3 | 0.75 | 2 | 地转漂浮 | 1', '17 | 特殊能量 | 同步率：\n·上限200点\n·A、空中攻击、E2命中时获取；\n·施放QTE、大招1后，分别获取40、30点同步率；\n·施放强化E时，减少100点同步率；\n·施放大招2后清空同步率。\n\n共鸣率：\n·上限4点\n·施放强化E、大招1后，分别获得1点共鸣率；\n·施放大招2后清空共鸣率。\n\n流光增幅状态：\n·施放QTE后获得，持续15秒，触发获得刷新持续时间；\n·状态期间施放大招1后，移除状态，额外获得1点共鸣率。\n\n强化E解锁前置：\n·施放A4获得，持续5秒，触发获得刷新持续时间；\n·【前置】持续期间，同步率>=100点时解锁强化E；\n·施放强化E后移除。\n\n强化E增幅次数：\n·施放大招1后获得2层，持续30秒，触发获得刷新持续时间；\n·施放强化E时消耗1层，使 强化E-震谐 替换为 强化E-震谐增幅、强化E-聚爆 替换为 强化E-聚爆增幅。\n\n轨迹无消耗状态：\n·施放大招1后获得，持续30秒，触发获得刷新持续时间；\n·状态期间，施放强化E不会移除目标持有的震谐轨迹/聚爆轨迹\n·施放强化E后，移除该状态。\n\n大招2解锁前置：\n·施放大招1后获得，持续60秒，触发获得刷新持续时间；\n·速蓄状态期间，施放强化重击后获得200点同步率；\n·【前置】持续期间，同步率和共鸣率达到上限时解锁大招2；\n·施放大招2后移除。\n\n速蓄状态：\n·【大招2解锁前置】持续期间，共鸣率达到上限时获得；\n·状态期间，蓄力达到一段派生帧后自动施放强化重击；\n·施放强化重击、施放大招2、【前置】持续结束后移除该状态。\n\nC1速蓄状态：\n·解锁C1后，在非战斗状态下不处于重击/强化重击/大招2动作中超过4秒时获得；\n·获得后覆盖常规速蓄状态，且不会因【前置】结束而移除；\n·状态期间，蓄力达到一段派生帧后自动施放强化重击；\n·状态期间未持有【前置】时，施放强化重击后获得100点同步率\n·施放强化重击、施放大招2后，移除该状态。', '10* | E1-QTE切换爱弥斯 | 切换形态共享冷却1秒，立即施放爱弥斯A3 | 0.75 | 2 | 地面', 'E1-QTE切换机兵 | - | - | 共鸣技能 | -', 'E1-QTE切换爱弥斯 | - | - | 共鸣技能 | -'], 'warnings': ['Multiple previous-character Outro trigger frames found; selected value left null.']}`
- Action stub preview: `{'id': 'aemeath_qte_intro', 'character_id': 'aemeath', 'action_type': 'swap', 'policy_selectable': False, 'review_only': True, 'action_time': None, 'combat_time_cost': None, 'hits': [{'damage_multiplier': 0.1346}, {'damage_multiplier': 0.1346}, {'damage_multiplier': 1.0766}, {'damage_multiplier': 0.653}, {'damage_multiplier': 0.9795}], 'tags': ['qte', 'intro', 'variation'], 'notes': ['This is not applied to simulation yet.']}`

## D. Metadata Separated From Action

- Previous-character Outro trigger: `[40.0, 48.0]`
- Cannot-switch note: `True`
- Flow Light / 15s state grants: `[{'state_name_raw': '流光增幅', 'start_frame': 1.0, 'duration_seconds': 15.0, 'source_text': '第1F获得流光增幅状态，持续15秒'}]`
- E1-QTE switch notes: `[('E1-QTE切换机兵', 2771), ('E1-QTE切换爱弥斯', 2915), ('E1-QTE切换机兵', 2712), ('E1-QTE切换爱弥斯', 2764)]`

## E. Excluded Rows

- Seraphic Duet / enhanced E rows are excluded from QTE executable rows.
- Overdrive and Finale rows are excluded from QTE executable rows.
- Tune-break rows are excluded from QTE executable rows.
- E1-QTE switch rows are metadata only and do not contribute damage or timing.
- Metadata-only rows: 7
- Unrelated Aemeath rows: 7
- Other-character rows excluded: 524

## F. Implementation Note

- This report produces action-ready review candidates.
- It does not modify data/actions.json.
- Aemeath QTE remains disabled and non-policy.
- A future patch can turn `aemeath_qte_intro` into a real transition action after review.
