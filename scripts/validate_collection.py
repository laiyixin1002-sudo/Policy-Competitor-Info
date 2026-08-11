from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


CN_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail the report build when collection is stale or incomplete.")
    parser.add_argument("--report", type=Path, default=ROOT / "data" / "weekly_report.json")
    parser.add_argument("--min-new-items", type=int, default=1)
    args = parser.parse_args()
    data = json.loads(args.report.read_text(encoding="utf-8"))
    meta = data.get("collection_meta") or {}
    if int(meta.get("new_item_count", 0)) < args.min_new_items:
        raise SystemExit("Collection validation failed: no new source item was recorded")
    statuses = meta.get("source_fetch_status") or []
    failed = [item for item in statuses if item.get("status") != "ok"]
    if failed:
        raise SystemExit(f"Collection validation failed: source errors: {failed}")
    facts = data.get("facts") or []
    if not facts:
        raise SystemExit("Collection validation failed: report has no facts")
    fingerprints = [item.get("dedupe_fingerprint") for item in facts]
    if len(fingerprints) != len(set(fingerprints)):
        raise SystemExit("Collection validation failed: duplicate fact fingerprints")
    print(f"COLLECTION_VALIDATION_OK new={meta['new_item_count']} facts={len(facts)}")


if __name__ == "__main__":
    main()
