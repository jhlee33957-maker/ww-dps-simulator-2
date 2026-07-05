# Mornye Action Data Time / Resource Source Guard

| Sheet | Row | Column | Raw value | Display value | Interpreted meaning |
| --- | ---: | --- | --- | --- | --- |
| 角色-女 | 4135 | C | `观测重击-时停` | `观测重击-时停` | Inversion time-stop setup row |
| 角色-女 | 4135 | V | `=0-10000*0.01` | `-100` | Consumes 100 observation special resource/core |
| 角色-女 | 4135 | AC | `时停` | `时停` | Plain time stop, not global time stop |
| 角色-女 | 4135 | AI | `=INT(1.3*base!$B$2)+ROUND(1.3*base!$B$2-INT(1.3*base!$B$2),0)+(1-1.3>=1-0.5/base!$B$2)` | `78` | Enemy time-stop frame value |
| 角色-女 | 4135 | AL | `=INT(1.3*base!$B$2)+ROUND(1.3*base!$B$2-INT(1.3*base!$B$2),0)+(1-1.3>=1-0.5/base!$B$2)` | `78` | Ally time-stop frame value |
| 角色-女 | 4136 | C | `观测重击` | `观测重击` | Inversion damage row |
| 角色-女 | 4136 | D | `="脱手后延迟"&ROUNDUP(0.2*base!$B$2,0)&"F生效,命中后赋予目标30秒【观测标记】"` | `脱手后延迟12F生效,命中后赋予目标30秒【观测标记】` | Applies Observation Marker text |
| 角色-女 | 4136 | N | `=INT(1.3*base!$B$2)+ROUND(1.3*base!$B$2-INT(1.3*base!$B$2),0)+(1-1.3>=1-0.5/base!$B$2)` | `78` | Inversion action end frame |
| 角色-女 | 4148 | C | `QTE` | `QTE` | QTE setup row |
| 角色-女 | 4148 | D | `="第"&ROUND(1.3333334*base!$B$2,0)&"F前不能切人、不响应输入，第"&ROUNDUP(0.5862494*base!$B$2,0)&"F触发上一角色延奏
第"&ROUNDUP(1.1381084*base!$B$2,0)&"F获得30秒观测状态、清空核心"` | `第80F前不能切人、不响应输入，第36F触发上一角色延奏
第69F获得30秒观测状态、清空核心` | QTE source note contains 80F前不能切人 |
| 角色-女 | 4148 | D | `="第"&ROUND(1.3333334*base!$B$2,0)&"F前不能切人、不响应输入，第"&ROUNDUP(0.5862494*base!$B$2,0)&"F触发上一角色延奏
第"&ROUNDUP(1.1381084*base!$B$2,0)&"F获得30秒观测状态、清空核心"` | `第80F前不能切人、不响应输入，第36F触发上一角色延奏
第69F获得30秒观测状态、清空核心` | QTE source note contains 不响应输入 |
| 角色-女 | 4148 | D | `="第"&ROUND(1.3333334*base!$B$2,0)&"F前不能切人、不响应输入，第"&ROUNDUP(0.5862494*base!$B$2,0)&"F触发上一角色延奏
第"&ROUNDUP(1.1381084*base!$B$2,0)&"F获得30秒观测状态、清空核心"` | `第80F前不能切人、不响应输入，第36F触发上一角色延奏
第69F获得30秒观测状态、清空核心` | QTE source note contains 69F |
| 角色-女 | 4148 | D | `="第"&ROUND(1.3333334*base!$B$2,0)&"F前不能切人、不响应输入，第"&ROUNDUP(0.5862494*base!$B$2,0)&"F触发上一角色延奏
第"&ROUNDUP(1.1381084*base!$B$2,0)&"F获得30秒观测状态、清空核心"` | `第80F前不能切人、不响应输入，第36F触发上一角色延奏
第69F获得30秒观测状态、清空核心` | QTE source note contains 观测状态 |
| 角色-女 | 4148 | D | `="第"&ROUND(1.3333334*base!$B$2,0)&"F前不能切人、不响应输入，第"&ROUNDUP(0.5862494*base!$B$2,0)&"F触发上一角色延奏
第"&ROUNDUP(1.1381084*base!$B$2,0)&"F获得30秒观测状态、清空核心"` | `第80F前不能切人、不响应输入，第36F触发上一角色延奏
第69F获得30秒观测状态、清空核心` | QTE source note contains 清空核心 |
| 角色-女 | 4148 | D | `="第"&ROUND(1.3333334*base!$B$2,0)&"F前不能切人、不响应输入，第"&ROUNDUP(0.5862494*base!$B$2,0)&"F触发上一角色延奏
第"&ROUNDUP(1.1381084*base!$B$2,0)&"F获得30秒观测状态、清空核心"` | `第80F前不能切人、不响应输入，第36F触发上一角色延奏
第69F获得30秒观测状态、清空核心` | QTE raw note, including previous Outro trigger frame text |
| 角色-女 | 4148 | U | `=0+10` | `10` | Base Concerto recovery +10 |
| 角色-女 | 4148 | V | `=0-10000*0.01` | `-100` | Clears core/special resource |
| 角色-女 | 4148 | AC | `时停` | `时停` | Plain time stop, not global time stop |
| 角色-女 | 4148 | AI | `=IF(base!$B$3=FALSE,INT(1.3333334*base!$B$2)+ROUND(1.3333334*base!$B$2-INT(1.3333334*base!$B$2),0)+(1-1.3333334>=1-0.5/base!$B$2),0)` | `80` | Enemy time-stop frame value |
| 角色-女 | 4148 | AL | `=IF(base!$B$3=FALSE,INT(1.3333334*base!$B$2)+ROUND(1.3333334*base!$B$2-INT(1.3333334*base!$B$2),0)+(1-1.3333334>=1-0.5/base!$B$2),0)` | `80` | Ally time-stop frame value |
| 角色-女 | 4149 | C | `QTE-伤害` | `QTE-伤害` | QTE damage row |
| 角色-女 | 4149 | N | `=INT(1.7*base!$B$2)+ROUND(1.7*base!$B$2-INT(1.7*base!$B$2),0)+(1-1.7>=1-0.5/base!$B$2)` | `102` | QTE damage/action end frame |
| 角色-女 | 4143 | C | `E2-分布式阵列` | `E2-分布式阵列` | Distributed Array setup row |
| 角色-女 | 4143 | U | `=0+10` | `10` | Distributed Array base Concerto +10 |
| 角色-女 | 4144 | C | `E2-1` | `E2-1` | E2-1 damage row |
| 角色-女 | 4144 | V | `=0+1500*0.01` | `15` | E2-1 special resource/core +15 |
| 角色-女 | 4145 | C | `E2-2` | `E2-2` | E2-2 damage row |
| 角色-女 | 4145 | V | `=0+1500*0.01` | `15` | E2-2 special resource/core +15 |
| 角色-女 | 4146 | C | `E2-3` | `E2-3` | E2-3 damage row |
| 角色-女 | 4146 | V | `=0+1500*0.01` | `15` | E2-3 special resource/core +15 |
| 角色-女 | 4147 | C | `E2-4` | `E2-4` | E2-4 damage row |
| 角色-女 | 4147 | V | `=0+1500*0.01` | `15` | E2-4 special resource/core +15 |
| 角色-女 | 4150 | C | `大招-前置` | `大招-前置` | Liberation setup row |
| 角色-女 | 4150 | D | `="无敌期间不能切人，第"&ROUND(6*base!$B$2,0)&"F后切人不退场
第"&ROUND(4.4*base!$B$2,0)+1&"F成功销毁谐振场后，生成强谐振场"` | `无敌期间不能切人，第360F后切人不退场
第265F成功销毁谐振场后，生成强谐振场` | Liberation source note contains 无敌期间不能切人 |
| 角色-女 | 4150 | D | `="无敌期间不能切人，第"&ROUND(6*base!$B$2,0)&"F后切人不退场
第"&ROUND(4.4*base!$B$2,0)+1&"F成功销毁谐振场后，生成强谐振场"` | `无敌期间不能切人，第360F后切人不退场
第265F成功销毁谐振场后，生成强谐振场` | Liberation source note contains 第360F后切人不退场 |
| 角色-女 | 4150 | D | `="无敌期间不能切人，第"&ROUND(6*base!$B$2,0)&"F后切人不退场
第"&ROUND(4.4*base!$B$2,0)+1&"F成功销毁谐振场后，生成强谐振场"` | `无敌期间不能切人，第360F后切人不退场
第265F成功销毁谐振场后，生成强谐振场` | Liberation source note contains 第265F |
| 角色-女 | 4150 | D | `="无敌期间不能切人，第"&ROUND(6*base!$B$2,0)&"F后切人不退场
第"&ROUND(4.4*base!$B$2,0)+1&"F成功销毁谐振场后，生成强谐振场"` | `无敌期间不能切人，第360F后切人不退场
第265F成功销毁谐振场后，生成强谐振场` | Liberation source note contains 强谐振场 |
| 角色-女 | 4150 | U | `=0+20` | `20` | Liberation Concerto +20 |
| 角色-女 | 4150 | AC | `时停` | `时停` | Liberation setup plain time stop row |
| 角色-女 | 4150 | AI | `=IF(base!$B$3=FALSE,INT(5*base!$B$2)+ROUND(5*base!$B$2-INT(5*base!$B$2),0)+(1-5>=1-0.5/base!$B$2),0)` | `300` | Enemy time-stop frame value |
| 角色-女 | 4150 | AL | `=IF(base!$B$3=FALSE,INT(5*base!$B$2)+ROUND(5*base!$B$2-INT(5*base!$B$2),0)+(1-5>=1-0.5/base!$B$2),0)` | `300` | Ally time-stop frame value |
| 角色-女 | 4151 | C | `大招-全局时停` | `大招-全局时停` | Liberation global time-stop row |
| 角色-女 | 4151 | AC | `全局时停` | `全局时停` | Global time stop marker |
| 角色-女 | 4151 | AI | `=INT(5*base!$B$2)+ROUND(5*base!$B$2-INT(5*base!$B$2),0)+(1-5>=1-0.5/base!$B$2)` | `300` | Global time-stop enemy frame value |
| 角色-女 | 4151 | AL | `=INT(5*base!$B$2)+ROUND(5*base!$B$2-INT(5*base!$B$2),0)+(1-5>=1-0.5/base!$B$2)` | `300` | Global time-stop ally frame value |
| 角色-女 | 4153 | C | `大招-伤害` | `大招-伤害` | Liberation damage row |
| 角色-女 | 4153 | N | `=INT(4.7*base!$B$2)+ROUND(4.7*base!$B$2-INT(4.7*base!$B$2),0)+(1-4.7>=1-0.5/base!$B$2)` | `282` | Normal-state damage end frame |
| 角色-女 | 4154 | C | `大招-伤害` | `大招-伤害` | Liberation observation-state damage row |
| 角色-女 | 4154 | D | `观测状态，圆柱(1100,0,400)` | `观测状态，圆柱(1100,0,400)` | Observation-state damage text |
| 角色-女 | 4154 | N | `=INT(4.933671*base!$B$2)+ROUND(4.933671*base!$B$2-INT(4.933671*base!$B$2),0)+(1-4.933671>=1-0.5/base!$B$2)` | `296` | Observation-state damage end frame covered by 300F global time stop |
| 角色-女 | 4164 | D | `特殊能量：
静质量能=相对动能，上限100点

观测状态：
·施放强化重击、QTE后获得30秒观测状态；
·期间不可恢复耐力
·状态持续时间自然结束时，清空特殊能量
·钩锁、翱翔、使用载具、处于地面状态、处于后台、施放空中攻击下落时，移除该状态。

干涉标记：
·持有观测标记的偏移状态目标受到谐度破坏伤害时，获得8/20秒干涉标记。
·莫宁自身共鸣效率大于100%的部分，每1%使持有干涉标记的目标受到攻击造成的伤害加成+0.25%，至多40%。

被动1：
施放QTE、观测A3后，获得20点协奏能量

延奏：
被下一角色触发延奏后，全队获得0类通用伤害加深25%` | `特殊能量：
静质量能=相对动能，上限100点

观测状态：
·施放强化重击、QTE后获得30秒观测状态；
·期间不可恢复耐力
·状态持续时间自然结束时，清空特殊能量
·钩锁、翱翔、使用载具、处于地面状态、处于后台、施放空中攻击下落时，移除该状态。

干涉标记：
·持有观测标记的偏移状态目标受到谐度破坏伤害时，获得8/20秒干涉标记。
·莫宁自身共鸣效率大于100%的部分，每1%使持有干涉标记的目标受到攻击造成的伤害加成+0.25%，至多40%。

被动1：
施放QTE、观测A3后，获得20点协奏能量

延奏：
被下一角色触发延奏后，全队获得0类通用伤害加深25%` | Passive source text contains QTE |
| 角色-女 | 4164 | D | `特殊能量：
静质量能=相对动能，上限100点

观测状态：
·施放强化重击、QTE后获得30秒观测状态；
·期间不可恢复耐力
·状态持续时间自然结束时，清空特殊能量
·钩锁、翱翔、使用载具、处于地面状态、处于后台、施放空中攻击下落时，移除该状态。

干涉标记：
·持有观测标记的偏移状态目标受到谐度破坏伤害时，获得8/20秒干涉标记。
·莫宁自身共鸣效率大于100%的部分，每1%使持有干涉标记的目标受到攻击造成的伤害加成+0.25%，至多40%。

被动1：
施放QTE、观测A3后，获得20点协奏能量

延奏：
被下一角色触发延奏后，全队获得0类通用伤害加深25%` | `特殊能量：
静质量能=相对动能，上限100点

观测状态：
·施放强化重击、QTE后获得30秒观测状态；
·期间不可恢复耐力
·状态持续时间自然结束时，清空特殊能量
·钩锁、翱翔、使用载具、处于地面状态、处于后台、施放空中攻击下落时，移除该状态。

干涉标记：
·持有观测标记的偏移状态目标受到谐度破坏伤害时，获得8/20秒干涉标记。
·莫宁自身共鸣效率大于100%的部分，每1%使持有干涉标记的目标受到攻击造成的伤害加成+0.25%，至多40%。

被动1：
施放QTE、观测A3后，获得20点协奏能量

延奏：
被下一角色触发延奏后，全队获得0类通用伤害加深25%` | Passive source text contains 观测A3 |
| 角色-女 | 4164 | D | `特殊能量：
静质量能=相对动能，上限100点

观测状态：
·施放强化重击、QTE后获得30秒观测状态；
·期间不可恢复耐力
·状态持续时间自然结束时，清空特殊能量
·钩锁、翱翔、使用载具、处于地面状态、处于后台、施放空中攻击下落时，移除该状态。

干涉标记：
·持有观测标记的偏移状态目标受到谐度破坏伤害时，获得8/20秒干涉标记。
·莫宁自身共鸣效率大于100%的部分，每1%使持有干涉标记的目标受到攻击造成的伤害加成+0.25%，至多40%。

被动1：
施放QTE、观测A3后，获得20点协奏能量

延奏：
被下一角色触发延奏后，全队获得0类通用伤害加深25%` | `特殊能量：
静质量能=相对动能，上限100点

观测状态：
·施放强化重击、QTE后获得30秒观测状态；
·期间不可恢复耐力
·状态持续时间自然结束时，清空特殊能量
·钩锁、翱翔、使用载具、处于地面状态、处于后台、施放空中攻击下落时，移除该状态。

干涉标记：
·持有观测标记的偏移状态目标受到谐度破坏伤害时，获得8/20秒干涉标记。
·莫宁自身共鸣效率大于100%的部分，每1%使持有干涉标记的目标受到攻击造成的伤害加成+0.25%，至多40%。

被动1：
施放QTE、观测A3后，获得20点协奏能量

延奏：
被下一角色触发延奏后，全队获得0类通用伤害加深25%` | Passive source text contains 协奏 |
| 角色-女 | 4164 | D | `特殊能量：
静质量能=相对动能，上限100点

观测状态：
·施放强化重击、QTE后获得30秒观测状态；
·期间不可恢复耐力
·状态持续时间自然结束时，清空特殊能量
·钩锁、翱翔、使用载具、处于地面状态、处于后台、施放空中攻击下落时，移除该状态。

干涉标记：
·持有观测标记的偏移状态目标受到谐度破坏伤害时，获得8/20秒干涉标记。
·莫宁自身共鸣效率大于100%的部分，每1%使持有干涉标记的目标受到攻击造成的伤害加成+0.25%，至多40%。

被动1：
施放QTE、观测A3后，获得20点协奏能量

延奏：
被下一角色触发延奏后，全队获得0类通用伤害加深25%` | `特殊能量：
静质量能=相对动能，上限100点

观测状态：
·施放强化重击、QTE后获得30秒观测状态；
·期间不可恢复耐力
·状态持续时间自然结束时，清空特殊能量
·钩锁、翱翔、使用载具、处于地面状态、处于后台、施放空中攻击下落时，移除该状态。

干涉标记：
·持有观测标记的偏移状态目标受到谐度破坏伤害时，获得8/20秒干涉标记。
·莫宁自身共鸣效率大于100%的部分，每1%使持有干涉标记的目标受到攻击造成的伤害加成+0.25%，至多40%。

被动1：
施放QTE、观测A3后，获得20点协奏能量

延奏：
被下一角色触发延奏后，全队获得0类通用伤害加深25%` | Passive source text contains 20 |
| 角色-女 | 4155 | C | `谐度破坏-时停` | `谐度破坏-时停` | Tune rupture plain time-stop row |
| 角色-女 | 4155 | AC | `时停` | `时停` | Plain time stop |
| 角色-女 | 4155 | AI | `=INT(1.0734751*base!$B$2)+ROUND(1.0734751*base!$B$2-INT(1.0734751*base!$B$2),0)+(1-1.0734751>=1-0.5/base!$B$2)` | `64` | Enemy time-stop frame value |
| 角色-女 | 4155 | AL | `=INT(1.0734751*base!$B$2)+ROUND(1.0734751*base!$B$2-INT(1.0734751*base!$B$2),0)+(1-1.0734751>=1-0.5/base!$B$2)` | `64` | Ally time-stop frame value |
| 角色-女 | 4156 | C | `谐度破坏-全局时停` | `谐度破坏-全局时停` | Tune rupture global time-stop row |
| 角色-女 | 4156 | AC | `全局时停` | `全局时停` | Global time stop marker |
| 角色-女 | 4156 | AI | `=INT(1.5666666*base!$B$2)+ROUND(1.5666666*base!$B$2-INT(1.5666666*base!$B$2),0)+(1-1.5666666>=1-0.5/base!$B$2)` | `94` | Global time-stop enemy frame value |
| 角色-女 | 4156 | AL | `=INT(1.5666666*base!$B$2)+ROUND(1.5666666*base!$B$2-INT(1.5666666*base!$B$2),0)+(1-1.5666666>=1-0.5/base!$B$2)` | `94` | Global time-stop ally frame value |
| 角色-女 | 4159 | C | `谐度破坏-3` | `谐度破坏-3` | Tune rupture third damage row |
| 角色-女 | 4159 | N | `=INT(1.5627743*base!$B$2)+ROUND(1.5627743*base!$B$2-INT(1.5627743*base!$B$2),0)+(1-1.5627743>=1-0.5/base!$B$2)` | `94` | Tune rupture end frame |

## Warnings
- Request expected QTE note text `35F`, but workbook display text contains `36F`; preserved as source discrepancy.
