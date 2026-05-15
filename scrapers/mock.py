import random
import json
import os
import hashlib
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)

_PLATFORM_URLS = {
    "Boss直聘": "https://www.zhipin.com/job_detail/{hash}.html",
    "智联招聘": "https://jobs.zhaopin.com/{hash}.htm",
    "猎聘": "https://www.liepin.com/job/{hash}.shtml",
    "前程无忧": "https://jobs.51job.com/{city}/{hash}.html",
    "拉勾": "https://www.lagou.com/jobs/{hash}.html",
    "脉脉": "https://maimai.cn/job/{hash}",
}


class MockScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.platform_name = "模拟数据"
        self.base_url = ""

    def search(self, keyword, city="", max_pages=1, progress_callback=None):
        if progress_callback:
            progress_callback("[模拟数据] 正在加载演示数据...")
        demo_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "demo_data.json"
        )
        if os.path.exists(demo_file):
            with open(demo_file, "r", encoding="utf-8") as f:
                all_jobs = json.load(f)
        else:
            all_jobs = self._generate_mock_data(keyword, city)

        if progress_callback:
            progress_callback("[模拟数据] 正在筛选匹配岗位...")
        filtered = []
        for job in all_jobs:
            if keyword.lower() in job.get("job_title", "").lower():
                if not city or city in job.get("location", ""):
                    filtered.append(job)

        if not filtered:
            if progress_callback:
                progress_callback("[模拟数据] 未匹配到，正在动态生成数据...")
            all_jobs = self._generate_mock_data(keyword, city)
            for job in all_jobs:
                if not city or city in job.get("location", ""):
                    filtered.append(job)

        if progress_callback:
            progress_callback(f"[模拟数据] 已获取 {len(filtered)} 条岗位数据")
        logger.info(f"[模拟数据] 返回 {len(filtered)} 条岗位")
        return filtered

    def _generate_mock_data(self, keyword, city=""):
        companies = [
            ("字节跳动", "10000人以上", "互联网"),
            ("阿里巴巴", "10000人以上", "互联网"),
            ("腾讯", "10000人以上", "互联网"),
            ("美团", "10000人以上", "互联网"),
            ("华为", "10000人以上", "通信"),
            ("小米", "5000-9999人", "互联网"),
            ("百度", "10000人以上", "互联网"),
            ("京东", "10000人以上", "电商"),
            ("网易", "10000人以上", "互联网"),
            ("拼多多", "10000人以上", "电商"),
            ("快手", "5000-9999人", "互联网"),
            ("滴滴出行", "5000-9999人", "出行"),
            ("携程", "5000-9999人", "旅游"),
            ("蚂蚁集团", "10000人以上", "金融科技"),
            ("商汤科技", "1000-4999人", "AI"),
            ("旷视科技", "1000-4999人", "AI"),
            ("大疆创新", "5000-9999人", "硬件"),
            ("OPPO", "10000人以上", "硬件"),
            ("VIVO", "10000人以上", "硬件"),
            ("联想", "10000人以上", "硬件"),
            ("中软国际", "10000人以上", "外包"),
            ("软通动力", "10000人以上", "外包"),
            ("用友网络", "5000-9999人", "企业服务"),
            ("金蝶软件", "5000-9999人", "企业服务"),
            ("科大讯飞", "5000-9999人", "AI"),
            ("微众银行", "1000-4999人", "金融科技"),
            ("平安科技", "5000-9999人", "金融科技"),
            ("顺丰科技", "1000-4999人", "物流"),
            ("B站", "5000-9999人", "互联网"),
            ("小红书", "1000-4999人", "互联网"),
            ("得物", "1000-4999人", "电商"),
            ("米哈游", "1000-4999人", "游戏"),
            ("莉莉丝", "500-999人", "游戏"),
            ("三七互娱", "1000-4999人", "游戏"),
            ("理想汽车", "5000-9999人", "新能源"),
            ("蔚来汽车", "5000-9999人", "新能源"),
            ("小鹏汽车", "5000-9999人", "新能源"),
            ("比亚迪", "10000人以上", "新能源"),
            ("宁德时代", "10000人以上", "新能源"),
            ("中兴通讯", "10000人以上", "通信"),
        ]

        cities = ["北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "南京", "苏州", "西安", "长沙", "重庆"]
        experiences = ["1-3年", "3-5年", "5-10年", "应届生", "1年以下", "不限", "3-5年", "5-10年"]
        educations = ["本科", "硕士", "大专", "本科", "本科", "硕士", "博士", "不限"]
        platforms = ["Boss直聘", "智联招聘", "猎聘", "前程无忧", "拉勾", "脉脉"]

        salary_ranges_by_exp = {
            "应届生": [(8, 15), (10, 18), (6, 12), (12, 20)],
            "1年以下": [(10, 18), (8, 15), (12, 20)],
            "1-3年": [(15, 25), (12, 22), (18, 30), (20, 35)],
            "3-5年": [(20, 35), (25, 40), (30, 50), (18, 30)],
            "5-10年": [(30, 50), (35, 60), (40, 70), (25, 45)],
            "不限": [(10, 20), (15, 30), (12, 25)],
        }

        titles_by_keyword = {
            "Python": ["Python开发工程师", "Python后端工程师", "Python高级工程师", "Python全栈工程师", "Python数据工程师", "Python爬虫工程师", "Python运维开发", "Python算法工程师"],
            "Java": ["Java开发工程师", "Java高级工程师", "Java架构师", "Java后端工程师", "Java全栈工程师", "Java大数据工程师", "Java微服务工程师"],
            "前端": ["前端开发工程师", "前端高级工程师", "前端架构师", "React开发工程师", "Vue开发工程师", "全栈工程师", "前端负责人"],
            "产品经理": ["产品经理", "高级产品经理", "产品总监", "B端产品经理", "C端产品经理", "数据产品经理", "AI产品经理"],
            "数据分析": ["数据分析师", "高级数据分析师", "数据挖掘工程师", "BI工程师", "数据运营", "商业分析师"],
            "AI": ["AI工程师", "算法工程师", "机器学习工程师", "深度学习工程师", "NLP工程师", "CV工程师", "大模型工程师", "AIGC工程师"],
            "测试": ["测试工程师", "自动化测试工程师", "测试开发工程师", "性能测试工程师", "QA负责人", "测试经理"],
            "运维": ["运维工程师", "DevOps工程师", "SRE工程师", "云原生工程师", "运维架构师", "K8s工程师"],
            "设计": ["UI设计师", "UX设计师", "交互设计师", "视觉设计师", "产品设计师", "设计总监"],
        }

        keyword_lower = keyword.lower()
        titles = []
        for k, v in titles_by_keyword.items():
            if k.lower() in keyword_lower or keyword_lower in k.lower():
                titles = v
                break
        if not titles:
            titles = [f"{keyword}工程师", f"高级{keyword}工程师", f"{keyword}开发工程师", f"{keyword}专员", f"{keyword}经理", f"{keyword}架构师"]

        jobs = []
        for i in range(60):
            company = random.choice(companies)
            exp = random.choice(experiences)
            salary_range = random.choice(salary_ranges_by_exp.get(exp, [(15, 25)]))
            salary_min = salary_range[0] + random.randint(-2, 2)
            salary_max = salary_range[1] + random.randint(-3, 3)
            salary_min = max(salary_min, 5)
            salary_max = max(salary_max, salary_min + 3)
            months = random.choice([12, 12, 12, 13, 14, 15, 16])
            salary_avg = round((salary_min + salary_max) / 2 * months / 12, 1)
            loc = random.choice(cities) if not city else city
            title = random.choice(titles)
            plat = random.choice(platforms)
            url_hash = hashlib.md5(f"{title}{company[0]}{i}".encode()).hexdigest()[:12]
            url_template = _PLATFORM_URLS.get(plat, "")
            job_url = url_template.format(hash=url_hash, city=loc) if url_template else ""

            jobs.append({
                "job_title": title,
                "company": company[0],
                "location": loc,
                "salary_raw": f"{salary_min}-{salary_max}K" + (f"·{months}薪" if months > 12 else ""),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_avg": salary_avg,
                "experience": exp,
                "education": random.choice(educations),
                "company_size": company[1],
                "company_type": company[2],
                "platform": plat,
                "job_url": job_url,
            })

        return jobs

    def _parse_list_page(self, html):
        return []

    def _fetch_page(self, url, params=None, encoding=None):
        return None
