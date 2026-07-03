# Aemeath QTE / Intro / Outro Review

## A. Summary

- Source workbook path: `C:\Users\coree\OneDrive\Documents\GitHub\ww-dps-simulator-2\ww-dps-simulator-2\data\source\鸣潮动作数据汇总.xlsx`
- Selected sheets: `{'frame_sheet': '角色-女', 'skill_type_sheet': '角色技能类型'}`
- Total Aemeath QTE/Intro/Outro candidate rows: 24
- Groups created: 1
- Excluded other-character rows: 524
- Excluded header rows: 2
- Excluded unrelated rows: 6871
- review_only = true
- simulation_applied = false
- Action candidate output: `C:\Users\coree\OneDrive\Documents\GitHub\ww-dps-simulator-2\ww-dps-simulator-2\data\extracted\aemeath_qte_action_candidates.json`
- Action candidate report: `C:\Users\coree\OneDrive\Documents\GitHub\ww-dps-simulator-2\ww-dps-simulator-2\reports\aemeath_qte_action_candidate_review.md`

## B. Aemeath QTE Group

- Group ID: `aemeath_qte_intro`
- Source rows: `[('角色-女', 2771), ('角色-女', 2772), ('角色-女', 2776), ('角色-女', 2789), ('角色-女', 2790), ('角色-女', 2791), ('角色-女', 2792), ('角色-女', 2793), ('角色-女', 2798), ('角色-女', 2802), ('角色-女', 2806), ('角色-女', 2915), ('角色-女', 2921), ('角色-女', 2934), ('角色-女', 2935), ('角色-女', 2936), ('角色-女', 2937), ('角色技能类型', 2712), ('角色技能类型', 2726), ('角色技能类型', 2727), ('角色技能类型', 2728), ('角色技能类型', 2764), ('角色技能类型', 2781), ('角色技能类型', 2782)]`
- Source action labels: `['E1-QTE切换机兵', 'E2-合击', '强化E-降临', 'QTE', 'QTE-1', 'QTE-2', 'QTE-3', '大招1-前置', '大招2-前置', '谐度破坏-时停', '特殊能量', 'E1-QTE切换爱弥斯', '强化E-登台', 'QTE', 'QTE-1', 'QTE-2', '谐度破坏-时停', 'E1-QTE切换机兵', 'QTE-1', 'QTE-2', 'QTE-3', 'E1-QTE切换爱弥斯', 'QTE-1', 'QTE-2']`
- previous-character outro trigger frame: `48.0`
- Cannot-switch note parsed: `True`
- State grants: `[{'state': 'starlume_acceleration_or_flow_light_amp_candidate', 'state_name_raw': '流光增幅', 'start_frame': 1.0, 'duration_seconds': 15.0, 'source_text': '第1F获得流光增幅状态，持续15秒'}]`
- QTE hit rows: `[('QTE-1', 2790), ('QTE-2', 2791), ('QTE-3', 2792), ('QTE-1', 2935), ('QTE-2', 2936)]`
- QTE coefficient rows: `[('QTE-1', 2726), ('QTE-2', 2727), ('QTE-3', 2728), ('QTE-1', 2781), ('QTE-2', 2782)]`
- Parsed multipliers: `[0.1346, 0.1346, 1.0766, 0.653, 0.9795]`
- Damage type: `变奏伤害`
- Skill category: `变奏`
- Warnings: `['Review-only. Not applied to simulation.', 'Future implementation must wire this group into the transition pipeline explicitly.']`

### Notice Text

- 12 | 强化E-降临 | 立即切换至机兵，无敌期间不能切人
减少100点同步率，获得1点共鸣率
移除轨迹无消耗状态，技能结束后移除1层强化E增幅次数 | 1 | 180 | -100 | 0.2373 | 10 | 地面 | 时停 | 0 | 1 | 101 | 0 | 1 | 101
- 13 | QTE | 无敌期间不能切人
第48F触发上一角色延奏
第1F获得流光增幅状态，持续15秒
流光增幅状态期间施放大招1，可额外获得1点共鸣率 | 1 | 60 | 10 | 40 | 0.3164 | 11 | 地面 | 时停 | 0 | 1 | 50 | 0 | 1 | 50
- 14 | 大招1-前置 | 无敌期间不能切人，第238F移除流光增幅状态
第1F切换至机兵，获得30点同步率、1点共鸣率
第1F获得2层30秒强化E增幅次数，获得60秒【大招2解锁前置】 | 1 | 262 | 20 | 30 | 0 | 10 | 地面 | 时停 | 0 | 1 | 262 | 0 | 1 | 262
- 15 | 大招2-前置 | 无敌期间不能切人
第1F切换至爱弥斯，移除速蓄状态、强化E解锁状态
第1F清空同步率、共鸣率，技能结束后移除【大招2解锁前置】 | 1 | 340 | 20 | -200 | 0 | 10 | 地面 | 时停 | 0 | 1 | 340 | 0 | 1 | 340
- 16 | 谐度破坏-时停 | 无敌期间不能切人 | 1 | 90 | 1 | 11 | 地面 | 时停 | 0 | 1 | 70 | 0 | 1 | 70
- 17 | 特殊能量 | 同步率：
·上限200点
·A、空中攻击、E2命中时获取；
·施放QTE、大招1后，分别获取40、30点同步率；
·施放强化E时，减少100点同步率；
·施放大招2后清空同步率。

共鸣率：
·上限4点
·施放强化E、大招1后，分别获得1点共鸣率；
·施放大招2后清空共鸣率。

流光增幅状态：
·施放QTE后获得，持续15秒，触发获得刷新持续时间；
·状态期间施放大招1后，移除状态，额外获得1点共鸣率。

强化E解锁前置：
·施放A4获得，持续5秒，触发获得刷新持续时间；
·【前置】持续期间，同步率>=100点时解锁强化E；
·施放强化E后移除。

强化E增幅次数：
·施放大招1后获得2层，持续30秒，触发获得刷新持续时间；
·施放强化E时消耗1层，使 强化E-震谐 替换为 强化E-震谐增幅、强化E-聚爆 替换为 强化E-聚爆增幅。

轨迹无消耗状态：
·施放大招1后获得，持续30秒，触发获得刷新持续时间；
·状态期间，施放强化E不会移除目标持有的震谐轨迹/聚爆轨迹
·施放强化E后，移除该状态。

大招2解锁前置：
·施放大招1后获得，持续60秒，触发获得刷新持续时间；
·速蓄状态期间，施放强化重击后获得200点同步率；
·【前置】持续期间，同步率和共鸣率达到上限时解锁大招2；
·施放大招2后移除。

速蓄状态：
·【大招2解锁前置】持续期间，共鸣率达到上限时获得；
·状态期间，蓄力达到一段派生帧后自动施放强化重击；
·施放强化重击、施放大招2、【前置】持续结束后移除该状态。

C1速蓄状态：
·解锁C1后，在非战斗状态下不处于重击/强化重击/大招2动作中超过4秒时获得；
·获得后覆盖常规速蓄状态，且不会因【前置】结束而移除；
·状态期间，蓄力达到一段派生帧后自动施放强化重击；
·状态期间未持有【前置】时，施放强化重击后获得100点同步率
·施放强化重击、施放大招2后，移除该状态。
- 12 | 强化E-登台 | 立即切换至爱弥斯，无敌期间不能切人
减少100点同步率，获得1点共鸣率
移除轨迹无消耗状态，技能结束后移除1层强化E增幅次数 | 1 | 145 | -100 | 0.2373 | 10 | 地面 | 时停 | 0 | 1 | 65 | 0 | 1 | 65
- 13 | QTE | 无敌期间不能切人，第40F触发上一角色延奏
第1F获得流光增幅状态，持续15秒
流光增幅状态期间施放大招1，可额外获得1点共鸣率 | 1 | 72 | 10 | 40 | 0.3164 | 11 | 地面 | 时停 | 0 | 1 | 46 | 0 | 1 | 46
- 14 | 谐度破坏-时停 | 无敌期间不能切人 | 1 | 94 | 1 | 11 | 地面 | 时停 | 0 | 1 | 64 | 0 | 1 | 64

## C. Excluded Row Summary

- Other-character QTE-like rows excluded: 524
- Header rows excluded: 2
- Unrelated rows excluded: 6871

## D. Implementation Note

- Aemeath QTE data exists in the workbook.
- It is not yet applied to simulation.
- Current party swap uses transition/fallback placeholder timing unless real QTE/Intro/Outro is implemented.
- Future implementation should wire this QTE group into the transition pipeline.
