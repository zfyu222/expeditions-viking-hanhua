#!/usr/bin/env python3
"""
使用 UnityPy 直接替换 resources.assets 中的英文 TextAsset 为中文
精确名称匹配，避免误匹配 EnglishNorse 等变体
"""

import os
import shutil
import UnityPy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_DIR = os.path.join(BASE_DIR, "Game", "Expeditions Viking_Data")
RESOURCES_FILE = os.path.join(GAME_DIR, "resources.assets")
BACKUP_DIR = os.path.join(BASE_DIR, "backup")
CHINESE_DIR = os.path.join(BASE_DIR, "Chinese_Localization", "Chinese", "Localization")

# 精确名称匹配
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


def main():
    # 1. 备份
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, "resources.assets")
    if not os.path.exists(backup_path):
        shutil.copy2(RESOURCES_FILE, backup_path)
        print(f"[备份] resources.assets")

    # 2. 加载中文内容
    chinese_data = {}
    for name, xml_file in REPLACEMENTS.items():
        filepath = os.path.join(CHINESE_DIR, xml_file)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                chinese_data[name] = f.read()
            print(f"[加载] {xml_file}: {len(chinese_data[name])} chars")

    # 3. 打开并替换（精确名称匹配）
    print(f"\n打开: {RESOURCES_FILE}")
    env = UnityPy.load(RESOURCES_FILE)

    replaced = 0
    for obj in env.objects:
        if str(obj.type) == "49":  # TextAsset type ID
            data = obj.read()
            name = data.m_Name
            if name and name in chinese_data:
                data.m_Script = chinese_data[name]
                data.save()
                replaced += 1
                print(f"  [替换] {name}: {len(chinese_data[name])} chars")

    # 4. 保存
    print(f"\n保存...")
    with open(RESOURCES_FILE, "wb") as f:
        f.write(env.file.save())

    print(f"\n完成！共替换 {replaced} 个 TextAsset")
    print(f"备份: {backup_path}")


if __name__ == "__main__":
    main()
