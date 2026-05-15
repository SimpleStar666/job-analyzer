import json
import os
import sys
import logging
import queue
import threading
from datetime import datetime

from flask import Flask, render_template, request, jsonify, Response, stream_with_context

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from config import OUTPUT_DIR, MAX_PAGES, DEMO_DATA_FILE, FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from scrapers.boss import BossScraper
from scrapers.zhilian import ZhilianScraper
from scrapers.liepin import LiepinScraper
from scrapers.job51 import Job51Scraper
from scrapers.lagou import LagouScraper
from scrapers.maimai import MaimaiScraper
from scrapers.mock import MockScraper
from processor.cleaner import clean_jobs
from processor.deduplicator import deduplicate
from processor.salary_parser import enrich_salary
from processor.analyzer import analyze
from exporter.exporter import export_csv, export_json, export_html_report

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
)

logger = logging.getLogger(__name__)


def get_demo_result():
    if os.path.exists(DEMO_DATA_FILE):
        with open(DEMO_DATA_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    else:
        mock = MockScraper()
        jobs = mock.search("Python")
    cleaned = clean_jobs(jobs)
    deduped = deduplicate(cleaned)
    enriched = enrich_salary(deduped)
    result = analyze(enriched)
    return result


def run_pipeline(keyword, city="", platforms=None, max_pages=MAX_PAGES, use_mock=True):
    scraper_map = {
        "boss": BossScraper,
        "zhilian": ZhilianScraper,
        "liepin": LiepinScraper,
        "job51": Job51Scraper,
        "lagou": LagouScraper,
        "maimai": MaimaiScraper,
    }
    if use_mock or not platforms:
        scrapers = [MockScraper()]
    else:
        scrapers = [scraper_map[p]() for p in platforms if p in scraper_map]

    all_jobs = []
    for scraper in scrapers:
        try:
            jobs = scraper.search(keyword, city=city, max_pages=max_pages)
            all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"[{scraper.platform_name}] 爬取失败: {e}")

    cleaned = clean_jobs(all_jobs)
    deduped = deduplicate(cleaned)
    enriched = enrich_salary(deduped)
    result = analyze(enriched)
    return result


def _sse_event(data):
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_scraping_thread(q, keyword, city, platforms, max_pages, use_mock):
    try:
        scraper_map = {
            "boss": BossScraper,
            "zhilian": ZhilianScraper,
            "liepin": LiepinScraper,
            "job51": Job51Scraper,
            "lagou": LagouScraper,
            "maimai": MaimaiScraper,
        }
        if use_mock or not platforms:
            scrapers = [MockScraper()]
        else:
            scrapers = [scraper_map[p]() for p in platforms if p in scraper_map]

        def cb(msg):
            q.put({"type": "scraper_progress", "message": msg})

        all_jobs = []
        for scraper in scrapers:
            try:
                jobs = scraper.search(keyword, city=city, max_pages=max_pages,
                                      progress_callback=cb)
                all_jobs.extend(jobs)
            except Exception as e:
                q.put({"type": "scraper_error", "message": f"[{scraper.platform_name}] 爬取失败: {e}"})

        q.put({"type": "scraping_done", "jobs": all_jobs})
    except Exception as e:
        q.put({"type": "error", "message": str(e)})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/demo")
def demo():
    result = get_demo_result()
    return jsonify(result)


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    keyword = data.get("keyword", "").strip()
    city = data.get("city", "").strip()
    platforms = data.get("platforms", [])
    use_mock = data.get("use_mock", True)
    max_pages = data.get("max_pages", MAX_PAGES)

    if not keyword:
        return jsonify({"error": "请输入搜索关键词"}), 400

    try:
        result = run_pipeline(keyword, city=city, platforms=platforms,
                              max_pages=max_pages, use_mock=use_mock)
        return jsonify(result)
    except Exception as e:
        logger.exception("搜索失败")
        return jsonify({"error": str(e)}), 500


@app.route("/api/search/stream", methods=["POST"])
def search_stream():
    data = request.get_json() or {}
    keyword = data.get("keyword", "").strip()
    city = data.get("city", "").strip()
    platforms = data.get("platforms", [])
    use_mock = data.get("use_mock", True)
    max_pages = data.get("max_pages", MAX_PAGES)

    if not keyword:
        return jsonify({"error": "请输入搜索关键词"}), 400

    scraper_map = {
        "boss": BossScraper,
        "zhilian": ZhilianScraper,
        "liepin": LiepinScraper,
        "job51": Job51Scraper,
        "lagou": LagouScraper,
        "maimai": MaimaiScraper,
    }
    if use_mock or not platforms:
        scraping_label = 3
    else:
        scraping_label = len([p for p in platforms if p in scraper_map]) * max_pages

    total_steps = scraping_label + 4
    step = [0]

    def progress_event(msg):
        step[0] += 1
        pct = int(step[0] / total_steps * 100) if total_steps > 0 else 100
        pct = min(pct, 99)
        return _sse_event({
            "type": "progress",
            "step": step[0],
            "total": total_steps,
            "percent": pct,
            "message": msg,
        })

    def generate():
        yield _sse_event({
            "type": "start",
            "total": total_steps,
            "message": f"开始搜索「{keyword}」，预计 {total_steps} 个步骤",
        })

        q = queue.Queue()
        thread = threading.Thread(
            target=_run_scraping_thread,
            args=(q, keyword, city, platforms, max_pages, use_mock),
        )
        thread.start()

        scraping_done = False
        while not scraping_done:
            try:
                item = q.get(timeout=0.5)
            except queue.Empty:
                yield _sse_event({"type": "heartbeat"})
                continue

            if item["type"] == "scraper_progress":
                yield progress_event(item["message"])
            elif item["type"] == "scraper_error":
                yield _sse_event({"type": "log", "message": item["message"], "level": "warn"})
            elif item["type"] == "scraping_done":
                scraping_done = True
                all_jobs = item["jobs"]
            elif item["type"] == "error":
                yield _sse_event({"type": "error", "message": item["message"]})
                return

        thread.join()

        if not all_jobs and not use_mock:
            yield _sse_event({
                "type": "log",
                "message": "⚠️ 真实爬虫未获取到数据 — 招聘网站通常需要JS渲染，静态HTML解析无法获取动态内容。自动回退到模拟数据...",
                "level": "warn",
            })
            yield progress_event("🔄 真实爬取无结果，正在回退到模拟数据...")
            mock_scraper = MockScraper()
            all_jobs = mock_scraper.search(keyword, city=city, max_pages=max_pages)
            yield _sse_event({
                "type": "log",
                "message": f"✅ 模拟数据已生成 {len(all_jobs)} 条岗位",
                "level": "",
            })

        yield progress_event("🧹 正在清洗数据，去除HTML标签和空白字符...")
        cleaned = clean_jobs(all_jobs)

        yield progress_event("🔍 正在智能去重，合并相同公司+岗位+地点...")
        deduped = deduplicate(cleaned)

        yield progress_event("💰 正在解析薪资数据，标准化为月薪(K)...")
        enriched = enrich_salary(deduped)

        yield progress_event("📊 正在分析岗位数据，计算性价比评分和统计分布...")
        result = analyze(enriched)

        yield _sse_event({
            "type": "complete",
            "percent": 100,
            "result": result,
        })

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/export", methods=["POST"])
def export():
    data = request.get_json() or {}
    keyword = data.get("keyword", "unknown")
    result_data = data.get("result", {})
    fmt = data.get("format", "json")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(OUTPUT_DIR, f"{keyword}_{timestamp}")

    try:
        if fmt == "csv":
            filepath = f"{base}.csv"
            export_csv(result_data.get("jobs", []), filepath)
        elif fmt == "html":
            filepath = f"{base}.html"
            export_html_report(result_data, filepath, keyword)
        else:
            filepath = f"{base}.json"
            export_json(result_data, filepath)
        return jsonify({"status": "ok", "filepath": filepath})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)