from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "weekly_report.json"
CN_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


def monday_0900(now: datetime) -> datetime:
    now = now.astimezone(CN_TZ)
    this_monday = now.date() - timedelta(days=now.weekday())
    return datetime.combine(this_monday, datetime.min.time(), CN_TZ).replace(hour=9)


def report_window(now: datetime) -> tuple[str, str, str]:
    end_at = monday_0900(now)
    if now < end_at:
        end_at -= timedelta(days=7)
    start_at = end_at - timedelta(days=7)
    return (
        start_at.strftime("%Y-%m-%d"),
        end_at.strftime("%Y-%m-%d"),
        end_at.strftime("%Y-%m-%d %H:%M"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Update weekly report period for Monday 09:00 Asia/Shanghai publishing.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to weekly_report.json")
    parser.add_argument("--now", help="Optional ISO datetime for deterministic testing, e.g. 2026-07-13T09:00:00+08:00")
    args = parser.parse_args()

    now = datetime.fromisoformat(args.now) if args.now else datetime.now(CN_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=CN_TZ)

    period_start, period_end, generated_at = report_window(now)
    data = json.loads(args.input.read_text(encoding="utf-8"))
    data["period_start"] = period_start
    data["period_end"] = period_end
    data["generated_at"] = generated_at
    args.input.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"period_start={period_start}")
    print(f"period_end={period_end}")
    print(f"generated_at={generated_at}")


if __name__ == "__main__":
    main()
