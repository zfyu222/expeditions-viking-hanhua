# API 短 ID 传输修复审计（2026-10-18）

## 修改范围

仅修改共享基础程序的 3 个文件；基于已有用户修改继续，未覆盖其他修改。未修改项目数据库、配置、旧交接 input.md、结果或 AINiee 源码；未发起付费 API、未运行测试。

- workflow_task_contract.py：生成版本 1 的 session/task/input_hash 绑定映射；R0000635_90867238af 以真实 ordinal 前缀传输为 R0000635。映射完整覆盖 scope、拒绝重号，回复拒绝未知或重复短 ID、跨任务 envelope、映射版本/范围不符。模型可仅返回 records；显式给出 task_id/input_hash 时必须一致。
- workflow_batches.py：仅新生成 API translate、pilot_translate、review、final_review 交接创建 api_id_transport.v1.json；输入 records、模板、候选内 ID 和 ID 键统一为短表示。完整 canonical result.template.json、task payload/hash 和原校验器保持原协议。Codex 与旧无映射交接保持原行为。
- translation_workflow.py：先保存 response.raw.txt 和 response.parsed.json，再按当前有效 session 的映射还原 canonical result.json，继续同一 batch-finish 入口。原文、术语、metadata、保护映射、六维证据保留；不按顺序推断 ID，不生成语义证据。

## 静态阅读结论

已阅读技能及 custom_workflow/batch_execution 参考、render_batch_input、output_template/api_output_template、run_api 及原批次校验路径。原校验器继续验证 canonical task_id/input_hash、范围、唯一性及真实作者；缺失条目仍走原有可靠性处理。新传输不修改已完成的前 14 批 450 条，也不处置旧失败交接。可在主流程核实旧在途状态后启动新的 API run。AINiee pinned 模块均未修改，本次不触发其 hash 变化。仅代码与差异阅读，未进行运行验证。

## 文件 SHA256

| 文件 | 修改前 | 修改后 |
|---|---|---|
| workflow_batches.py | D77A33B966899A7ABB15B4BF5C8C417DFDFC506F3C15B7FFF45A08AA965FA246 | 5627A8065110009B7BE46212B3F2B9FA90C4B5AB09D67F1E3A1689D9DDE805A9 |
| workflow_task_contract.py | EFC739EAA99F818AA8EC21266794977AAA709B0AE8EA9421F10C617A76EEAF69 | 92D3E0D0A6454064B7A89CD1C12CBAABC9A5699F3D37FF36E008AFBA7E400311 |
| translation_workflow.py | 49D68376B909E8221F453601E294E843C42BD4546330768EBA2653D89411C14D | 1A3AF3478C018E8D6CC94C53672CB587E0683359682CA09667D94527E61E6EE6 |
