"""生成并记录本轮 v1.3 载荷的实机验证结果（由用户实机确认）。"""

import hashlib
import json
from pathlib import Path

BASE = Path(r"D:\StaticHanHua\Projects\Expeditions Viking")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(path, game_path=None):
    record = {"path": path, "sha256": sha(BASE / path)}
    if game_path:
        record["game_path"] = game_path
    return record


report = {
    "translation_sha256": sha(BASE / "expeditions-viking_text_translated.csv"),
    "game_version": "Steam 当前版本（Unity 5.6.4f1，原始 resources.assets 344,539,620 字节）",
    "platform": "Steam（Windows）",
    "payload_files": [
        entry("ReleasePayload/resources.assets.hdiff", "ZFY_Translation_Patch/resources.assets.hdiff"),
        entry("ReleasePayload/hpatchz.exe", "ZFY_Translation_Patch/hpatchz.exe"),
        entry("ReleasePayload/应用汉化补丁.bat", "ZFY_Translation_Patch/应用汉化补丁.bat"),
    ],
    "evidence_files": [
        entry("TranslateFiles/reports/repack_verification.json"),
        entry("TranslateFiles/reports/build_xml_verification.json"),
        entry("TranslateFiles/reports/repack_translation_prep.json"),
    ],
    "checks": [
        {
            "category": "fonts",
            "status": "pass",
            "scene": "启动后主界面与对白界面",
            "notes": "用户实机确认中文字体显示正常，无缺字或方块。",
        },
        {
            "category": "layout",
            "status": "pass",
            "scene": "对白与选项文本",
            "notes": "用户实机确认文本排版正常，选项与对白未出现换行错乱。",
        },
        {
            "category": "ui",
            "status": "pass",
            "scene": "游戏内 UI 与技能/物品提示",
            "notes": "用户实机确认界面文本为中文。",
        },
        {
            "category": "dialogue",
            "status": "pass",
            "scene": "对话与玩家选项",
            "notes": "用户实机确认对话与选项显示中文，未再出现英文选项片段。",
        },
        {
            "category": "quest",
            "status": "not_applicable",
            "scene": "",
            "notes": "本轮实机确认未单独覆盖任务日志界面，按未验证项记录。",
        },
    ],
    "notes": "载荷由 2026-10-19 回填的 resources.assets 生成差分；用户在部署后实机确认字体、排版、UI 与对话正常。",
}

path = BASE / "TranslateFiles/reports/in_game_check_manual_v13.json"
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
