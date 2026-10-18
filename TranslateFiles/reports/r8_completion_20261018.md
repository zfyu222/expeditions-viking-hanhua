# revision 8 术语审校收尾与 API 交接

- 日期：2026-10-18（北京时间）。
- 原文：`expeditions-viking_text.csv`，23,195 条。
- 审校基准：revision 8 原快照 5,331 条，原有 187 批加 19 条补验收任务，共 188 个有效任务；全表 refs 恰好覆盖一次。
- 同源重复：403 组语义字段相同，保留来源后机械合并；276 组已有结论存在差异，以 36 个定向包裁决，全部通过身份、范围、来源、连续摘录及阻断问题检查。
- 两条旧 addition 的 `translation` 字段仅在派生构建中正规化为 `recommended_translation`。watch tower、Stronghold 的细分类“建筑”保留到 note，正式分类使用允许的“其他”；原审校文件不改。
- 正式冻结表：`glossary/r8/freeze_731eced6/built/glossary_reviewed.json`。
- 冻结 SHA-256：`8b1369e804c5c7f66803e0961da266077ff087a5ecc849b9e6806ece5c8b31a4`。
- 冻结数量：人物 1,386，术语 1,728，禁翻 415，合计 3,529。
- 完整审校决定及合并来源：`glossary/r8/freeze_731eced6/glossary_decisions.json`；构建变更及清单在其 `built/` 子目录。
- 冻结前备份：`backups/before_r8_freeze_ec867add6f23/`，不入库。

## 实现边界

本次特殊适配只存在于项目 `scripts/r8_continue.py` 和 `scripts/r8_glossary_resolution.py`，导入共享构建器执行原有质量检查。共享基础程序及技能文档中的特殊适配已撤销；原任务状态、真实审校身份与旧失败产物保留，不把废弃任务伪装为完成。

## 后续 API 执行

用户已选择自定义 API，沿用本地配置的 `mimo-v2.6-flash`，不复制或提交凭据。API 后端切换通过既有 configure，保留 r8 冻结表且 semantic_reset=false；旧 `history/config_r9.json` 已先归档到 `history/pre_api_r9_3a466ff98ad3/`。

原 150 条试译预计翻译 7 批、审校 10 批，超过 12 次执行预算。通过既有 reduce-pilot 缩至 30 条代表性样本，预计翻译 2 批、独立审校 3 批，累计上限 6 次；已完成术语审校不重跑。

首轮 API runner 在任务分配前因单条完整输入 16,947 Token 超过 16,384 的项目保护预算而终止，尚未发出付费请求或取得译文。后续仅通过项目内输入预算适配继续，保留完整原文、术语与质量门槛；先完成试译及 Sol 验收，再开放全文翻译。

## API 试译阻断与保存结果

- 项目输入预算调整为 24,576 后，运行回执 `api_runs/6551eae2fbfb4f95a0cc04747f0ed8d6.json` 返回 `needs_attention`。5 次请求均已收到结果，不得盲目重放。
- 根因之一是 AINiee 匹配器把 `[Executioner:Name]` 等实际冻结的游戏标记推断为正则字符类，生成单字母伪术语；不是 r8 原表含有这些单字母条目。
- `scripts/viking_term_adapter.py` 只在本项目进程内用独立 helper 子类将实际冻结的方括号标记按字面解释，保留其他匹配行为。`scripts/api_round.py` 以及常规 CLI `scripts/workflow.py` 统一启用它。共享文件和冻结原件均未改动。
- `scripts/recheck_paid_pilot.py` 对保存候选执行原严格校验，数据库以只读方式打开。报告 `paid_pilot_literal_recheck_20261018.json`：30 条中 16 条通过、14 条仍有普通术语门槛失败，没有新增方括号标记。整批尚未接纳，不能据此声称试译通过；不自动补造例外或审校结论。
- 试译执行次数准确为 **5/6**，3 个任务停留于终结失败交接，没有正在运行的 API 请求，已建 5 个交接均已请求。剩余 1 次不足以完成修复与独立审校；已向用户申请恢复默认 12 次上限，保留已用次数、原结果及真实作者，等待决定前不继续请求。

## 用户批准恢复预算后的进展

- 用户批准恢复默认 12 次上限，并明确：通用基础程序缺陷可以修复共享程序，r8 的特殊兼容仍限于项目内。
- 共享 `ainiee_bridge.py` 现将完整方括号游戏标记按字面匹配；项目入口已移除临时 adapter 启用。AINiee 本体及 pinned provenance 未变。详见 `shared_literal_fix_20261018.md`。
- 共享 configure 增加仅调整试译预算的安全入口，在暂停、无执行器锁、无保留请求、无等待交接且运行任务均为终结试译交接时，保留 revision、任务及累计次数。共享 pilot-plan 不再将已经计次的在途任务重复计算为未来领取；批次同步由 configure 统一判断安全性，保留项目覆盖后的无变更情形。
- 项目恢复脚本备份并复检原候选，保留作者及旧回复，延长已确认停止的原租约并记录旧值；分配 14 条定向修复，累计 8/12。恢复报告为 `paid_pilot_resume_20261018.json`。
- 修复执行回执 `api_runs/6ae729c83dd44fdd83a5afd58fc58657.json`：3 包全部接纳，failed=0。30 条试译全部保存，术语表和原始审校记录不变。
- 修复完成后，按实际译文及语境例外重算，独立审校需 6 批而非之前的预估 3 批，预计累计 14 次，超过批准的 12 次。尚未派发独立审校。只读内存预估显示 20 条代表性子样本需 3 批，累计 11 次；已向用户申请是否采用现有 reduce-pilot 缩样复用方案。所有 30 条付费结果均保留。
