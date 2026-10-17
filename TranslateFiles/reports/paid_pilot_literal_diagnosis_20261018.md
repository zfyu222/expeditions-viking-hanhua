# r12 付费试译候选离线复检

本次未发出 API 请求，未修改工作流数据库、冻结表、原始付费回复、译文或例外，未修改共享工具与技能。

## 根因

`AINiee/ModuleFolders/Domain/PromptBuilder/GlossaryHelper.py` 的 `normalize_row` 无条件重新推断 `src_state`；现有纯字母方括号例外仅识别 `\[[A-Za-z]+\]`。因此冻结表中的 `[Executioner:Name]`、`[Player:snake/mare]`、`[Hunter/Huntress]` 被解释为正则字符类。`collect_matched_rows` 再把 `src` 改成 `match.group(0)`，产生 `n`、`t`、`/`、`:` 等伪术语；严格术语门槛要求译文包含相应完整 dst，导致失败。冻结表没有这些单字母术语；无需重做 r8。

例如任务 `pilot_translate-r12-00002-6cfa15f4-s162976c3/7543e41d1eee830536f96bdfaeeae173.json` 的匹配项保留 `source=[Executioner:Name]`，但 `src=n/t`、`dst=[Executioner:Name]`、`src_state=regex`。

## 项目内修复

`scripts/viking_term_adapter.py` 提供独立 helper 子类，只将冻结表实际存在且符合游戏方括号标记格式的 source 作为字面量处理；其他正则推断逻辑保持原样。没有修改原 helper 类、共享文件或冻结表。

`scripts/api_round.py` 已启用该 adapter；后续共享流程 CLI 应经 `scripts/workflow.py` 入口调用，同样启用 adapter。导入共享工作流的其他项目脚本应显式调用 `install(shared.bridge)`。

## 复检结果与复用边界

逐条原/修复后诊断、原 receipt 及计数见 `paid_pilot_literal_recheck_20261018.json`。通过原 `validate_body_row` 离线严格门槛的候选为 **16/30**，剩余 **14/30** 仍有普通术语缺失或语境歧义，均保留失败。三个整批均未全过，因此没有重开或接纳任何会话。

残余诊断包含 `rest`、`don`、`executed`、`man`、`are`、`father`、`hird`、`chance`、`end`、`Greedy`、`arms`、`throwing`、`saw`、`god`、`head`，以及两条教程的 `aoo`、`flanked`、`shield`。这些需要后续语义审校判断，不能批量编造例外或自动放宽门槛。

30 条恢复占位符后的候选均未出现原文没有的额外方括号标记；抽看人物背景、教程及首批叙事回复，没有发现为满足单字母伪术语而塞入对应完整英文变量的现象。该检查不等同于完整语义审校。

## 当前预算与后续

只读 `pilot_plan`：已用执行 **5**，当前上限 **6**；5 个 pilot API 记录均为 received，已建 handoff 均已请求，未请求 session **0**。原错误中的 “Pilot repair budget exhausted after repair allocation” 没有留下第六个 pilot handoff/quality_attempt。

当前 3 个任务仍 running，正式接纳的试译/审校为 0/0；计划报告 translation_batches=2、review_batches=3、within_budget=false。由于整批尚未接纳，该预估仍包含已持有付费候选的翻译范围，不能直接理解成还需重付两批翻译。

保留全部累计记录与当前候选。后续先处理 14 条真实诊断，再复检原候选；仅对未通过范围申请必要语义修复，并完成 3 批独立试译审校及 Sol 验收。若调整上限，应使用现有 configure 留下审计，保留已用 5 次，不清历史、不重做 r8。本次没有调整预算。
