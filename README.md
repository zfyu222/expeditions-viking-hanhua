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
| 翻译引擎 | AiNiee（DeepSeek V4 Flash） |
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

- 按用户要求，仅从 revision 16、payload 不含 `strict_translation` 和 `draft_scan_key` 的 1,063 个已完成 translate 任务恢复 23,195 条原始草稿；未使用后续 draft-repair 译文。按记录 ID 对齐，核对任务输入哈希、源文/序号、冻结表、文体、有效批次结果、会话结果、API 调用及实际作者 lineage。
- 恢复原始语境例外（10 条记录），仅还原原任务已知保护映射（2,821 条记录），不改写原译。首轮快照：`TranslateFiles/snapshots/r16_first_draft_20261018T142909Z_9c5af3c9/`（drafts.jsonl、单列 drafts.csv、task_manifest.json 及哈希 manifest）。这是审校前快照，不是正式交付 CSV。
- 当前状态完整备份：`TranslateFiles/backups/restore_r16_first_drafts_20261018T142909Z_9c5af3c9/`。旧候选、队列及检查缓存已归档；建立 revision 17 程序审校范围，旧修复计数不参与本轮。全部付费、执行、作者及 lineage 历史逐表哈希核对保持不变；r8 冻结表、文体和已接受试译保持。
- 本轮下一步仅调用官方 runner 的 `--stage draft_check`，自动处理必要修复及统一复查；结束后返回主流程，不启动独立语义审校、导出或回填。恢复审计：`TranslateFiles/reports/restore_r16_first_drafts.json`；项目内恢复脚本：`TranslateFiles/scripts/restore_r16_first_drafts.py`，未调用 restart-body。

### 2026-10-18：按最新规则重新启动正式翻译

- 用户明确要求不沿用旧正文数据，按更新的正式流程重新开始。旧运行器已停止，6,530 条旧草稿及 672 个旧正式任务归档；原 API 消耗、作者与原始回复保留。
- 通过公开 `restart-body` 建立新正文范围，所有 23,195 条回到 source，正式候选和检查缓存清空；r8 冻结、源文、文体与试译接受记录保留。正文重启范围 revision 15，同步当前本地批次配置后为 revision 16。
- 本轮使用官方 `Tools/localization/run_api_round.py`，API 批内数字短编号和句内 `[P1]` 短占位符；同一阶段进程自动完成草稿扫描及常规修复，正式独立审校仍另行推进。
- 当前本地接口为 `deepseek-flash`，并发 5，正文预算 1024 原文 Token，完整输入预算 16384；不再启用项目旧 API 包装的输入预算覆盖。
- 新基线核对记录：`TranslateFiles/reports/new_formal_restart_20261018.json`。r13 原始完整备份在 `TranslateFiles/backups/restart_body_0582f94f910f4c8e99cecf292549db4f/`，不入库。

### 第 3 步：回填

```powershell
# 生成中文 XML 文件（从翻译 CSV 写回 XML 结构）
python build_localization.py

# 用 UABEA CLI 批量替换 resources.assets 中的 TextAsset
python batch_replace_uabea.py
```

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

| TextAsset 名称 | PathID | 原始大小 | 中文大小（2026-07-25 回填） |
|---|---|---|---|
| GUIEnglish | 9040 | 197,875 | 194,254 |
| HomesteadUpgradesEnglish | 9063 | 17,040 | 17,098 |
| DialogueEnglish | 9146 | 3,786,345 | 3,900,150 |
| SkillsEnglish | 9165 | 96,222 | 103,180 |
| ItemsEnglish | 9309 | 20,829 | 21,104 |
| InputEnglish | 9744 | 2,242 | 2,430 |
| SceneDataEnglish | 9795 | 48,802 | 48,119 |
| TutorialEnglish | 9799 | 31,947 | 29,626 |
| CharacterNamesEnglish | 9804 | 79,027 | 115,603 |

### 回填验证

- 验证方法：用 UABEA `exporttext` 从回填后的 `resources.assets` 导出 `DialogueEnglish`（pathId=9146），确认内容为中文。
- 验证结果：通过。导出 XML 中 `<Localize>` 节点文本均为中文，与 `extracted_for_ainiee_translated.csv` 一一对应（如 `00008015-...` → "沮丧之情，如粗笔重墨般涂抹在他那张日渐苍老的脸上。"）。
- 文件大小变化：原始 `resources.assets` = 344,539,620 bytes → 回填后 = 344,690,844 bytes（+151,224 bytes，中文 UTF-8 编码体积大于英文）。
- 9/9 TextAsset 全部导入成功。

## 版本记录

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-07-19 | 首次回填 | `build_localization.py` + `batch_replace_uabea.py`，9 个 TextAsset 替换 |
| 2026-07-25 | 重新回填 | 译文 CSV 更新后重新生成 XML 并回填；`batch_replace_uabea.py` 改为以原始备份为干净基底重建，新增已知 pathId 快速校验模式 |
| 2026-07-25 | 排查回填不生效 | 定位到游戏读取 `Documents\My Games\Expeditions Viking\Custom Localization\` 覆盖文件夹（旧汉化），删除后回填生效 |
| 2026-09-19 | 修复动态分支英文 | 本地化 291 个 `[Player:…/…]` 可见分支并重新回填；资源导出校验通过，待游戏内验证 |
| 2026-09-19 | 补全名称称号 | 本地化 51 条根级称号/名称并重新回填；资源导出校验通过，待游戏内验证 |
| 2026-09-20 | 发布 v1.2 | 生成不含游戏原始资源的 HDiffPatch 差分补丁；在独立临时游戏目录一键安装并哈希校验通过 |

## 对外发布

- 补丁：`Dispatch/Expeditions Viking_子非鱼汉化1.2.zip`
- 支持版本/平台：Steam Windows 版，Unity 5.6.4f1；仅支持原始 `resources.assets` 为 344,539,620 bytes 的安装。
- 载荷：`resources.assets.hdiff` 差分文件、HDiffPatch 应用器与一键安装脚本；不包含游戏本体或原始资源文件。
- 验证结果：已在实际游戏中确认汉化资源、对话、动态称谓和角色名称正常加载；独立临时目录按玩家安装流程还原后 SHA-256 与当前汉化资源一致。
- 已知问题：AI 自动翻译，部分长文本、术语与语气仍可能需要润色；其他 Mod 或不同游戏版本会导致差分拒绝应用。
- GitHub Release：`https://github.com/zfyu222/expeditions-viking-hanhua/releases/tag/v1.2`
- GitHub 下载资产命名：`Expeditions.Viking_ChinesePatch_.{版本号}.zip`（例如 `Expeditions.Viking_ChinesePatch_.1.2.zip`）。后续发布沿用此格式；项目本地归档仍按中文补丁命名规范保存。
- 百度网盘：待镜像上传。

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
