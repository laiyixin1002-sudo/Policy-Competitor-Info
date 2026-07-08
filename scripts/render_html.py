from __future__ import annotations

import argparse
import html
import json
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "weekly_report.html"
DEFAULT_INPUT = ROOT / "data" / "weekly_report.json"
REPORTS_DIR = ROOT / "reports"
BASE_URL = "https://laiyixin1002-sudo.github.io/Policy-Competitor-Info/reports"


def clip_text(value: str, max_chars: int) -> str:
    value = " ".join(str(value or "").split())
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def render_highlights(items: list[str]) -> str:
    return "\n        ".join(f"<li>{esc(clip_text(item, 98))}</li>" for item in items[:8])


def render_deal_strip(fact: dict) -> str:
    amount = fact.get("amount")
    stage = fact.get("stage")
    if not amount and not stage:
        return ""
    amount = amount or "未披露"
    stage = stage or fact.get("source_type") or "信息"
    return f"""<div class="deal-strip">
            <div class="deal"><span>金额</span><strong>{esc(amount)}</strong></div>
            <div class="deal stage"><span>阶段</span><strong>{esc(stage)}</strong></div>
          </div>"""


def render_fact_card(fact: dict) -> str:
    title = esc(fact.get("title"))
    summary = esc(clip_text(fact.get("fact_summary", ""), 80))
    publisher = esc(fact.get("publisher"))
    region = esc(fact.get("region"))
    date = esc(fact.get("date"))
    domain = esc(fact.get("source_domain"))
    source_type = esc(fact.get("source_type", "来源"))
    source_url = esc(fact.get("source_url"))
    status = esc(fact.get("url_status"))
    insight = esc(clip_text(fact.get("sales_insight", ""), 60))
    modules = fact.get("system_modules") or []
    tags = "\n          ".join(f'<span class="tag">{esc(module)}</span>' for module in modules[:4])

    return f"""<article class="card">
          <h4>{title}</h4>
          <p class="fact">{summary}</p>
          <div class="sub">{publisher} · {region} · {date}</div>
          {render_deal_strip(fact)}
          <div class="tags">
          {tags}
          </div>
          <p class="insight"><strong>销售启发：</strong>{insight}</p>
          <div class="card-footer">
            <span class="status">{source_type} · {domain} · {status}</span>
            <a class="btn" href="{source_url}" target="_blank" rel="noopener">🔗 来源</a>
          </div>
        </article>"""


def group_facts(items: list[dict]) -> OrderedDict[str, list[dict]]:
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for item in items:
        category = str(item.get("category") or "未分组")
        grouped.setdefault(category, []).append(item)
    return grouped


def render_grouped_cards(items: list[dict]) -> str:
    if not items:
        return '<div class="empty">暂无信息</div>'

    groups = []
    for category, facts in group_facts(items).items():
        cards = "\n        ".join(render_fact_card(item) for item in facts)
        groups.append(
            f"""<div class="group">
        <h3>{esc(category)}</h3>
        <div class="grid">
        {cards}
        </div>
      </div>"""
        )
    return "\n      ".join(groups)


def render_opportunity_actions(items: list[dict]) -> str:
    if not items:
        return '<div class="empty">暂无建议</div>'
    return "\n        ".join(
        f"""<article class="action">
          <span class="priority">{esc(item.get("priority"))}</span>
          <h3>{esc(item.get("title"))}</h3>
          <p>{esc(item.get("description"))}</p>
        </article>"""
        for item in items
    )


def validate_report(data: dict) -> None:
    required_fact_fields = {
        "title",
        "fact_summary",
        "publisher",
        "region",
        "date",
        "source_domain",
        "source_url",
        "url_status",
        "system_modules",
        "sales_insight",
        "dedupe_fingerprint",
    }
    highlights = data.get("highlights") or []
    if not 5 <= len(highlights) <= 8:
        raise ValueError("highlights must contain 5 to 8 items")

    for index, fact in enumerate(data.get("facts") or [], start=1):
        missing = required_fact_fields - set(fact)
        if missing:
            raise ValueError(f"facts[{index}] missing fields: {sorted(missing)}")
        if len(fact.get("system_modules") or []) > 4:
            raise ValueError(f"facts[{index}] has more than 4 system modules")
        if fact.get("url_status") != "ok":
            raise ValueError(f"facts[{index}] must have url_status ok")


def build_report_html(data: dict) -> str:
    period_start = data["period_start"]
    period_end = data["period_end"]
    page_title = f"药学情报周报_{period_start}_{period_end}"
    replacements = {
        "page_title": page_title,
        "report_title": esc(data.get("report_title", "药学情报周报")),
        "collection_note": esc(data.get("collection_note", "")),
        "period_start": esc(period_start),
        "period_end": esc(period_end),
        "generated_at": esc(data.get("generated_at", "")),
        "highlights_html": render_highlights(data.get("highlights") or []),
        "facts_html": render_grouped_cards(data.get("facts") or []),
        "opportunity_actions_html": render_opportunity_actions(data.get("opportunity_actions") or []),
    }

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, value in replacements.items():
        template = template.replace("{{ " + key + " }}", value)
    return template


def build_index(report_files: list[Path]) -> str:
    links = []
    for file_path in sorted(report_files, reverse=True):
        name = file_path.name
        url = f"{BASE_URL}/{name}"
        label = html.escape(file_path.stem, quote=True)
        links.append(f'<li><a href="{html.escape(name, quote=True)}">{label}</a><span>{html.escape(url)}</span></li>')

    items = "\n        ".join(links) if links else "<li>暂无周报</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>药学情报周报列表</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; background: #f6f7f9; color: #17202a; }}
    main {{ width: min(900px, 100%); margin: 0 auto; padding: 24px 16px 40px; }}
    h1 {{ margin: 0 0 18px; font-size: clamp(24px, 5vw, 34px); letter-spacing: 0; }}
    ul {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }}
    li {{ background: #fff; border: 1px solid #dfe4ea; border-radius: 8px; padding: 14px; display: grid; gap: 6px; }}
    a {{ color: #176b87; font-weight: 700; text-decoration: none; }}
    span {{ color: #65717f; font-size: 13px; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <main>
    <h1>药学情报周报列表</h1>
    <ul>
        {items}
    </ul>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render weekly pharmacy intelligence report HTML.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to weekly_report.json")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    validate_report(data)

    REPORTS_DIR.mkdir(exist_ok=True)
    output_name = f"药学情报周报_{data['period_start']}_{data['period_end']}.html"
    output_path = REPORTS_DIR / output_name
    output_path.write_text(build_report_html(data), encoding="utf-8")

    report_files = [path for path in REPORTS_DIR.glob("药学情报周报_*.html") if path.name != "index.html"]
    (REPORTS_DIR / "index.html").write_text(build_index(report_files), encoding="utf-8")

    print(f"Rendered: {output_path}")
    print(f"Index: {REPORTS_DIR / 'index.html'}")
    print(f"Share URL: {BASE_URL}/{output_name}")


if __name__ == "__main__":
    main()
