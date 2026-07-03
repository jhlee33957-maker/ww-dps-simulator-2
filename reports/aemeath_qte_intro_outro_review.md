# Aemeath QTE / Intro / Outro Review

Status: review-only, not applied, not executable.

Mojibake hints retained for reviewer search: ?섇쪕, 兩뜹쪕

Candidate rows: 1216

## Review Notes

- These rows are not mapped into simulator actions.
- Aemeath QTE/Intro/Outro remains disabled in transition_config.json.
- Generic party swap fallback timing remains placeholder-only.

## Candidates

### 角色-女 row 1

- Source action: `名称`
- Confidence: very_low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 名称 | ID | 动作 | 备注 | 发生帧 | 持续帧 | 顿帧-自 | 顿帧-敌 | 无敌启动帧 | 无敌持续帧 | 优先级改变 | 派生帧 | 派生持续帧 | 动作结束帧 | 可弹刀 | 可脱手 | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD343B90> | 削韧值 | 偏谐值 | 大招回收 | 协奏回收 | 核心回收1 | 核心回收2 | 核心回收3 | 受击韧性系数 | 中断优先级 | 位置状态 | 状态转换时间 | 时间膨胀类型 | 自膨胀系数 | 膨胀发生 | 膨胀持续 | 敌膨胀系数 | 膨胀发生 | 膨胀持续 | 友膨胀系数 | 膨胀发生 | 膨胀持续 | 命中类型 | 位置基准 | 跟随骨骼 | 解除跟随 | 判定缩放倍数 | 位置基准偏移 | 中心位置偏移 | 判定范围

### 角色-女 row 117

- Source action: `14`
- Confidence: very_low
- Coefficients: `[{'raw': '1.0666667', 'value': 1.0666667}, {'raw': '0.5625', 'value': 0.5625}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 14 | 重击 | 协奏能量 +(4*核心能量数)，大招能量 +(2.5*核心能量数) | =ROUNDUP(1.0666667*base!$B$2,0) | -1 | × | × | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B0EAEED0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BB631190> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B2E58470> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B2EC0440> | -4 | 0.5625 | 3 | 地面 | 目标 | 优昙 | 根 | (0,0,70) | 球形(250,0,0)

### 角色-女 row 122

- Source action: `16`
- Confidence: low
- Coefficients: `[{'raw': '1.6425352', 'value': 1.6425352}, {'raw': '0.7709859', 'value': 0.7709859}, {'raw': '0.867', 'value': 0.867}, {'raw': '1.8101408', 'value': 1.8101408}, {'raw': '1.629894', 'value': 1.629894}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.7709859', 'value': 0.7709859}, {'raw': '0.7709859', 'value': 0.7709859}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 16 | QTE | ="第"&ROUNDUP(1.6425352*base!$B$2,0)&"F前不响应输入；第"&ROUNDUP(0.7709859*base!$B$2,0)&"F触发上一角色延奏" | =INT(0.867*base!$B$2)+1 | =INT(0.1*base!$B$2) | =ROUNDUP(0*base!$B$2,0)+1 | =ROUNDUP(1.8101408*base!$B$2,0) | =ROUNDUP(1.629894*base!$B$2,0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD379AF0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD37A030> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD37B9B0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD379C70> | 0.3164 | 11,1 | 地面 | 时停 | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.7709859*base!$B$2,0),0) | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.7709859*base!$B$2,0),0) | 目标 | 优昙 | 根 | (100,0,-80) | 矩形(250,300,200)

### 角色-女 row 123

- Source action: `17`
- Confidence: low
- Coefficients: `[{'raw': '0.75920796', 'value': 0.75920796}, {'raw': '0.2917866', 'value': 0.2917866}, {'raw': '0.42764997', 'value': 0.42764997}, {'raw': '1.06786', 'value': 1.06786}, {'raw': '0.178', 'value': 0.178}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.06', 'value': 0.06}]`
- Frame candidates: `[{'raw': '378F', 'frames': 378.0, 'seconds_at_60fps': 6.3}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 17 | E | ="协奏能量 +(8*核心能量数)；第"&ROUNDUP(0.75920796*base!$B$2,0)&"F改变中断优先级，第"&ROUNDUP(0.2917866*base!$B$2,0)&"F回血" | =ROUNDUP(0.42764997*base!$B$2,0) | =INT(0.1*base!$B$2) | =MAX(CEILING($AF123*(1-$AD123),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI123*(1-$AG123),1)-INT(base!$B$3<>TRUE),0) | =ROUNDUP(0.9*base!$B$2,0) | =ROUNDUP(1.06786*base!$B$2,0) | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD378FE0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD379340> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD379070> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3790D0> | -4 | 0.178 | 4,1 | 地面 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.06*base!$B$2,0),0) | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.06*base!$B$2,0),0) | 目标 | 白芷 | 球形(500,0,0)

### 角色-女 row 206

- Source action: `15#`
- Confidence: very_low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '10秒', 'seconds': 10.0}]`
- 15s state notes: `[]`
- Raw row: 15# | 地面E-椿花魔女 | 立即获得10秒椿花魔女状态、减少70点协奏能量 | =0-70 | -1 | -1 | -1 | 4 | 地面

### 角色-女 row 217

- Source action: `16#`
- Confidence: very_low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '10秒', 'seconds': 10.0}]`
- 15s state notes: `[]`
- Raw row: 16# | 空中E-椿花魔女 | 立即获得40点耐力、10秒椿花魔女状态、减少70点协奏能量 | =0-70 | 4 | 空中

### 角色-女 row 222

- Source action: `17`
- Confidence: low
- Coefficients: `[{'raw': '0.74793935', 'value': 0.74793935}, {'raw': '0.74793935', 'value': 0.74793935}, {'raw': '0.71564347', 'value': 0.71564347}, {'raw': '0.71564347', 'value': 0.71564347}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 17 | QTE | ="第"&ROUND(0.74793935*base!$B$2+(0.74793935*base!$B$2<=base!$C$2),0)&"F触发协奏反应" | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(0.71564347*base!$B$2+(0.71564347*base!$B$2<=base!$C$2),0) | 1 | 4 | 地面

### 角色-女 row 223

- Source action: `QTE-敌我顿帧`
- Confidence: low
- Coefficients: `[{'raw': '0.031', 'value': 0.031}, {'raw': '0.031', 'value': 0.031}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-敌我顿帧 | 持续作用 | =ROUND(0.031*base!$B$2+(0.031*base!$B$2<=base!$C$2),0) | =ROUND(0.6*base!$B$2+(0.6*base!$B$2<=base!$C$2),0) | × | × | 4 | 地面 | 攻击顿帧 | 0.1 | 0.1 | 目标队友 | 旧椿 | (-100,0,0) | 矩形(4000,4000,4000)

### 角色-女 row 224

- Source action: `QTE-1`
- Confidence: low
- Coefficients: `[{'raw': '0.3069878', 'value': 0.3069878}, {'raw': '0.3069878', 'value': 0.3069878}, {'raw': '0.4333333', 'value': 0.4333333}, {'raw': '0.4333333', 'value': 0.4333333}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.03', 'value': 0.03}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-1 | 命中后获得椿花瓣、椿花蕾 | =ROUND(0.3069878*base!$B$2+(0.3069878*base!$B$2<=base!$C$2),0) | =ROUND(0.2*base!$B$2+(0.2*base!$B$2<=base!$C$2),0) | =MAX(CEILING($AF224*(1-$AD224),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI224*(1-$AG224),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD38BA40> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD38BA10> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD38B9E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD38B9B0> | 1 | 1 | 4 | 地转空 | =ROUND(0.4333333*base!$B$2+(0.4333333*base!$B$2<=base!$C$2),0) | 攻击顿帧 | 0.6 | =ROUND(0.03*base!$B$2+(0.03*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0.6 | =ROUND(0.03*base!$B$2+(0.03*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 目标 | 旧椿 | 根 | (0,150,100) | 矩形(150,200,100)

### 角色-女 row 225

- Source action: `QTE-2`
- Confidence: low
- Coefficients: `[{'raw': '0.545835', 'value': 0.545835}, {'raw': '0.545835', 'value': 0.545835}, {'raw': '0.7501382', 'value': 0.7501382}, {'raw': '0.7501382', 'value': 0.7501382}, {'raw': '0.7469799', 'value': 0.7469799}, {'raw': '0.7469799', 'value': 0.7469799}, {'raw': '0.41867357', 'value': 0.41867357}, {'raw': '0.41867357', 'value': 0.41867357}, {'raw': '0.7615376', 'value': 0.7615376}, {'raw': '0.7615376', 'value': 0.7615376}, {'raw': '0.08', 'value': 0.08}, {'raw': '0.08', 'value': 0.08}, {'raw': '0.08', 'value': 0.08}, {'raw': '0.08', 'value': 0.08}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-2 | =ROUND((0.545835+0.1)*base!$B$2+((0.545835+0.1)*base!$B$2<=base!$C$2),0) | =ROUND((0.5-0.1)*base!$B$2+((0.5-0.1)*base!$B$2<=base!$C$2),0) | =MAX(CEILING($AF225*(1-$AD225),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI225*(1-$AG225),1)-INT(base!$B$3<>TRUE),0) | =ROUND(0.7501382*base!$B$2+(0.7501382*base!$B$2<=base!$C$2),0) | =ROUND(0.7469799*base!$B$2+(0.7469799*base!$B$2<=base!$C$2),0) | =ROUND(0.41867357*base!$B$2+(0.41867357*base!$B$2<=base!$C$2),0) | =ROUND(0.7615376*base!$B$2+(0.7615376*base!$B$2<=base!$C$2),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD342C30> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD340DA0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD340AD0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD342240> | 4,1 | 空中 | 攻击顿帧 | 0.2 | =ROUND(0.08*base!$B$2+(0.08*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0.2 | =ROUND(0.08*base!$B$2+(0.08*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 目标 | 旧椿 | (150,0,150) | 矩形(200,200,100)

### 角色-女 row 232

- Source action: `19`
- Confidence: medium
- Coefficients: `[{'raw': '5%', 'value': 0.05}, {'raw': '0.34%', 'value': 0.0034000000000000002}, {'raw': '20%', 'value': 0.2}, {'raw': '1.34%', 'value': 0.0134}, {'raw': '20%', 'value': 0.2}, {'raw': '1.34%', 'value': 0.0134}]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '10秒', 'seconds': 10.0}]`
- 15s state notes: `[]`
- Raw row: 19 | 共鸣回路 | 椿花标记：
·瓣：上限1层，A5、QTE 命中后获得；
·蕊：上限1层，空中A、空中重击 命中后获得；
·蕾：上限1层，重击、QTE 命中后获得；
·每持有一种椿花标记，获得 5%+回路等级*0.34% 攻击加成；
·处于椿花魔女状态时，不可获得椿花标记；
·施放 地面E、魔女地面E、空中E、魔女地面E、大招 结束或中断后，移除所有椿花标记。

椿花魔女：
·同时持有椿花瓣、椿花蕊、椿花蕾时，解锁 E-椿花魔女、大招-椿花魔女 ，施放后获得椿花魔女状态；
·状态持续10秒，期间获得70%受击削韧减免、20%+1.34%回路等级 暗伤加成、20%+回路等级*1.34% 暗伤暴击率。

### 角色-女 row 244

- Source action: `20`
- Confidence: low
- Coefficients: `[{'raw': '15%', 'value': 0.15}, {'raw': '20%', 'value': 0.2}, {'raw': '20%', 'value': 0.2}, {'raw': '20%', 'value': 0.2}]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '0.65秒', 'seconds': 0.65}, {'raw': '10秒', 'seconds': 10.0}, {'raw': '0.65秒', 'seconds': 0.65}, {'raw': '15秒', 'seconds': 15.0}, {'raw': '15秒', 'seconds': 15.0}, {'raw': '0.65秒', 'seconds': 0.65}, {'raw': '15秒', 'seconds': 15.0}, {'raw': '15秒', 'seconds': 15.0}, {'raw': '0.65秒', 'seconds': 0.65}]`
- 15s state notes: `['20 | 协奏反应 | 冰暗/火暗/雷暗/风暗/光暗反应：\n触发反应0.65秒后\n·造成5次1.88%倍率的对应属性伤害\n  命中后10秒内降低目标30%对应抗性\n\n暗冰/暗火/暗雷/暗风反应：\n触发反应0.65秒后\n·15秒内处于前台时暗伤加成+15%\n·15秒内处于后台时暗伤加成+20%\n\n暗光反应：\n触发反应0.65秒后\n·15秒内处于前台的角色冰伤加成+20%\n·15秒内全队火雷风光暗伤加成+20%\n\n暗暗反应：\n触发反应0.65秒后\n·造成3次33.34%伤害倍率的暗伤']`
- Raw row: 20 | 协奏反应 | 冰暗/火暗/雷暗/风暗/光暗反应：
触发反应0.65秒后
·造成5次1.88%倍率的对应属性伤害
  命中后10秒内降低目标30%对应抗性

暗冰/暗火/暗雷/暗风反应：
触发反应0.65秒后
·15秒内处于前台时暗伤加成+15%
·15秒内处于后台时暗伤加成+20%

暗光反应：
触发反应0.65秒后
·15秒内处于前台的角色冰伤加成+20%
·15秒内全队火雷风光暗伤加成+20%

暗暗反应：
触发反应0.65秒后
·造成3次33.34%伤害倍率的暗伤

### 角色-女 row 290

- Source action: `11`
- Confidence: low
- Coefficients: `[{'raw': '0.7597527', 'value': 0.7597527}, {'raw': '0.19564074', 'value': 0.19564074}, {'raw': '1.3937728', 'value': 1.3937728}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.74846184', 'value': 0.74846184}, {'raw': '0.74846184', 'value': 0.74846184}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 11 | QTE | ="第"&ROUNDUP(0.7597527*base!$B$2,0)&"F前不响应输入；第"&ROUNDUP(0.19564074*base!$B$2,0)&"F触发上一角色延奏" | =ROUNDUP(0*base!$B$2,0)+1 | =ROUNDUP(1.3937728*base!$B$2,0) | =0+10 | 0.3164 | 11 | 空中 | 时停 | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.74846184*base!$B$2,0),0) | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.74846184*base!$B$2,0),0)

### 角色-女 row 291

- Source action: `QTE-空中A4`
- Confidence: medium
- Coefficients: `[{'raw': '0.104809895', 'value': 0.104809895}, {'raw': '0.10616106', 'value': 0.10616106}, {'raw': '0.15', 'value': 0.15}, {'raw': '0.75', 'value': 0.75}, {'raw': '1.9233333', 'value': 1.9233333}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}]`
- Frame candidates: `[{'raw': '331F', 'frames': 331.0, 'seconds_at_60fps': 5.5167}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-空中A4 | ="第"&ROUNDUP(0.104809895*base!$B$2,0)&"F进入心眼状态" | =ROUNDUP(0.10616106*base!$B$2,0) | =ROUND(0.15*base!$B$2,0) | =MAX(CEILING($AF291*(1-$AD291),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI291*(1-$AG291),1)-INT(base!$B$3<>TRUE),0) | =ROUNDUP(0.75*base!$B$2,0) | =ROUNDUP(1.9233333*base!$B$2,0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD331F70> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3327B0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3325A0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3336B0> | 11 | 空中 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 0.3 | =IF(base!$B$3=FALSE,ROUNDUP(0.1*base!$B$2,0),0) | 目标 | 长离 | (200,0,100) | 矩形(300,200,200)

### 角色-女 row 292

- Source action: `QTE-空中A4-飞道`
- Confidence: low
- Coefficients: `[{'raw': '0.30616106', 'value': 0.30616106}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-空中A4-飞道 | 顿帧影响时停时长 | =ROUNDUP(0.30616106*base!$B$2,0) | =ROUND(0.6*base!$B$2,0) | =MAX(CEILING($AF292*(1-$AD292),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI292*(1-$AG292),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E9CA0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E8EF0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E9BE0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E9580> | 11 | 空中 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 目标 | =$C$291 | (0,0,300) | (0,0,-300) | 圆柱(600,0,200)

### 角色-女 row 293

- Source action: `QTE-空中A4-飞道`
- Confidence: low
- Coefficients: `[{'raw': '0.39616106', 'value': 0.39616106}, {'raw': '0.09', 'value': 0.09}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-空中A4-飞道 | =ROUNDUP(0.39616106*base!$B$2,0) | =ROUNDUP(0.09*base!$B$2,0) | =MAX(CEILING($AF293*(1-$AD293),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI293*(1-$AG293),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E9640> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E9610> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E95E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E94C0> | 11 | 空中 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 目标 | =$C$291 | (0,0,300) | (0,0,-300) | 圆柱(600,0,200)

### 角色-女 row 294

- Source action: `QTE-空中A4-飞道`
- Confidence: low
- Coefficients: `[{'raw': '0.48616106', 'value': 0.48616106}, {'raw': '0.09', 'value': 0.09}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-空中A4-飞道 | =ROUNDUP(0.48616106*base!$B$2,0) | =ROUNDUP(0.09*base!$B$2,0) | =MAX(CEILING($AF294*(1-$AD294),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI294*(1-$AG294),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EACC0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EAC90> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EAC60> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EAC30> | 11 | 空中 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 目标 | =$C$291 | (0,0,300) | (0,0,-300) | 圆柱(600,0,200)

### 角色-女 row 295

- Source action: `QTE-空中A4-飞道`
- Confidence: low
- Coefficients: `[{'raw': '0.57616106', 'value': 0.57616106}, {'raw': '0.09', 'value': 0.09}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-空中A4-飞道 | =ROUNDUP(0.57616106*base!$B$2,0) | =ROUNDUP(0.09*base!$B$2,0) | =MAX(CEILING($AF295*(1-$AD295),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI295*(1-$AG295),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E8380> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EBE30> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E8350> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EBF20> | 11,2 | 空中 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 0.01 | =IF(base!$B$3=FALSE,ROUNDUP(0.03*base!$B$2,0),0) | 目标 | =$C$291 | (0,0,300) | (0,0,-300) | 圆柱(600,0,200)

### 角色-女 row 403

- Source action: `19`
- Confidence: medium
- Coefficients: `[{'raw': '0.5496941', 'value': 0.5496941}, {'raw': '1.263274', 'value': 1.263274}, {'raw': '1.3291956', 'value': 1.3291956}, {'raw': '1.3291956', 'value': 1.3291956}, {'raw': '1.3291956', 'value': 1.3291956}, {'raw': '1.3291956', 'value': 1.3291956}, {'raw': '1.3291956', 'value': 1.3291956}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.5038076', 'value': 0.5038076}, {'raw': '0.5038076', 'value': 0.5038076}, {'raw': '0.5038076', 'value': 0.5038076}, {'raw': '0.5038076', 'value': 0.5038076}, {'raw': '0.5038076', 'value': 0.5038076}, {'raw': '0.5038076', 'value': 0.5038076}, {'raw': '0.5038076', 'value': 0.5038076}, {'raw': '0.5038076', 'value': 0.5038076}]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '25秒', 'seconds': 25.0}]`
- 15s state notes: `[]`
- Raw row: 19 | QTE | ="获得25秒溟海苏生状态，重复获得不刷新持续时间"&CHAR(10)&"第"&ROUNDUP(0.5496941*base!$B$2,0)&"F触发上一角色延奏"&CHAR(10)&"第"&ROUNDUP(1.263274*base!$B$2,0)&"F前不响应输入"&CHAR(10)&"第"&ROUNDUP(1.3291956*base!$B$2,0)&"F前不能切人" | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(1.3291956*base!$B$2)+ROUND(1.3291956*base!$B$2-INT(1.3291956*base!$B$2),0)+(1-1.3291956>=1-0.5/base!$B$2) | =0+10 | 1 | 0.3164 | 11 | 地面 | 时停 | 0 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =IF(base!$B$3=FALSE,INT(0.5038076*base!$B$2)+ROUND(0.5038076*base!$B$2-INT(0.5038076*base!$B$2),0)+(1-0.5038076>=1-0.5/base!$B$2),0) | 0 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =IF(base!$B$3=FALSE,INT(0.5038076*base!$B$2)+ROUND(0.5038076*base!$B$2-INT(0.5038076*base!$B$2),0)+(1-0.5038076>=1-0.5/base!$B$2),0)

### 角色-女 row 404

- Source action: `QTE-1`
- Confidence: low
- Coefficients: `[{'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-1 | =INT(0.6*base!$B$2)+ROUND(0.6*base!$B$2-INT(0.6*base!$B$2),0)+(1-0.6>=1-0.5/base!$B$2) | =INT(0.1*base!$B$2)+ROUND(0.1*base!$B$2-INT(0.1*base!$B$2),0)+(1-0.1>=1-0.5/base!$B$2) | =MAX(CEILING($AI404*(1-$AG404),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BF9E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BC9E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BE690> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BD5E0> | 11 | 地面 | 攻击顿帧 | 0.5 | =IF(base!$B$3=FALSE,INT(0.01*base!$B$2)+ROUND(0.01*base!$B$2-INT(0.01*base!$B$2),0)+(1-0.01>=1-0.5/base!$B$2),0) | 目标 | 坎特蕾拉 | 伞 | 矩形(180,180,150)

### 角色-女 row 405

- Source action: `QTE-2`
- Confidence: low
- Coefficients: `[{'raw': '0.6999999', 'value': 0.6999999}, {'raw': '0.6999999', 'value': 0.6999999}, {'raw': '0.6999999', 'value': 0.6999999}, {'raw': '0.6999999', 'value': 0.6999999}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-2 | =INT(0.6999999*base!$B$2)+ROUND(0.6999999*base!$B$2-INT(0.6999999*base!$B$2),0)+(1-0.6999999>=1-0.5/base!$B$2) | =INT(0.1*base!$B$2)+ROUND(0.1*base!$B$2-INT(0.1*base!$B$2),0)+(1-0.1>=1-0.5/base!$B$2) | =MAX(CEILING($AI405*(1-$AG405),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BD670> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BD640> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BD580> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BD4C0> | 11 | 地面 | 攻击顿帧 | 0.3 | =IF(base!$B$3=FALSE,INT(0.06*base!$B$2)+ROUND(0.06*base!$B$2-INT(0.06*base!$B$2),0)+(1-0.06>=1-0.5/base!$B$2),0) | 目标 | 坎特蕾拉 | 伞 | 矩形(180,180,150)

### 角色-女 row 406

- Source action: `QTE-3`
- Confidence: low
- Coefficients: `[{'raw': '0.79999995', 'value': 0.79999995}, {'raw': '0.79999995', 'value': 0.79999995}, {'raw': '0.79999995', 'value': 0.79999995}, {'raw': '0.79999995', 'value': 0.79999995}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-3 | =INT(0.79999995*base!$B$2)+ROUND(0.79999995*base!$B$2-INT(0.79999995*base!$B$2),0)+(1-0.79999995>=1-0.5/base!$B$2) | =INT(0.200000002980232*base!$B$2)+ROUND(0.200000002980232*base!$B$2-INT(0.200000002980232*base!$B$2),0)+(1-0.200000002980232>=1-0.5/base!$B$2) | =MAX(CEILING($AI406*(1-$AG406),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD333380> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD332AE0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD332180> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD332AB0> | 11 | 地面 | 攻击顿帧 | 0.1 | =IF(base!$B$3=FALSE,INT(0.06*base!$B$2)+ROUND(0.06*base!$B$2-INT(0.06*base!$B$2),0)+(1-0.06>=1-0.5/base!$B$2),0) | 目标 | 坎特蕾拉 | 伞 | 矩形(180,180,150)

### 角色-女 row 407

- Source action: `QTE-4`
- Confidence: low
- Coefficients: `[{'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '1.263943', 'value': 1.263943}, {'raw': '1.263943', 'value': 1.263943}, {'raw': '1.263943', 'value': 1.263943}, {'raw': '1.263943', 'value': 1.263943}, {'raw': '1.0632981', 'value': 1.0632981}, {'raw': '1.0632981', 'value': 1.0632981}, {'raw': '1.0632981', 'value': 1.0632981}, {'raw': '1.0632981', 'value': 1.0632981}, {'raw': '2.3624299', 'value': 2.3624299}, {'raw': '2.3624299', 'value': 2.3624299}, {'raw': '2.3624299', 'value': 2.3624299}, {'raw': '2.3624299', 'value': 2.3624299}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-4 | =INT(0.9*base!$B$2)+ROUND(0.9*base!$B$2-INT(0.9*base!$B$2),0)+(1-0.9>=1-0.5/base!$B$2) | =INT(0.200000002980232*base!$B$2)+ROUND(0.200000002980232*base!$B$2-INT(0.200000002980232*base!$B$2),0)+(1-0.200000002980232>=1-0.5/base!$B$2) | =MAX(CEILING($AI407*(1-$AG407),1)-INT(base!$B$3<>TRUE),0) | =INT(1.263943*base!$B$2)+ROUND(1.263943*base!$B$2-INT(1.263943*base!$B$2),0)+(1-1.263943>=1-0.5/base!$B$2) | =INT(1.0632981*base!$B$2)+ROUND(1.0632981*base!$B$2-INT(1.0632981*base!$B$2),0)+(1-1.0632981>=1-0.5/base!$B$2) | =INT(2.3624299*base!$B$2)+ROUND(2.3624299*base!$B$2-INT(2.3624299*base!$B$2),0)+(1-2.3624299>=1-0.5/base!$B$2) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD38AAB0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD38BF20> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD389BB0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD38A810> | 11,2 | 地面 | 攻击顿帧 | 0.1 | =IF(base!$B$3=FALSE,INT(0.06*base!$B$2)+ROUND(0.06*base!$B$2-INT(0.06*base!$B$2),0)+(1-0.06>=1-0.5/base!$B$2),0) | 目标 | 坎特蕾拉 | 伞 | 矩形(160,160,100)

### 角色-女 row 408

- Source action: `20`
- Confidence: medium
- Coefficients: `[{'raw': '0.59999996', 'value': 0.59999996}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.329196', 'value': 1.329196}, {'raw': '1.329196', 'value': 1.329196}, {'raw': '1.329196', 'value': 1.329196}, {'raw': '1.329196', 'value': 1.329196}, {'raw': '1.329196', 'value': 1.329196}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.67129624', 'value': 0.67129624}, {'raw': '0.67129624', 'value': 0.67129624}, {'raw': '0.67129624', 'value': 0.67129624}, {'raw': '0.67129624', 'value': 0.67129624}, {'raw': '0.67129624', 'value': 0.67129624}, {'raw': '0.67129624', 'value': 0.67129624}, {'raw': '0.67129624', 'value': 0.67129624}, {'raw': '0.67129624', 'value': 0.67129624}]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '25秒', 'seconds': 25.0}]`
- 15s state notes: `[]`
- Raw row: 20 | 强化QTE | ="清除强化A计数"&CHAR(10)&"获得25秒溟海苏生状态，重复获得不刷新持续时间"&CHAR(10)&"第"&ROUNDUP(0.59999996*base!$B$2,0)&"F触发上一角色延奏"&CHAR(10)&"第"&ROUNDUP(1.3333333*base!$B$2,0)&"F前不响应输入"&CHAR(10)&"第"&ROUNDUP(1.329196*base!$B$2,0)&"F前不能切人" | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(1.329196*base!$B$2)+ROUND(1.329196*base!$B$2-INT(1.329196*base!$B$2),0)+(1-1.329196>=1-0.5/base!$B$2) | =0+10 | 1 | 0.3164 | 11 | 地面 | 时停 | 0 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =IF(base!$B$3=FALSE,INT(0.67129624*base!$B$2)+ROUND(0.67129624*base!$B$2-INT(0.67129624*base!$B$2),0)+(1-0.67129624>=1-0.5/base!$B$2),0) | 0 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =IF(base!$B$3=FALSE,INT(0.67129624*base!$B$2)+ROUND(0.67129624*base!$B$2-INT(0.67129624*base!$B$2),0)+(1-0.67129624>=1-0.5/base!$B$2),0)

### 角色-女 row 409

- Source action: `强化QTE-水母1`
- Confidence: low
- Coefficients: `[{'raw': '0.06666666', 'value': 0.06666666}, {'raw': '0.06666666', 'value': 0.06666666}, {'raw': '0.06666666', 'value': 0.06666666}, {'raw': '0.06666666', 'value': 0.06666666}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 强化QTE-水母1 | =INT(0.06666666*base!$B$2)+ROUND(0.06666666*base!$B$2-INT(0.06666666*base!$B$2),0)+(1-0.06666666>=1-0.5/base!$B$2) | =INT(1*base!$B$2)+ROUND(1*base!$B$2-INT(1*base!$B$2),0)+(1-1>=1-0.5/base!$B$2) | =MAX(CEILING($AI409*(1-$AG409),1)-INT(base!$B$3<>TRUE),0) | × | √ | 11 | 地面 | 攻击顿帧 | 0.5 | =IF(base!$B$3=FALSE,INT(0.01*base!$B$2)+ROUND(0.01*base!$B$2-INT(0.01*base!$B$2),0)+(1-0.01>=1-0.5/base!$B$2),0) | 目标 | 坎特蕾拉 | (-200,50,150) | 矩形(10,20,20)

### 角色-女 row 410

- Source action: `强化QTE-水母2`
- Confidence: low
- Coefficients: `[{'raw': '0.19999999', 'value': 0.19999999}, {'raw': '0.19999999', 'value': 0.19999999}, {'raw': '0.19999999', 'value': 0.19999999}, {'raw': '0.19999999', 'value': 0.19999999}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 强化QTE-水母2 | =INT(0.19999999*base!$B$2)+ROUND(0.19999999*base!$B$2-INT(0.19999999*base!$B$2),0)+(1-0.19999999>=1-0.5/base!$B$2) | =INT(1*base!$B$2)+ROUND(1*base!$B$2-INT(1*base!$B$2),0)+(1-1>=1-0.5/base!$B$2) | =MAX(CEILING($AI410*(1-$AG410),1)-INT(base!$B$3<>TRUE),0) | × | √ | 11 | 地面 | 攻击顿帧 | 0.3 | =IF(base!$B$3=FALSE,INT(0.06*base!$B$2)+ROUND(0.06*base!$B$2-INT(0.06*base!$B$2),0)+(1-0.06>=1-0.5/base!$B$2),0) | 目标 | 坎特蕾拉 | (-200,-50,150) | 矩形(10,20,20)

### 角色-女 row 411

- Source action: `强化QTE-水母3`
- Confidence: low
- Coefficients: `[{'raw': '0.29999998', 'value': 0.29999998}, {'raw': '0.29999998', 'value': 0.29999998}, {'raw': '0.29999998', 'value': 0.29999998}, {'raw': '0.29999998', 'value': 0.29999998}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 强化QTE-水母3 | =INT(0.29999998*base!$B$2)+ROUND(0.29999998*base!$B$2-INT(0.29999998*base!$B$2),0)+(1-0.29999998>=1-0.5/base!$B$2) | =INT(1*base!$B$2)+ROUND(1*base!$B$2-INT(1*base!$B$2),0)+(1-1>=1-0.5/base!$B$2) | =MAX(CEILING($AI411*(1-$AG411),1)-INT(base!$B$3<>TRUE),0) | × | √ | 11 | 地面 | 攻击顿帧 | 0.1 | =IF(base!$B$3=FALSE,INT(0.06*base!$B$2)+ROUND(0.06*base!$B$2-INT(0.06*base!$B$2),0)+(1-0.06>=1-0.5/base!$B$2),0) | 目标 | 坎特蕾拉 | (-200,90,90) | 矩形(10,20,20)

### 角色-女 row 412

- Source action: `强化QTE-水母爆炸`
- Confidence: low
- Coefficients: `[{'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.03', 'value': 0.03}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 强化QTE-水母爆炸 | =INT(0.200000002980232*base!$B$2)+ROUND(0.200000002980232*base!$B$2-INT(0.200000002980232*base!$B$2),0)+(1-0.200000002980232>=1-0.5/base!$B$2) | =MAX(CEILING($AF412*(1-$AD412),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI412*(1-$AG412),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD444A40> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD444AA0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD444B90> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD444BC0> | 11 | 地面 | 攻击顿帧 | 0.2 | =IF(base!$B$3=FALSE,INT(0.01*base!$B$2)+ROUND(0.01*base!$B$2-INT(0.01*base!$B$2),0)+(1-0.01>=1-0.5/base!$B$2),0) | 0.01 | =IF(base!$B$3=FALSE,INT(0.03*base!$B$2)+ROUND(0.03*base!$B$2-INT(0.03*base!$B$2),0)+(1-0.03>=1-0.5/base!$B$2),0) | 目标 | 水母 | 根 | 矩形(200,200,100)

### 角色-女 row 413

- Source action: `强化QTE-4`
- Confidence: low
- Coefficients: `[{'raw': '0.79999995', 'value': 0.79999995}, {'raw': '0.79999995', 'value': 0.79999995}, {'raw': '0.79999995', 'value': 0.79999995}, {'raw': '0.79999995', 'value': 0.79999995}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '0.200000002980232', 'value': 0.200000002980232}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '0.46242332', 'value': 0.46242332}, {'raw': '0.46242332', 'value': 0.46242332}, {'raw': '0.46242332', 'value': 0.46242332}, {'raw': '0.46242332', 'value': 0.46242332}, {'raw': '1.7934427', 'value': 1.7934427}, {'raw': '1.7934427', 'value': 1.7934427}, {'raw': '1.7934427', 'value': 1.7934427}, {'raw': '1.7934427', 'value': 1.7934427}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.05', 'value': 0.05}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 强化QTE-4 | =INT(0.79999995*base!$B$2)+ROUND(0.79999995*base!$B$2-INT(0.79999995*base!$B$2),0)+(1-0.79999995>=1-0.5/base!$B$2) | =INT(0.200000002980232*base!$B$2)+ROUND(0.200000002980232*base!$B$2-INT(0.200000002980232*base!$B$2),0)+(1-0.200000002980232>=1-0.5/base!$B$2) | =MAX(CEILING($AF413*(1-$AD413),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI413*(1-$AG413),1)-INT(base!$B$3<>TRUE),0) | =INT(1.3333333*base!$B$2)+ROUND(1.3333333*base!$B$2-INT(1.3333333*base!$B$2),0)+(1-1.3333333>=1-0.5/base!$B$2) | =INT(0.46242332*base!$B$2)+ROUND(0.46242332*base!$B$2-INT(0.46242332*base!$B$2),0)+(1-0.46242332>=1-0.5/base!$B$2) | =INT(1.7934427*base!$B$2)+ROUND(1.7934427*base!$B$2-INT(1.7934427*base!$B$2),0)+(1-1.7934427>=1-0.5/base!$B$2) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EBB30> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EBB60> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EB470> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EBDA0> | 11,2 | 地面 | 攻击顿帧 | 1 | =IF(base!$B$3=FALSE,INT(0.06*base!$B$2)+ROUND(0.06*base!$B$2-INT(0.06*base!$B$2),0)+(1-0.06>=1-0.5/base!$B$2),0) | 0.05 | =IF(base!$B$3=FALSE,INT(0.1*base!$B$2)+ROUND(0.1*base!$B$2-INT(0.1*base!$B$2),0)+(1-0.1>=1-0.5/base!$B$2),0) | 目标 | 坎特蕾拉 | 根 | (100,0,0) | 矩形(350,350,275)

### 角色-女 row 425

- Source action: `24`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 24 | 迷梦惊醒触发条件 | 命中后不会触发惊醒：
    大招-协同、强化A3-水母爆炸、强化QTE-水母爆炸
    探索工具伤害、队友协同伤害（不清除迷梦）
    赫卡忒子类型伤害（不清除迷梦）

命中后强制触发惊醒并重新赋予迷梦：
    E2-斑驳幻梦扩散、E3-感知汲取2、大招-C6迷梦判定

### 角色-女 row 580

- Source action: `33`
- Confidence: low
- Coefficients: `[{'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.2333332', 'value': 1.2333332}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}, {'raw': '1.3333333', 'value': 1.3333333}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 33 | QTE | ="第"&ROUNDUP(1.3*base!$B$2,0)&"F前不响应输入,第"&ROUNDUP(1.3333333*base!$B$2,0)&"F前不能切人
第"&ROUNDUP(1.2333332*base!$B$2,0)&"F触发上一角色延奏,第"&ROUNDUP(1.3*base!$B$2,0)&"F获得50点冗余动能" | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(1.3333333*base!$B$2)+ROUND(1.3333333*base!$B$2-INT(1.3333333*base!$B$2),0)+(1-1.3333333>=1-0.5/base!$B$2) | =0+10 | 0.3164 | 11 | 地面 | 时停 | 0 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =IF(base!$B$3=FALSE,INT(1.3333333*base!$B$2)+ROUND(1.3333333*base!$B$2-INT(1.3333333*base!$B$2),0)+(1-1.3333333>=1-0.5/base!$B$2),0) | 0 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =IF(base!$B$3=FALSE,INT(1.3333333*base!$B$2)+ROUND(1.3333333*base!$B$2-INT(1.3333333*base!$B$2),0)+(1-1.3333333>=1-0.5/base!$B$2),0)

### 角色-女 row 581

- Source action: `QTE-牵引`
- Confidence: low
- Coefficients: `[{'raw': '0.3297175', 'value': 0.3297175}, {'raw': '0.3297175', 'value': 0.3297175}, {'raw': '0.3297175', 'value': 0.3297175}, {'raw': '0.3297175', 'value': 0.3297175}, {'raw': '0.533334', 'value': 0.533334}, {'raw': '0.533334', 'value': 0.533334}, {'raw': '0.533334', 'value': 0.533334}, {'raw': '0.533334', 'value': 0.533334}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-牵引 | =INT(0.3297175*base!$B$2)+ROUND(0.3297175*base!$B$2-INT(0.3297175*base!$B$2),0)+(1-0.3297175>=1-0.5/base!$B$2) | =INT(0.533334*base!$B$2)+ROUND(0.533334*base!$B$2-INT(0.533334*base!$B$2),0)+(1-0.533334>=1-0.5/base!$B$2) | × | √ | 0 | 0 | 0 | 0 | 11 | 地面 | 目标 | 赞妮 | (170,0,170) | 圆柱(450,0,170)

### 角色-女 row 582

- Source action: `QTE-1`
- Confidence: low
- Coefficients: `[{'raw': '0.3297175', 'value': 0.3297175}, {'raw': '0.3297175', 'value': 0.3297175}, {'raw': '0.3297175', 'value': 0.3297175}, {'raw': '0.3297175', 'value': 0.3297175}, {'raw': '0.533334', 'value': 0.533334}, {'raw': '0.533334', 'value': 0.533334}, {'raw': '0.533334', 'value': 0.533334}, {'raw': '0.533334', 'value': 0.533334}, {'raw': '0.02', 'value': 0.02}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-1 | ="持续帧内每"&ROUNDUP(0.1*base!$B$2,0)&"F进行一次判定，最多5次" | =INT(0.3297175*base!$B$2)+ROUND(0.3297175*base!$B$2-INT(0.3297175*base!$B$2),0)+(1-0.3297175>=1-0.5/base!$B$2) | =INT(0.533334*base!$B$2)+ROUND(0.533334*base!$B$2-INT(0.533334*base!$B$2),0)+(1-0.533334>=1-0.5/base!$B$2) | =MAX(CEILING($AI582*(1-$AG582),1)-INT(base!$B$3<>TRUE),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD444290> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD444CB0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD444170> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD444560> | 11 | 地面 | 攻击顿帧 | 0.02 | =IF(base!$B$3=FALSE,INT(0.05*base!$B$2)+ROUND(0.05*base!$B$2-INT(0.05*base!$B$2),0)+(1-0.05>=1-0.5/base!$B$2),0) | 目标 | 赞妮 | (170,0,170) | 圆柱(500,0,170)

### 角色-女 row 583

- Source action: `QTE-2`
- Confidence: low
- Coefficients: `[{'raw': '1.4999999', 'value': 1.4999999}, {'raw': '1.4999999', 'value': 1.4999999}, {'raw': '1.4999999', 'value': 1.4999999}, {'raw': '1.4999999', 'value': 1.4999999}, {'raw': '1.1674445', 'value': 1.1674445}, {'raw': '1.1674445', 'value': 1.1674445}, {'raw': '1.1674445', 'value': 1.1674445}, {'raw': '1.1674445', 'value': 1.1674445}, {'raw': '1.6333332', 'value': 1.6333332}, {'raw': '1.6333332', 'value': 1.6333332}, {'raw': '1.6333332', 'value': 1.6333332}, {'raw': '1.6333332', 'value': 1.6333332}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-2 | =INT(1.3*base!$B$2)+ROUND(1.3*base!$B$2-INT(1.3*base!$B$2),0)+(1-1.3>=1-0.5/base!$B$2) | =INT(0.1*base!$B$2)+ROUND(0.1*base!$B$2-INT(0.1*base!$B$2),0)+(1-0.1>=1-0.5/base!$B$2) | =INT(1.4999999*base!$B$2)+ROUND(1.4999999*base!$B$2-INT(1.4999999*base!$B$2),0)+(1-1.4999999>=1-0.5/base!$B$2) | =INT(1.1674445*base!$B$2)+ROUND(1.1674445*base!$B$2-INT(1.1674445*base!$B$2),0)+(1-1.1674445>=1-0.5/base!$B$2) | =INT(1.6333332*base!$B$2)+ROUND(1.6333332*base!$B$2-INT(1.6333332*base!$B$2),0)+(1-1.6333332>=1-0.5/base!$B$2) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD2CE6C0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD2CE8D0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD2CF680> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD2CF740> | =0+50 | 11,5,2 | 地面 | 目标 | 赞妮 | 根 | (280,0,150) | 圆柱(600,0,150)

### 角色-女 row 592

- Source action: `36`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 36 | 延奏-伤害 | 命中后清空目标烈阳余烬 | =INT(0.1*base!$B$2)+ROUND(0.1*base!$B$2-INT(0.1*base!$B$2),0)+(1-0.1>=1-0.5/base!$B$2) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3329C0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD378A40> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD379310> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD378710> | 1 | 11 | 地面 | 目标 | 目标 | (-1000,0,0) | (1000,0,0) | 矩形(300,175,175)

### 角色-女 row 596

- Source action: `38`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '6秒', 'seconds': 6.0}]`
- 15s state notes: `[]`
- Raw row: 38 | 烈阳余烬-被动 | 烈阳余烬最多存在60层，每层持续6秒
每层烈阳余烬可使目标受到 延奏-伤害 造成的伤害提高10%
转换烈阳余烬等同于赋予光噪效应，可触发光噪赋予触发器
10层可触发此间永驻之光效果2，该触发与光噪效应触发相互独立

监听光噪效应赋予层数触发器：
·无法实现光噪赋予效果，光噪赋予触发器不受影响
·光噪效应上限10层，溢出赋予层数正常计入监听
·每赋予一层光噪效应获得5点焰光1
·每次赋予光噪效应时，立即结算赋予后已有层数光噪伤害，并赋予等量应赋予层数的烈阳余烬 | =INT(6*base!$B$2)+ROUND(6*base!$B$2-INT(6*base!$B$2),0)+(1-6>=1-0.5/base!$B$2) | 5

### 角色-女 row 663

- Source action: `19`
- Confidence: low
- Coefficients: `[{'raw': '1.1333333', 'value': 1.1333333}, {'raw': '0.93333334', 'value': 0.93333334}, {'raw': '1.0333333', 'value': 1.0333333}, {'raw': '1.0333333', 'value': 1.0333333}, {'raw': '1.0333333', 'value': 1.0333333}, {'raw': '1.0333333', 'value': 1.0333333}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.26666668', 'value': 0.26666668}, {'raw': '0.26666668', 'value': 0.26666668}, {'raw': '0.26666668', 'value': 0.26666668}, {'raw': '0.26666668', 'value': 0.26666668}, {'raw': '0.26666668', 'value': 0.26666668}, {'raw': '0.26666668', 'value': 0.26666668}, {'raw': '0.26666668', 'value': 0.26666668}, {'raw': '0.26666668', 'value': 0.26666668}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 19 | QTE | ="第"&ROUNDUP(1.1333333*base!$B$2,0)&"F前不响应输入、不能切人
第"&ROUNDUP(0.93333334*base!$B$2,0)&"F触发上一角色延奏
第"&ROUND(0*base!$B$2,0)+1&"F获得100点战势、20点权柄" | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(1.0333333*base!$B$2)+ROUND(1.0333333*base!$B$2-INT(1.0333333*base!$B$2),0)+(1-1.0333333>=1-0.5/base!$B$2) | =0+10 | =base!$ER$80/base!$ER$80*100 | =0+20 | 0.3164 | 11 | 地面 | 时停 | 0 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(0.26666668*base!$B$2)+ROUND(0.26666668*base!$B$2-INT(0.26666668*base!$B$2),0)+(1-0.26666668>=1-0.5/base!$B$2) | 0 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(0.26666668*base!$B$2)+ROUND(0.26666668*base!$B$2-INT(0.26666668*base!$B$2),0)+(1-0.26666668>=1-0.5/base!$B$2)

### 角色-女 row 664

- Source action: `QTE-顿帧`
- Confidence: low
- Coefficients: `[{'raw': '0.01', 'value': 0.01}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-顿帧 | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(1.2*base!$B$2)+ROUND(1.2*base!$B$2-INT(1.2*base!$B$2),0)+(1-1.2>=1-0.5/base!$B$2) | =MAX(CEILING($AI664*(1-$AG664),1)-INT(base!$B$3<>TRUE),0) | × | × | 11 | 地面 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,INT(1.8*base!$B$2)+ROUND(1.8*base!$B$2-INT(1.8*base!$B$2),0)+(1-1.8>=1-0.5/base!$B$2),0) | 目标 | 奥古斯塔 | 根 | (0,0,300) | 圆柱(450,0,500)

### 角色-女 row 665

- Source action: `QTE-1`
- Confidence: medium
- Coefficients: `[{'raw': '0.76666665', 'value': 0.76666665}, {'raw': '0.76666665', 'value': 0.76666665}, {'raw': '0.76666665', 'value': 0.76666665}, {'raw': '0.76666665', 'value': 0.76666665}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}]`
- Frame candidates: `[{'raw': '5F', 'frames': 5.0, 'seconds_at_60fps': 0.0833}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-1 | =INT(0.76666665*base!$B$2)+ROUND(0.76666665*base!$B$2-INT(0.76666665*base!$B$2),0)+(1-0.76666665>=1-0.5/base!$B$2) | =INT(0.2*base!$B$2)+ROUND(0.2*base!$B$2-INT(0.2*base!$B$2),0)+(1-0.2>=1-0.5/base!$B$2) | =MAX(CEILING($AF665*(1-$AD665),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI665*(1-$AG665),1)-INT(base!$B$3<>TRUE),0) | √ | × | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BC5F0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BF6E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BE570> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BFA10> | 11 | 地面 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,INT(0.05*base!$B$2)+ROUND(0.05*base!$B$2-INT(0.05*base!$B$2),0)+(1-0.05>=1-0.5/base!$B$2),0) | 0.01 | =IF(base!$B$3=FALSE,INT(0.05*base!$B$2)+ROUND(0.05*base!$B$2-INT(0.05*base!$B$2),0)+(1-0.05>=1-0.5/base!$B$2),0) | 目标 | 奥古斯塔 | 根 | (0,0,200) | 圆柱(450,0,500)

### 角色-女 row 666

- Source action: `QTE-2`
- Confidence: low
- Coefficients: `[{'raw': '1.1333333', 'value': 1.1333333}, {'raw': '1.1333333', 'value': 1.1333333}, {'raw': '1.1333333', 'value': 1.1333333}, {'raw': '1.1333333', 'value': 1.1333333}, {'raw': '0.25883907', 'value': 0.25883907}, {'raw': '0.25883907', 'value': 0.25883907}, {'raw': '0.25883907', 'value': 0.25883907}, {'raw': '0.25883907', 'value': 0.25883907}, {'raw': '1.3829285', 'value': 1.3829285}, {'raw': '1.3829285', 'value': 1.3829285}, {'raw': '1.3829285', 'value': 1.3829285}, {'raw': '1.3829285', 'value': 1.3829285}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-2 | =INT(1*base!$B$2)+ROUND(1*base!$B$2-INT(1*base!$B$2),0)+(1-1>=1-0.5/base!$B$2) | =INT(0.2*base!$B$2)+ROUND(0.2*base!$B$2-INT(0.2*base!$B$2),0)+(1-0.2>=1-0.5/base!$B$2) | =MAX(CEILING($AF666*(1-$AD666),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI666*(1-$AG666),1)-INT(base!$B$3<>TRUE),0) | =INT(1.1333333*base!$B$2)+ROUND(1.1333333*base!$B$2-INT(1.1333333*base!$B$2),0)+(1-1.1333333>=1-0.5/base!$B$2) | =INT(0.25883907*base!$B$2)+ROUND(0.25883907*base!$B$2-INT(0.25883907*base!$B$2),0)+(1-0.25883907>=1-0.5/base!$B$2) | =INT(1.3829285*base!$B$2)+ROUND(1.3829285*base!$B$2-INT(1.3829285*base!$B$2),0)+(1-1.3829285>=1-0.5/base!$B$2) | √ | × | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BC590> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BF6B0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BF950> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3BC3B0> | 11,2 | 地面 | 攻击顿帧 | 0.01 | =IF(base!$B$3=FALSE,INT(0.05*base!$B$2)+ROUND(0.05*base!$B$2-INT(0.05*base!$B$2),0)+(1-0.05>=1-0.5/base!$B$2),0) | 0.01 | =IF(base!$B$3=FALSE,INT(0.05*base!$B$2)+ROUND(0.05*base!$B$2-INT(0.05*base!$B$2),0)+(1-0.05>=1-0.5/base!$B$2),0) | 目标 | 奥古斯塔 | 根 | (0,0,200) | 圆柱(450,0,500)

### 角色-女 row 674

- Source action: `21`
- Confidence: medium
- Coefficients: `[{'raw': '2.1666667', 'value': 2.1666667}, {'raw': '2.966667', 'value': 2.966667}, {'raw': '2.966667', 'value': 2.966667}, {'raw': '2.966667', 'value': 2.966667}, {'raw': '2.966667', 'value': 2.966667}]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '30秒', 'seconds': 30.0}, {'raw': '10秒', 'seconds': 10.0}]`
- 15s state notes: `[]`
- Raw row: 21 | 大招-前置 | ="清空大招A计数
第"&ROUNDUP(2.1666667*base!$B$2,0)&"F前不响应输入，大招状态期间不能切人、不会被命中
第"&ROUNDUP(0*base!$B$2,0)+1&"F全队获得30秒界域状态，期间监听各角色自身QTE施放
第"&ROUNDUP(0*base!$B$2,0)+1&"F获得10秒大招状态，状态持续时间仅跟随角色动作时间
大招状态结束后自动施放强化大招" | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(2.966667*base!$B$2)+ROUND(2.966667*base!$B$2-INT(2.966667*base!$B$2),0)+(1-2.966667>=1-0.5/base!$B$2) | =0+20 | 0 | 10 | 地面

### 角色-女 row 700

- Source action: `26`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '14秒', 'seconds': 14.0}, {'raw': '14秒', 'seconds': 14.0}]`
- 15s state notes: `[]`
- Raw row: 26 | 延奏 | 下一登场角色获得：
·0类通用伤害加深，持续14秒，非前台状态移除该效果
·奥古斯塔监听该角色14秒内是否通过QTE切换下一角色
  成功触发监听时，奥古斯塔获得1层威慑、1层众愿
  非前台状态移除该效果 | 1 | 11 | 地面

### 角色-女 row 705

- Source action: `27`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '10秒', 'seconds': 10.0}]`
- 15s state notes: `[]`
- Raw row: 27 | 界域状态 | 编队效果，全队生效
·期间角色施放变奏后，获得1层护盾，持续10秒，切人不继承。
  重复获得可覆盖护盾并刷新持续时间，不可叠加。 | =INT(30*base!$B$2)+ROUND(30*base!$B$2-INT(30*base!$B$2),0)+(1-30>=1-0.5/base!$B$2)

### 角色-女 row 722

- Source action: `28`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 28 | 特殊能量 | ="核心回收1：战势
核心回收2：权柄

战势：文本上限100点，效果实现上限650点
权柄：文本上限100点，效果实现上限5000点

各技能动作施放或命中后基于文本的能量获取值：

 施放 重击后撤 后， 战势-100
 施放 重击升龙 后， 战势-100
 施放 E1-斩锋  后， 权柄+10
 施放 E4-落袭  后， 权柄-100
 施放 QTE      后， 战势+100,权柄+20
 施放 誓锋不陨 后， 权柄+40

  动作             战势            权柄"&"
 A1               "&ROUND(dmg!$BE$1853/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1853/base!$ES$80*100,2)&"
 A2-1             "&ROUND(dmg!$BE$1854/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1854/base!$ES$80*100,2)&"
 A2-2             "&ROUND(dmg!$BE$1855/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1855/base!$ES$80*100,2)&"
 A2-1D            "&ROUND(dmg!$BE$1856/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1856/base!$ES$80*100,2)&"
 A2-2D            "&ROUND(dmg!$BE$1857/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1857/base!$ES$80*100,2)&"
 A3-1             "&ROUND(dmg!$BE$1858/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1858/base!$ES$80*100,2)&"
 A3-2             "&ROUND(dmg!$BE$1859/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1859/base!$ES$80*100,2)&"
 A3-3             "&ROUND(dmg!$BE$1860/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1860/base!$ES$80*100,2)&"
 A4-1             "&ROUND(dmg!$BE$1861/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1861/base!$ES$80*100,2)&"
 A4-2             "&ROUND(dmg!$BE$1862/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1862/base!$ES$80*100,2)&"
 A4-3             "&ROUND(dmg!$BE$1863/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1863/base!$ES$80*100,2)&"
 重击-1           "&ROUND(dmg!$BE$1864/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1864/base!$ES$80*100,2)&"
 重击-2           "&ROUND(dmg!$BE$1865/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1865/base!$ES$80*100,2)&"
 重击-1D          "&ROUND(dmg!$BE$1866/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1866/base!$ES$80*100,2)&"
 重击-2D          "&ROUND(dmg!$BE$1867/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1867/base!$ES$80*100,2)&"
 重击后撤         "&ROUND(dmg!$BE$1868/base!$ER$80*100,2)&"                "&ROUND(dmg!$BF$1868/base!$ES$80*100,2)&"
 重击后撤D        "&ROUND(dmg!$BE$1870/base!$ER$80*100,2)&"                "&ROUND(dmg!$BF$1870/base!$ES$80*100,2)&"
 重击旋切-1       "&ROUND(dmg!$BE$1874/base!$ER$80*100,2)&"                "&ROUND(dmg!$BF$1874/base!$ES$80*100,2)&"
 重击旋切-2       "&ROUND(dmg!$BE$1875/base!$ER$80*100,2)&"                "&ROUND(dmg!$BF$1875/base!$ES$80*100,2)&"
 重击升龙-1       "&ROUND(dmg!$BE$1879/base!$ER$80*100,2)&"                "&ROUND(dmg!$BF$1879/base!$ES$80*100,2)&"
 重击升龙-2       "&ROUND(dmg!$BE$1880/base!$ER$80*100,2)&"                "&ROUND(dmg!$BF$1880/base!$ES$80*100,2)&"
 空中攻击-下落    "&ROUND(dmg!$BE$1884/base!$ER$80*100,2)&"             "&ROUND(dmg!$BF$1884/base!$ES$80*100,2)&"
 空中攻击-落地    "&ROUND(dmg!$BE$1885/base!$ER$80*100,2)&"             "&ROUND(dmg!$BF$1885/base!$ES$80*100,2)&"
 空中攻击-下落D   "&ROUND(dmg!$BE$1886/base!$ER$80*100,2)&"             "&ROUND(dmg!$BF$1886/base!$ES$80*100,2)&"
 空中攻击-落地D   "&ROUND(dmg!$BE$1887/base!$ER$80*100,2)&"             "&ROUND(dmg!$BF$1887/base!$ES$80*100,2)&"
 E1-斩锋1         "&ROUND(dmg!$BE$1888/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1888/base!$ES$80*100,2)&"
 E1-斩锋2         "&ROUND(dmg!$BE$1889/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1889/base!$ES$80*100,2)&"
 E1-斩锋3         "&ROUND(dmg!$BE$1890/base!$ER$80*100,2)&"            "&ROUND(dmg!$BF$1890/base!$ES$80*100,2)&"
"

### 角色-女 row 830

- Source action: `23`
- Confidence: low
- Coefficients: `[{'raw': '0.5366425', 'value': 0.5366425}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.7132551', 'value': 0.7132551}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.48207822', 'value': 0.48207822}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '1.0299997', 'value': 1.0299997}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '1.0299997', 'value': 1.0299997}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '1.0299997', 'value': 1.0299997}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '1.0299997', 'value': 1.0299997}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.4019824', 'value': 0.4019824}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.4019824', 'value': 0.4019824}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.4019824', 'value': 0.4019824}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.4019824', 'value': 0.4019824}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.4019824', 'value': 0.4019824}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.4019824', 'value': 0.4019824}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.4019824', 'value': 0.4019824}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.4019824', 'value': 0.4019824}, {'raw': '0.12667334', 'value': 0.12667334}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 23 | QTE | ="第"&ROUND((0.5366425+0.12667334*1.5)*base!$B$2,0)&"F前不响应输入，第"&ROUND((0.7132551+0.12667334*1.5)*base!$B$2,0)&"F前不能切人
第"&ROUND((0.48207822+0.12667334*1.5)*base!$B$2,0)&"F触发上一角色延奏" | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT((1.0299997+0.12667334*1.5)*base!$B$2)+ROUND((1.0299997+0.12667334*1.5)*base!$B$2-INT((1.0299997+0.12667334*1.5)*base!$B$2),0)+(1-(1.0299997+0.12667334*1.5)>=1-0.5/base!$B$2) | =0+10 | 0.3164 | 11 | 地面 | 时停 | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =INT((0.4019824+0.12667334*1.5)*base!$B$2)+ROUND((0.4019824+0.12667334*1.5)*base!$B$2-INT((0.4019824+0.12667334*1.5)*base!$B$2),0)+(1-(0.4019824+0.12667334*1.5)>=1-0.5/base!$B$2) | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =INT((0.4019824+0.12667334*1.5)*base!$B$2)+ROUND((0.4019824+0.12667334*1.5)*base!$B$2-INT((0.4019824+0.12667334*1.5)*base!$B$2),0)+(1-(0.4019824+0.12667334*1.5)>=1-0.5/base!$B$2)

### 角色-女 row 831

- Source action: `QTE-伤害`
- Confidence: low
- Coefficients: `[{'raw': '0.47266334', 'value': 0.47266334}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.47266334', 'value': 0.47266334}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.47266334', 'value': 0.47266334}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.47266334', 'value': 0.47266334}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.5347166', 'value': 0.5347166}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.5347166', 'value': 0.5347166}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.5347166', 'value': 0.5347166}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.5347166', 'value': 0.5347166}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '1.0998964', 'value': 1.0998964}, {'raw': '1.0998964', 'value': 1.0998964}, {'raw': '1.0998964', 'value': 1.0998964}, {'raw': '1.0998964', 'value': 1.0998964}, {'raw': '1.0199997', 'value': 1.0199997}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '1.0199997', 'value': 1.0199997}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '1.0199997', 'value': 1.0199997}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '1.0199997', 'value': 1.0199997}, {'raw': '0.12667334', 'value': 0.12667334}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-伤害 | =INT((0.47266334+0.12667334*1.5)*base!$B$2)+ROUND((0.47266334+0.12667334*1.5)*base!$B$2-INT((0.47266334+0.12667334*1.5)*base!$B$2),0)+(1-(0.47266334+0.12667334*1.5)>=1-0.5/base!$B$2) | =INT(0.3*base!$B$2)+ROUND(0.3*base!$B$2-INT(0.3*base!$B$2),0)+(1-0.3>=1-0.5/base!$B$2) | =MAX(CEILING($AF831*(1-$AD831),1)-INT(base!$B$3<>TRUE),0) | =INT((0.5347166+0.12667334*1.5)*base!$B$2)+ROUND((0.5347166+0.12667334*1.5)*base!$B$2-INT((0.5347166+0.12667334*1.5)*base!$B$2),0)+(1-(0.5347166+0.12667334*1.5)>=1-0.5/base!$B$2) | =INT(1.0998964*base!$B$2)+ROUND(1.0998964*base!$B$2-INT(1.0998964*base!$B$2),0)+(1-1.0998964>=1-0.5/base!$B$2) | =INT((1.0199997+0.12667334*1.5)*base!$B$2)+ROUND((1.0199997+0.12667334*1.5)*base!$B$2-INT((1.0199997+0.12667334*1.5)*base!$B$2),0)+(1-(1.0199997+0.12667334*1.5)>=1-0.5/base!$B$2) | √ | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3D38A40> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3D3B050> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3D3B350> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3D3AF90> | 10 | 11,2 | 地面 | 攻击顿帧 | 0.2 | =INT(0.1*base!$B$2)+ROUND(0.1*base!$B$2-INT(0.1*base!$B$2),0)+(1-0.1>=1-0.5/base!$B$2) | 1 | =INT(0.033*base!$B$2)+ROUND(0.033*base!$B$2-INT(0.033*base!$B$2),0)+(1-0.033>=1-0.5/base!$B$2) | 目标 | 嘉贝莉娜 | (320,0,200) | 矩形(380,300,200)

### 角色-女 row 840

- Source action: `26`
- Confidence: low
- Coefficients: `[{'raw': '0.15', 'value': 0.15}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.067', 'value': 0.067}, {'raw': '0.067', 'value': 0.067}, {'raw': '0.067', 'value': 0.067}, {'raw': '0.067', 'value': 0.067}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 26 | 延奏-1 | ="持续帧内每"&ROUNDUP(0.15*base!$B$2,0)&"F进行一次判定，最多3次" | =INT(0*base!$B$2)+ROUND(0*base!$B$2-INT(0*base!$B$2),0)+(1-0>=1-0.5/base!$B$2) | =INT(0.6*base!$B$2)+ROUND(0.6*base!$B$2-INT(0.6*base!$B$2),0)+(1-0.6>=1-0.5/base!$B$2) | =MAX(CEILING($AI840*(1-$AG840),1)-INT(base!$B$3<>TRUE),0) | √ | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD302A20> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD301460> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD303D40> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD300740> | 1 | 11 | 地面 | 攻击顿帧 | 0.05 | =INT(0.067*base!$B$2)+ROUND(0.067*base!$B$2-INT(0.067*base!$B$2),0)+(1-0.067>=1-0.5/base!$B$2) | 目标 | 目标 | 圆柱(600,0,200)

### 角色-女 row 841

- Source action: `延奏-2`
- Confidence: medium
- Coefficients: `[{'raw': '0.55', 'value': 0.55}, {'raw': '0.55', 'value': 0.55}, {'raw': '0.55', 'value': 0.55}, {'raw': '0.55', 'value': 0.55}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}, {'raw': '0.033', 'value': 0.033}]`
- Frame candidates: `[{'raw': '9F', 'frames': 9.0, 'seconds_at_60fps': 0.15}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 延奏-2 | 圆柱(600,0,200) | =INT(0.55*base!$B$2)+ROUND(0.55*base!$B$2-INT(0.55*base!$B$2),0)+(1-0.55>=1-0.5/base!$B$2) | =INT(0.2*base!$B$2)+ROUND(0.2*base!$B$2-INT(0.2*base!$B$2),0)+(1-0.2>=1-0.5/base!$B$2) | =MAX(CEILING($AF841*(1-$AD841),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI841*(1-$AG841),1)-INT(base!$B$3<>TRUE),0) | √ | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E9280> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EA1E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3EA270> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3E9F40> | 11 | 地面 | 攻击顿帧 | 0.05 | =INT(0.033*base!$B$2)+ROUND(0.033*base!$B$2-INT(0.033*base!$B$2),0)+(1-0.033>=1-0.5/base!$B$2) | 0.05 | =INT(0.033*base!$B$2)+ROUND(0.033*base!$B$2-INT(0.033*base!$B$2),0)+(1-0.033>=1-0.5/base!$B$2) | 目标 | =C840 | 圆柱(600,0,200)

### 角色-女 row 845

- Source action: `28`
- Confidence: medium
- Coefficients: `[{'raw': '90%', 'value': 0.9}]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '50秒', 'seconds': 50.0}, {'raw': '0.1秒', 'seconds': 0.1}, {'raw': '4秒', 'seconds': 4.0}]`
- 15s state notes: `[]`
- Raw row: 28 | 特殊能量 | 能量获取：
·罪火获取上限100点，仅通过常态攻击命中获取
·净炼火上限100点，仅由罪火等量转化获取
·余火获取上限40点
  不处于恶魔位格时，监听全队不同名声骸技能施放，每次触发监听获取8点余火
·通过任意方式移除恶魔位格时，清空净炼火、余火，重置不同名声骸监听次数

恶魔位格：
·罪火获取达到上限后，施放E3-恶翼扬升可获得50秒恶魔位格
·每1点余火使 恶魔A、恶魔重击、恶魔空中攻击、E2 造成的伤害提升1.5%，该提升作用于目标减伤区
·期间攻击命中消耗净炼火，全部消耗后第0.1秒移除恶魔位格

内燃烧：
·施放 恶魔A4、E1、E2、E3、QTE、地狱穿行 后，4秒内攻击力加成提升20%/90%、受击削韧减免25%

### 角色-女 row 863

- Source action: `30`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '5.5秒', 'seconds': 5.5}, {'raw': '5秒', 'seconds': 5.0}]`
- 15s state notes: `[]`
- Raw row: 30 | 被动技能 | 被动1：
·各分类技能命中后，赋予目标1层受到嘉贝莉娜延奏和分类技能造成的伤害加深Buff，每层持续5.5秒，可叠加4层，持续时间结束后清空层数，重复赋予刷新持续时间。
·每次赋予目标Buff后，5秒内该目标不可被同分类技能再次赋予Buff，每个分类独立计算冷却时间。

该技能分类仅适用于被动1：

    1  |  A1、A2、A3、A4
    2  |  恶魔A1、恶魔A2、恶魔A3、恶魔A4、恶魔A5
    3  |  重击1、重击2、重击3
    4  |  恶魔重击1、恶魔重击2、恶魔重击3
    5  |  A3-D、恶魔A3-D
    6  |  空中攻击、恶魔空中攻击
    7  |  E1-迫近、E2-掠袭
    8  |  E3-恶翼扬升
    9  |  地狱穿行
    10 |  QTE
    11 |  大招

### 角色-女 row 967

- Source action: `25`
- Confidence: low
- Coefficients: `[{'raw': '0.49999997', 'value': 0.49999997}, {'raw': '0.49999997', 'value': 0.49999997}, {'raw': '0.3164', 'value': 0.3164}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 25 | QTE | ="无敌期间不能切人，第"&ROUND(0.49999997*base!$B$2+(0.49999997*base!$B$2<=base!$C$2),0)&"F触发上一角色延奏" | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(1*base!$B$2+(1*base!$B$2<=base!$C$2),0) | =0+10 | =0+100+100 | 0.3164 | 11 | 地面 | 时停 | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(0.8*base!$B$2+(0.8*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(0.8*base!$B$2+(0.8*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE)

### 角色-女 row 968

- Source action: `QTE-箭矢`
- Confidence: low
- Coefficients: `[{'raw': '0.6333333', 'value': 0.6333333}, {'raw': '0.6333333', 'value': 0.6333333}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-箭矢 | 碰撞或持续帧结束后生成伤害 | =ROUND(0.6333333*base!$B$2+(0.6333333*base!$B$2<=base!$C$2),0) | =ROUND(0.2*base!$B$2+(0.2*base!$B$2<=base!$C$2),0) | × | √ | 11 | 地面 | 目标 | 绯雪 | (50,0,110) | 矩形(50,50,50)

### 角色-女 row 969

- Source action: `QTE-伤害`
- Confidence: low
- Coefficients: `[{'raw': '0.8333329', 'value': 0.8333329}, {'raw': '0.8333329', 'value': 0.8333329}, {'raw': '1.4999999', 'value': 1.4999999}, {'raw': '1.4999999', 'value': 1.4999999}, {'raw': '0.08', 'value': 0.08}, {'raw': '0.08', 'value': 0.08}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.134', 'value': 0.134}, {'raw': '0.134', 'value': 0.134}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-伤害 | 命中后赋予目标1层霜渐效应 | =ROUND(0.2*base!$B$2+(0.2*base!$B$2<=base!$C$2),0) | =MAX(CEILING($AF969*(1-$AD969),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI969*(1-$AG969),1)-INT(base!$B$3<>TRUE),0) | =ROUND(1*base!$B$2+(1*base!$B$2<=base!$C$2),0) | =ROUND(1*base!$B$2+(1*base!$B$2<=base!$C$2),0) | =ROUND(0.8333329*base!$B$2+(0.8333329*base!$B$2<=base!$C$2),0) | =ROUND(1.4999999*base!$B$2+(1.4999999*base!$B$2<=base!$C$2),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF992C30> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF993170> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF990E30> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF991970> | 11,1 | 地面 | 攻击顿帧 | 0.1 | =ROUND(0.08*base!$B$2+(0.08*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0.01 | =ROUND(0.134*base!$B$2+(0.134*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 目标 | =C968 | 球形(500,0,0)

### 角色-女 row 970

- Source action: `26`
- Confidence: low
- Coefficients: `[{'raw': '0.3164', 'value': 0.3164}, {'raw': '0.7676781', 'value': 0.7676781}, {'raw': '0.7676781', 'value': 0.7676781}, {'raw': '0.7676781', 'value': 0.7676781}, {'raw': '0.7676781', 'value': 0.7676781}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 26 | 预求QTE | ="无敌期间不能切人，第"&ROUND(0.5*base!$B$2+(0.5*base!$B$2<=base!$C$2),0)&"F触发上一角色延奏。可派生居合架势" | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(1*base!$B$2+(1*base!$B$2<=base!$C$2),0) | =0+10 | 0.3164 | 11 | 地面 | 时停 | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(0.7676781*base!$B$2+(0.7676781*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(0.7676781*base!$B$2+(0.7676781*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE)

### 角色-女 row 971

- Source action: `预求QTE-箭矢`
- Confidence: low
- Coefficients: `[{'raw': '0.6333334', 'value': 0.6333334}, {'raw': '0.6333334', 'value': 0.6333334}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 预求QTE-箭矢 | 碰撞或持续帧结束后生成伤害 | =ROUND(0.6333334*base!$B$2+(0.6333334*base!$B$2<=base!$C$2),0) | =ROUND(0.2*base!$B$2+(0.2*base!$B$2<=base!$C$2),0) | × | √ | 11 | 地面 | 目标 | 绯雪 | (50,0,200) | 矩形(50,50,50)

### 角色-女 row 972

- Source action: `预求QTE-伤害`
- Confidence: low
- Coefficients: `[{'raw': '0.8333329', 'value': 0.8333329}, {'raw': '0.8333329', 'value': 0.8333329}, {'raw': '1.5000001', 'value': 1.5000001}, {'raw': '1.5000001', 'value': 1.5000001}, {'raw': '0.08', 'value': 0.08}, {'raw': '0.08', 'value': 0.08}, {'raw': '0.01', 'value': 0.01}, {'raw': '0.134', 'value': 0.134}, {'raw': '0.134', 'value': 0.134}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 预求QTE-伤害 | 命中后赋予目标1层霜渐效应 | =ROUND(0.2*base!$B$2+(0.2*base!$B$2<=base!$C$2),0) | =MAX(CEILING($AF972*(1-$AD972),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI972*(1-$AG972),1)-INT(base!$B$3<>TRUE),0) | =ROUND(1*base!$B$2+(1*base!$B$2<=base!$C$2),0) | =ROUND(1*base!$B$2+(1*base!$B$2<=base!$C$2),0) | =ROUND(0.8333329*base!$B$2+(0.8333329*base!$B$2<=base!$C$2),0) | =ROUND(1.5000001*base!$B$2+(1.5000001*base!$B$2<=base!$C$2),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8D64E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8D4230> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BA925D00> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD301700> | 11,1 | 地面 | 攻击顿帧 | 0.1 | =ROUND(0.08*base!$B$2+(0.08*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0.01 | =ROUND(0.134*base!$B$2+(0.134*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 目标 | =C971 | 球形(500,0,0)

### 角色-女 row 994

- Source action: `32`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 32 | 特殊能量 | 心念：
上限300点
·不处于预求身状态时，施放 A3 后，获得100点；
·不处于预求身状态时，施放 QTE 后，获得200点；
·施放 E-常世身 后获得效果【A3 BUFF】，持有该效果时施放 A3 后，额外获得100点；
·施放 重击、大招拔刀、大招归刃 后，清空心念
·心念达到上限时，解锁 重击

寒意：
上限300点
·预求A、预求空中A、预求重击 命中后可获得；
·施放 预求E 后，获得75点；
·施放 大招拔刀 后，获得50点；
·施放 大招归刃 后，清空寒意；
·寒意达到100点后，解锁 居合架势；
  施放 居合 后，减少100点

### 角色-女 row 1066

- Source action: `强化A4-断舍离2`
- Confidence: very_low
- Coefficients: `[{'raw': '2.4999998', 'value': 2.4999998}, {'raw': '2.4999998', 'value': 2.4999998}, {'raw': '0.90684396', 'value': 0.90684396}, {'raw': '0.90684396', 'value': 0.90684396}, {'raw': '0.96745384', 'value': 0.96745384}, {'raw': '0.96745384', 'value': 0.96745384}, {'raw': '1.6227297', 'value': 1.6227297}, {'raw': '1.6227297', 'value': 1.6227297}, {'raw': '1.1999999', 'value': 1.1999999}, {'raw': '1.1999999', 'value': 1.1999999}, {'raw': '0.01', 'value': 0.01}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 强化A4-断舍离2 | ="第"&ROUND(0.9*base!$B$2+(0.9*base!$B$2<=base!$C$2),0)&"F获得20点协奏能量，第"&ROUND(2.4999998*base!$B$2+(2.4999998*base!$B$2<=base!$C$2),0)&"F或结束技能后清空C6铭记层数" | =ROUND(0.90684396*base!$B$2+(0.90684396*base!$B$2<=base!$C$2),0) | =ROUND(0.2*base!$B$2+(0.2*base!$B$2<=base!$C$2),0) | =MAX(CEILING($AF1066*(1-$AD1066),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI1066*(1-$AG1066),1)-INT(base!$B$3<>TRUE),0) | =ROUND(0.96745384*base!$B$2+(0.96745384*base!$B$2<=base!$C$2),0) | =ROUND(1.6227297*base!$B$2+(1.6227297*base!$B$2<=base!$C$2),0) | =ROUND(1.1999999*base!$B$2+(1.1999999*base!$B$2<=base!$C$2),0) | √ | × | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD303770> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD302990> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD303650> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD300E90> | 4 | 地面 | 攻击顿帧 | 0.5 | =ROUND(0.2*base!$B$2+(0.2*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0.01 | =ROUND(0.3*base!$B$2+(0.3*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 目标 | 洛瑟菈 | (950,0,500) | 圆柱(1000,0,500)

### 角色-女 row 1078

- Source action: `15`
- Confidence: very_low
- Coefficients: `[{'raw': '0.8930398', 'value': 0.8930398}, {'raw': '0.8930398', 'value': 0.8930398}, {'raw': '0.178', 'value': 0.178}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 15 | E-追光 | ="判定成功。第"&ROUND(0.8930398*base!$B$2+(0.8930398*base!$B$2<=base!$C$2),0)&"F获得50点印象、20点协奏能量" | =0+20 | =0+50 | 0.178 | 5 | 地面

### 角色-女 row 1083

- Source action: `16`
- Confidence: low
- Coefficients: `[{'raw': '0.48631907', 'value': 0.48631907}, {'raw': '0.48631907', 'value': 0.48631907}, {'raw': '1.3554819', 'value': 1.3554819}, {'raw': '1.3554819', 'value': 1.3554819}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '1.3493285', 'value': 1.3493285}, {'raw': '1.3493285', 'value': 1.3493285}, {'raw': '1.3493285', 'value': 1.3493285}, {'raw': '1.3493285', 'value': 1.3493285}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 16 | QTE | ="无敌期间不能切人，第"&ROUND(0.48631907*base!$B$2+(0.48631907*base!$B$2<=base!$C$2),0)&"F触发上一角色延奏" | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(1.3554819*base!$B$2+(1.3554819*base!$B$2<=base!$C$2),0) | =0+10 | 0.3164 | 11 | 地面 | 时停 | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(1.3493285*base!$B$2+(1.3493285*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(1.3493285*base!$B$2+(1.3493285*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE)

### 角色-女 row 1084

- Source action: `QTE-伤害`
- Confidence: medium
- Coefficients: `[{'raw': '0.6342424', 'value': 0.6342424}, {'raw': '0.6342424', 'value': 0.6342424}, {'raw': '1.3558708', 'value': 1.3558708}, {'raw': '1.3558708', 'value': 1.3558708}, {'raw': '1.5000001', 'value': 1.5000001}, {'raw': '1.5000001', 'value': 1.5000001}, {'raw': '1.3585584', 'value': 1.3585584}, {'raw': '1.3585584', 'value': 1.3585584}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.05', 'value': 0.05}]`
- Frame candidates: `[{'raw': '8F', 'frames': 8.0, 'seconds_at_60fps': 0.1333}, {'raw': '8F', 'frames': 8.0, 'seconds_at_60fps': 0.1333}, {'raw': '8F', 'frames': 8.0, 'seconds_at_60fps': 0.1333}, {'raw': '8F', 'frames': 8.0, 'seconds_at_60fps': 0.1333}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-伤害 | 命中后赋予目标1层霜渐效应 | =ROUND(0.6342424*base!$B$2+(0.6342424*base!$B$2<=base!$C$2),0) | =ROUND(0.3*base!$B$2+(0.3*base!$B$2<=base!$C$2),0) | =MAX(CEILING($AI1084*(1-$AG1084),1)-INT(base!$B$3<>TRUE),0) | =ROUND(0.7*base!$B$2+(0.7*base!$B$2<=base!$C$2),0) | =ROUND(1.3558708*base!$B$2+(1.3558708*base!$B$2<=base!$C$2),0) | =ROUND(1.5000001*base!$B$2+(1.5000001*base!$B$2<=base!$C$2),0) | =ROUND(1.3585584*base!$B$2+(1.3585584*base!$B$2<=base!$C$2),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8F1850> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8F19A0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8F0140> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8F1A90> | =0+100 | 11,4 | 地面 | 攻击顿帧 | 0.3 | =ROUND(0.05*base!$B$2+(0.05*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 目标 | 目标 | 球形(400,0,0)

### 角色-女 row 1085

- Source action: `17`
- Confidence: low
- Coefficients: `[{'raw': '0.07851261', 'value': 0.07851261}, {'raw': '0.07851261', 'value': 0.07851261}, {'raw': '0.86997485', 'value': 0.86997485}, {'raw': '0.86997485', 'value': 0.86997485}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.86997485', 'value': 0.86997485}, {'raw': '0.86997485', 'value': 0.86997485}, {'raw': '0.86997485', 'value': 0.86997485}, {'raw': '0.86997485', 'value': 0.86997485}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 17 | 强化QTE | ="无敌期间不能切人，第"&ROUND(0.07851261*base!$B$2+(0.07851261*base!$B$2<=base!$C$2),0)&"F触发上一角色延奏" | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(0.86997485*base!$B$2+(0.86997485*base!$B$2<=base!$C$2),0) | =0+10 | 0.3164 | 11 | 地面 | 时停 | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(0.86997485*base!$B$2+(0.86997485*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 0 | =ROUND(0*base!$B$2+(0*base!$B$2<=base!$C$2),0) | =ROUND(0.86997485*base!$B$2+(0.86997485*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE)

### 角色-女 row 1086

- Source action: `强化QTE-伤害`
- Confidence: medium
- Coefficients: `[{'raw': '0.45104045', 'value': 0.45104045}, {'raw': '0.45104045', 'value': 0.45104045}, {'raw': '0.86997485', 'value': 0.86997485}, {'raw': '0.86997485', 'value': 0.86997485}, {'raw': '0.7966919', 'value': 0.7966919}, {'raw': '0.7966919', 'value': 0.7966919}, {'raw': '0.87725306', 'value': 0.87725306}, {'raw': '0.87725306', 'value': 0.87725306}, {'raw': '0.08', 'value': 0.08}, {'raw': '0.08', 'value': 0.08}]`
- Frame candidates: `[{'raw': '8F', 'frames': 8.0, 'seconds_at_60fps': 0.1333}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 强化QTE-伤害 | 命中后赋予目标1层霜渐效应 | =ROUND(0.45104045*base!$B$2+(0.45104045*base!$B$2<=base!$C$2),0) | =ROUND(0.2*base!$B$2+(0.2*base!$B$2<=base!$C$2),0) | =MAX(CEILING($AI1086*(1-$AG1086),1)-INT(base!$B$3<>TRUE),0) | =ROUND(0.86997485*base!$B$2+(0.86997485*base!$B$2<=base!$C$2),0) | =ROUND(0.7966919*base!$B$2+(0.7966919*base!$B$2<=base!$C$2),0) | =ROUND(0.87725306*base!$B$2+(0.87725306*base!$B$2<=base!$C$2),0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8EA720> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8E8FB0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8EAC90> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8BB3E0> | 11 | 地面 | 攻击顿帧 | 0.2 | =ROUND(0.08*base!$B$2+(0.08*base!$B$2<=base!$C$2),0)*(base!$B$3<>TRUE) | 目标 | 洛瑟菈 | (0,0,200) | 圆柱(800,0,200)

### 角色-女 row 1094

- Source action: `20`
- Confidence: medium
- Coefficients: `[{'raw': '10%', 'value': 0.1}]`
- Frame candidates: `[]`
- Action-time candidates: `[{'raw': '30秒', 'seconds': 30.0}, {'raw': '0.5秒', 'seconds': 0.5}, {'raw': '0.2秒', 'seconds': 0.2}, {'raw': '30秒', 'seconds': 30.0}]`
- 15s state notes: `[]`
- Raw row: 20 | 特殊能量 | 印象：
上限150点。
·施放 A3-乏善可陈/A3-可圈可点 后，获得25/50点；
·施放 E-补光/E-追光 后，获得25/50点；
·施放 QTE 后，获得50点；
·达到150点后，解锁大招；
·强化状态期间大于49点时，施放强化A3时可额外生成 强化A3-遗忘、强化A3-视为声骸，同时消耗50点。

霜渐模态·胶卷：
上限4层，激活被动2后提升至10层。
·持续30秒，重复获得刷新持续时间，时间结束后清空层数；
·施放 大招 后，获得4层；
·激活被动2后，每消耗50点印象，获得2层；
·拥有层数时，监听其他前台角色成功赋予目标霜渐效应。
  成功触发监听后，赋予半径30米内的目标1+1层霜渐效应，冷却0.5秒；
  成功触发监听后，消耗1层胶卷，冷却0.2秒。

声骸模态·变焦：
上限1层，激活被动2后提升至4层。
·持续30秒，重复获得刷新持续时间，时间结束后清空层数；
·施放 大招 后，获得1层；
·激活被动2后，每消耗50点印象，获得1层；
·拥有层数时，每层使前台角色的声骸暴击伤害+10%。

强化状态：
·施放 大招 后获得；
·状态持续期间，受击削韧减免25%、仅能施放强化A、强化QTE

### 角色-女 row 1131

- Source action: `11`
- Confidence: low
- Coefficients: `[{'raw': '1.1876839', 'value': 1.1876839}, {'raw': '0.9333333', 'value': 0.9333333}, {'raw': '0.76724', 'value': 0.76724}, {'raw': '1.6947573', 'value': 1.6947573}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.8666666', 'value': 0.8666666}, {'raw': '0.8666666', 'value': 0.8666666}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 11 | QTE-下落 | ="第"&ROUNDUP(1.1876839*base!$B$2,0)&"F前不响应输入；第"&ROUNDUP(0.9333333*base!$B$2,0)&"F触发上一角色延奏" | =ROUNDUP(0.76724*base!$B$2,0) | =ROUND(0.3*base!$B$2,0) | =ROUNDUP(0*base!$B$2,0)+1 | =ROUNDUP(1.6947573*base!$B$2,0) | √ | √ | 5 | 0 | 0 | 0 | 50 | 0.3164 | 11 | 空中 | 时停 | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.8666666*base!$B$2,0),0) | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.8666666*base!$B$2,0),0) | 目标 | 光主 | (0,0,100) | 矩形(200,200,200)

### 角色-女 row 1132

- Source action: `QTE-落地`
- Confidence: low
- Coefficients: `[{'raw': '0.9333333', 'value': 0.9333333}, {'raw': '1.1999999', 'value': 1.1999999}, {'raw': '1.6926615', 'value': 1.6926615}, {'raw': '0.8666666', 'value': 0.8666666}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-落地 | =ROUNDUP(0.9333333*base!$B$2,0) | =ROUND(0.2*base!$B$2,0) | =ROUNDUP(1.1999999*base!$B$2,0) | =ROUNDUP(1.6926615*base!$B$2,0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3BA7BF0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3BA4770> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3BA7CB0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3BA5B20> | 11,1 | 空转地 | =ROUND(0.8666666*base!$B$2,0) | 目标 | 光主 | (50,0,200) | 矩形(200,200,200)

### 角色-女 row 1145

- Source action: `16`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 16 | 延奏 | 球形半径20米 | =ROUND(3*base!$B$2,0) | × | √ | 1 | 0 | 地面 | 攻击顿帧 | 0.1 | =IF(base!$B$3=FALSE,ROUNDUP((3+0.2)*base!$B$2,0),0)

### 角色-女 row 1192

- Source action: `21`
- Confidence: low
- Coefficients: `[{'raw': '0.6505578', 'value': 0.6505578}, {'raw': '0.813452', 'value': 0.813452}, {'raw': '0.628434', 'value': 0.628434}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '0.637874', 'value': 0.637874}, {'raw': '0.637874', 'value': 0.637874}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 21 | QTE | ="第"&ROUNDUP(0.6505578*base!$B$2,0)&"F触发上一角色延奏"&CHAR(10)&"第"&ROUNDUP(0.813452*base!$B$2,0)&"F前不响应输入" | =ROUNDUP(0*base!$B$2,0)+1 | =ROUNDUP(0.628434*base!$B$2,0) | =0+10 | 30 | 0.3164 | 11 | 空中 | 时停 | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.637874*base!$B$2,0),0) | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.637874*base!$B$2,0),0)

### 角色-女 row 1193

- Source action: `QTE-攻击`
- Confidence: low
- Coefficients: `[{'raw': '0.7084213', 'value': 0.7084213}, {'raw': '0.814439', 'value': 0.814439}, {'raw': '1.550807', 'value': 1.550807}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.09', 'value': 0.09}, {'raw': '0.03', 'value': 0.03}, {'raw': '0.09', 'value': 0.09}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-攻击 | =ROUNDUP(0.7084213*base!$B$2,0) | =ROUND(0.3*base!$B$2,0) | =MAX(CEILING($AF1193*(1-$AD1193),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI1193*(1-$AG1193),1)-INT(base!$B$3<>TRUE),0) | =ROUNDUP(0.814439*base!$B$2,0) | =ROUNDUP(1.550807*base!$B$2,0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD303650> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD3021E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD302990> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD434320> | 11,1 | 空中 | 攻击顿帧 | 0.03 | =IF(base!$B$3=FALSE,ROUNDUP(0.09*base!$B$2,0),0) | 0.03 | =IF(base!$B$3=FALSE,ROUNDUP(0.09*base!$B$2,0),0) | 目标 | 暗主 | (100,0,150) | 矩形(200,150,120)

### 角色-女 row 1198

- Source action: `23`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[{'raw': '938F', 'frames': 938.0, 'seconds_at_60fps': 15.6333}]`
- Action-time candidates: `[{'raw': '4s', 'seconds': 4.0}, {'raw': '1s', 'seconds': 1.0}]`
- 15s state notes: `[]`
- Raw row: 23 | 延奏-伤害 | 圆柱，半径(500,0,100)，4s内每1s进行一次判定，最多5次 | =ROUND(0.1*base!$B$2,0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF939010> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF939100> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF938F20> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF938EF0> | 1 | 0 | 地面 | 目标 | 暗主 | 圆柱(500,0,100)

### 角色-女 row 1234

- Source action: `14`
- Confidence: low
- Coefficients: `[{'raw': '0.56666667', 'value': 0.56666667}, {'raw': '0.3164', 'value': 0.3164}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 14 | QTE | ="第"&ROUNDUP(0.56666667*base!$B$2,0)&"F触发上一角色延奏；第"&ROUNDUP(0.9*base!$B$2,0)&"F前不响应输入" | =ROUNDUP(0*base!$B$2,0)+1 | =ROUNDUP(1.2*base!$B$2,0) | =0+10 | 1 | 0.3164 | 11 | 地转空 | =INT(0.6*base!$B$2)+ROUND(0.6*base!$B$2-INT(0.6*base!$B$2),0)+(1-0.6>=1-0.5/base!$B$2) | 时停 | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.6*base!$B$2,0),0) | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.6*base!$B$2,0),0)

### 角色-女 row 1235

- Source action: `QTE-伤害`
- Confidence: medium
- Coefficients: `[{'raw': '0.633333', 'value': 0.633333}, {'raw': '0.134', 'value': 0.134}]`
- Frame candidates: `[{'raw': '5F', 'frames': 5.0, 'seconds_at_60fps': 0.0833}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-伤害 | ="持续帧内每"&ROUNDUP(0.1*base!$B$2,0)&"F进行一次判定，最多2次" | =ROUNDUP(0.633333*base!$B$2,0) | =ROUND(0.134*base!$B$2,0) | =ROUNDUP(0.9*base!$B$2,0) | =ROUNDUP(1.2*base!$B$2,0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8C5C10> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8C5490> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8C5F10> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8C4290> | 11,1 | 空中 | 目标 | 自己 | 根 | (0,0,50) | 矩形(200,150,150)

### 角色-女 row 1269

- Source action: `E-走射`
- Confidence: very_low
- Coefficients: `[{'raw': '0.6248264', 'value': 0.6248264}, {'raw': '0.5520654', 'value': 0.5520654}, {'raw': '0.38126776', 'value': 0.38126776}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: E-走射 | ="切人立即消失；每"&ROUNDUP((0.6248264-0.5520654)*base!$B$2,0)&"F发射一颗子弹，每颗回收0.5协奏能量" | =ROUNDUP(0.38126776*base!$B$2,0) | =ROUND(1*base!$B$2,0) | =ROUNDUP(0*base!$B$2,0)+1 | -1 | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8AF890> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8AF7D0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8AEED0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8AEA50> | -1 | 3,4 | 地面 | 目标 | 炽霞 | 武器 | 矩形(50,5,5)

### 角色-女 row 1276

- Source action: `13`
- Confidence: low
- Coefficients: `[{'raw': '0.83641976', 'value': 0.83641976}, {'raw': '1.2053113', 'value': 1.2053113}, {'raw': '1.5390124', 'value': 1.5390124}, {'raw': '0.16281497', 'value': 0.16281497}, {'raw': '1.5352328', 'value': 1.5352328}, {'raw': '0.3164', 'value': 0.3164}, {'raw': '1.0030134', 'value': 1.0030134}, {'raw': '0.6686756', 'value': 0.6686756}, {'raw': '0.6686756', 'value': 0.6686756}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 13 | QTE-1 | ="第"&ROUNDUP(0.83641976*base!$B$2,0)&"F触发上一角色延奏"&CHAR(10)&"第"&ROUNDUP(1.2053113*base!$B$2,0)&"F前不响应输入"&CHAR(10)&"第"&ROUNDUP(1.5390124*base!$B$2,0)&"F前不能切人" | =ROUNDUP(0.16281497*base!$B$2,0) | =ROUND(0.2*base!$B$2,0) | =ROUNDUP(0*base!$B$2,0)+1 | =ROUNDUP(1.5352328*base!$B$2,0) | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD436000> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD4365A0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD4370E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD4358E0> | 15 | 0.3164 | 11 | 空转地 | =ROUND(1.0030134*base!$B$2,0) | 时停 | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.6686756*base!$B$2,0),0) | 0 | =ROUNDUP(0*base!$B$2,0)+1 | =IF(base!$B$3=FALSE,ROUNDUP(0.6686756*base!$B$2,0),0) | 目标 | 炽霞 | (60,0,120) | 矩形(50,5,5)

### 角色-女 row 1277

- Source action: `QTE-2`
- Confidence: low
- Coefficients: `[{'raw': '0.24844994', 'value': 0.24844994}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-2 | =ROUNDUP(0.24844994*base!$B$2,0) | =ROUND(0.2*base!$B$2,0) | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B10710> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B12C60> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B11A30> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B13EC0> | 11 | 地面 | 目标 | 炽霞 | (60,0,120) | 矩形(50,5,5)

### 角色-女 row 1278

- Source action: `QTE-3`
- Confidence: low
- Coefficients: `[{'raw': '0.35211447', 'value': 0.35211447}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-3 | =ROUNDUP(0.35211447*base!$B$2,0) | =ROUND(0.2*base!$B$2,0) | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B12480> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD436000> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD4365A0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD4370E0> | 11 | 地面 | 目标 | 炽霞 | (60,0,120) | 矩形(50,5,5)

### 角色-女 row 1279

- Source action: `QTE-4`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[{'raw': '4369F', 'frames': 4369.0, 'seconds_at_60fps': 72.8167}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-4 | =ROUNDUP(0.4*base!$B$2,0) | =ROUND(0.2*base!$B$2,0) | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B13EC0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B12C00> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD4358E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200BD4369F0> | 11 | 地面 | 目标 | 炽霞 | (60,0,120) | 矩形(50,5,5)

### 角色-女 row 1280

- Source action: `QTE-5`
- Confidence: medium
- Coefficients: `[{'raw': '0.69257927', 'value': 0.69257927}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.06', 'value': 0.06}]`
- Frame candidates: `[{'raw': '9F', 'frames': 9.0, 'seconds_at_60fps': 0.15}]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-5 | =ROUNDUP(0.69257927*base!$B$2,0) | =ROUND(0.3*base!$B$2,0) | =MAX(CEILING($AF1280*(1-$AD1280),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI1280*(1-$AG1280),1)-INT(base!$B$3<>TRUE),0) | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B9FB7DD0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF896C60> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF895CD0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF8947D0> | 11 | 地面 | 攻击顿帧 | 0.05 | =IF(base!$B$3=FALSE,ROUNDUP(0.06*base!$B$2,0),0) | 0.05 | =IF(base!$B$3=FALSE,ROUNDUP(0.06*base!$B$2,0),0) | 目标 | 炽霞 | (40,20,67) | 矩形(50,5,5)

### 角色-女 row 1281

- Source action: `QTE-6`
- Confidence: low
- Coefficients: `[{'raw': '0.8118397', 'value': 0.8118397}, {'raw': '1.1008482', 'value': 1.1008482}, {'raw': '1.7121764', 'value': 1.7121764}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.06', 'value': 0.06}, {'raw': '0.05', 'value': 0.05}, {'raw': '0.06', 'value': 0.06}]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: QTE-6 | =ROUNDUP(0.8118397*base!$B$2,0) | =ROUND(0.3*base!$B$2,0) | =MAX(CEILING($AF1281*(1-$AD1281),1)-INT(base!$B$3<>TRUE),0) | =MAX(CEILING($AI1281*(1-$AG1281),1)-INT(base!$B$3<>TRUE),0) | =ROUNDUP(1.1008482*base!$B$2,0) | =ROUNDUP(1.7121764*base!$B$2,0) | × | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF91B6E0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF91BB60> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF919C70> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200CF91AA80> | 11,2 | 地面 | 攻击顿帧 | 0.05 | =IF(base!$B$3=FALSE,ROUNDUP(0.06*base!$B$2,0),0) | 0.05 | =IF(base!$B$3=FALSE,ROUNDUP(0.06*base!$B$2,0),0) | 目标 | 炽霞 | (40,20,67) | 矩形(50,5,5)

### 角色-女 row 1297

- Source action: `15`
- Confidence: low
- Coefficients: `[]`
- Frame candidates: `[]`
- Action-time candidates: `[]`
- 15s state notes: `[]`
- Raw row: 15 | 延奏-伤害 | =ROUND(0.2*base!$B$2,0) | √ | √ | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B35700> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B344A0> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B34B30> | <openpyxl.worksheet.formula.ArrayFormula object at 0x00000200B3B34620> | 1 | 0 | 地面 | 目标 | 炽霞 | 圆柱(500,0,100)

... 1136 additional candidates omitted from report preview.
