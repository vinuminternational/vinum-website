#!/usr/bin/env python3
"""Prepare transparent bottle image candidates for missing Ichon shop products.
Review-only: NEVER edits ichon-wine-shop.html or publishes to the live website.
"""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_wine_image import search, candidate

PRODUCTS = [
 ("라 폴 GSM", "La Folle GSM Grenache Syrah Mourvedre wine bottle"),
 ("클로 뒤 몽 올리베 리락", "Clos du Mont Olivet Lirac wine bottle"),
 ("샤또 푸이게르", "Chateau Fougueyrat wine bottle"),
 ("엘레베 카리냥", "Eleve Carignan wine bottle"),
 ("장 마리 부즈레 알리고떼", "Jean Marie Bouzereau Bourgogne Aligote wine bottle"),
 ("마주앙 뫼르소 레 그랑 샤롱", "Mazoyeres Meursault Les Grands Charrons wine bottle"),
 ("루이 페드리에", "Louis Perdrier sparkling wine bottle"),
 ("도멘 빌러 홀더허스트 리슬링", "Domaine Biller Holderhurst Riesling wine bottle"),
 ("샤르도네 드 노 뉘", "Chardonnay de nos nuits wine bottle"),
 ("샤또 드 말리니 쁘띠 샤블리", "Chateau de Maligny Petit Chablis wine bottle"),
 ("앙드레 끌루에 브뤼", "Andre Clouet Brut Grande Reserve Champagne bottle"),
 ("샤또 드 말리니 샤블리", "Chateau de Maligny Chablis wine bottle"),
 ("베르나딘 뀌스까", "Bernardine Cusca wine bottle"),
]
OUT = ROOT / "image-review" / "ichon-next-13"
OUT.mkdir(parents=True,exist_ok=True)
report = []
for idx,(name,query) in enumerate(PRODUCTS,1):
    item_report={"name":name,"query":query,"status":"NO_CANDIDATE","candidates":[]}
    try:
        for j,item in enumerate(search(query,limit=6),1):
            path=OUT / f"product-{idx:02d}-candidate-{j}.png"
            try:
                candidate(item,path)
                item_report["candidates"].append({
                  "file":str(path.relative_to(ROOT)),
                  "source_url":item.get("link"),
                  "source_page":item.get("image",{}).get("contextLink"),
                  "source_title":item.get("title")
                })
                if len(item_report["candidates"]) >= 2:
                    break
            except Exception as exc:
                item_report.setdefault("errors",[]).append(str(exc)[:140])
        if item_report["candidates"]:
            item_report["status"]="MANUAL_PRODUCT_AND_LABEL_REVIEW_REQUIRED"
    except Exception as exc:
        item_report["error"]=str(exc)[:250]
    report.append(item_report)
    print(name, item_report["status"],len(item_report["candidates"]),flush=True)
(OUT/"review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("Candidates created. Do not publish until each product identity and label are confirmed.")
