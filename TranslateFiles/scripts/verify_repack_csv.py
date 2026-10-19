import csv
import json
import re
from pathlib import Path

BASE = Path(r"D:\StaticHanHua\Projects\Expeditions Viking")
src = [r[0] for r in csv.reader(open(BASE / "expeditions-viking_text.csv", encoding="utf-8-sig", newline=""))]
rep = [r[0] for r in csv.reader(open(BASE / "TranslateFiles/repack/translation_for_repack.csv", encoding="utf-8-sig", newline=""))]
off = [r[0] for r in csv.reader(open(BASE / "expeditions-viking_text_translated.csv", encoding="utf-8-sig", newline=""))]

TAG = re.compile(r"\[[^\]]*\]")
PLAYER = re.compile(r"\[Player:[^\]]*\]")
CJK = re.compile(r"[\u4e00-\u9fff]")


def tokens(text):
    return sorted(t for t in TAG.findall(text) if not t.startswith("[Player:"))


problems = []
for i, (s, r) in enumerate(zip(src, rep)):
    if tokens(s) != tokens(r):
        problems.append({"index": i, "kind": "tag_mismatch", "source": s, "repack": r})
    if not r.strip():
        problems.append({"index": i, "kind": "empty", "source": s})

leftover_player = [i for i, r in enumerate(rep)
                   if any("/" in t.split(":", 1)[1] and re.search(r"[A-Za-z]{2,}", t.split(":", 1)[1])
                          for t in PLAYER.findall(r))]
double_bracket = [i for i, s in enumerate(src) if "[[" in s and (rep[i].count("[[") != s.count("[[") or rep[i].count("]]") != s.count("]]"))]
equal = [i for i in range(len(src)) if src[i] == rep[i]]
no_cjk = [i for i, r in enumerate(rep) if not CJK.search(r)]
changed = [i for i in range(len(src)) if rep[i] != off[i]]

report = {
    "rows": len(rep),
    "source_rows": len(src),
    "tag_problems": problems[:20],
    "tag_problem_count": len(problems),
    "player_tag_with_ascii": leftover_player[:20],
    "player_tag_with_ascii_count": len(leftover_player),
    "double_bracket_mismatch": double_bracket[:20],
    "double_bracket_mismatch_count": len(double_bracket),
    "equal_to_source": len(equal),
    "no_cjk": len(no_cjk),
    "changed_vs_official": len(changed),
    "changed_indices_sample": changed[:10],
}
(BASE / "TranslateFiles/reports/repack_csv_verification.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if not isinstance(v, list)}, ensure_ascii=False, indent=2))
print("tag_problem_sample", problems[:5])
