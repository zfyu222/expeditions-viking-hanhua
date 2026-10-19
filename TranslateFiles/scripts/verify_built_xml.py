import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(r"D:\StaticHanHua\Projects\Expeditions Viking")
sys.path.insert(0, str(BASE))
from build_localization import CUSTOM_CATEGORY_DIRS, build_key

CJK = re.compile(r"[\u4e00-\u9fff]")
PLAYER = re.compile(r"\[Player:([^\]]*)\]")

rows = list(csv.DictReader(open(BASE / "extracted_strings.csv", encoding="utf-8-sig")))
rep = [r[0] for r in csv.reader(open(BASE / "TranslateFiles/repack/translation_for_repack.csv", encoding="utf-8-sig", newline=""))]
expected = {(r["category"], r["key"]): rep[i] for i, r in enumerate(rows)}


def collect(category, path):
    tree = ET.parse(path)
    root = tree.getroot()
    found = {}
    if category == "dialogue":
        for elem in root.findall("Localize"):
            found[elem.get("id", "")] = elem.text or ""
        return found
    parent_map = {c: p for p in root.iter() for c in p}
    for elem in root.iter():
        if elem.tag == root.tag or elem.tag is ET.Comment:
            continue
        if len(elem) == 0 and elem.text and elem.text.strip():
            found[build_key(root, elem, parent_map)] = elem.text
        elif elem.tag in ("Female", "Male"):
            uid = elem.get("id", "")
            for child in elem:
                if child.text and child.text.strip():
                    found[f"{elem.tag}/{uid}/{child.tag}"] = child.text
    return found


report = {"categories": {}, "problems": []}
for category, dirname in CUSTOM_CATEGORY_DIRS.items():
    path = BASE / "Chinese_Localization/Chinese/Localization" / dirname / f"{dirname}Chinese.xml"
    found = collect(category, path)
    cat_expected = {k[1]: v for k, v in expected.items() if k[0] == category}
    mismatched = [k for k in cat_expected if k in found and found[k] != cat_expected[k]]
    missing = [k for k in cat_expected if k not in found]
    english = [k for k, v in found.items() if k in cat_expected and not CJK.search(v) and v.strip()]
    variants = [t for v in found.values() for t in PLAYER.findall(v) if "/" in t and re.search(r"[A-Za-z]{2,}", t)]
    report["categories"][category] = {
        "expected": len(cat_expected), "found": len(found),
        "mismatched": len(mismatched), "missing": len(missing),
        "english_kept": len(english), "english_variants": len(variants),
        "mismatched_sample": mismatched[:5], "missing_sample": missing[:5],
        "english_sample": [(k, found[k][:60]) for k in english[:5]],
    }
    for k in mismatched[:3]:
        report["problems"].append({"category": category, "key": k, "expected": cat_expected[k], "actual": found[k]})

(BASE / "TranslateFiles/reports/build_xml_verification.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report["categories"], ensure_ascii=False, indent=2))
