# Expeditions: Viking 汉化项目

## 游戏信息

| 项目 | 内容 |
|------|------|
| 游戏名 | Expeditions: Viking |
| 引擎 | Unity 5.6.4f1 |
| 脚本后端 | Mono |
| 文本总量 | 23195 条（9 个类别） |
| 本地化格式 | XML（Unity TextAsset） |
| 汉化方式 | 直接替换 `resources.assets` 中的英文 TextAsset |
| 翻译引擎 | 自定义 API（deepseek-flash），AINiee 共用处理；Sol 定向修复与争议裁决 |
| 汉化质量 | AI 自动翻译，非人工精翻 |

## 目录结构

```
Expeditions Viking/
├── Game/                              # 游戏文件
│   └── Expeditions Viking_Data/
│       └── resources.assets           # 本地化文本所在文件（340MB）
│
├── output/full-project/               # AssetRipper 导出
│   └── ExportedProject/Assets/
│       └── Resources/localization/    # 各语言本地化文件
│           ├── dialogue/              # 对话（8语言 × XML）
│           ├── gui/                   # 界面UI
│           ├── homesteadupgrades/     # 家园升级
│           ├── input/                 # 输入提示
│           ├── items/                 # 物品
│           ├── names/                 # 角色名称
│           ├── scenedata/             # 场景数据
│           ├── skills/                # 技能
│           └── tutorial/              # 教程
│
├── Chinese_Localization/Chinese/Localization/
│   ├── Dialogue/DialogueChinese.xml        # 中文对话（18339条）
│   ├── GUI/GUIChinese.xml                  # 中文UI（1994条）
│   ├── Skills/SkillsChinese.xml            # 中文技能（752条）
│   ├── Items/ItemsChinese.xml              # 中文物品（219条）
│   ├── Tutorial/TutorialChinese.xml        # 中文教程（147条）
│   ├── HomesteadUpgrades/...Chinese.xml    # 中文家园（100条）
│   ├── Names/NamesChinese.xml              # 中文人名（1241条）
│   ├── SceneData/SceneDataChinese.xml      # 中文场景（357条）
│   └── Input/InputChinese.xml              # 中文输入（46条）
│
├── backup/resources.assets           # 原始文件备份
├── ExpeditionsViking_中文汉化.zip     # 汉化发布包（151.6MB）
└── README.md                         # 本文件
```

## 汉化流程

### 第 1 步：提取文本

```powershell
# 用 AssetRipper-CLI 导出完整 Unity 工程
cd Projects\Expeditions Viking
Set-Alias arc "..\..\Tools\AssetRipper-CLI\artifacts\bin\...\AssetRipper.Tools.ExportRunner.exe"
arc export ./Game --output ./output/full-project --profile full-project

# 将英文 XML 转换为 AiNiee 翻译用的 CSV
python extract_for_translation.py
# 输出: extracted_for_ainiee.csv（23195条，两列：原文,译文）
```

### 第 2 步：AI 翻译

```powershell
# 启动 AiNiee
cd Tools\AINiee
.\venv\Scripts\python.exe AiNiee.py

# 操作：接口管理 → 确认 DeepSeek 已激活 → 拖入 extracted_for_ainiee.csv
#      → 源语言 English → 目标语言 简体中文 → 开始翻译
# 输出: extracted_for_ainiee_translated.csv
```

> **翻译提示词建议**：告知大模型这是维京时代背景的策略 RPG，包含 BBCode 标签和占位符，对话粗犷直接，UI 文本简洁。

### 2026-10-18：自定义术语审校恢复 revision 8

- 当前续作使用自定义 Codex 工作流，标准执行模型为 Luna；原文为项目根目录 `expeditions-viking_text.csv`，共 23,195 条。
- 按用户要求恢复 revision 8 的原始术语快照和已验收结论；复用原有 187 批，补齐旧 00083 中尚未入验收的 19 条后，5,331 条术语均有逐项审校记录。
- revision 9 的全量重审已停止，其已完成结果保留为历史，不作为本次交付基准。新快照的预合并规则不追溯改写 revision 8。
- 恢复通过工作流程序执行，数据库和配置已备份至 `TranslateFiles/backups/restore_glossary_r9_to_r8_449218961bf04aee88de53ec6a896286/`；备份及运行状态不入库。
- r8 已完成冻结：复用 5,331 条逐项审校记录，403 组等价重复由程序合并，276 组分歧经 36 个定向包裁决；正式术语表共 3,529 项（人物 1,386、术语 1,728、禁翻 415）。
- 冻结产物：`TranslateFiles/glossary/r8/freeze_731eced6/built/glossary_reviewed.json`，SHA-256 为 `8b1369e804c5c7f66803e0961da266077ff087a5ecc849b9e6806ece5c8b31a4`。原审校、合并及裁决来源均保留。
- 特殊收尾实现仅位于本项目 `TranslateFiles/scripts/`；共享基础程序的特殊改动已撤销。后续配置修订只切执行方式或预算，不重做 r8 术语审校。
- 用户已指定下一阶段改用自定义 API，沿用本地配置的 `mimo-v2.6-flash`。旧版 30 条试译的独立审校和 Sol 试译验收流程已被下面的新版校准流程替代；旧结果和付费历史保留。凭据不入项目、不入库。
- 续作与冻结报告见 `TranslateFiles/reports/r8_completion_20261018.md`；阶段运行记录见 `TranslateFiles/TranslateDoc.md`。

### 2026-10-18：新版试译整体校准已接受

- 按用户最新要求，使用 `pilot_translate → pilot-report → 主 AI pilot-decide` 重新试译；不再做独立 API 试译审校或额外 Sol 逐项验收。复用已保存的 30 条样本 ID，旧试译队列通过公开恢复和重试入口归档，不重跑 r8。
- 首轮 30 条完整保存后，主 AI 阅读原译文及诊断，调整普通词义/专名、条件语气、亲属长幼和口语称呼规则，只重试 4 条受影响样本；该轮 1 批完成、失败 0。文体配置 revision 13，未触发语义全量重置。
- 新版校准已接受，报告哈希 `574f7dd66f06341dc98e9b6a18c875928ef0d8a2542dbe76a6ecb8ed0a988b00`；归档为 `TranslateFiles/reports/accepted/pilot_574f7dd66f06341d/`。
- 仍记录 9 条机械术语诊断，多数为普通词义或受保护标记内部词形，不是语义错误率或正式验收通过。动态性别分支被整体保护、可见英文分支仍需后续项目专项处理。正式全文翻译、独立审校、导出和实机门槛继续保留。
- r8 冻结哈希未变。接受试译后已恢复正式翻译基线，23,195 条均待正文翻译，无运行中任务。详情见 `TranslateFiles/reports/pilot_new_method_20261018.md`。

### 2026-10-18：恢复首轮原稿，单独执行新版程序审校

后续进度（2026-10-19）：独立 review 已保存 146 批、2,230 条候选，剩余 1,335 批，尚未整轮验收。按用户要求先修复格式接收与重试流程，隔离副本以 2 次真实 API 请求验证 34 条记录，JSON 格式链路通过，1 条语义证据问题仍被严格拒收。正式数据及队列未受验证影响；详见 `TranslateFiles/TranslateDoc.md` 与 `TranslateFiles/reports/api_format_upgrade_validation.json`。

各阶段补齐（2026-10-19）：已将规范化、阶段专用格式诊断重试、回复元数据及中断恢复检查覆盖全部自定义 API 阶段。36 项契约检查、56 项流程回归及本轮 11 次隔离真实请求验证通过；本项目审校候选、队列和 r8 冻结不变。详见 `TranslateFiles/reports/api_all_stages_reliability_20261019.json`。02-30-api 定时任务已删除。

- 按用户要求，仅从 revision 16、payload 不含 `strict_translation` 和 `draft_scan_key` 的 1,063 个已完成 translate 任务恢复 23,195 条原始草稿；未使用后续 draft-repair 译文。按记录 ID 对齐，核对任务输入哈希、源文/序号、冻结表、文体、有效批次结果、会话结果、API 调用及实际作者 lineage。
- 恢复原始语境例外（10 条记录），仅还原原任务已知保护映射（2,821 条记录），不改写原译。首轮快照：`TranslateFiles/snapshots/r16_first_draft_20261018T142909Z_9c5af3c9/`（drafts.jsonl、单列 drafts.csv、task_manifest.json 及哈希 manifest）。这是审校前快照，不是正式交付 CSV。
- 当前状态完整备份：`TranslateFiles/backups/restore_r16_first_drafts_20261018T142909Z_9c5af3c9/`。旧候选、队列及检查缓存已归档；建立 revision 17 程序审校范围，旧修复计数不参与本轮。全部付费、执行、作者及 lineage 历史逐表哈希核对保持不变；r8 冻结表、文体和已接受试译保持。
- 本轮下一步仅调用官方 runner 的 `--stage draft_check`，自动处理必要修复及统一复查；结束后返回主流程，不启动独立语义审校、导出或回填。恢复审计：`TranslateFiles/reports/restore_r16_first_drafts.json`；项目内恢复脚本：`TranslateFiles/scripts/restore_r16_first_drafts.py`，未调用 restart-body。
- 本轮程序审校已完成：首次检查 4,451 条受影响，6 轮常规修复后余 416 条；发现其中 414 条含已还原原始标签却被要求 `[P1]` 的程序诊断，修复共同验收器并使旧检查缓存失效，重新全量检查后实际余 17 条。归档 56 个未尝试的旧升级包，保留全部已付费请求和已完成修复历史，不改候选稿。
- 17 条由两个新的 gpt-6-sol 实例定向修复；统一复查 17 条通过，最终全量验收 23,195 条通过，0 失败，无待办/在途任务。首轮草稿快照哈希复核未变。完成报告 `TranslateFiles/reports/restored_r16_draft_check_completion.json`；最终回执 `TranslateFiles/reports/api_runs/f431079d6f54487d98d2e18f93ffaf6c.json`。本轮止于程序审校，不代表独立语义审校已完成，未导出或回填。

### 2026-10-18：按最新规则重新启动正式翻译

- 用户明确要求不沿用旧正文数据，按更新的正式流程重新开始。旧运行器已停止，6,530 条旧草稿及 672 个旧正式任务归档；原 API 消耗、作者与原始回复保留。
- 通过公开 `restart-body` 建立新正文范围，所有 23,195 条回到 source，正式候选和检查缓存清空；r8 冻结、源文、文体与试译接受记录保留。正文重启范围 revision 15，同步当前本地批次配置后为 revision 16。
- 本轮使用官方 `Tools/localization/run_api_round.py`，API 批内数字短编号和句内 `[P1]` 短占位符；同一阶段进程自动完成草稿扫描及常规修复，正式独立审校仍另行推进。
- 当前本地接口为 `deepseek-flash`，并发 5，正文预算 1024 原文 Token，完整输入预算 16384；不再启用项目旧 API 包装的输入预算覆盖。
- 新基线核对记录：`TranslateFiles/reports/new_formal_restart_20261018.json`。r13 原始完整备份在 `TranslateFiles/backups/restart_body_0582f94f910f4c8e99cecf292549db4f/`，不入库。


## 2026-10-19：独立语义审校与正式导出完成

- 延续 revision 17 已保存候选，首轮独立审校完整覆盖 23,195 条。统一验收首轮 22,056 条通过、1,139 条需处理；后续仅重派失败项，保留通过记录、真实来源、作者及累计修复次数。首个失败门槛统计不代表翻译准确率。
- 保留所有付费回复，Sol 对 20 个异常批次作无损格式恢复，共收回 340 条候选，没有为这些恢复新增 API 请求。另有缺少必需字段的批次交新 Sol 独立完成；不自动补 keep、译文或证据。
- 本次接续实际发送 1,720 次 API 请求（包括 237 次失败尝试），服务端报告输入 5,758,196、输出 5,270,021、总计 11,028,217 Token；缓存 2,459,648 为输入子项，不另相加。旧消费及作者历史保留。
- 审校修复按共同累计预算升级：Sol 定向修复保留已满足术语及语境例外；最后所有 23,195 条均到 review。最终报告的 41 项明确遗留提示经 Sol 裁决，3 条确需修复并通过复查；更新报告只再核对 2 项，其余裁决复用。最终质量轮 2 已批准，未启动全文润色。
- 正式译文 `expeditions-viking_text_translated.csv` 由官方 export 生成，无表头、单列、按源记录顺序。导出前全库结构、保护内容及术语/已审语境例外检查通过；最终验收报告 `TranslateFiles/reports/final_validation.json`，本轮汇总 `TranslateFiles/reports/review_completion_20261019.json`。
- r8 冻结术语哈希及审校前 r16 草稿快照哈希不变。没有重新提取术语、重译全文或调用 restart-body；API 模型仍为 deepseek-flash，升级及争议角色使用独立 gpt-6-sol 实例。
- 待下一阶段：动态可见分支仍整体保护（已有清单 498 次、53 种形式），需项目内专项处理及回填后实机检查。本次未修改游戏载荷、未回填或发布，新导出实机状态为 pending_repack；此前版本的实机结论不能替代本轮验证。
- 接续中发现历史无关例外在 API term_refs 中无法表达撤销，已由独立 Sol 使用完整共同 Codex 协议具证撤销并正常收集；未改共享程序或放宽门槛。

### 第 3 步：回填

```powershell
# 1. 由正式译文生成回填用副本（回补漏译的选项片段、本地化性别分支）
python TranslateFiles\scripts\repack_prepare.py --variants

# 2. 校验回填副本（行数、标签、占位符、性别分支）
python TranslateFiles\scripts\verify_repack_csv.py

# 3. 生成中文 XML 文件（从回填副本写回 XML 结构）
python build_localization.py

# 4. 校验 XML 与译文逐条一致
python TranslateFiles\scripts\verify_built_xml.py

# 5. 用 UABEA CLI 从原始备份重建并替换 resources.assets 中的 9 个 TextAsset
python batch_replace_uabea.py

# 6. 从部署后的资源导出，逐字节比对 XML 与资源内容
python TranslateFiles\scripts\verify_deployed_assets.py
```

### 2026-10-19：新译文回填完成（已实机验证）

- 输入为本轮正式译文 `expeditions-viking_text_translated.csv`（23,195 条，单列，按源记录顺序）。已确认与 `extracted_strings.csv` 逐行对齐（原文完全一致），因此按行号映射回 9 个类别的 key。
- 回填不改动已验收译文，而是生成回填副本 `TranslateFiles/repack/translation_for_repack.csv`，共修订 238 条记录（240 处操作，其中 2 条与整体回补重合）：
  - 100 条整体漏译的选项（`{Attack.}`、`{Leave.}` 等）沿用 v1.2 已发布译法回补；
  - 136 条仅花括号片段漏译的对白，仅替换 `{…}` 内文本，句体保留本轮译文；
  - 4 条定向修订：`Asleifr`→阿斯莱夫（术语表）、`Ready`→戒备（术语表）、`[[hotkey]]` 双层转义修复、1 条全角括号统一为花括号。
- 291 处 `[Player:甲/乙]` 动态性别分支（50 种形式）已本地化为 `[Player:男子/女子]` 等；`[Player:Name]`、`[Shipname]` 等运行时变量原样保留。校验英文残留 0。
- `build_localization.py` 改为读取单列译文并支持 `--translated/--output/--report`；同时修复同名路径跨类别串译（`TooltipHomesteadStatPower` 等 2 组在 GUI 与家园文件中的译文互相覆盖），key 现按类别隔离。
- 生成结果：9 个中文 XML + `ProcQuestEnglish.xml`（保持英文），写入 23,195 条译文；逐条反查 0 缺失、0 不一致、0 英文性别分支。纯占位模板（`[x]`、`[size="16"][name]` 等）与拉丁语／古英语／盖尔语风味文本按原样保留（共 279 条原文未译）。
- 回填：从 `backup/resources.assets`（344,539,620 bytes）重建，9/9 TextAsset 导入成功；部署后 `resources.assets` = 344,633,140 bytes，SHA-256 `0c07814ce8ace8232e1b7fd8be69f2c44eeac58447ed9d29ddb25901efde92d3`。
- 验证：从部署后的资源重新导出 9 个 TextAsset，与生成的 XML 逐字节一致（9/9）；对白中 `{…}` 英文片段 0，英文性别分支 0，`[[hotkey]]` 与 `{攻击。}` 均已就位。报告见 `TranslateFiles/reports/repack_verification.json`、`repack_translation_prep.json`、`build_xml_verification.json`。
- 实机结果：用户在部署后实机确认字体、排版、UI 与对白/选项正常；任务日志界面未单独检查。可发布。

### 2026-10-19：v1.4 补充审校与重新打包

- 针对 v1.3 回填副本中的 238 条改动完成逐条独立语义审校，六维证据和真实审校者保存在 `TranslateFiles/reports/repack_review_evidence_20261019.json`。整轮统一验收，失败项定向修复，最终 Sol 质量轮 3 已批准。
- 相比 v1.3 回填候选共修正 13 条；另对 6 条因整句禁翻项回退为英文的玩家选项定向复核，保留冻结表，通过具体语境例外确认其为玩家可见文本。
- 已审 238 条纳入正式译文，SHA-256 `bcb10634df1ac8053408cae6492186a674a808982e4e85f3c05c2257a77f7a9b`。回填脚本优先使用绑定该哈希的补充验收报告，禁止再从旧版译文覆盖已审正文；回填副本只另作 291 处、272 条记录的性别分支本地化。
- 23,195 条文本与部署资源逐条一致，9/9 TextAsset 与生成 XML 逐字节一致；新版 `resources.assets` SHA-256 `307cb72ef9b5d1cc34dc2755ec226bdd72e49e154b940354195fd00f2aa3009b`。
- v1.4 ZIP 校验和、累计更新日志及压缩包实际安装通过；安装后资源哈希一致，备份、重复安装拒绝与错误版本拒绝/恢复均通过。报告见 `release_v14_static_validation.json`、`release_v14_archive_validation.json`。
- 用户明确要求“不用进入游戏测试，好了就直接打包发布”。本版未启动游戏、不新增实机通过记录；项目专用发布入口保留正式语义验收、源文/载荷哈希及静态安装校验，以记录的用户指令取代本版新实机测试门槛，未修改共享发布程序。v1.3 的实机证据保留为历史，不能视作 v1.4 的实机结论。
- 下方旧版独立打包复核中指出的 238 条审校缺口已由本节闭环；任务日志界面仍未单独实测。

### 2026-10-19：独立打包复核

- 重新从当前游戏资源导出 9 个 TextAsset，全部与生成 XML 逐字节一致；按类别及 key 对齐核对回填副本的 23,195 条文本，缺失或不一致为 0。
- 正式译文 SHA-256 仍为 `c0c645ab…be4d62f`；回填副本为 `a93470b4…3e7cfea`。共 510 条记录与正式译文不同，包含 238 条正文/选项等修订及 272 条可见性别分支本地化。
- 本地 v1.3 ZIP 完整性、清单载荷哈希和已有实机证据哈希均通过；从原始备份重新应用差分，得到的资源 SHA-256 为 `0c07814c…efde92d3`，与当前部署文件相同。复核未改游戏文件。
- 结论：打包技术校验通过，仍有审校覆盖缺口。238 条回填修订未经过本轮正式独立语义审校；已发布来源不等于本轮语义验收。任务日志的 `not_applicable` 在现有实机记录中实际表示“未单独检查”，不能解释为无须验证。
- 本次未重新启动游戏，沿用并核对已有用户实机记录；差分重建测试不冒充整套交互式安装器测试。详细报告：`TranslateFiles/reports/repack_acceptance_20261019.json`。

### 2026-09-19：动态性别分支标签修复

- 问题：翻译阶段把 `[Player:brother/sis]` 一类标签整体作为不可翻译变量保留；游戏会将斜杠两侧的词直接显示，因此会出现 `brother`、`man` 等英文。
- 修复：新增 `localize_player_variants.py`，只本地化带 `/` 的 `[Player:…/…]` 可见分支，保留 `[Player:Name]`、`[Shipname]` 等运行时标识变量。
- 覆盖：翻译源及生成的 `DialogueChinese.xml` 中共 291 处动态分支；已导出回填后的 `DialogueEnglish`（pathId 9146）校验，英文分支残留为 0。
- 回填：已用 `batch_replace_uabea.py` 从原始备份重建并部署 9 个本地化 TextAsset 至 `resources.assets`。
- 待验证：需关闭游戏后重新启动，并实际进入对话确认性别分支显示和文本排版正常；测试前确保 `Custom Localization` 覆盖目录未加载旧文件。

### 2026-09-19：名称称号字段补全

- 问题：旧版名称提取器只收集 `Male` / `Female` 节点，遗漏了根级称号和动物名；例如 `Ragnhildr` 已译为“拉根希尔德”，但 `<White>the White</White>` 仍保留英文。
- 修复：在 `build_localization.py` 中加入 51 条名称静态字段映射，覆盖“白衣者”、角色别名、狼群名称等会直接显示的字段。
- 验证：已从部署后的 `CharacterNamesEnglish`（pathId 9804）导出；`White = 白衣者`，纯英文名称字段残留为 0。

## 关键文件说明

| 文件 | 用途 |
|------|------|
| `extract_for_translation.py` | 第1步：提取英文 XML → 两列 CSV |
| `prepare_for_ainiee.py` | 生成 AiNiee 兼容格式（两列无 header） |
| `extracted_strings.csv` | 提取结果（含 key + category） |
| `extracted_for_ainiee.csv` | 翻译输入文件 |
| `extracted_for_ainiee_translated.csv` | AiNiee 翻译输出（原文列已被替换为中文） |
| `build_localization.py` | 第3步：译文 CSV → 中文 XML 文件 |
| `batch_replace_uabea.py` | 第3步：用 UABEA CLI 写入 resources.assets |

## 重新汉化指南

### 调整翻译后重新回填

1. 修改 `extracted_for_ainiee_translated.csv` 中的译文
2. 运行 `python build_localization.py` 重新生成中文 XML
3. 运行 `python batch_replace_uabea.py` 写回游戏

### 只改某个类别的翻译

```powershell
# 1. 修改 Chinese_Localization/Chinese/Localization/ 下的对应 XML
# 2. 用 UABEA GUI 手动 Import Dump（右键 TextAsset → Import Dump）
#    或者修改 batch_replace_uabea.py 的 REPLACEMENTS 字典只保留要更新的
# 3. 运行 python batch_replace_uabea.py
```

### 更换翻译引擎重新翻译

```powershell
# 1. 修改 Tools/AINiee/Resource/config.json 中的 API 配置
# 2. 重新执行第 2 步（AiNiee 翻译）
# 3. 重新执行第 3 步（build_localization.py + batch_replace_uabea.py）
```

## 技术备忘

### resources.assets 中的 TextAsset pathId（Unity 5.6）

| TextAsset 名称 | PathID | 原始大小 | 中文大小（2026-10-19 回填） |
|---|---|---|---|
| GUIEnglish | 9040 | 197,875 | 193,142 |
| HomesteadUpgradesEnglish | 9063 | 17,040 | 17,144 |
| DialogueEnglish | 9146 | 3,786,345 | 3,809,951 |
| SkillsEnglish | 9165 | 96,222 | 101,994 |
| ItemsEnglish | 9309 | 20,829 | 20,937 |
| InputEnglish | 9744 | 2,242 | 2,406 |
| SceneDataEnglish | 9795 | 48,802 | 47,683 |
| TutorialEnglish | 9799 | 31,947 | 27,878 |
| CharacterNamesEnglish | 9804 | 79,027 | 152,712 |

### 回填验证

- 验证方法：用 UABEA `exporttext` 从回填后的 `resources.assets` 逐个导出 9 个 TextAsset，与生成的 XML 做 SHA-256 逐字节比对，并统计对白中的英文残留。
- 验证结果（2026-10-19）：9/9 逐字节一致；对白 24,606 个 `<Localize>` 节点中 18,332 个为中文，`{…}` 英文片段 0、英文性别分支 0；`00008015-...` → "他那沮丧的神情，明明白白写在这张日渐苍老的脸上。"；`[[hotkey]]`、`{攻击。}` 均正确写入。
- 文件大小变化：原始 `resources.assets` = 344,539,620 bytes → 2026-10-19 回填后 = 344,633,140 bytes。
- 9/9 TextAsset 全部导入成功。

## 已知问题

- v1.4 按用户明确要求未启动游戏进行新的实机测试；已完成静态资源、差分、压缩包实际安装、备份及错误版本保护验证。
- v1.3 载荷曾实机验证字体、排版、UI、对白/选项；任务日志界面未单独检查，旧记录为 `not_applicable`，不代表已验证。
- v1.3 回填副本的 238 条补译已在 v1.4 完成独立审校并纳入正式译文；后续回填从已审正式 CSV 生成，仅继续本地化可见性别分支。
- 正式译文已包含本轮审校后的 238 条回填改动；回填副本仅另作可见性别分支本地化。`final_validation.json` 对正式 CSV 有效，部署资源绑定另见 v1.4 静态及压缩包验证报告。
- 纯占位模板与拉丁语／古英语／盖尔语风味台词保持原样（279 条），属预期保留。
- 对白中 `[Player:甲/乙]` 分支必须保持 `[Player:…/…]` 形式；若后续译文重新保护该标签，需再次运行 `repack_prepare.py --variants`。
- AI 自动翻译，长文本、术语与语气仍可能需要润色；`Custom Localization` 覆盖目录会屏蔽回填结果。

## 版本记录

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-10-19 | 发布 v1.4 | 238 条回填补译独立审校通过，修订 13 条，正式译文与资源重建并通过实际安装校验；用户要求跳过新的实机测试 |
| 2026-10-19 | 发布 v1.3 | 基于新译文生成 HDiffPatch 差分补丁并发布；实机确认字体/排版/UI/对白正常，临时目录按玩家流程安装后哈希与载荷一致 |
| 2026-10-19 | 新译文回填 | 用正式译文重建 9 个 TextAsset 并部署；修订 238 条记录（整体回补 100 + 花括号片段 136 + 定向 4，2 处重合），291 处性别分支本地化；资源导出 9/9 逐字节一致 |
| 2026-07-19 | 首次回填 | `build_localization.py` + `batch_replace_uabea.py`，9 个 TextAsset 替换 |
| 2026-07-25 | 重新回填 | 译文 CSV 更新后重新生成 XML 并回填；`batch_replace_uabea.py` 改为以原始备份为干净基底重建，新增已知 pathId 快速校验模式 |
| 2026-07-25 | 排查回填不生效 | 定位到游戏读取 `Documents\My Games\Expeditions Viking\Custom Localization\` 覆盖文件夹（旧汉化），删除后回填生效 |
| 2026-09-19 | 修复动态分支英文 | 本地化 291 个 `[Player:…/…]` 可见分支并重新回填；资源导出校验通过，待游戏内验证 |
| 2026-09-19 | 补全名称称号 | 本地化 51 条根级称号/名称并重新回填；资源导出校验通过，待游戏内验证 |
| 2026-09-20 | 发布 v1.2 | 生成不含游戏原始资源的 HDiffPatch 差分补丁；在独立临时游戏目录一键安装并哈希校验通过 |

## 对外发布

### v1.4（当前最新稳定版）

- 补丁：`Dispatch/Expeditions Viking_子非鱼汉化1.4.zip`（1,997,947 bytes），SHA-256 `60622bf984f717f0919bf9f977f808011e0945304855445f20b964e9a32631e4`。
- 载荷：`ZFY_Translation_Patch/resources.assets.hdiff`、`hpatchz.exe` 和一键安装脚本；不含原始游戏资源、凭据或开发日志。
- 支持 Steam Windows / Unity 5.6.4f1 的原始资源（344,539,620 bytes，SHA-256 `5ffb6e09…c3e9eba8`）。
- GitHub Release：`https://github.com/zfyu222/expeditions-viking-hanhua/releases/tag/v1.4`；下载资产名 `Expeditions.Viking_ChinesePatch_.1.4.zip`。
- 验证：238 条补充语义审校通过；全文与资源、差分、压缩包完整性及实际一键安装校验通过。按用户明确指令跳过本版新的游戏内测试，任务日志未单独实测。
- 已确认 Release 为公开、非草稿、最新稳定版；匿名下载 ZIP 后 SHA-256 与本地发布包一致。
- 百度网盘：当前会话未提供上传 MCP，尚未镜像。

### v1.3 历史发布

- 历史版本：**v1.3**（2026-10-19），已由 v1.4 接替。
- 补丁：`Dispatch/Expeditions Viking_子非鱼汉化1.3.zip`（1,459,964 bytes）
- 支持版本/平台：Steam Windows 版，Unity 5.6.4f1；仅支持原始 `resources.assets` 为 344,539,620 bytes 的安装。
- 载荷：`ZFY_Translation_Patch/` 下的 `resources.assets.hdiff`（1,186,334 bytes）、HDiffPatch 应用器 `hpatchz.exe`（v5.1.3）与一键安装脚本；不含游戏本体或原始资源文件。
- 验证结果：用户已在 Steam Windows 版实机确认字体、排版、UI 与对白/选项正常；在独立临时目录按玩家流程完整安装，结果为 `resources.assets` SHA-256 `0c07814c…efde92d3`，与应用前测试载荷一致，原始文件备份与失败回滚路径均正常。
- 已知问题：AI 自动翻译，部分长文本、术语与语气仍可能需要润色；任务日志界面本轮未单独实机验证；其他 Mod 或不同游戏版本会导致差分拒绝应用。
- GitHub Release：`https://github.com/zfyu222/expeditions-viking-hanhua/releases/tag/v1.3`
- GitHub 下载资产命名：`Expeditions.Viking_ChinesePatch_.{版本号}.zip`（本版为 `Expeditions.Viking_ChinesePatch_.1.3.zip`）。后续发布沿用此格式；项目本地归档仍按中文补丁命名规范保存。
- 百度网盘：待镜像上传（当前会话未加载 `baidu-netdisk-local-uploader` MCP 工具）。
- v1.2 归档仍保留在 `Dispatch/`，未覆盖。

### ⚠ 关键：Custom Localization 覆盖文件夹（务必先处理）

游戏会优先读取**用户数据目录**里的本地化文件，覆盖 `resources.assets` 中的 TextAsset：

```
C:\Users\<用户名>\Documents\My Games\Expeditions Viking\Custom Localization\
```

**症状**：往 `resources.assets` 回填后，游戏里仍显示旧译文、破损占位符（如 `<玩家:名字>: Not found!`），且截图里的中文措辞在项目译文 CSV 中搜不到。

**原因**：该目录下存在旧的汉化文件（来自早期安装/其他汉化包），优先级高于 `resources.assets`，导致回填不生效。

**解决**：测试回填效果前，**先删除或清空** `Custom Localization` 文件夹，再启动游戏。否则任何 `resources.assets` 的修改都不会在游戏中体现。

> 排查方法：若游戏显示的中文在 `extracted_for_ainiee_translated.csv` 和已部署 XML 中都搜不到，几乎可以确定是此覆盖文件夹在作祟。

### UABEA CLI 修复记录

本项目 CLI 指令需要 UABEA 源码的以下修复才能正常工作（已修复并编译）：

| 问题 | 修复文件 | 行号 |
|------|----------|------|
| 非交互式控制台崩溃 | `Program.cs` | 30 |
| 缺少 classdata.tpk 加载 | `CommandLineHandler.cs` 新增 `LoadClassPackage()` | - |
| importtext 文件句柄未释放 | `CommandLineHandler.cs` importtext 方法 | 767 |

详见 `CODEBUDDY.md` 中 UABEAvalonia 章节。

### 游戏版本信息

- Unity 版本：5.6.4f1
- resources.assets 大小：344,539,620 bytes
- TypeTreeEnabled：False
- TextAsset 数量：858（含多语言变体）
- 实际替换：9 个英文 TextAsset
