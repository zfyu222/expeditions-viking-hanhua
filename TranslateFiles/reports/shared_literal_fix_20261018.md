# 方括号术语通用修复记录

修复位于共享 `Tools/localization/ainiee_bridge.py` 的 `FrozenMatcher.get_source_state`。完整的标识符、命名标记及斜线选项按字面量匹配，包括 `[Executioner:Name]`、`[Player:snake/mare]`、`[Hunter/Huntress]`。包含范围连字符、反斜杠、脱字符等正则字符类语法时继续使用基类推断，因此 `[a-z]`、`[A-Z0-9]` 的处理路径不变。

这是自定义工作流共享适配器修复。没有修改 AINiee GUI helper 的现有 `_LITERAL_BRACKET_IDENTIFIER_PATTERN`、`normalize_row` 或显式 `src_state` 处理语义。其他 source 继续委托原 helper。

## 最小改动范围

- 共享 `ainiee_bridge.py`：为既有 `FrozenMatcher` 添加 `get_source_state`，共 11 行。
- `TranslateFiles/scripts/api_round.py` 和 `workflow.py`：移除项目 adapter 导入与 `install(shared.bridge)`。
- `TranslateFiles/scripts/recheck_paid_pilot.py`：移除项目 monkeypatch 的导入、切换和重置；仅按当前共享实现复检一次，结果字段改为 `current` / `all_pass_current`，避免把同一个实现伪装成前后对照。
- 保留 `viking_term_adapter.py` 及既有诊断、复检报告，供历史解释。

没有运行测试、复检脚本或 API；仅做代码及差异阅读。没有修改数据库、预算、冻结表、原始付费结果或其接受状态，没有提交 Git。

## SHA256（修复前 → 修复后）

| 文件 | 修复前 | 修复后 |
|---|---|---|
| `Tools/localization/ainiee_bridge.py` | `afa052708bb8dd04fe0c3ecc305055120fdb686d417478499cd94ab52f06bf2c` | `4fe9e140a5a633ba4bae7b9906699c7788d7e80bb195ac8a422677b8d8717260` |
| `TranslateFiles/scripts/api_round.py` | `224484991c6c4d6fffcfcbcf85fe4981ed897291b32e08a2da99c57e585a8445` | `c3339df3d5cf0a93072a6489c19795a769d0fb92e4eae12ffb36ebeaef4a7f69` |
| `TranslateFiles/scripts/workflow.py` | `54bf3fd7703907c058bc709849fbcae2e311ab06c2239c398868b9eb220c9d12` | `1b784bf5d09c84a55f8bc5ec1b36644faded27ad26e011843b36e7da3a1692de` |
| `TranslateFiles/scripts/recheck_paid_pilot.py` | `e4dc7e513858f1d6fa82c4d212985b0149bcfb663eb82e8f2f9f3420839b6aa3` | `e9d11873de94f35e0008e0c41b4e1634edb88a04d1224298e9ccc571b00d2c7c` |

AINiee `ModuleFolders/Domain/PromptBuilder/GlossaryHelper.py` 的 SHA256 前后均为 `6b3072989b77c84787774439c79aaea7d4727fcda104667d8833b53bb490446f`。

## Provenance 与复用边界

`bridge.provenance()` 记录 AINiee 的 Git commit 及 `GlossaryHelper.py`、`TextProcessor.py`、`LLMClientFactory.py`、`OpenaiRequester.py` 四个模块 SHA256。此次仅修改共享适配器及三个项目入口，四个 pinned 模块均未修改，因此不会因这次修复触发 `Workflow.config()` 的 AINiee provenance 不匹配，不需要迁移或重建 r8。

若未来修改 pinned 模块，必须先保留旧 provenance 和既有产出，经有审计的工作流迁移明确记录新旧模块哈希、原因、受影响范围及必要增量复检；不能直接改数据库 provenance、绕过比较或新建工作流来丢弃既有术语审校与预算历史。当前修复不执行该迁移。

源头修正只消除方括号字符类伪术语。历史报告中的其他真实术语问题仍须按现有流程处理，不能据此自动接纳全部付费候选。
