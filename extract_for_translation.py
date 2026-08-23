#!/usr/bin/env python3
"""
Expeditions Viking 汉化 - 第1步：提取文本为 CSV 翻译格式
从导出的英文 XML 本地化文件中提取文本，转换为 AiNiee 兼容的 CSV 格式
"""

import os
import re
import csv
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALIZATION_DIR = os.path.join(BASE_DIR, "output", "full-project", "ExportedProject", "Assets", "Resources", "localization")

# 各类别对应的目录和文件名模式
CATEGORIES = {
    "dialogue": ("dialogue", "DialogueEnglish.txt"),
    "gui": ("gui", "GUIEnglish.txt"),
    "homestead": ("homesteadupgrades", "HomesteadUpgradesEnglish.txt"),
    "input": ("input", "InputEnglish.txt"),
    "items": ("items", "ItemsEnglish.txt"),
    "names": ("names", "CharacterNamesEnglish.txt"),
    "scenedata": ("scenedata", "SceneDataEnglish.txt"),
    "skills": ("skills", "SkillsEnglish.txt"),
    "tutorial": ("tutorial", "TutorialEnglish.txt"),
}


def parse_dialogue_xml(filepath):
    """解析对话 XML：<Localize id="xxx" localized="yyy">text</Localize>"""
    entries = []
    tree = ET.parse(filepath)
    root = tree.getroot()
    for elem in root.findall("Localize"):
        uid = elem.get("id", "")
        text = (elem.text or "").strip()
        # 空文本跳过
        if not text:
            continue
        entries.append((uid, text))
    return entries


def parse_generic_xml(filepath):
    """解析通用 XML：<TagName>text</TagName> 格式"""
    entries = []
    tree = ET.parse(filepath)
    root = tree.getroot()
    # 收集所有叶子元素（没有子元素的元素）
    for elem in root.iter():
        # 跳过根元素和注释
        if elem.tag == root.tag or elem.tag is ET.Comment:
            continue
        # 如果元素没有子元素（或只有文本），就提取
        if len(elem) == 0:
            text = (elem.text or "").strip()
            if text:  # 只保留有内容的
                # 获取完整的 XML 路径作为 key
                path = get_xml_path(root, elem)
                entries.append((path, text))
        elif elem.tag in ("Female", "Male"):
            # 名字类特殊处理：获取 Base 子元素
            base_elem = elem.find("Base")
            if base_elem is not None and base_elem.text:
                uid = elem.get("id", "")
                text = base_elem.text.strip()
                path = f"{elem.tag}/{uid}/Base"
                entries.append((path, text))
    return entries


def get_xml_path(root, elem):
    """获取元素相对于根的路径"""
    parts = [elem.tag]
    parent = elem
    while True:
        parent_found = False
        for p in root.iter():
            if parent in list(p):
                parts.insert(0, p.tag)
                parent = p
                parent_found = True
                break
        if not parent_found or parent == root:
            break
    # 如果 tag 有 id 属性，加上
    if elem.get("id"):
        parts[-1] = f'{parts[-1]}[@{elem.get("id")}]'
    return "/".join(parts)


def parse_names_xml(filepath):
    """解析名字 XML：包含嵌套结构的名字"""
    entries = []
    tree = ET.parse(filepath)
    root = tree.getroot()
    for elem in root.iter():
        if elem.tag in ("Female", "Male"):
            uid = elem.get("id", "")
            base_elem = elem.find("Base")
            if base_elem is not None and base_elem.text:
                text = base_elem.text.strip()
                if text:
                    entries.append((f"{elem.tag}/{uid}/Base", text))
            # 也可能有其他形态（如 Genitive, Accusative 等）
            for child in elem:
                if child.tag != "Base" and child.text and child.text.strip():
                    entries.append((f"{elem.tag}/{uid}/{child.tag}", child.text.strip()))
    return entries


def main():
    os.makedirs(BASE_DIR, exist_ok=True)

    for cat_name, (subdir, filename) in CATEGORIES.items():
        filepath = os.path.join(LOCALIZATION_DIR, subdir, filename)
        if not os.path.exists(filepath):
            print(f"[跳过] 文件不存在: {filepath}")
            continue

        print(f"[处理] {cat_name}: {filename}")

        # 根据类别选择解析方式
        if cat_name == "dialogue":
            entries = parse_dialogue_xml(filepath)
        elif cat_name == "names":
            entries = parse_names_xml(filepath)
        else:
            entries = parse_generic_xml(filepath)

        # 输出 CSV：key,原文,译文
        csv_path = os.path.join(BASE_DIR, f"extracted_{cat_name}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["key", "原文", "译文"])
            for key, text in entries:
                writer.writerow([key, text, ""])

        print(f"  -> 提取 {len(entries)} 条记录 -> {csv_path}")

    # 合并所有 CSV 为一个总文件
    all_entries = []
    for cat_name, _ in CATEGORIES.items():
        csv_path = os.path.join(BASE_DIR, f"extracted_{cat_name}.csv")
        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                header = next(reader, None)  # 跳过表头
                for row in reader:
                    if len(row) >= 2 and row[1].strip():
                        all_entries.append((row[0], row[1], cat_name))

    merged_path = os.path.join(BASE_DIR, "extracted_strings.csv")
    with open(merged_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "原文", "译文", "category"])
        for key, text, cat in all_entries:
            writer.writerow([key, text, "", cat])

    print(f"\n[汇总] 总计 {len(all_entries)} 条待翻译文本")
    print(f"合并文件: {merged_path}")
    print("\n下一步：将 extracted_strings.csv 拖入 AiNiee 进行翻译")


if __name__ == "__main__":
    main()
