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

## 2026-10-19：独立审校接续与格式流程改进

- 已启动独立 API review。首段运行 170 次请求，保存 141 批、2,144 条候选；28 次格式失败中 18 次 JSON 语法、5 次 keep/translation 字段、2 次短编号、3 次术语引用。整轮未完成，不宣称语义通过。
- Sol 离线恢复 5 个交接、86 条候选，原始回复、实际作者/会话及全部消耗保留，没有补造证据或请求 API。当前 review 共 146 批、2,230 条候选，剩余 1,335 批；恢复报告 `reports/review_paid_format_recovery.json`。
- 用户要求先改流程。共用程序新增合法整数短编号的无损归一化；格式重试附具体错误、JSON 行列和有限片段，补充输入仍检查完整预算；保留原尝试上限和真实作者。未知/重复/布尔编号、缺少 keep/translation 或证据仍拒收。回复元数据补记 finish_reason 与返回模型。
- 隔离副本真实验证仅发 2 次请求，共 34 条：普通审校和带具体格式诊断的重试均成功解析、映射、保存。两次 finish_reason=stop，服务已确认兼容 JSON object 模式，随后仅在本机 extra_body 中启用此模式。无静默降级重发。
- 严格验收保留：34 条中有 1 条 logic 证据状态不合格，正常拒绝，不算语义通过；验证结果不并入正式项目候选。原生产项目仍为 2,230 条候选，无在途请求。验证与真实 Token 记录见 `reports/api_format_upgrade_validation.json`。
- 当前先完成流程改进，尚未恢复剩余 review；不导出或回填。

## 2026-10-19：各 API 阶段可靠性补齐完成

- 用户要求立即开发，已删除 02-30-api 定时任务。范围为自定义翻译共用 API 的提取、术语审校、试译、翻译、程序返修、审校、润色、复审及恢复；未扩大本项目的实际汉化范围。
- 提取输出 analysis 不强加记录编号；术语 e/f、本条 t 与正文记录编号按已绑定字段命名空间无损规范化。未知、只读关联、布尔/浮点和转换后重复仍拒收，出处序号与语义内容不改。
- 格式重试按阶段给出正确输出约定，修复提取/翻译重试中错误要求 keep 的问题；附具体字段/条目及 JSON 行列、有限片段，保留次数与完整输入预算。中断恢复后的坏回复重发同样携带具体诊断，原回复及旧 rejection 不覆盖。
- 全阶段共用 JSON 模式、回复 metadata 与性能日志。恢复时补回 parsed，缺少历史用量或旧库缺 session_id 时保留未知；不补造 stop、用量或语义通过。
- 36 项契约/边界检查、56 项流程/传输/并发/执行器一致性回归通过，并额外复核术语旧回复恢复。新独立样本完整跑通各阶段；另用历史失败回复验证恢复后重发，总计 11 次真实 API 请求，服务端报告输入 15,746、输出 6,566、总计 22,312 Token（缓存 6,528 为输入子项，不另相加）。
- 生产 revision 17、r8 冻结哈希、146 个 review 完成批、1,335 个待办批及 2,230 条候选保持不变；无在途请求。本次不继续生产审校、不导出或回填。
- 汇总报告：`reports/api_all_stages_reliability_20261019.json`；隔离验证及原始回复：`D:/StaticHanHua/Tools/localization/verification/api_reliability_all_stages_20261019/`。小样本验证不保证模型永不输出错误；原有证据及语义门槛继续执行。

## 2026-10-19：独立语义审校与正式导出完成

- 延续 revision 17 已保存候选，首轮独立审校完整覆盖 23,195 条。统一验收首轮 22,056 条通过、1,139 条需处理；后续仅重派失败项，保留通过记录、真实来源、作者及累计修复次数。首个失败门槛统计不代表翻译准确率。
- 保留所有付费回复，Sol 对 20 个异常批次作无损格式恢复，共收回 340 条候选，没有为这些恢复新增 API 请求。另有缺少必需字段的批次交新 Sol 独立完成；不自动补 keep、译文或证据。
- 本次接续实际发送 1,720 次 API 请求（包括 237 次失败尝试），服务端报告输入 5,758,196、输出 5,270,021、总计 11,028,217 Token；缓存 2,459,648 为输入子项，不另相加。旧消费及作者历史保留。
- 审校修复按共同累计预算升级：Sol 定向修复保留已满足术语及语境例外；最后所有 23,195 条均到 review。最终报告的 41 项明确遗留提示经 Sol 裁决，3 条确需修复并通过复查；更新报告只再核对 2 项，其余裁决复用。最终质量轮 2 已批准，未启动全文润色。
- 正式译文 `expeditions-viking_text_translated.csv` 由官方 export 生成，无表头、单列、按源记录顺序。导出前全库结构、保护内容及术语/已审语境例外检查通过；最终验收报告 `TranslateFiles/reports/final_validation.json`，本轮汇总 `TranslateFiles/reports/review_completion_20261019.json`。
- r8 冻结术语哈希及审校前 r16 草稿快照哈希不变。没有重新提取术语、重译全文或调用 restart-body；API 模型仍为 deepseek-flash，升级及争议角色使用独立 gpt-6-sol 实例。
- 待下一阶段：动态可见分支仍整体保护（已有清单 498 次、53 种形式），需项目内专项处理及回填后实机检查。本次未修改游戏载荷、未回填或发布，新导出实机状态为 pending_repack；此前版本的实机结论不能替代本轮验证。
- 接续中发现历史无关例外在 API term_refs 中无法表达撤销，已由独立 Sol 使用完整共同 Codex 协议具证撤销并正常收集；未改共享程序或放宽门槛。


## 2026-10-19：238 条回填补译审校闭环与 v1.4

- 用户授权独立审校全部 238 条回填改动及必要后继修复、打包发布。项目脚本在备份后按源记录 ID 导入已有回填候选，原 API 消耗、作者及修复计数保留；其余 22,957 条通过结论沿用。
- 共用 API 审校整轮收集，局部协议失败由新 Sol 实例定向处理；统一扫描后仅修复失败项。对 6 条整句禁翻导致的选项漏译回退补充项目显示机制，按具体语境例外复查，冻结术语未变。
- 238 条全部通过；与原回填候选相比修正 13 条，六维证据及真实来源见 `reports/repack_review_evidence_20261019.json`。最终遗留 2 项争议经新 Sol 判 contextual，质量轮 3 批准，正式 export 完成。
- 正式译文 SHA-256 `bcb10634df1ac8053408cae6492186a674a808982e4e85f3c05c2257a77f7a9b`；新资源 SHA-256 `307cb72ef9b5d1cc34dc2755ec226bdd72e49e154b940354195fd00f2aa3009b`。回填只另处理 291 处性别分支，禁止旧补译覆盖已审正式译文。
- 用户随后明确要求不进入游戏测试，完成后直接发布。已记录 `reports/release_v14_user_instruction.json`，本版只作资源、差分及实际安装验证，未生成新的实机通过结论。项目专用发布入口验证正式语义与实际载荷绑定，未放宽共享程序。
- v1.4 ZIP 已从 `Dispatch/Files/` 生成，压缩包校验和、更新日志及按玩家流程实际安装均通过，错误版本拒绝/恢复正常。报告：`reports/release_v14_static_validation.json`、`reports/release_v14_archive_validation.json`。

- 发布完成：GitHub 最新稳定版 `v1.4`，https://github.com/zfyu222/expeditions-viking-hanhua/releases/tag/v1.4 。上传资产 `Expeditions.Viking_ChinesePatch_.1.4.zip` 为 1,997,947 bytes，匿名下载后 SHA-256 `60622bf984f717f0919bf9f977f808011e0945304855445f20b964e9a32631e4` 与本地 ZIP 一致。发布记录见 `reports/release_v14_publication.json`。
- 当前无百度网盘上传 MCP，网盘镜像未上传；未修改网盘旧版文件。旧 GitHub Releases 及本地归档均保留。
