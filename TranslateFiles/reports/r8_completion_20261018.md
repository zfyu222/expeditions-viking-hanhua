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
