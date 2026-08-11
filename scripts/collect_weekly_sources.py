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
SYSTEM_MARKERS = ("信息化", "系统", "平台", "软件", "审方", "合理用药", "药学监护", "药学管理", "HIS")
DRUG_ONLY_MARKERS = ("药品挂网", "药品集采", "药品价格确认", "中选产品信息", "同步药品挂网", "药品交易")


def clean_text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return " ".join(value.replace("\xa0", " ").split())


def parse_as_of(value: str | None) -> datetime:
    if not value:
        return datetime.now(CN_TZ)
    result = datetime.fromisoformat(value)
    return result.replace(tzinfo=CN_TZ) if result.tzinfo is None else result.astimezone(CN_TZ)


def fetch_text(url: str, insecure: bool = False) -> str:
    request = Request(url, headers={"User-Agent": "Policy-Competitor-Info/1.1 pharmacy-information-collector"})
    context = ssl._create_unverified_context() if insecure else None
    with urlopen(request, timeout=30, context=context) as response:
        body = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return body.decode(charset, errors="replace")


def parse_date(value: str) -> str | None:
    match = re.search(r"(20\d{2})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2})", value)
    return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}" if match else None


def fingerprint(title: str, date: str, domain: str) -> str:
    normalized = " ".join(f"{title}|{date}|{domain}".lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_fact(title: str, date: str, source_url: str, source_name: str, domain: str, metadata: dict | None = None) -> dict:
    metadata = metadata or {}
    region = metadata.get("region", "区域")
    source_type = metadata.get("source_type", "官方项目公告")
    system_scope = metadata.get("system_scope", "药学信息化、合理用药与医院系统接口")
    return {
        "category": f"药学信息化项目 · {region}",
        "title": title,
        "source_title": metadata.get("source_title", title),
        "fact_summary": metadata.get("fact_summary", f"{title}。项目范围聚焦{system_scope}，具体采购边界、接口要求和执行时间以官方原文及附件为准。"),
        "publisher": source_name,
        "region": region,
        "date": date,
        "source_type": source_type,
        "system_scope": system_scope,
        "purchaser": metadata.get("purchaser", source_name),
        "budget": metadata.get("budget", "未披露"),
        "registration_deadline": metadata.get("registration_deadline", "以原公告为准"),
        "bid_opening_time": metadata.get("bid_opening_time", "以原公告为准"),
        "source_domain": domain,
        "source_url": source_url,
        "url_status": "ok",
        "system_modules": ["药学信息化", "合理用药", "药学服务", "HIS接口"],
        "sales_insight": "重点关注药学业务闭环、HIS/EMR接口、规则库维护、药师工作量与上线交付边界。",
        "dedupe_fingerprint": fingerprint(title, date, domain),
    }


def parse_gdmede(source: dict, text: str) -> list[dict]:
    pattern = re.compile(r'<a href="([^"]+)"[^>]*class="u-messageItem"[^>]*>(.*?)</a>', re.S)
    title_pattern = re.compile(r'class="u-messageItem-txt"[^>]*>(.*?)</div>', re.S)
    date_pattern = re.compile(r'class="u-messageItem-date"[^>]*>(.*?)</div>', re.S)
    results = []
    include = tuple(source.get("include_keywords") or [])
    exclude = tuple(source.get("exclude_keywords") or [])
    for href, block in pattern.findall(text):
        title_match = title_pattern.search(block)
        date_match = date_pattern.search(block)
        if not title_match or not date_match:
            continue
        title = clean_text(title_match.group(1))
        date = parse_date(clean_text(date_match.group(1)))
        if not title or not date or not any(keyword in title for keyword in include):
            continue
        if any(keyword in title for keyword in exclude) and not any(marker in title for marker in SYSTEM_MARKERS):
            continue
        results.append(make_fact(title, date, urljoin(source["url"], href), source["name"], source["official_domain"], {"region": "广东（广州）"}))
    return results


def parse_verified_items(source: dict) -> list[dict]:
    return [
        make_fact(
            item["title"], item["date"], item["source_url"], item["source_name"],
            item.get("official_domain", source.get("official_domain", "")), item,
        )
        for item in source.get("items") or []
    ]


def load_json(path: Path, default: object) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def ensure_fingerprint(fact: dict) -> dict:
    if not fact.get("dedupe_fingerprint"):
        fact["dedupe_fingerprint"] = fingerprint(str(fact.get("title", "")), str(fact.get("date", "")), str(fact.get("source_domain", "")))
    return fact


def is_allowed_fact(fact: dict) -> bool:
    text = " ".join(str(fact.get(key, "")) for key in ("title", "category", "source_type", "system_scope"))
    if not any(marker in text for marker in SYSTEM_MARKERS):
        return False
    return not any(marker in text for marker in DRUG_ONLY_MARKERS)


def build_regional_rows(facts: list[dict]) -> list[dict]:
    return [
        {
            "region": fact.get("region", "区域"),
            "stage": fact.get("source_type", "官方项目公告"),
            "purchaser": fact.get("purchaser", fact.get("publisher", "官方采购单位")),
            "project_name": fact.get("title", ""),
            "products": fact.get("system_scope", "药学信息化系统/医院系统模块"),
            "budget": fact.get("budget", "未披露"),
            "registration_deadline": fact.get("registration_deadline", "以原公告为准"),
            "bid_opening_time": fact.get("bid_opening_time", "以原公告为准"),
            "source_name": fact.get("publisher", "官方来源"),
            "source_level": "官方项目公告",
            "source_domain": fact.get("source_domain", ""),
            "source_url": fact.get("source_url", ""),
        }
        for fact in facts
    ]


def build_highlights(facts: list[dict], source_count: int, new_count: int) -> list[str]:
    highlights = [
        f"本次成功抓取 {source_count} 个官方来源，识别 {new_count} 条此前未入库的药学信息化项目动态。",
        "本期只保留药学信息化项目；采购标的、接口和执行边界仍需核验原文附件。",
        "当前重点方向：住院药学监护、合理用药审查、药物重整、药学记录、HIS接口与药学管理模块。",
    ]
    highlights.extend(f"{fact['date']}：{fact['title']}" for fact in facts[:6])
    while len(highlights) < 5:
        highlights.append("药学信息化项目应重点核验业务闭环、接口范围、规则库维护和上线交付责任。")
    return highlights[:8]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect pharmacy information-system projects and exclude drug-only procurement notices.")
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
    history = [ensure_fingerprint(dict(item)) for item in history_payload.get("facts", []) if is_allowed_fact(item)]
    seen = {item["dedupe_fingerprint"] for item in history}
    collected: list[dict] = []
    statuses = []
    source_count = 0
    for source in sources:
        try:
            if source.get("kind") == "verified_items":
                items = parse_verified_items(source)
            else:
                text = fetch_text(source["url"], insecure=args.insecure)
                if source.get("kind") == "gdmede_announcements":
                    items = parse_gdmede(source, text)
                else:
                    raise ValueError(f"unsupported source kind: {source.get('kind')}")
            fresh_items = [item for item in items if item["date"] >= cutoff and item["date"] <= as_of.date().isoformat() and is_allowed_fact(item)]
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
    history_payload = {"schema_version": "1.0", "dedupe_rule": "sha256(title|date|domain)", "last_collection_at": as_of.strftime("%Y-%m-%d %H:%M %z"), "facts": history}

    report = json.loads(args.report.read_text(encoding="utf-8"))
    recent = sorted((item for item in history if item.get("date", "") >= cutoff and is_allowed_fact(item)), key=lambda item: (item.get("date", ""), item.get("title", "")), reverse=True)
    report["facts"] = recent[:12]
    report["regional_procurements"] = build_regional_rows(recent[:12])
    report["highlights"] = build_highlights(recent, source_count, len(collected))
    report["collection_note"] = (
        f"本期统计区间 {report.get('period_start')} 至 {report.get('period_end')}；"
        f"内容由官方来源采集，回溯 {lookback_days} 天，新增入库 {len(collected)} 条药学信息化项目，已屏蔽纯药品采购内容。"
    )
    report["opportunity_actions"] = [
        {"priority": "P0", "title": "核验药学系统采购边界", "description": "确认药学监护、审方、合理用药、药学服务、规则库和HIS/EMR接口范围，避免把药品采购内容纳入产品线索。"},
        {"priority": "P1", "title": "建立系统接口需求表", "description": "记录HIS、EMR、医嘱、检验检查、医保、移动端和数据交换接口，区分标准能力、定制开发与交付责任。"},
        {"priority": "P1", "title": "跟进药师使用闭环", "description": "关注处方审核、住院药学监护、药物重整、用药咨询、药学记录和统计分析等可验收业务闭环。"},
    ]
    report["collection_meta"] = {"run_at": as_of.strftime("%Y-%m-%d %H:%M:%S%z"), "lookback_days": lookback_days, "source_fetch_status": statuses, "source_count": source_count, "new_item_count": len(collected), "fresh_item_count": len(recent), "content_scope": "pharmacy_information_systems_only"}
    args.history.write_text(json.dumps(history_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"COLLECTION_OK sources={source_count} fresh={len(recent)} new={len(collected)} cutoff={cutoff} scope=pharmacy_information_systems_only")
    for item in collected:
        print(f"NEW {item['date']} {item['title']} {item['source_url']}")


if __name__ == "__main__":
    main()
