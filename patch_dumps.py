#!/usr/bin/env python3
"""
修改 UABEA text dump 文件中的 m_Script 值为中文 XML
UABEA dump 格式：
0 TextAsset Base
 1 string m_Name = "DialogueEnglish"
 1 string m_Script = "..."

替换策略：读取整个 dump 文件，将 m_Script 的值替换为中文 XML 内容
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DUMP_DIR = os.path.join(BASE_DIR, "AAA")  # GUI dump 输出目录
CHINESE_DIR = os.path.join(BASE_DIR, "Chinese_Localization", "Chinese", "Localization")
OUTPUT_DIR = os.path.join(BASE_DIR, "AAA_patched")

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


def patch_dump_file(dump_path, name, chinese_path, output_path):
    """修改 dump 文件中的 m_Script 值"""
    with open(dump_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    with open(chinese_path, "r", encoding="utf-8") as f:
        chinese_xml = f.read()
    
    # UABEA dump 中 m_Script 的格式:
    # 1 string m_Script = "escaped content"
    # 需要把中文 XML 内容做 C# 字符串转义
    
    # 转义中文 XML 内容
    escaped = chinese_xml.replace("\\", "\\\\").replace('"', '\\"').replace("\r\n", "\\r\\n").replace("\n", "\\r\\n")
    
    # 替换 m_Script 的值
    # 匹配:  1 string m_Script = "..." 
    pattern = r'( 1 string m_Script = )"([^"]*(?:\\.[^"]*)*)"'
    new_content = re.sub(pattern, f'\\1"{escaped}"', content, count=1)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return len(new_content)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 找到所有 dump 文件
    dump_files = {}
    for f in os.listdir(DUMP_DIR):
        if f.endswith(".txt"):
            for name in REPLACEMENTS:
                if name in f:
                    dump_files[name] = os.path.join(DUMP_DIR, f)
                    break
    
    print(f"找到 {len(dump_files)} 个 dump 文件:")
    for name, path in dump_files.items():
        print(f"  {name}: {os.path.basename(path)}")
    
    # 检查缺失的
    missing = set(REPLACEMENTS.keys()) - set(dump_files.keys())
    if missing:
        print(f"\n需要在 GUI 中导出以下 dump 文件: {missing}")
    
    # 修改每个 dump
    print("\n修改 dump 文件...")
    for name, dump_path in dump_files.items():
        chinese_path = os.path.join(CHINESE_DIR, REPLACEMENTS[name])
        if not os.path.exists(chinese_path):
            print(f"  [跳过] {name}: 中文文件不存在")
            continue
        
        output_path = os.path.join(OUTPUT_DIR, os.path.basename(dump_path))
        size = patch_dump_file(dump_path, name, chinese_path, output_path)
        print(f"  [OK] {name} -> {os.path.basename(output_path)} ({size} bytes)")
    
    print(f"\n完成！修改后的 dump 文件在: {OUTPUT_DIR}")
    print("在 UABEA GUI 中对每个 TextAsset 右键 -> Import Dump -> 选择对应的 patched dump 文件")


if __name__ == "__main__":
    main()
