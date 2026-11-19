#!/usr/bin/env python3
"""Prepare approved ICHON shop bottle cutouts on a review branch only."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_wine_image import search, candidate

PRODUCTS = [
    ("빅 벨티 까베르네 소비뇽", "Big Beltie Cabernet Sauvignon wine bottle cow label", "big-beltie-cabernet-sauvignon.png"),
    ("도멘 드루앵 로렌 피노 누아", "Domaine Drouhin Oregon Laurene Pinot Noir wine bottle", "domaine-drouhin-laurene-pinot-noir.png"),
]
HTML = ROOT / "ichon-wine-shop.html"
image_dir = ROOT / "images" / "ichon"
image_dir.mkdir(parents=True, exist_ok=True)
html = HTML.read_text(encoding="utf-8")
report = []
for name, query, filename in PRODUCTS:
    dest = image_dir / filename
    status = "not_found"
    for item in search(query, limit=10):
        try:
            candidate(item, dest)
            status = "prepared_for_visual_review"
            report.append({"product": name, "file": str(dest.relative_to(ROOT)), "source": item.get("link"), "source_page": item.get("image",{}).get("contextLink"), "status": status})
            break
        except Exception as exc:
            status = str(exc)[:120]
    if not dest.exists():
        report.append({"product":name,"status":"failed","error":status})
        continue
    import re
    pattern = r'("name"\s*:\s*"' + re.escape(name) + r'"[^{}]*?"image"\s*:\s*")images/ichon/product-image-pending\.svg(")'
    html, count = re.subn(pattern, lambda m: m.group(1)+"images/ichon/"+filename+m.group(2), html, count=1)
    if count != 1:
        raise RuntimeError("Product image field not found for "+name)
HTML.write_text(html, encoding="utf-8")
(ROOT / "ichon-image-review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
if not any(x["status"]=="prepared_for_visual_review" for x in report):
    raise RuntimeError("No image candidates could be prepared")
print(json.dumps(report,ensure_ascii=False,indent=2))
