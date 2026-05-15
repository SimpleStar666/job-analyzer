#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import OUTPUT_DIR, MAX_PAGES
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


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def get_scrapers(platforms, use_mock=False):
    if use_mock:
        return [MockScraper()]
    scraper_map = {
        "boss": BossScraper,
        "zhilian": ZhilianScraper,
        "liepin": LiepinScraper,
        "job51": Job51Scraper,
        "lagou": LagouScraper,
        "maimai": MaimaiScraper,
    }
    if "all" in platforms:
        return [cls() for cls in scraper_map.values()]
    return [scraper_map[p]() for p in platforms if p in scraper_map]


def run_search(keyword, city="", platforms=None, max_pages=MAX_PAGES, use_mock=False):
    if platforms is None:
        platforms = ["all"]
    scrapers = get_scrapers(platforms, use_mock)
    all_jobs = []
    for scraper in scrapers:
        try:
            jobs = scraper.search(keyword, city=city, max_pages=max_pages)
            all_jobs.extend(jobs)
            logging.info(f"[{scraper.platform_name}] 获取 {len(jobs)} 条岗位")
        except Exception as e:
            logging.error(f"[{scraper.platform_name}] 爬取失败: {e}")
    return all_jobs


def run_pipeline(keyword, city="", platforms=None, max_pages=MAX_PAGES, use_mock=False):
    raw_jobs = run_search(keyword, city, platforms, max_pages, use_mock)
    cleaned = clean_jobs(raw_jobs)
    deduped = deduplicate(cleaned)
    enriched = enrich_salary(deduped)
    result = analyze(enriched)
    return result


def print_summary(result, keyword):
    summary = result.get("summary", {})
    if not summary:
        print("\n⚠️  未找到相关岗位数据")
        return

    print(f"\n{'='*60}")
    print(f"  📊 岗位分析报告 - {keyword}")
    print(f"{'='*60}")
    print(f"  岗位总数:   {summary.get('total_jobs', 0)}")
    print(f"  平均薪资:   {summary.get('salary_avg', 0)}K/月")
    print(f"  薪资中位数: {summary.get('salary_median', 0)}K/月")
    print(f"  薪资范围:   {summary.get('salary_min', 0)}K ~ {summary.get('salary_max', 0)}K")

    top_cities = summary.get("top_cities", [])
    if top_cities:
        print(f"\n  🏙️  热门城市: {', '.join(f'{c}({n})' for c, n in top_cities)}")

    top_exp = summary.get("top_experience", [])
    if top_exp:
        print(f"  💼 经验要求: {', '.join(f'{e}({n})' for e, n in top_exp)}")

    top_edu = summary.get("top_education", [])
    if top_edu:
        print(f"  🎓 学历要求: {', '.join(f'{e}({n})' for e, n in top_edu)}")

    jobs = result.get("jobs", [])
    if jobs:
        print(f"\n{'='*60}")
        print(f"  岗位列表 (按薪资从低到高)")
        print(f"{'='*60}")
        print(f"  {'#':<3} {'岗位':<20} {'公司':<14} {'城市':<6} {'薪资':<16} {'均薪':<8} {'经验':<8} {'推荐'}")
        print(f"  {'-'*90}")
        for i, job in enumerate(jobs, 1):
            title = job.get("job_title", "")[:18]
            company = job.get("company", "")[:12]
            location = job.get("location", "")[:4]
            salary = job.get("salary_raw", "")
            avg = f"{job.get('salary_avg', 0)}K"
            exp = job.get("experience", "")[:6]
            rec = job.get("recommendation", "")
            print(f"  {i:<3} {title:<20} {company:<14} {location:<6} {salary:<16} {avg:<8} {exp:<8} {rec}")

        high_value = [j for j in jobs if "高性价比" in j.get("recommendation", "")]
        if high_value:
            print(f"\n{'='*60}")
            print(f"  ⭐ 高性价比推荐 (Top {min(5, len(high_value))})")
            print(f"{'='*60}")
            for j in high_value[:5]:
                print(f"  {j['job_title']} @ {j['company']} ({j['location']}) "
                      f"- {j['salary_raw']} [性价比: {j['value_score']}]")


def save_results(result, keyword, output_dir=None):
    if output_dir is None:
        output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(output_dir, f"{keyword}_{timestamp}")

    export_csv(result["jobs"], f"{base}.csv")
    export_json(result, f"{base}.json")
    export_html_report(result, f"{base}.html", keyword)
    print(f"\n📁 结果已保存:")
    print(f"   CSV: {base}.csv")
    print(f"   JSON: {base}.json")
    print(f"   HTML: {base}.html")


def main():
    parser = argparse.ArgumentParser(
        description="📊 JobAnalyzer - 岗位情况分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py search Python                    # 搜索Python岗位(模拟数据)
  python cli.py search Java --city 北京           # 搜索北京Java岗位
  python cli.py search 前端 --platforms boss      # 仅从Boss直聘搜索
  python cli.py search AI --live                  # 使用真实爬虫
  python cli.py search Python --export            # 搜索并导出结果
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    search_parser = subparsers.add_parser("search", help="搜索岗位")
    search_parser.add_argument("keyword", help="搜索关键词")
    search_parser.add_argument("--city", default="", help="城市筛选")
    search_parser.add_argument("--platforms", nargs="+", default=["all"],
                               choices=["boss", "zhilian", "liepin", "job51", "lagou", "maimai", "all"],
                               help="招聘平台")
    search_parser.add_argument("--max-pages", type=int, default=MAX_PAGES,
                               help="每平台最大翻页数")
    search_parser.add_argument("--live", action="store_true",
                               help="使用真实爬虫(默认使用模拟数据)")
    search_parser.add_argument("--export", action="store_true",
                               help="导出结果到文件")
    search_parser.add_argument("--output-dir", default=OUTPUT_DIR,
                               help="输出目录")
    search_parser.add_argument("-v", "--verbose", action="store_true",
                               help="详细日志")

    demo_parser = subparsers.add_parser("demo", help="运行演示(使用内置数据)")
    demo_parser.add_argument("keyword", nargs="?", default="Python",
                             help="演示关键词(默认Python)")
    demo_parser.add_argument("--export", action="store_true",
                             help="导出结果到文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    setup_logging(getattr(args, "verbose", False))

    if args.command == "demo":
        print("🎯 运行演示模式 (内置模拟数据)...")
        result = run_pipeline(args.keyword, use_mock=True)
        print_summary(result, args.keyword)
        if args.export:
            save_results(result, args.keyword)

    elif args.command == "search":
        use_mock = not args.live
        if use_mock:
            print("💡 使用模拟数据模式 (加 --live 使用真实爬虫)")
        else:
            print("🌐 使用真实爬虫模式 (注意反爬策略)")

        result = run_pipeline(
            keyword=args.keyword,
            city=args.city,
            platforms=args.platforms,
            max_pages=args.max_pages,
            use_mock=use_mock,
        )
        print_summary(result, args.keyword)
        if args.export:
            save_results(result, args.keyword, args.output_dir)


if __name__ == "__main__":
    main()
