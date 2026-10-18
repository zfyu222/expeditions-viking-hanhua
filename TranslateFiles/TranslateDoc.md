# 翻译操作记录

- 工作流：custom
- 自定义执行后端：api
- 原文：项目根目录 `expeditions-viking_text.csv`
- 正式译文：项目根目录 `expeditions-viking_text_translated.csv`
- 中间产物：`TranslateFiles/`

由 game-translate 技能调用流程程序；正文前完成全文术语整理及冻结。
试译：固定随机样本 → pilot_translate → pilot-report → 主 AI pilot-decide；按需 pilot-retry。
试译用于校准流程和风格，不要求逐句零错误；正式译文仍须完整独立审校和导出验收。

## 当前正式翻译：按最新规则重新开始

- 用户要求忽略旧正文数据、重新开始正式阶段。旧运行器已停止并归档；旧 6,530 条草稿及全部 672 个正式任务不参与本轮，原回复、API 消耗、作者和历史仍保留。
- 新正式范围经公开 restart-body 建立（revision 15），同步当前本地调度配置后 revision 16；全部 23,195 条 source，无译文、无旧正式候选/检查缓存、无在途请求。冻结 r8 哈希及已接受试译保留。
- 使用官方 `D:/StaticHanHua/Tools/localization/run_api_round.py --project <本项目> --stage translate`，不再调用旧 `TranslateFiles/scripts/api_round.py` 包装。
- 新协议：批内 `1`、`2` 等短编号，句内 `[P1]` 等短标记；程序恢复完整 ID 和保护内容。最新流程的 translate 仅收齐草稿；程序审校另行调用 draft_check，遇外部 Sol 任务/异常交回。阶段之间不自动串联。
- 当前全局本地模型 deepseek-flash、并发 5、max_requests 10000、max_completion_tokens 16384；正文 1024 原文 Token，完整输入预算 16384。凭据不复制、不输出。
- 旧进程中断的 reserved 请求保留为 interrupted_restart，usage 未知，不按零消耗或免费取消处理。旧消费累计不清零。
- 基线记录见 `reports/new_formal_restart_20261018.json`，原始备份见 `backups/restart_body_0582f94f910f4c8e99cecf292549db4f/`。

## 恢复 r16 首轮原稿与独立程序审校

- 已从 1,063 个首轮任务结果按 ID 恢复 23,195 条原稿，精确覆盖，无重复；排除带 strict_translation/draft_scan_key 的返修任务。任务输入指纹、源文绑定、会话结果、API 调用及实际作者逐项核对通过。
- 原例外及原始结果字段完整保存在快照，恢复只执行已知保护映射替换。快照 `snapshots/r16_first_draft_20261018T142909Z_9c5af3c9/`；恢复报告 `reports/restore_r16_first_drafts.json`。
- 完整恢复前备份及旧审校归档见 `backups/restore_r16_first_drafts_20261018T142909Z_9c5af3c9/`。新检查范围 revision 17，沿用共同程序的 revision 预算边界隔离旧修复计数；保留原任务结果、付费/执行/作者/lineage 历史，哈希核对未变。
- 只执行官方 runner `--stage draft_check`，结束后交回主流程。此次不启动 review、export 或回填。
- 已完成：6 轮常规修复；修复原始保护字面形式的通用程序误报后重新全量检查，17 条实际遗留交两个新 gpt-6-sol 实例修复。第 9 轮局部复查 17/17 通过，第 10 轮最终全量检查 23,195/23,195 通过，0 失败，无待办及在途任务。首轮快照哈希保持。
- 常规阶段 API 实际发送 700 次（含 11 次失败尝试），服务端报告输入 3,187,868、输出 535,072、总计 3,722,940 Token，缓存子项不额外相加。修复程序误报后的两次扫描阶段均未发送 API 请求；Sol 修复身份独立记录。报告 `reports/restored_r16_draft_check_completion.json`。
- 当前停在主流程：独立语义审校、正式导出、回填均未启动。
