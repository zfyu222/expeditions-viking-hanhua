# -*- coding: utf-8 -*-
import csv
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

fixes = {
    4801: "心烦意乱的[Upset:Name]揪着村长的衣领。老头儿虽然血流如注，但还有一口气在。",
    10836: "落败的[Player:He/She]可向胜者宣誓效忠，否则[Player:his/her]性命将被剥夺。若我二人中有人在决斗中倒下，他的尸身将安葬于此。",
    10901: "你把武器交给[VoiceOfReason:Name]保管时，[VoiceOfReason:him/her]凑到你耳边，低语了几句。",
    14711: "当然，那档子事本与我无关，可他是穿着我上好的皮袄、佩着我贵重的宝剑溜走的——那可是[i]我的[/i]上好皮袄和贵重的宝剑！",
    22920: '[color="orange"]-15[/color] 敌人侧翼伤害倍率',
}

with open("extracted_for_ainiee.csv", encoding="utf-8-sig", newline="") as f:
    src = [r[0] if r else "" for r in csv.reader(f)]
with open("extracted_for_ainiee_translated.csv", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))

for ln, text in fixes.items():
    rows[ln - 1][0] = text

with open("extracted_for_ainiee_translated.csv", "w", encoding="utf-8-sig", newline="") as f:
    csv.writer(f).writerows(rows)

tag = re.compile(r"\[[^\[\]]*\]|【[^【】]*】")
src_tag = re.compile(r"\[[^\[\]]*\]")
dst = [r[0] if r else "" for r in rows]
bad_cn = [i + 1 for i, d in enumerate(dst) if any(re.search(r"[一-鿿]", t) or t.startswith("【") for t in tag.findall(d))]
bad_cnt = [i + 1 for i, (s, d) in enumerate(zip(src, dst)) if sorted(src_tag.findall(s)) != sorted(tag.findall(d))]
print("含中文/全角标签行数:", len(bad_cn))
print("标签多重集合不一致行数:", len(bad_cnt), bad_cnt)
