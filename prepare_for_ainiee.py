#!/usr/bin/env python3
"""
生成 AiNiee 兼容的两列 CSV 格式（原文,译文）
"""

import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "extracted_strings.csv")

# 读取并转换为两列格式
entries = []
with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        entries.append((row["原文"], "", row["key"], row["category"]))

# 输出两列 CSV（AiNiee 标准格式）
output_path = os.path.join(BASE_DIR, "extracted_for_ainiee.csv")
with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["原文", "译文"])
    for original, translation, key, category in entries:
        writer.writerow([original, translation])

print(f"生成 AiNiee 翻译输入文件: {output_path}")
print(f"共 {len(entries)} 条待翻译文本")
print(f"\n请将此文件拖入 AiNiee 进行翻译。")
print(f"翻译完成后输出文件通常在同目录下，文件名带 _translated 后缀。")
