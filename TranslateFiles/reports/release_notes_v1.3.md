# 《Expeditions Viking》子非鱼AI汉化补丁 v1.3

为 Steam Windows 版《Expeditions Viking》制作的简体中文汉化补丁，覆盖全部 23,195 条本地化文本。

## 汉化内容

对话与玩家选项、界面 UI、技能、物品、教程、家园升级、角色名称与称号、场景数据、输入提示。

## 适用版本

- Steam 当前版本（Unity 5.6.4f1）
- 仅支持原始 `resources.assets` 为 344,539,620 字节的安装
- 平台：Steam（Windows）

## 安装方法

1. 退出游戏。
2. 把压缩包内的 `ZFY_Translation_Patch` 文件夹解压到游戏根目录（与 `Expeditions Viking_Data` 同级）。
3. 运行 `ZFY_Translation_Patch\应用汉化补丁.bat`，脚本会自动备份原 `resources.assets` 并应用差分。
4. 启动游戏，在语言设置中选择 **English**（汉化替换的是英文文本资源）。

## 卸载 / 恢复

删除 `ZFY_Translation_Patch` 文件夹，把 `Expeditions Viking_Data\resources.assets.zfy.backup` 改回 `resources.assets` 覆盖现有文件。

## 实机验证

已在 Steam Windows 版实机确认字体、排版、UI 与对白/选项显示正常；另在独立临时目录按玩家安装流程完整还原，结果 `resources.assets` 的 SHA-256 与测试载荷一致。

## 已知问题

- AI 自动翻译，部分长文本、术语与语气仍可能需要润色。
- 任务日志界面本轮未单独实机验证。
- 其他 Mod 或不同游戏版本会导致差分校验失败。

## 后续更新

补丁后续可能会更新，建议关注或订阅本项目的 GitHub 仓库 / Releases，或收藏、订阅网盘发布渠道，及时获取新版补丁。

## 更新日志

- v1.2（2026-09-20）：修复动态性别称谓残留英文，并补全角色名称称号与动物名翻译。
- v1.3（2026-10-19）：基于全新一轮 AI 翻译重建全部 23,195 条文本；回补 238 条选项漏译、修正 291 处性别称谓分支、统一术语与转义格式。

## 文件校验

压缩包内附 `SHA256SUMS.txt` 与 `PATCH_MANIFEST.json`，可用于核对文件完整性。
