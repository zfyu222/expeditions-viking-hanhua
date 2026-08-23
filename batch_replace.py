#!/usr/bin/env python3
"""
使用 UABEA CLI 批量替换 resources.assets 中的英文 TextAsset 为中文
"""

import os
import subprocess
import shutil
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UABEA = r"D:\StaticHanHua\Tools\UABEA\UABEAvalonia\bin\Release\net8.0\UABEAvalonia.exe"
ASSETS_FILE = os.path.join(BASE_DIR, "Game", "Expeditions Viking_Data", "resources.assets")
CHINESE_DIR = os.path.join(BASE_DIR, "Chinese_Localization", "Chinese", "Localization")
WORK_DIR = r"C:\Temp\uabea_work"

# 英文名称 -> 中文文件
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

# 已知的英文文件大小（从原始导出）
EXPECTED_SIZES = {
    "DialogueEnglish": 3877517,  # ~3.7MB
    "GUIEnglish": 51833,
    "SkillsEnglish": 36033,
    "ItemsEnglish": 8420,
    "TutorialEnglish": 20920,
    "HomesteadUpgradesEnglish": 3165,
    "CharacterNamesEnglish": 153022,
    "SceneDataEnglish": 8833,
    "InputEnglish": 1517,
}


def run_uabea(args):
    """运行 UABEA CLI"""
    result = subprocess.run(
        [UABEA] + args,
        capture_output=True, text=True, timeout=60
    )
    return result.stdout, result.stderr, result.returncode


def main():
    os.makedirs(WORK_DIR, exist_ok=True)
    work_assets = os.path.join(WORK_DIR, "resources.assets")
    
    # 复制
    print(f"复制 assets 到 {work_assets}")
    shutil.copy2(ASSETS_FILE, work_assets)
    
    # 获取所有 TextAsset pathId
    print("\n获取 TextAsset 列表...")
    stdout, _, _ = run_uabea(["list", work_assets, "49"])
    
    # 解析 list 输出
    path_ids = []
    size_map = {}
    for line in stdout.split("\n"):
        match = re.match(r'^(\d+)\s+49\s+\S+\s+(\d+)', line.strip())
        if match:
            pid = int(match.group(1))
            size = int(match.group(2))
            path_ids.append(pid)
            size_map[pid] = size
    
    print(f"找到 {len(path_ids)} 个 TextAsset")
    
    # 通过大小匹配找到对应的 TextAsset
    # 对每个 TextAsset 导出并获取名称
    print("\n导出所有 TextAsset 获取名称...")
    name_to_pathid = {}
    for pid in path_ids:
        size = size_map[pid]
        out_file = os.path.join(WORK_DIR, f"export_{pid}.txt")
        stdout, _, _ = run_uabea(["exporttext", work_assets, str(pid), out_file])
        
        # 解析导出输出
        name_match = re.search(r'Exported TextAsset "([^"]+)"', stdout)
        if name_match:
            name = name_match.group(1)
            name_to_pathid[name] = pid
            # 检查是否是我们需要的
            if name in REPLACEMENTS:
                print(f"  [MATCH] {name} (pathId={pid}, size={size})")
    
    # 进行替换
    print("\n=== 导入中文 ===")
    replaced = 0
    for ename, cfile in REPLACEMENTS.items():
        if ename in name_to_pathid:
            pid = name_to_pathid[ename]
            chinese_path = os.path.join(CHINESE_DIR, cfile)
            
            if not os.path.exists(chinese_path):
                print(f"  [跳过] {ename}: 中文文件不存在")
                continue
            
            stdout, stderr, rc = run_uabea(["importtext", work_assets, str(pid), chinese_path])
            if rc == 0 and "Error" not in stdout:
                replaced += 1
                print(f"  [OK] {ename} (pathId={pid})")
                if stdout.strip():
                    print(f"    {stdout.strip()}")
            else:
                print(f"  [FAIL] {ename}: {stdout.strip()} {stderr.strip()}")
        else:
            print(f"  [未找到] {ename}")
    
    if replaced == 0:
        print("\n没有成功替换任何 TextAsset！")
        print("可能的原因：")
        print("  1. pathId 不正确")
        print("  2. importtext 命令失败")
        print("\n请关闭所有正在使用 resources.assets 的进程后重试。")
        return
    
    # 复制回游戏目录
    print(f"\n=== 部署 ===")
    # 备份
    backup_path = os.path.join(BASE_DIR, "backup", "resources.assets")
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    if not os.path.exists(backup_path):
        shutil.copy2(ASSETS_FILE, backup_path)
        print(f"已备份到 {backup_path}")
    
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
