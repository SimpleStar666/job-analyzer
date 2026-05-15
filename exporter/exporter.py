import csv
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def export_csv(jobs, filepath):
    if not jobs:
        logger.warning("无数据可导出")
        return
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    fieldnames = [
        "job_title", "company", "location", "salary_raw",
        "salary_min", "salary_max", "salary_avg",
        "experience", "education", "company_size", "company_type",
        "platform", "value_score", "recommendation", "job_url",
    ]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for job in jobs:
            writer.writerow(job)
    logger.info(f"CSV导出完成: {filepath} ({len(jobs)} 条)")


def export_json(data, filepath):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON导出完成: {filepath}")


def export_html_report(data, filepath, keyword):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    jobs = data.get("jobs", [])
    summary = data.get("summary", {})

    html = _build_html(keyword, jobs, summary, data)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"HTML报告导出完成: {filepath}")


def _build_html(keyword, jobs, summary, data):
    rows_html = ""
    for i, job in enumerate(jobs, 1):
        rec = job.get("recommendation", "")
        rec_class = ""
        if "高性价比" in rec:
            rec_class = "style='color:#52c41a;font-weight:bold'"
        elif "不错" in rec:
            rec_class = "style='color:#1890ff'"
        elif "偏低" in rec:
            rec_class = "style='color:#ff4d4f'"
        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td>{job.get('job_title','')}</td>
            <td>{job.get('company','')}</td>
            <td>{job.get('location','')}</td>
            <td>{job.get('salary_raw','')}</td>
            <td>{job.get('salary_avg',0)}K</td>
            <td>{job.get('experience','')}</td>
            <td>{job.get('education','')}</td>
            <td>{job.get('company_size','')}</td>
            <td>{job.get('company_type','')}</td>
            <td>{job.get('platform','')}</td>
            <td>{job.get('value_score',0)}</td>
            <td {rec_class}>{rec}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>岗位分析报告 - {keyword}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }}
.container {{ max-width: 1400px; margin: 0 auto; }}
h1 {{ color: #1a1a1a; border-bottom: 2px solid #1890ff; padding-bottom: 10px; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
.summary-card {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.summary-card h3 {{ margin: 0 0 8px 0; color: #666; font-size: 14px; }}
.summary-card .value {{ font-size: 24px; font-weight: bold; color: #1890ff; }}
table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
th {{ background: #1890ff; color: white; padding: 12px 8px; text-align: left; font-size: 13px; }}
td {{ padding: 10px 8px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }}
tr:hover {{ background: #e6f7ff; }}
</style>
</head>
<body>
<div class="container">
<h1>📊 岗位分析报告 - {keyword}</h1>
<div class="summary">
    <div class="summary-card"><h3>岗位总数</h3><div class="value">{summary.get('total_jobs',0)}</div></div>
    <div class="summary-card"><h3>平均薪资</h3><div class="value">{summary.get('salary_avg',0)}K</div></div>
    <div class="summary-card"><h3>薪资中位数</h3><div class="value">{summary.get('salary_median',0)}K</div></div>
    <div class="summary-card"><h3>薪资范围</h3><div class="value">{summary.get('salary_min',0)}K ~ {summary.get('salary_max',0)}K</div></div>
</div>
<table>
<tr><th>#</th><th>岗位</th><th>公司</th><th>城市</th><th>薪资</th><th>均薪</th><th>经验</th><th>学历</th><th>规模</th><th>行业</th><th>来源</th><th>性价比</th><th>推荐</th></tr>
{rows_html}
</table>
</div>
</body>
</html>"""
