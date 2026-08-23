#!/usr/bin/env python3
"""
在 resources.assets 中搜索 TextAsset 名称，匹配 pathId
通过读取二进制文件中的名称字符串来定位
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_FILE = os.path.join(BASE_DIR, "Game", "Expeditions Viking_Data", "resources.assets")

TARGET_NAMES = [
    "DialogueEnglish",
    "GUIEnglish",
    "SkillsEnglish",
    "ItemsEnglish",
    "TutorialEnglish",
    "HomesteadUpgradesEnglish",
    "CharacterNamesEnglish",
    "SceneDataEnglish",
    "InputEnglish",
]

def main():
    with open(ASSETS_FILE, "rb") as f:
        data = f.read()

    print(f"文件大小: {len(data)} bytes\n")

    for name in TARGET_NAMES:
        name_bytes = name.encode("utf-8")
        # 搜索名称
        positions = []
        pos = 0
        while True:
            idx = data.find(name_bytes, pos)
            if idx == -1:
                break
            positions.append(idx)
            pos = idx + 1

        print(f"{name}: 找到 {len(positions)} 处匹配")
        if positions:
            for p in positions[:3]:
                # 显示周围上下文
                ctx_start = max(0, p - 20)
                ctx_end = min(len(data), p + len(name_bytes) + 40)
                ctx = data[ctx_start:ctx_end]
                print(f"  偏移 0x{p:X}: {ctx[:50]}...")
        print()


if __name__ == "__main__":
    main()
