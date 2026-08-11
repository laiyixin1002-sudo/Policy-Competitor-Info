# Policy-Competitor-Info

药学情报周报自动生成系统。

当前阶段已跑通结构化示例数据到 GitHub Pages 静态 HTML 的生成链路：

- `config/`: 来源与关键词配置
- `data/`: 事实历史与示例周报数据
- `templates/`: 周报 HTML 模板
- `scripts/`: 渲染脚本
- `reports/`: GitHub Pages 可发布页面

本地渲染：

```powershell
python scripts/render_html.py
```

每周自动发布：

- GitHub Actions: `.github/workflows/weekly-report.yml`
- 官方采集：`python scripts/collect_weekly_sources.py --min-new-items 1`
- 新鲜度门禁：`python scripts/validate_collection.py --min-new-items 1`；本期未采集到新条目时构建失败，不会发布旧内容。
- 产品口径：仅保留药学信息化、临床药学、合理用药、审方、药学监护、HIS药学模块等系统项目；纯药品挂网、药品集采、药品价格和中选药品公告直接过滤。
- 触发时间：每周一 09:00（Asia/Shanghai），对应 cron `0 1 * * 1`
- 统计区间：上周一 09:00 前推 7 天，页面正文显示为 `YYYY-MM-DD ~ YYYY-MM-DD`
- 输出路径：`reports/药学情报周报_YYYY-MM-DD_YYYY-MM-DD.html`
- 转发链接：页面首屏和 `reports/index.html` 均展示“周报标题 + URL”

手动生成下一期：

```powershell
python scripts/update_report_period.py
python scripts/render_html.py
```
