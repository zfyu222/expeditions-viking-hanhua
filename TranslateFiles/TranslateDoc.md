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
- 新协议：批内 `1`、`2` 等短编号，句内 `[P1]` 等短标记；程序恢复完整 ID 和保护内容。translate 在同一进程内自动完成草稿扫描及常规修复，遇外部 Sol 任务/异常再交回。阶段之间不自动串联。
- 当前全局本地模型 deepseek-flash、并发 5、max_requests 10000、max_completion_tokens 16384；正文 1024 原文 Token，完整输入预算 16384。凭据不复制、不输出。
- 旧进程中断的 reserved 请求保留为 interrupted_restart，usage 未知，不按零消耗或免费取消处理。旧消费累计不清零。
- 基线记录见 `reports/new_formal_restart_20261018.json`，原始备份见 `backups/restart_body_0582f94f910f4c8e99cecf292549db4f/`。
