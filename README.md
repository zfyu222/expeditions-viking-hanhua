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
