#!/usr/bin/env python3
"""Extract a reviewable inventory from the static website without executing its JavaScript.

This is a discovery step only. Inventory status cannot be inferred from the site
unless explicit status fields exist; all extracted products default to 'hold'.
"""
import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "index.html").read_text(encoding="utf-8")
# The catalog includes an array concatenation. Match literal name/category/brand
# fields only; do not evaluate arbitrary JavaScript from the website.
pattern = re.compile(r'\{\s*"name"\s*:\s*"(?P<name>(?:\\.|[^"\\])*)"(?P<fields>.{0,1600}?)"category"\s*:\s*"(?P<category>[^"]+)"', re.S)
seen = set()
rows = []
for match in pattern.finditer(source):
    name = html.unescape(match.group("name")).strip()
    if not name or name in seen:
        continue
    seen.add(name)
    category = match.group("category")
    # Only a conservative catalog draft; product ID requires confirmation.
    pid = "product-" + str(len(rows) + 1).zfill(3)
    rows.append({"product_id": pid, "product_name": name,
                 "status": "hold", "category": category})
output = ROOT / "image-products-discovered.csv"
with output.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["product_id", "product_name", "status", "category"])
    writer.writeheader()
    writer.writerows(rows)
print(f"Discovered {len(rows)} candidate products; all on hold pending review: {output}")
