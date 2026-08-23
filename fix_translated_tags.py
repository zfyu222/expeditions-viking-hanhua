# -*- coding: utf-8 -*-
"""
修复 AINiee 译文中被翻译/破坏的格式化占位符。

问题类型：
  1. [Shipname]  -> [船名] / 【船名】        （内容被翻译，半角转全角）
  2. [Player:Name] -> [玩家：名字]           （变量被翻译）
  3. [Shipname]  -> {船名}                   （方括号被转成花括号）
  4. [i]...[/i] 整对丢失 / 变量被删除        （数量不一致，无法自动修复）

修复策略：
  A. 源文与译文的标签数量一致 -> 按出现顺序对位还原（安全，标签内容取自源文原文）
  B. 数量不一致时，尝试救援：译文中"短无标点中文花括号"（如 {船名}）视为损坏标签参与对位
  C. 仍无法对应的 -> 导出 need_retranslate.csv，待配置禁翻表后重翻

注意：源文中的 {Attack.} 这类花括号是玩家选项文本，本身需要翻译，全程不参与标签计算。
"""
import csv
import re
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC = BASE / "extracted_for_ainiee.csv"
DST = BASE / "extracted_for_ainiee_translated.csv"
BAK = BASE / "extracted_for_ainiee_translated_backup.csv"
RETRANS = BASE / "need_retranslate.csv"

# 源文中的保护标签：仅方括号变量/富文本标签
SRC_TAG = re.compile(r"\[[^\[\]]*\]")
# 译文中的标签候选：半角 [...] 或全角 【...】
DST_TAG = re.compile(r"\[[^\[\]]*\]|【[^【】]*】")
# 救援通道：译文里疑似由 [...] 转换来的花括号变量（短、无空格无标点、含中文）
CURLY_VAR = re.compile(r"\{([^{}\s。，、；：？！…—]{1,12})\}")
CN = re.compile(r"[一-鿿]")


def is_corrupted(tag: str) -> bool:
    """译文标签候选是否已损坏：含中文，或被转成全角【】"""
    return bool(CN.search(tag)) or tag.startswith("【")


def load_csv(path: Path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    src_rows = load_csv(SRC)
    dst_rows = load_csv(DST)
    if len(src_rows) != len(dst_rows):
        print(f"[错误] 行数不一致：原文 {len(src_rows)} 行，译文 {len(dst_rows)} 行")
        return 1

    # 只备份一次，重复运行不会覆盖最初备份
    if not BAK.exists():
        shutil.copy2(DST, BAK)
        print(f"已备份原译文 -> {BAK.name}")

    fixed = []        # A: 数量一致，对位还原
    rescued = []      # B: 花括号变量救援
    extra_ok = []     # AI 额外添加的合法标签，保留不动
    retrans = []      # C: 待重翻

    # 清理表头残留的 BOM（原文件存在双重 BOM）
    header = [cell.lstrip("﻿") for cell in dst_rows[0]]
    out_rows = [header]

    for lineno, (s_row, d_row) in enumerate(zip(src_rows[1:], dst_rows[1:]), start=2):
        s_text = s_row[0] if s_row else ""
        # 译文文件结构：第 0 列是译文，第 1 列为空（AINiee 输出格式）
        d_text = d_row[0] if d_row else ""

        s_tags = SRC_TAG.findall(s_text)
        d_tags = DST_TAG.findall(d_text)
        corrupted = [t for t in d_tags if is_corrupted(t)]

        if not corrupted and len(s_tags) == len(d_tags):
            # 无损坏（含 0==0），原样保留
            out_rows.append(d_row)
            continue

        if s_tags and len(s_tags) == len(d_tags):
            # A. 数量一致：按顺序对位还原（含被翻译/全角化的标签）
            it = iter(s_tags)
            new_text = DST_TAG.sub(lambda _m: next(it), d_text)
            out_rows.append([new_text] + list(d_row[1:]))
            fixed.append(lineno)
            continue

        # B. 数量不一致：尝试花括号变量救援
        #    例：src "...of [Shipname]..." 译 "…瞧清了{船名}的真容…"
        if s_tags:
            # 按位置合并 [...] / 【...】 / {变量} 三类候选
            spans = []
            for m in DST_TAG.finditer(d_text):
                spans.append((m.start(), m.group(0)))
            for m in CURLY_VAR.finditer(d_text):
                if CN.search(m.group(1)):  # 内容必须含中文才算损坏变量
                    spans.append((m.start(), m.group(0)))
            spans.sort(key=lambda x: x[0])

            if len(spans) == len(s_tags) and any(is_corrupted(t) for _, t in spans):
                pieces, pos = [], 0
                for (start, old), new_tag in zip(spans, s_tags):
                    pieces.append(d_text[pos:start])
                    pieces.append(new_tag)
                    pos = start + len(old)
                pieces.append(d_text[pos:])
                new_text = "".join(pieces)
                out_rows.append([new_text] + list(d_row[1:]))
                rescued.append(lineno)
                continue

        if not corrupted and len(d_tags) > len(s_tags):
            # AI 自行添加了合法标签（如加斜体），无害，保留
            extra_ok.append(lineno)
            out_rows.append(d_row)
            continue

        # C. 救不回来：保留原样并记入待重翻清单
        retrans.append((lineno, s_text, d_text))
        out_rows.append(d_row)

    # 写回修复后的译文（保持 UTF-8 BOM，与 AINiee 输出一致）
    with open(DST, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(out_rows)

    # 导出待重翻清单
    with open(RETRANS, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["行号", "原文", "当前译文"])
        w.writerows(retrans)

    print("=" * 60)
    print(f"A 对位还原修复 : {len(fixed)} 行")
    print(f"B 花括号变量救援: {len(rescued)} 行")
    print(f"  AI 多加合法标签: {len(extra_ok)} 行（保留未动）")
    print(f"C 待重新翻译   : {len(retrans)} 行 -> {RETRANS.name}")
    print("=" * 60)

    if retrans:
        print("\n待重翻示例（前 5 行）：")
        for lineno, s, d in retrans[:5]:
            print(f"  行{lineno}: {s[:50]}")
            print(f"         {d[:50]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
