#!/usr/bin/env python3
"""Скачивает настоящие иконки Simple Icons прямо в icons/ (нужен интернет).

    python download_icons.py          # все бейджи из badges.json
    python download_icons.py react vue python    # только указанные id
    python build.py

Старые иконки перед заменой копируются в icons_backup/.
Если иконки нет в Simple Icons, бейдж остаётся с прежней.
"""
import json, shutil, sys, urllib.error, urllib.request
from pathlib import Path

from import_icons import ALIASES

ROOT = Path(__file__).parent
BASE = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{}.svg"

def fetch(slug):
    try:
        req = urllib.request.Request(BASE.format(slug), headers={"User-Agent": "badges-catalog"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def main():
    cfg = json.loads((ROOT / "badges.json").read_text(encoding="utf-8"))
    ids = [it["id"] for c in cfg["categories"] for it in c["items"]]
    only = sys.argv[1:]
    if only:
        ids = [i for i in ids if i in only]
    icons, backup = ROOT / "icons", ROOT / "icons_backup"
    icons.mkdir(exist_ok=True)
    backup.mkdir(exist_ok=True)
    ok, miss = [], []
    for bid in ids:
        slugs = list(dict.fromkeys(ALIASES.get(bid, []) + [bid.replace("-", ""), bid]))
        svg = next((s for s in (fetch(x) for x in slugs) if s), None)
        if svg is None:
            miss.append(bid)
            continue
        old = icons / f"{bid}.svg"
        if old.exists() and not (backup / old.name).exists():
            shutil.copyfile(old, backup / old.name)
        old.write_text(svg, encoding="utf-8")
        ok.append(bid)
        print("ok  ", bid)
    print(f"\nСкачано настоящих: {len(ok)}")
    print(f"Нет в Simple Icons ({len(miss)}), остались прежние: {', '.join(miss)}")

if __name__ == "__main__":
    main()
