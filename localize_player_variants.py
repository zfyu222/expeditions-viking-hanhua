#!/usr/bin/env python3
"""本地化 [Player:甲/乙] 中由游戏直接显示的性别分支词。"""

import csv
import re
import shutil
from pathlib import Path


BASE = Path(__file__).resolve().parent
TRANSLATIONS = BASE / "extracted_for_ainiee_translated.csv"
BACKUP = BASE / "extracted_for_ainiee_translated_before_player_variants.csv"
TAG = re.compile(r"\[Player:([^\]]*/[^\]]*)\]")

# 这些值不是变量名：游戏会根据玩家性别直接将斜杠两侧之一绘制出来。
# 未包含 / 的 [Player:Name]、[Player:Father] 等真正运行时变量不会匹配。
VARIANTS = {
    "man/woman": "男子/女子",
    "Man/Woman": "男子/女子",
    "son/daughter": "儿子/女儿",
    "son/daughter-in-law": "儿子/儿媳",
    "son/girl": "儿子/姑娘",
    "his/her": "他/她",
    "His/Her": "他/她",
    "he/she": "他/她",
    "He/She": "他/她",
    "he himself/she herself": "他自己/她自己",
    "him/her": "他/她",
    "himself/herself": "他自己/她自己",
    "Hlaford/Hlafdia": "领主/女领主",
    "hlaford/hlafdia": "领主/女领主",
    "king/queen": "国王/女王",
    "King/Queen": "国王/女王",
    "brother/sister": "兄弟/姐妹",
    "Brother/Sister": "兄弟/姐妹",
    "brother/sis": "兄弟/姐妹",
    "boy/girl": "男孩/女孩",
    "boys/girls": "男孩们/女孩们",
    "lad/lass": "小伙子/姑娘",
    "Norseman/Norsewoman": "诺斯人/诺斯女子",
    "Velkominn/Velkomin": "欢迎/欢迎",
    "nephew/niece": "侄子/侄女",
    "warrior/shieldmaiden": "战士/盾女",
    "warrior/thieldmaiden": "战士/盾女",
    "chieftain/warrior woman": "酋长/女战士",
    "craftsman/craftswoman": "工匠/女工匠",
    "master/mistress": "主人/女主人",
    "guy/lady": "家伙/女士",
    "handsome/beautiful": "英俊/美丽",
    "honourable/beautiful": "尊贵/美丽",
    "tender/sisterly": "温柔/姐妹般",
    "woman/sister": "女子/姐妹",
    "man/girl": "男子/姑娘",
    "men/women": "男人/女人",
    "brothers/brother and sister": "兄弟们/兄妹",
    "big lug/silly girl": "傻大个/傻姑娘",
    "bastard/bitch": "混蛋/贱人",
    "Bastard/Bitch": "混蛋/贱人",
    "bastard/woman": "混蛋/女人",
    "bastardr/bikkja": "混蛋/贱人",
    "Bastardr/Bikkja": "混蛋/贱人",
    "bikkju-sonr/bikkja": "狗娘养的/贱人",
    "son of a bitch/little mare": "狗娘养的/小母马",
    "son of a bitch/bitch": "狗娘养的/贱人",
    "snake/mare": "蛇/母马",
    "Thorr/Freyja": "托尔/芙蕾雅",
    "you son/daughter": "你这儿子/你这女儿",
}


def replace_tag(match: re.Match[str], unknown: set[str], replaced: list[int]) -> str:
    value = match.group(1)
    translated = VARIANTS.get(value)
    if translated is None:
        unknown.add(value)
        return match.group(0)
    replaced[0] += 1
    return f"[Player:{translated}]"


def main() -> int:
    with TRANSLATIONS.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not BACKUP.exists():
        shutil.copy2(TRANSLATIONS, BACKUP)

    unknown: set[str] = set()
    replaced = [0]
    output = [rows[0]]
    for row in rows[1:]:
        if row:
            row[0] = TAG.sub(lambda m: replace_tag(m, unknown, replaced), row[0])
        output.append(row)

    if unknown:
        raise RuntimeError(f"发现未映射的 Player 分支：{', '.join(sorted(unknown))}")

    with TRANSLATIONS.open("w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(output)

    print(f"已本地化 {replaced[0]} 个 [Player:…/…] 分支标签。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
