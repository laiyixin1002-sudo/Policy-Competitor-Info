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
- 触发时间：每周一 09:00（Asia/Shanghai），对应 cron `0 1 * * 1`
- 统计区间：上周一 09:00 前推 7 天，页面正文显示为 `YYYY-MM-DD ~ YYYY-MM-DD`
- 输出路径：`reports/药学情报周报_YYYY-MM-DD_YYYY-MM-DD.html`
- 转发链接：页面首屏和 `reports/index.html` 均展示“周报标题 + URL”

手动生成下一期：

```powershell
python scripts/update_report_period.py
python scripts/render_html.py
```
