from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_MARKERS = ("信息化", "系统", "平台", "软件", "审方", "合理用药", "药学监护", "药学管理", "HIS")
DRUG_ONLY_MARKERS = ("药品挂网", "药品集采", "药品价格确认", "中选产品信息", "同步药品挂网", "药品交易")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail when the report contains stale or drug-only content.")
    parser.add_argument("--report", type=Path, default=ROOT / "data" / "weekly_report.json")
    parser.add_argument("--min-new-items", type=int, default=1)
    args = parser.parse_args()
    data = json.loads(args.report.read_text(encoding="utf-8"))
    meta = data.get("collection_meta") or {}
    if meta.get("content_scope") != "pharmacy_information_systems_only":
        raise SystemExit("Collection validation failed: wrong content scope")
    if int(meta.get("new_item_count", 0)) < args.min_new_items:
        raise SystemExit("Collection validation failed: no new system item was recorded")
    failed = [item for item in (meta.get("source_fetch_status") or []) if item.get("status") != "ok"]
    if failed:
        raise SystemExit(f"Collection validation failed: source errors: {failed}")
    facts = data.get("facts") or []
    if not facts:
        raise SystemExit("Collection validation failed: report has no system facts")
    fingerprints = [item.get("dedupe_fingerprint") for item in facts]
    if len(fingerprints) != len(set(fingerprints)):
        raise SystemExit("Collection validation failed: duplicate fact fingerprints")
    rejected = []
    for item in facts:
        text = " ".join(str(item.get(key, "")) for key in ("title", "category", "source_type", "system_scope"))
        if not any(marker in text for marker in SYSTEM_MARKERS):
            rejected.append(item.get("title", "unknown"))
        elif any(marker in text for marker in DRUG_ONLY_MARKERS):
            rejected.append(item.get("title", "unknown"))
    if rejected:
        raise SystemExit(f"Collection validation failed: drug-only items found: {rejected}")
    print(f"COLLECTION_VALIDATION_OK new={meta['new_item_count']} facts={len(facts)} scope=pharmacy_information_systems_only")


if __name__ == "__main__":
    main()
