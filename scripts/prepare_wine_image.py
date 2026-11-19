#!/usr/bin/env python3
"""Search candidate bottle images, remove backgrounds, and prepare review artifacts.
Requires SERPAPI_KEY for online image search.
Never modifies existing product images or the public product catalog.
"""
import argparse
import io
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "image-review"
OUT.mkdir(exist_ok=True)
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "VinumImageReview/1.0"

def slugify(value):
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result[:65] or "wine"

def search(name, limit=5):
    key = os.getenv("SERPAPI_KEY")
    if not key:
        raise RuntimeError("Set SERPAPI_KEY in GitHub Actions secrets")
    response = SESSION.get("https://serpapi.com/search.json",
        params={"api_key": key, "engine": "google_images", "q": name + " wine bottle",
                "safe": "active", "num": limit}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError("SerpApi: " + str(payload["error"]))
    return [{"link": entry.get("original"), "title": entry.get("title"),
             "image": {"contextLink": entry.get("link")}}
            for entry in payload.get("images_results", [])[:limit] if entry.get("original")]

def candidate(item, dest):
    url = item.get("link", "")
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError("Unsupported image URL")
    response = SESSION.get(url, timeout=20, stream=True)
    response.raise_for_status()
    data = bytearray()
    for chunk in response.iter_content(65536):
        data.extend(chunk)
        if len(data) > 12 * 1024 * 1024:
            raise ValueError("Image exceeds 12MB")
    original = Image.open(io.BytesIO(data))
    original.verify()
    original = Image.open(io.BytesIO(data)).convert("RGBA")
    if min(original.size) < 180:
        raise ValueError("Image too small")
    cutout = remove(original)
    # Ignore near-transparent segmentation noise before measuring the bottle.
    alpha = cutout.getchannel("A")
    mask = alpha.point(lambda value: 255 if value >= 32 else 0)
    bbox = mask.getbbox()
    if not bbox:
        raise ValueError("Empty segmentation")
    cutout = cutout.crop(bbox)
    # Normalize the visible bottle height, not merely its source-image size.
    # 1056 px = 88% of the 1200 px transparent canvas.
    target_height, max_width = 1056, 780
    scale = min(target_height / cutout.height, max_width / cutout.width)
    new_size = (max(1, round(cutout.width * scale)),
                max(1, round(cutout.height * scale)))
    cutout = cutout.resize(new_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (900, 1200), (255, 255, 255, 0))
    canvas.alpha_composite(cutout, ((900-cutout.width)//2, (1200-cutout.height)//2))
    canvas.save(dest, optimize=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--id", required=True, help="Stable product identifier")
    args = parser.parse_args()
    product_id = slugify(args.id)
    folder = OUT / product_id
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    for i, item in enumerate(search(args.name), 1):
        path = folder / f"candidate-{i}.png"
        try:
            candidate(item, path)
            records.append({"file": str(path.relative_to(ROOT)), "source_url": item.get("link"),
                            "source_page": item.get("image", {}).get("contextLink"),
                            "title": item.get("title"), "status": "REVIEW_REQUIRED"})
        except Exception as exc:
            records.append({"source_url": item.get("link"), "error": str(exc)[:250]})
    (folder / "review.json").write_text(json.dumps(
        {"product_id": args.id, "name": args.name, "candidates": records,
         "notice": "Confirm label, producer, reuse rights and product identity before approval."},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("Created review candidates:", folder)

if __name__ == "__main__":
    main()
