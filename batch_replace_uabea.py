#!/usr/bin/env python3
"""
使用修复后的 UABEA CLI 批量替换 resources.assets 中的英文 TextAsset 为中文
"""

import os
import subprocess
import shutil
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UABEA = r"D:\StaticHanHua\Tools\UABEA\UABEAvalonia\bin\Release\net8.0\UABEAvalonia.exe"
ASSETS_FILE = os.path.join(BASE_DIR, "Game", "Expeditions Viking_Data", "resources.assets")
BACKUP_FILE = os.path.join(BASE_DIR, "backup", "resources.assets")
CHINESE_DIR = os.path.join(BASE_DIR, "Chinese_Localization", "Chinese", "Localization")
WORK_DIR = r"C:\Temp\uabea_work"

REPLACEMENTS = {
    "DialogueEnglish": "Dialogue/DialogueChinese.xml",
    "GUIEnglish": "GUI/GUIChinese.xml",
    "SkillsEnglish": "Skills/SkillsChinese.xml",
    "ItemsEnglish": "Items/ItemsChinese.xml",
    "TutorialEnglish": "Tutorial/TutorialChinese.xml",
    "HomesteadUpgradesEnglish": "HomesteadUpgrades/HomesteadUpgradesChinese.xml",
    "CharacterNamesEnglish": "Names/NamesChinese.xml",
    "SceneDataEnglish": "SceneData/SceneDataChinese.xml",
    "InputEnglish": "Input/InputChinese.xml",
}

# 已知 pathId（来自 README，Unity 5.6 下稳定不变）。优先使用以跳过 858 个 TextAsset 的逐个导出。
KNOWN_PATH_IDS = {
    "DialogueEnglish": 9146,
    "GUIEnglish": 9040,
    "SkillsEnglish": 9165,
    "ItemsEnglish": 9309,
    "TutorialEnglish": 9799,
    "HomesteadUpgradesEnglish": 9063,
    "CharacterNamesEnglish": 9804,
    "SceneDataEnglish": 9795,
    "InputEnglish": 9744,
}


def run_uabea(args):
    result = subprocess.run([UABEA] + args, capture_output=True, text=True, timeout=180)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def main():
    os.makedirs(WORK_DIR, exist_ok=True)
    work_assets = os.path.join(WORK_DIR, "resources.assets")
    
    # 1. 复制到工作目录（从原始英文备份开始，保证干净重建）
    if not os.path.exists(BACKUP_FILE):
        print(f"首次运行：备份原始文件到 {BACKUP_FILE}")
        os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
        shutil.copy2(ASSETS_FILE, BACKUP_FILE)
    print(f"从原始备份复制到工作目录: {work_assets}")
    shutil.copy2(BACKUP_FILE, work_assets)
    
    # 2-3. 定位 9 个目标 TextAsset 的 pathId
    # 优先用已知 pathId（快速模式，仅 9 次 exporttext 验证名称），
    # 验证失败则回退到全量扫描（858 个 TextAsset 逐个导出）。
    name_to_pathid = {}
    use_known = all(n in KNOWN_PATH_IDS for n in REPLACEMENTS)

    if use_known:
        print("\n[快速模式] 用已知 pathId 验证名称...")
        verified = True
        for name, pid in KNOWN_PATH_IDS.items():
            out_file = os.path.join(WORK_DIR, f"check_{pid}.txt")
            stdout, _, rc = run_uabea(["exporttext", work_assets, str(pid), out_file])
            name_match = re.search(r'Exported TextAsset "([^"]+)"', stdout)
            actual = name_match.group(1) if name_match else None
            if actual == name:
                name_to_pathid[name] = pid
                print(f"  [OK] {name} -> pathId={pid}")
            else:
                print(f"  [MISMATCH] 期望 {name}，实际 {actual}（pathId={pid}）")
                verified = False
            if os.path.exists(out_file):
                os.remove(out_file)
        if not verified:
            print("部分 pathId 校验失败，回退到全量扫描...")
            name_to_pathid = {}

    if not name_to_pathid:
        print("\n获取所有 TextAsset 的 pathId...")
        stdout, _, _ = run_uabea(["list", work_assets, "49"])

        path_ids = []
        for line in stdout.split("\n"):
            match = re.match(r'^(\d+)\s+49\s+\S+\s+(\d+)', line.strip())
            if match:
                path_ids.append(int(match.group(1)))

        print(f"找到 {len(path_ids)} 个 TextAsset")

        print("\n匹配 TextAsset 名称...")
        for pid in path_ids:
            out_file = os.path.join(WORK_DIR, f"check_{pid}.txt")
            stdout, _, rc = run_uabea(["exporttext", work_assets, str(pid), out_file])
            name_match = re.search(r'Exported TextAsset "([^"]+)"', stdout)
            if name_match:
                name = name_match.group(1)
                if name in REPLACEMENTS:
                    name_to_pathid[name] = pid
                    print(f"  [MATCH] {name} -> pathId={pid}")
            if os.path.exists(out_file):
                os.remove(out_file)

    print(f"\n匹配到 {len(name_to_pathid)}/9 个 TextAsset")
    
    # 4. 导入中文（importtext 直接覆盖文件，可连续调用）
    print("\n=== 导入中文 ===")
    replaced = 0
    for name, cfile in REPLACEMENTS.items():
        if name not in name_to_pathid:
            print(f"  [跳过] {name}: 未找到 pathId")
            continue
        
        pid = name_to_pathid[name]
        chinese_path = os.path.join(CHINESE_DIR, cfile)
        
        if not os.path.exists(chinese_path):
            print(f"  [跳过] {name}: 中文文件不存在")
            continue
        
        stdout, stderr, rc = run_uabea(["importtext", work_assets, str(pid), chinese_path])
        if rc == 0 and "Imported" in stdout:
            replaced += 1
            print(f"  [OK] {name} (pathId={pid})")
        else:
            print(f"  [FAIL] {name}: {stdout} {stderr}")
    
    # 5. 部署（原始备份已在第1步保护，这里直接覆盖游戏文件）
    print(f"\n=== 部署 ===")
    try:
        shutil.copy2(work_assets, ASSETS_FILE)
        print(f"已替换 {ASSETS_FILE}")
    except PermissionError:
        print(f"ERROR: 文件被占用，请关闭游戏后重试")
        print(f"临时文件在: {work_assets}")
        return
    
    print(f"\n成功替换 {replaced} 个 TextAsset！启动游戏测试。")


if __name__ == "__main__":
    main()
