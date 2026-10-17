# 翻译操作记录

- 工作流：custom
- 自定义执行后端：codex
- 原文：项目根目录 `expeditions-viking_text.csv`
- 正式译文：项目根目录 `expeditions-viking_text_translated.csv`
- 中间产物：`TranslateFiles/`

由 game-translate 技能调用流程程序；正文前完成全文术语整理及冻结。所有任务经过程序验收。

## 2026-10-18：恢复 revision 8 并增量收尾

- 用户指定以 revision 8 继续；使用 `restore-glossary-revision --revision 8 --worker-stopped` 恢复原配置和快照，先备份数据库及配置，保留所有历史结果与尝试记录。
- 原有 187 个完成任务覆盖 5,312/5,331 条。此前批准的 10 条定向任务已包含在这个数字内。
- 程序按未覆盖 refs 差集只增加任务 `glossary_review-r8-00189-4679e88f`，19 条已通过 `batch-finish`；现有逐项语义审校覆盖为 5,331/5,331，原有通过项未重派。
- revision 9 的 15 个完成任务保留历史，183 个待办与 3 个停止的在途任务转为 obsolete；未生成的在途结果不冒充完成。
- 冻结前的构建仍发现旧 additions 使用 `translation` 而非 `recommended_translation`，以及旧快照同源重复项。收尾沿用 r8：字段兼容和相同结论去重由程序处理，只对已有结论的具体分歧定向裁决；不创建全量重审 revision。
- 正文仍为 23,195 条 source，未启动试译或全文翻译。术语冻结完成后另行记录构建产物和验证结果。
