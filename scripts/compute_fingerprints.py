"""Compute dedupe fingerprints for new facts."""
import hashlib

def fingerprint(title, date, domain):
    normalized = " ".join(f"{title}|{date}|{domain}".lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

new_facts = [
    {
        "title": "广水市第一人民医院全市审方中心系统购置项目（包括所有市直医疗机构、卫生院）中标成交公告",
        "date": "2026-08-19",
        "domain": "www.ccgp.gov.cn"
    },
    {
        "title": "运城市盐湖区医疗集团中心药房信息系统采购项目（二次）的公开招标公告",
        "date": "2026-08-20",
        "domain": "www.ccgp.gov.cn"
    },
    {
        "title": "贵州医科大学第三附属医院合理用药监测系统V4.3、PASS临床药学管理系统V.30维保项目（三次）采购公告",
        "date": "2026-08-20",
        "domain": "www.sfy-gmc.com"
    },
    {
        "title": "关于做好基本药物优先配备使用工作的通知",
        "date": "2026-08-19",
        "domain": "wsjkw.hebei.gov.cn"
    },
    {
        "title": "滨湖双鹤2026年合理用药系统维保采购项目",
        "date": "2026-08-12",
        "domain": "szecp.crc.com.cn"
    }
]

for f in new_facts:
    fp = fingerprint(f["title"], f["date"], f["domain"])
    print(f"{fp} | {f['date']} | {f['title'][:60]}")
