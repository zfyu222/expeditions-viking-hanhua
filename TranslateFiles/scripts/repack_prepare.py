"""为第 3 步回填准备译文：回补 101 条被漏译的选项、可选本地化动态性别分支。

只读取正式译文，生成 TranslateFiles/repack/ 下的回填用副本，不改动已验收 CSV。
"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

BASE = Path(r"D:\StaticHanHua\Projects\Expeditions Viking")
GLOSSARY = BASE / "TranslateFiles/glossary/r8/freeze_731eced6/built/glossary_reviewed.json"
REPACK_DIR = BASE / "TranslateFiles/repack"

# 回补 v1.2 译文时的定向修订：
# - 3274：术语表 Asleifr 为「阿斯莱夫」，旧译文作「阿斯莱芙」
# - 16743：术语表 Ready 为「戒备」，旧译文未体现
# - 18812：源文用 [[hotkey]] 转义，新译丢了一层方括号，会破坏变量替换
# - 20056：源文为格式模板（前置逗号粘接），不改写格式，保留原样
OVERRIDES = {
    3274: ("{与阿斯莱夫一同入场。}", "术语统一：Asleifr → 阿斯莱夫"),
    16743: ("{持械戒备。}", "术语统一：Ready → 戒备"),
    18812: ("按下 [[hotkey]] 查看追随者", "恢复源文 [[hotkey]] 双层转义，避免变量插值失效"),
    9277: ("{攻击。} 他们看起来乱糟糟的，应该不会太难。赶紧了结吧。",
           "v1.2 此处用全角括号，按其他选项统一改为花括号"),
}
SKIP_RESTORE = {20056}

BRACE = re.compile(r"\{([^{}]*)\}")
BRACKET = re.compile(r"\[[^\]]*\]")
ASCII_WORD = re.compile(r"[A-Za-z]{2,}")
CJK = re.compile(r"[\u4e00-\u9fff]")


def english_brace_spans(text):
    spans = []
    for m in BRACE.finditer(text):
        if ASCII_WORD.search(BRACKET.sub("", m.group(1))):
            spans.append(m)
    return spans


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [row[0] if row else "" for row in csv.reader(f)]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bracket_tokens(text):
    return re.findall(r"\[[^\]]*\]", text)


def prepare_reviewed_base(official, review, variants):
    """Once supplementary review is accepted, never re-import legacy proposals."""
    official_path = BASE / 'expeditions-viking_text_translated.csv'
    if review.get('status') != 'accepted' or sha256(official_path) != review['official_sha256']:
        raise SystemExit('补充审校报告与正式译文不匹配；停止，避免覆盖已审结果。')
    out = list(official)
    localized = []
    replaced = 0
    if variants:
        import sys
        sys.path.insert(0, str(BASE))
        from localize_player_variants import TAG, VARIANTS
        unknown = set()
        for index, text in enumerate(out):
            def repl(match):
                nonlocal replaced
                key = match.group(1)
                if key not in VARIANTS:
                    unknown.add(key); return match.group(0)
                replaced += 1
                return '[Player:' + VARIANTS[key] + ']'
            out[index] = TAG.sub(repl, text)
            if out[index] != text:
                localized.append({'index': index, 'before': text, 'after': out[index]})
        if unknown:
            raise SystemExit('未映射的 Player 分支：' + repr(sorted(unknown)))
    REPACK_DIR.mkdir(parents=True, exist_ok=True)
    target = REPACK_DIR / 'translation_for_repack.csv'
    with target.open('w', encoding='utf-8', newline='') as stream:
        csv.writer(stream).writerows([[text] for text in out])
    (REPACK_DIR / 'player_variants_localized.json').write_text(
        json.dumps(localized, ensure_ascii=False, indent=2), encoding='utf-8')
    report = {'official_csv': str(official_path), 'official_sha256': sha256(official_path),
        'repack_csv': str(target), 'repack_sha256': sha256(target),
        'restored_count': 0, 'restored': [], 'brace_fixes_count': 0, 'brace_fixes': [],
        'overrides': [], 'problems': [], 'term_conflict_count': 0,
        'reviewed_repack_records': review['scope_records'],
        'review_report': 'TranslateFiles/reports/repack_review_acceptance_20261019.json',
        'player_variants': {'replaced': replaced, 'records': len(localized), 'unknown': []}}
    (BASE / 'TranslateFiles/reports/repack_translation_prep.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('official_sha256','repack_sha256','reviewed_repack_records','player_variants')},ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", action="store_true", help="同时本地化 [Player:x/y] 分支")
    args = parser.parse_args()

    rows = list(csv.DictReader(open(BASE / "extracted_strings.csv", encoding="utf-8-sig")))
    source = load_csv(BASE / "expeditions-viking_text.csv")
    official = load_csv(BASE / "expeditions-viking_text_translated.csv")
    accepted = BASE / 'TranslateFiles/reports/repack_review_acceptance_20261019.json'
    if accepted.exists():
        prepare_reviewed_base(official, json.loads(accepted.read_text(encoding='utf-8')), args.variants)
        return
    legacy = load_csv(BASE / "extracted_for_ainiee_translated.csv")[1:]
    assert len(rows) == len(source) == len(official) == len(legacy) == 23195

    glossary = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    terms = {}
    for group in ("characters", "terms"):
        for entry in glossary[group]:
            terms[entry["source"]] = entry["recommended_translation"]

    fixed = []
    problems = []
    for i, (src, cur) in enumerate(zip(source, official)):
        if src != cur or i in SKIP_RESTORE:
            continue
        candidate = legacy[i]
        if candidate == src:
            problems.append({"index": i, "reason": "legacy_also_untranslated", "source": src})
            continue
        if sorted(bracket_tokens(src)) != sorted(bracket_tokens(candidate)):
            problems.append({
                "index": i, "reason": "tag_mismatch", "source": src, "candidate": candidate,
                "source_tokens": bracket_tokens(src), "candidate_tokens": bracket_tokens(candidate),
            })
            continue
        hit = []
        for term, target in terms.items():
            if re.search(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", src):
                if target not in candidate:
                    hit.append({"term": term, "expected": target})
        fixed.append({
            "index": i, "category": rows[i]["category"], "key": rows[i]["key"],
            "source": src, "restored": candidate, "term_conflicts": hit, "origin": "v1.2_shipped",
        })

    out = list(official)
    for item in fixed:
        out[item["index"]] = item["restored"]

    overrides = []
    for index, (text, reason) in OVERRIDES.items():
        overrides.append({
            "index": index, "category": rows[index]["category"], "key": rows[index]["key"],
            "source": source[index], "before": out[index], "after": text, "reason": reason,
        })
        out[index] = text

    # 花括号选项片段漏译修复：沿用 v1.2 已发布的选项译法，只替换 { } 内文本
    brace_fixes = []
    for i, text in enumerate(out):
        if not english_brace_spans(text):
            continue
        braces_new = list(BRACE.finditer(text))
        braces_old = list(BRACE.finditer(legacy[i]))
        if len(braces_new) != len(braces_old):
            continue
        pieces = []
        last = 0
        for mn, mo in zip(braces_new, braces_old):
            old_inner = BRACKET.sub("", mo.group(1))
            if CJK.search(old_inner) and not ASCII_WORD.search(old_inner):
                pieces.append(text[last:mn.start()])
                pieces.append(mo.group(0))
                last = mn.end()
        if not pieces:
            continue
        pieces.append(text[last:])
        new_text = "".join(pieces)
        brace_fixes.append({
            "index": i, "category": rows[i]["category"], "key": rows[i]["key"],
            "source": source[i], "before": text, "after": new_text, "origin": "v1.2_shipped",
        })
        out[i] = new_text

    unresolved = [i for i, text in enumerate(out) if english_brace_spans(text)]
    if unresolved:
        raise SystemExit("仍有未译的花括号片段：%r" % unresolved[:20])

    variants_report = None
    if args.variants:
        import sys
        sys.path.insert(0, str(BASE))
        from localize_player_variants import TAG, VARIANTS
        unknown = set()
        count = 0
        localized = []
        for i, text in enumerate(out):
            def repl(m):
                nonlocal count
                value = m.group(1)
                if value not in VARIANTS:
                    unknown.add(value)
                    return m.group(0)
                count += 1
                return "[Player:" + VARIANTS[value] + "]"
            new = TAG.sub(repl, text)
            if new != text:
                localized.append({"index": i, "before": text, "after": new})
            out[i] = new
        if unknown:
            raise SystemExit("未映射的 Player 分支: %s" % sorted(unknown))
        variants_report = {"replaced": count, "records": len(localized), "unknown": sorted(unknown)}
        (REPACK_DIR / "player_variants_localized.json").write_text(
            json.dumps(localized, ensure_ascii=False, indent=2), encoding="utf-8")

    REPACK_DIR.mkdir(parents=True, exist_ok=True)
    target = REPACK_DIR / "translation_for_repack.csv"
    with open(target, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for text in out:
            writer.writerow([text])

    report = {
        "official_csv": str(BASE / "expeditions-viking_text_translated.csv"),
        "official_sha256": sha256(BASE / "expeditions-viking_text_translated.csv"),
        "repack_csv": str(target),
        "repack_sha256": sha256(target),
        "restored_count": len(fixed),
        "restored": fixed,
        "brace_fixes_count": len(brace_fixes),
        "brace_fixes": brace_fixes,
        "overrides": overrides,
        "problems": problems,
        "term_conflict_count": sum(1 for x in fixed if x["term_conflicts"]),
        "player_variants": variants_report,
    }
    (BASE / "TranslateFiles/reports/repack_translation_prep.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("restored=%d brace_fixes=%d overrides=%d problems=%d term_conflict_records=%d variants=%r" % (
        len(fixed), len(brace_fixes), len(overrides), len(problems),
        report["term_conflict_count"], variants_report))


if __name__ == "__main__":
    main()
