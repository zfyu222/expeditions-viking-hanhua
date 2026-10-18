# 新版试译整体校准

## 规则与来源

用户明确要求按更新后的试译方法重新执行。本次依据最新 game-translate：同一批保存样本翻译一轮，由主 AI 阅读 pilot-report 判断方案和风格；不设置独立 API 试译审校、逐句六维证据或额外 Sol 试译验收。

r8 冻结表沿用原 3,529 项，原 5,331 条审校及真实来源不改。旧 30 条试译和审校、API 消耗、预算豁免及失败交接全部保留。恢复前数据库备份位于 `backups/before_new_pilot_calibration_20261018/`，不入库。

## 实际执行

1. 确认旧 API 执行器已结束、无锁和 reserved 请求，公开 recover 三个旧终结交接；再用 pilot-retry 归档旧任务并重新翻译保存的 30 条样本。
2. 首轮为 3 批。2 批直接完成；25 条批次在一次格式重试后有一条 ID 哈希末位错误：R0000255_f6f233cea5 应为 R0000255_f6f233cea8。唯一缺失/未知 ID 属同一逻辑记录号 255，主 AI 实际核对原文与译文后仅正规化该字段；原始文件、哈希和审计均保留，译文与例外未改，原 batch-finish 接纳该批。见 `pilot_id_correction_20261018.json`。
3. 主 AI 对照全部 30 条原译文及诊断做整体校准，认为普通词义受专名干扰、条件语气、无依据的长幼关系和个别对白称呼需调整；使用 pilot-decide retry 仅重试 4 条。
4. 通过 pause/configure/resume 增加文体规则，revision 13，semantic_reset=false；普通词不得强套专名、保留条件推测、不补亲属长幼、称呼口语自然。定向 4 条一批完成，失败 0。
5. 主 AI 阅读四条新结果：发热条件恢复“若已持续数周”；town 不再误译为唐河；young man 改成自然称呼；sister 不再擅自添加姐姐。由 pilot-decide accept 接受方案，保留其余样本及所有轮次。

## 校准结论及范围

已阅读首轮全部 30 条原译文及定向重试的 4 条，认为修订后方案可进入全文翻译。叙述整体可读，UI 简洁，基本专名、BBCode 和字面转义保留。结论用于流程和风格校准，不声称全文正确率或样本逐句零错误。

当前 9 条机械术语失败多数涉及普通 rest/don/man/father/are 等词义，或 Greedy、aoo、flanked、shield 等保护标记内部词形；不据此强改正确译文或把 9/30 当作语义错误率。正式翻译仍须完成真实语境例外及独立审校。

明确遗留：`[Greedy:He/She]` 等可见分支被当前保护器整体隐藏，模型不能翻译其内部文本。该项目的性别分支本地化/回填策略需专项处理，保留 actor/name 标识；不把保护造成的英文分支算成试译模型自行漏译，也不宣称已解决。

校准接受后正式 23,195 条记录均恢复为 source，尚未执行全文正文，无运行中任务。r8 冻结 SHA256 仍为 `8b1369e804c5c7f66803e0961da266077ff087a5ecc849b9e6806ece5c8b31a4`。

## 归档

- 接受报告：`accepted/pilot_574f7dd66f06341d/report.json`。
- 主 AI 决定：同目录 `main_assessment.json`；报告哈希 `574f7dd66f06341dc98e9b6a18c875928ef0d8a2542dbe76a6ecb8ed0a988b00`。
- 各轮实际报告与决定：`pilot_rounds/`、`pilot_feedback/`。
- 首轮 runner：`api_runs/d29533e684414a1da46cc6bc6eb526bb.json`；状态反映 ID 正规化之前的失败，后续公开收集记录及校准报告为准。
- 定向验证 runner：`api_runs/a1065841b03445ce976f2bb100cfecc3.json`。

旧 `r8_completion_20261018.md` 中的独立试译审校、12 次预算阻断和 Sol 试译验收均为历史阶段，当前以本报告及新技能为准。
