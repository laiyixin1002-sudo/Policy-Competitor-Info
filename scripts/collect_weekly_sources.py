from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "data" / "weekly_report.json"
DEFAULT_HISTORY = ROOT / "data" / "facts_history.json"
DEFAULT_SOURCES = ROOT / "config" / "collection_sources.json"
CN_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


def clean_text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return " ".join(value.replace("\xa0", " ").split())


def parse_as_of(value: str | None) -> datetime:
    if not value:
        return datetime.now(CN_TZ)
    result = datetime.fromisoformat(value)
    return result.replace(tzinfo=CN_TZ) if result.tzinfo is None else result.astimezone(CN_TZ)


def fetch_text(url: str, insecure: bool = False) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Policy-Competitor-Info/1.0 weekly-source-collector",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    context = ssl._create_unverified_context() if insecure else None
    with urlopen(request, timeout=30, context=context) as response:
        body = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return body.decode(charset, errors="replace")


def parse_date(value: str) -> str | None:
    match = re.search(r"(20\d{2})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2})", value)
    if not match:
        return None
    return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"


def fingerprint(title: str, date: str, domain: str) -> str:
    normalized = " ".join(f"{title}|{date}|{domain}".lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_fact(title: str, date: str, source_url: str, source_name: str, domain: str) -> dict:
    return {
        "category": "区域挂网动态 · 广东省药品交易中心",
        "title": title,
        "fact_summary": f"{title}。该条来自广东省药品交易中心官方公告列表，具体产品、价格和执行范围以原文及附件为准。",
        "publisher": source_name,
        "region": "广东（广州）",
        "date": date,
        "source_type": "官方挂网/集采公告",
        "source_domain": domain,
        "source_url": source_url,
        "url_status": "ok",
        "system_modules": ["集采管控", "运营监管"],
        "sales_insight": "重点核对挂网批次、价格确认、中选产品及后续配送关系，避免把公告发布误判为已完成采购执行。",
        "dedupe_fingerprint": fingerprint(title, date, domain),
    }


def parse_gdmede(source: dict, text: str) -> list[dict]:
    pattern = re.compile(r'<a href="([^"]+)"[^>]*class="u-messageItem"[^>]*>(.*?)</a>', re.S)
    title_pattern = re.compile(r'class="u-messageItem-txt"[^>]*>(.*?)</div>', re.S)
    date_pattern = re.compile(r'class="u-messageItem-date"[^>]*>(.*?)</div>', re.S)
    results = []
    keywords = tuple(source.get("keywords") or [])
    for href, block in pattern.findall(text):
        title_match = title_pattern.search(block)
        date_match = date_pattern.search(block)
        if not title_match or not date_match:
            continue
        title = clean_text(title_match.group(1))
        date = parse_date(clean_text(date_match.group(1)))
        if not title or not date or not any(keyword in title for keyword in keywords):
            continue
        results.append(
            make_fact(
                title,
                date,
                urljoin(source["url"], href),
                source["name"],
                source["official_domain"],
            )
        )
    return results


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_fingerprint(fact: dict) -> dict:
    if not fact.get("dedupe_fingerprint"):
        fact["dedupe_fingerprint"] = fingerprint(
            str(fact.get("title", "")),
            str(fact.get("date", "")),
            str(fact.get("source_domain", "")),
        )
    return fact


def build_regional_rows(facts: list[dict]) -> list[dict]:
    rows = []
    for fact in facts:
        rows.append(
            {
                "region": fact.get("region", "区域"),
                "stage": fact.get("source_type", "官方公告"),
                "purchaser": fact.get("publisher", "官方采购平台"),
                "project_name": fact.get("title", ""),
                "products": "药品挂网/集采信息（详见原文及附件）",
                "budget": "未披露",
                "registration_deadline": "以原公告为准",
                "bid_opening_time": "不适用或以原公告为准",
                "source_name": fact.get("publisher", "官方来源"),
                "source_level": "官方公告",
                "source_domain": fact.get("source_domain", ""),
                "source_url": fact.get("source_url", ""),
            }
        )
    return rows


def build_highlights(facts: list[dict], source_count: int, new_count: int) -> list[str]:
    highlights = [
        f"本次成功抓取 {source_count} 个官方来源，识别 {new_count} 条此前未入库的挂网/集采动态。",
        "本期内容按官方公告发布日期去重；产品清单、价格和执行范围仍需打开原文附件核验。",
    ]
    highlights.extend(f"{fact['date']}：{fact['title']}" for fact in facts[:6])
    return highlights[:8]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect official pharmacy procurement and listing notices.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--as-of", help="ISO datetime; defaults to current Asia/Shanghai time")
    parser.add_argument("--min-new-items", type=int, default=None)
    parser.add_argument("--insecure", action="store_true", help="Use only for manual recovery when a source has a broken certificate")
    args = parser.parse_args()

    as_of = parse_as_of(args.as_of)
    config = load_json(args.sources, {})
    lookback_days = int(config.get("lookback_days", 60))
    minimum_new = args.min_new_items if args.min_new_items is not None else int(config.get("minimum_new_items", 1))
    cutoff = (as_of - timedelta(days=lookback_days)).date().isoformat()
    sources = config.get("sources") or []
    if not sources:
        raise SystemExit("No collection sources configured")

    history_payload = load_json(args.history, {"schema_version": "1.0", "dedupe_rule": "sha256(title|date|domain)", "facts": []})
    history = [ensure_fingerprint(dict(item)) for item in history_payload.get("facts", [])]
    seen = {item["dedupe_fingerprint"] for item in history}
    collected: list[dict] = []
    statuses = []
    source_count = 0
    for source in sources:
        try:
            text = fetch_text(source["url"], insecure=args.insecure)
            if source.get("kind") == "gdmede_announcements":
                items = parse_gdmede(source, text)
            else:
                raise ValueError(f"unsupported source kind: {source.get('kind')}")
            fresh_items = [item for item in items if item["date"] >= cutoff and item["date"] <= as_of.date().isoformat()]
            new_items = [item for item in fresh_items if item["dedupe_fingerprint"] not in seen]
            collected.extend(new_items)
            source_count += 1
            statuses.append({"id": source["id"], "status": "ok", "items": len(fresh_items), "new_items": len(new_items)})
        except Exception as exc:
            statuses.append({"id": source.get("id", "unknown"), "status": "error", "error": str(exc)})
            if source.get("required", True):
                raise SystemExit(f"Required source failed: {source.get('id')}: {exc}")

    if len(collected) < minimum_new:
        raise SystemExit(f"Freshness gate failed: collected {len(collected)} new items, minimum is {minimum_new}")

    for item in collected:
        history.append(item)
        seen.add(item["dedupe_fingerprint"])
    history.sort(key=lambda item: (item.get("date", ""), item.get("title", "")), reverse=True)
    history_payload = {
        "schema_version": "1.0",
        "dedupe_rule": "sha256(title|date|domain)",
        "last_collection_at": as_of.strftime("%Y-%m-%d %H:%M %z"),
        "facts": history,
    }

    report = json.loads(args.report.read_text(encoding="utf-8"))
    recent = [item for item in history if item.get("date", "") >= cutoff]
    recent.sort(key=lambda item: (item.get("date", ""), item.get("title", "")), reverse=True)
    report["facts"] = recent[:12]
    report["regional_procurements"] = build_regional_rows(recent[:12])
    report["highlights"] = build_highlights(recent, source_count, len(collected))
    report["collection_note"] = (
        f"本期统计区间 {report.get('period_start')} 至 {report.get('period_end')}；"
        f"内容由官方来源实时采集，回溯 {lookback_days} 天，新增入库 {len(collected)} 条。"
    )
    report["opportunity_actions"] = [
        {"priority": "P0", "title": "核验新增挂网产品", "description": "逐条打开官方公告及附件，确认产品、价格、医保编码、配送关系和执行时间后再进入客户简报。"},
        {"priority": "P1", "title": "建立区域目录差异表", "description": "对广东及后续接入区域记录新增、价格确认、中选补充和撤网状态，避免只记录公告标题。"},
        {"priority": "P1", "title": "跟进集采落地节点", "description": "把中选产品信息与医院目录、供应清单、配送关系及合理用药场景关联起来。"},
    ]
    report["collection_meta"] = {
        "run_at": as_of.strftime("%Y-%m-%d %H:%M:%S%z"),
        "lookback_days": lookback_days,
        "source_fetch_status": statuses,
        "source_count": source_count,
        "new_item_count": len(collected),
        "fresh_item_count": len(recent),
    }
    args.history.write_text(json.dumps(history_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"COLLECTION_OK sources={source_count} fresh={len(recent)} new={len(collected)} cutoff={cutoff}")
    for item in collected:
        print(f"NEW {item['date']} {item['title']} {item['source_url']}")


if __name__ == "__main__":
    main()
