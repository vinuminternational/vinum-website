#!/usr/bin/env python3
"""Run the existing image candidate pipeline for a bounded, explicit product list."""
import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"product_id", "product_name"}

def load_products(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError("CSV must contain product_id and product_name columns")
        rows = list(reader)
    products, seen = [], set()
    for row in rows:
        name = (row.get("product_name") or "").strip()
        pid = (row.get("product_id") or "").strip()
        status = (row.get("status") or "active").strip().lower()
        # Explicit opt-in only: hold, unknown, sold-out and discontinued never run.
        if status != "active":
            continue
        if not name or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", pid):
            raise ValueError(f"Invalid name or product_id: {row}")
        if pid in seen:
            raise ValueError(f"Duplicate product_id: {pid}")
        seen.add(pid)
        products.append((pid, name))
    return products

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="image-products.csv")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    path = (ROOT / args.csv).resolve()
    if not path.is_relative_to(ROOT) or path.suffix.lower() != ".csv":
        raise ValueError("CSV must be inside repository")
    products = load_products(path)
    if not 1 <= args.limit <= 10:
        raise ValueError("Batch limit must be between 1 and 10")
    if not products:
        raise ValueError("No active products to process")
    print(f"Processing {min(len(products), args.limit)} of {len(products)} active products")
    failed = []
    for pid, name in products[:args.limit]:
        print(f"Processing {pid}: {name}", flush=True)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/prepare_wine_image.py"),
                                 "--id", pid, "--name", name], check=False)
        if result.returncode:
            failed.append(pid)
    if failed:
        raise RuntimeError("Failed products: " + ", ".join(failed))

if __name__ == "__main__":
    main()
