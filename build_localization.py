#!/usr/bin/env python3
"""
Expeditions Viking 汉化 - 第3步：将翻译结果写回 XML 文件（修复版）
直接使用 extracted_strings.csv 中的 key 匹配
"""

import os
import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALIZATION_DIR = os.path.join(BASE_DIR, "output", "full-project", "ExportedProject", "Assets", "Resources", "localization")
TRANSLATED_CSV = os.path.join(BASE_DIR, "extracted_for_ainiee_translated.csv")
EXTRACTED_CSV = os.path.join(BASE_DIR, "extracted_strings.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "Chinese_Localization")

CATEGORY_FILES = {
    "dialogue": "DialogueEnglish.txt",
    "gui": "GUIEnglish.txt",
    "homestead": "HomesteadUpgradesEnglish.txt",
    "input": "InputEnglish.txt",
    "items": "ItemsEnglish.txt",
    "names": "CharacterNamesEnglish.txt",
    "scenedata": "SceneDataEnglish.txt",
    "skills": "SkillsEnglish.txt",
    "tutorial": "TutorialEnglish.txt",
}

CATEGORY_DIRS = {
    "dialogue": "dialogue",
    "gui": "gui",
    "homestead": "homesteadupgrades",
    "input": "input",
    "items": "items",
    "names": "names",
    "scenedata": "scenedata",
    "skills": "skills",
    "tutorial": "tutorial",
}

CUSTOM_CATEGORY_DIRS = {
    "dialogue": "Dialogue",
    "gui": "GUI",
    "homestead": "HomesteadUpgrades",
    "input": "Input",
    "items": "Items",
    "names": "Names",
    "scenedata": "SceneData",
    "skills": "Skills",
    "tutorial": "Tutorial",
}

# CharacterNamesEnglish 的根级称号、动物名不在 Male/Female 节点内，旧提取器未将
# 它们写入翻译 CSV。它们会直接拼接在角色名后（例如“Ragnhildr the White”），
# 因此在生成名称 XML 时明确覆盖；普通人名仍沿用 CSV 中的逐行译文。
NAME_STATIC_TRANSLATIONS = {
    "Wolf": "狼", "WolfDefinite": "那匹狼", "Hound": "猎犬",
    "HoundWar": "战犬", "Barghest": "巴格斯特", "WolfProwler": "巡猎狼",
    "WolfMother": "狼母", "WolfLeader": "狼群首领", "Jotunn": "巨人",
    "Aelius": "艾利乌斯", "Bareleg": "裸腿者", "Black": "黑衣者",
    "Blind": "盲者", "Braggart": "吹牛者", "BristleBeard": "硬胡子",
    "Broadsole": "阔脚", "Clever": "聪明人", "Clumsyfoot": "笨脚",
    "Cold": "冷酷者", "Crowtalker": "鸦语者", "CutCheek": "割颊者",
    "Dreamreader": "解梦者", "Flatnose": "塌鼻者", "Gashskull": "裂颅者",
    "Godi": "戈迪", "Halftroll": "半巨魔", "Harmfart": "臭屁",
    "Jumper": "跳跃者", "Old": "老者", "Peaceful": "和平者",
    "Ring": "赫林格", "Shrieking": "大嗓门", "Skullcleaver": "裂颅者",
    "Squinting": "眯眼者", "Tall": "高个子", "UndergroundOne": "地下人",
    "White": "白衣者", "Geri": "格里", "Freki": "弗雷基",
    "RheaSilvia": "雷亚·西尔维娅", "Emrys": "埃姆里斯", "Quintus": "昆图斯",
    "Lachlansson": "拉赫兰之子", "MacLachlain": "麦克·拉赫兰",
    "BowSwayer": "弓手", "GoodCheer": "好心情", "Handsome": "英俊者",
    "Keen": "敏锐者", "WestMan": "西方人", "TheWolf": "那匹狼",
}


def load_translations():
    """按行号顺序，将翻译结果与原始 key 配对"""
    # 读取翻译结果
    trans_list = []
    with open(TRANSLATED_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if row:
                trans_list.append(row[0].strip())

    # 读取原始 key 和 category
    key_to_trans = {}
    with open(EXTRACTED_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < len(trans_list) and trans_list[i]:
                key_to_trans[row["key"]] = trans_list[i]

    return key_to_trans


def generate_dialogue_xml(source_path, output_path, translations):
    """对话 XML：key 是 UUID"""
    tree = ET.parse(source_path)
    root = tree.getroot()
    
    count = 0
    for elem in root.findall("Localize"):
        uid = elem.get("id", "")
        if uid in translations:
            elem.text = translations[uid]
            count += 1
    
    write_xml(tree, output_path)
    return count


def generate_by_path(source_path, output_path, translations):
    """按路径匹配的 XML：key 格式为 Root/TagName 或 Root/.../TagName[@id]"""
    tree = ET.parse(source_path)
    root = tree.getroot()
    
    parent_map = {c: p for p in root.iter() for c in p}
    
    count = 0
    for elem in root.iter():
        if elem.tag == root.tag or elem.tag is ET.Comment:
            continue
        
        if len(elem) == 0 and elem.text and elem.text.strip():
            # 构建与提取时一致的 key
            path = build_key(root, elem, parent_map)
            if path in translations:
                elem.text = translations[path]
                count += 1
        
        elif elem.tag in ("Female", "Male"):
            uid = elem.get("id", "")
            for child in elem:
                if child.text and child.text.strip():
                    path = f"{elem.tag}/{uid}/{child.tag}"
                    if path in translations:
                        child.text = translations[path]
                        count += 1
    
    write_xml(tree, output_path)
    return count


def apply_static_name_translations(path):
    """补齐旧 CSV 提取范围之外、但会在游戏内直接显示的名称字段。"""
    tree = ET.parse(path)
    count = 0
    for elem in tree.getroot().iter():
        translated = NAME_STATIC_TRANSLATIONS.get(elem.tag)
        if translated is not None:
            elem.text = translated
            count += 1
    write_xml(tree, path)
    return count


def build_key(root, elem, parent_map):
    """构建与 extract_for_translation.py 一致的 key"""
    # 收集从 elem 到 root 的路径
    parts = []
    current = elem
    while current is not None and current != root:
        tag = current.tag
        if current.get("id"):
            tag = f'{tag}[@{current.get("id")}]'
        parts.insert(0, tag)
        current = parent_map.get(current)
    
    # 加上 Root 前缀（与提取脚本一致）
    return "Root/" + "/".join(parts)


def write_xml(tree, output_path):
    """写出格式化 XML"""
    rough_string = ET.tostring(tree.getroot(), encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="  ", encoding="utf-8")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pretty)


def main():
    translations = load_translations()
    total = sum(1 for v in translations.values() if v)
    print(f"加载翻译: {len(translations)} 条 key, {total} 条有译文")
    
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    
    total_written = 0
    for cat_name, filename in CATEGORY_FILES.items():
        subdir = CATEGORY_DIRS[cat_name]
        source_path = os.path.join(LOCALIZATION_DIR, subdir, filename)
        
        if not os.path.exists(source_path):
            print(f"[跳过] {source_path}")
            continue
        
        custom_subdir = CUSTOM_CATEGORY_DIRS[cat_name]
        output_path = os.path.join(OUTPUT_DIR, "Chinese", "Localization", custom_subdir, f"{custom_subdir}Chinese.xml")
        
        if cat_name == "dialogue":
            count = generate_dialogue_xml(source_path, output_path, translations)
        else:
            count = generate_by_path(source_path, output_path, translations)
            if cat_name == "names":
                static_count = apply_static_name_translations(output_path)
                print(f"[names] 额外写入了 {static_count} 条根级称号/名称")
        
        print(f"[{cat_name}] 写入了 {count} 条翻译")
        total_written += count
    
    # 复制 ProcQuestEnglish
    proc_src = os.path.join(LOCALIZATION_DIR, "dialogue", "ProcQuestEnglish.txt")
    proc_dst = os.path.join(OUTPUT_DIR, "Chinese", "Localization", "Dialogue", "ProcQuestEnglish.xml")
    if os.path.exists(proc_src):
        os.makedirs(os.path.dirname(proc_dst), exist_ok=True)
        tree = ET.parse(proc_src)
        write_xml(tree, proc_dst)
        print(f"[procquest] 已复制")
    
    print(f"\n总计写入 {total_written} 条翻译")
    print(f"输出: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
