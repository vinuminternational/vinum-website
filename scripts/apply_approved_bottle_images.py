#!/usr/bin/env python3
"""Replace only the three approved catalog image references."""
from pathlib import Path
p = Path("index.html")
s = p.read_text(encoding="utf-8")
replacements = {
    '"name":"안토니 루퍼트 옵티마"': ('"image":"images/optima-2022.webp"', '"image":"images/approved-optima.png"'),
    '"name":"로마린스 블랑 드 블랑"': ('"image":"images/lormarins-blanc-de-blancs.webp"', '"image":"images/approved-lormarins.png"'),
    '"name":"케이프 오브 굿 호프 슈냉 블랑"': ('"image":"images/cape-chenin-blanc-2026.webp"', '"image":"images/approved-cape-chenin.png"'),
}
for name, (old, new) in replacements.items():
    start = s.find(name)
    if start < 0:
        raise RuntimeError(f"Missing catalog entry: {name}")
    end = s.find('},{', start)
    if end < 0:
        raise RuntimeError(f"Could not isolate catalog entry: {name}")
    entry = s[start:end]
    if entry.count(old) != 1:
        raise RuntimeError(f"Expected exactly one original image reference for {name}")
    s = s[:start] + entry.replace(old, new, 1) + s[end:]
for file in ["approved-optima.png", "approved-lormarins.png", "approved-cape-chenin.png"]:
    if not (Path("images") / file).is_file():
        raise RuntimeError(f"Missing approved image: {file}")
p.write_text(s, encoding="utf-8")
print("Updated exactly three approved catalog image references.")
