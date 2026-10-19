import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(r"D:\StaticHanHua\Projects\Expeditions Viking")
VERIFY = Path(r"C:\Temp\uabea_verify")
ASSETS = BASE / "Game/Expeditions Viking_Data/resources.assets"
BACKUP = BASE / "backup/resources.assets"

PAIRS = [
    (9146, "Dialogue", "Dialogue"),
    (9040, "GUI", "GUI"),
    (9365, None, None),
]

CATS = {
    "Dialogue": "Dialogue",
    "GUI": "GUI",
    "Skills": "Skills",
    "Items": "Items",
    "Tutorial": "Tutorial",
    "HomesteadUpgrades": "HomesteadUpgrades",
    "Names": "Names",
    "SceneData": "SceneData",
    "Input": "Input",
}
ID_MAP = {
    "Dialogue": 9146, "GUI": 9040, "Skills": 9165, "Items": 9309,
    "Tutorial": 9799, "HomesteadUpgrades": 9063, "Names": 9804,
    "SceneData": 9795, "Input": 9744,
}
EXPORTED = "Skills.txt"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


CJK = re.compile(r"[\u4e00-\u9fff]")
PLAYER = re.compile(r"\[Player:([^\]]*)\]")
BRACE = re.compile(r"\{([^{}]*)\}")
BRACKET = re.compile(r"\[[^\]]*\]")
ASCII_WORD = re.compile(r"[A-Za-z]{2,}")

report = {
    "assets": {
        "path": str(ASSETS),
        "size": ASSETS.stat().st_size,
        "sha256": sha256(ASSETS),
        "backup_size": BACKUP.stat().st_size,
        "backup_sha256": sha256(BACKUP),
    },
    "text_assets": {},
}

mismatch = []
for name, folder in CATS.items():
    pid = ID_MAP[name]
    exported = VERIFY / ("Skills.txt" if name == "Skills" else "asset_%d.txt" % pid)
    xml = BASE / "Chinese_Localization/Chinese/Localization" / folder / (folder + "Chinese.xml")
    same = sha256(exported) == sha256(xml)
    if not same:
        mismatch.append(name)
    report["text_assets"][name] = {
        "path_id": pid, "exported_size": exported.stat().st_size,
        "xml_size": xml.stat().st_size, "byte_identical": same,
        "xml_sha256": sha256(xml),
    }

dialogue_text = (VERIFY / "asset_9146.txt").read_text(encoding="utf-8")
root = ET.fromstring(dialogue_text)
nodes = root.findall("Localize")
cjk = [e for e in nodes if CJK.search(e.text or "")]
player_variants = []
for e in nodes:
    for v in PLAYER.findall(e.text or ""):
        if "/" in v and ASCII_WORD.search(v):
            player_variants.append(v)
brace_english = [m.group(0) for e in nodes
                 for m in BRACE.finditer(e.text or "")
                 if ASCII_WORD.search(BRACKET.sub("", m.group(1)))]

report["dialogue"] = {
    "localize_nodes": len(nodes),
    "nodes_with_cjk": len(cjk),
    "english_gender_variants": len(player_variants),
    "english_brace_fragments": len(brace_english),
    "sample": {
        "00008015": next((e.text for e in nodes if e.get("id", "").startswith("00008015")), None),
        "hotkey_ok": "[[hotkey]]" in (VERIFY / "asset_9040.txt").read_text(encoding="utf-8"),
        "restored_choice_ok": "{攻击。}" in dialogue_text,
    },
}
report["all_text_assets_byte_identical"] = not mismatch
report["mismatched_assets"] = mismatch

(BASE / "TranslateFiles/reports/repack_verification.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
