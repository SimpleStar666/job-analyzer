import re
import logging
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class BossScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.platform_name = "Boss直聘"
        self.base_url = "https://www.zhipin.com"

    def search(self, keyword, city="", max_pages=5, progress_callback=None):
        jobs = []
        city_code = self._get_city_code(city)
        for page in range(1, max_pages + 1):
            if progress_callback:
                progress_callback(f"[Boss直聘] 正在爬取第 {page}/{max_pages} 页")
            url = f"{self.base_url}/web/geek/job"
            params = {
                "query": keyword,
                "city": city_code,
                "page": page,
            }
            html = self._fetch_page(url, params=params)
            if not html:
                logger.warning(f"[Boss直聘] 第{page}页请求失败，跳过")
                break
            page_jobs = self._parse_list_page(html)
            if not page_jobs:
                logger.info(f"[Boss直聘] 第{page}页无数据，停止翻页")
                break
            jobs.extend(page_jobs)
            logger.info(f"[Boss直聘] 第{page}页获取 {len(page_jobs)} 条岗位")
            if page < max_pages:
                self._random_delay()
        return [self._normalize_job(j) for j in jobs]

    def _get_city_code(self, city):
        city_map = {
            "北京": "101010100", "上海": "101020100", "广州": "101280100",
            "深圳": "101280600", "杭州": "101210100", "成都": "101270100",
            "武汉": "101200100", "南京": "101190100", "苏州": "101190400",
            "西安": "101110100", "长沙": "101250100", "重庆": "101040100",
            "天津": "101030100", "郑州": "101180100", "东莞": "101281600",
            "沈阳": "101070100", "青岛": "101120200", "合肥": "101220100",
            "佛山": "101280800", "大连": "101070200",
        }
        return city_map.get(city, "100010000")

    def _parse_list_page(self, html):
        jobs = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            job_cards = soup.select(".job-list-box .job-card-wrapper")
            if not job_cards:
                job_cards = soup.select(".search-job-result .job-list li")
            if not job_cards:
                job_cards = soup.select(".job-list ul li")
            for card in job_cards:
                try:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"[Boss直聘] 解析单条岗位失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"[Boss直聘] 解析列表页失败: {e}")
        return jobs

    def _parse_job_card(self, card):
        title_el = card.select_one(".job-name a") or card.select_one(".job-title") or card.select_one("a.job-name")
        if not title_el:
            return None
        job_title = title_el.get_text(strip=True)
        job_url = title_el.get("href", "")
        if job_url and not job_url.startswith("http"):
            job_url = urljoin(self.base_url, job_url)

        salary_el = card.select_one(".salary") or card.select_one(".job-salary") or card.select_one(".red")
        salary_raw = salary_el.get_text(strip=True) if salary_el else ""
        salary_min, salary_max, salary_avg = self._parse_salary(salary_raw)

        company_el = card.select_one(".company-name a") or card.select_one(".company-text a") or card.select_one(".info-company a")
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(".job-area") or card.select_one(".job-area-wrapper")
        location = location_el.get_text(strip=True) if location_el else ""

        tag_list = card.select(".tag-list li") or card.select(".job-info .tag-list span")
        experience = ""
        education = ""
        if len(tag_list) >= 1:
            experience = tag_list[0].get_text(strip=True)
        if len(tag_list) >= 2:
            education = tag_list[1].get_text(strip=True)

        size_el = card.select_one(".company-tag li") or card.select_one(".info-desc")
        company_size = size_el.get_text(strip=True) if size_el else ""

        type_el = card.select_one(".company-tag li:nth-child(2)") or card.select_one(".company-industry")
        company_type = type_el.get_text(strip=True) if type_el else ""

        return {
            "job_title": job_title,
            "company": company,
            "location": location,
            "salary_raw": salary_raw,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_avg": salary_avg,
            "experience": experience,
            "education": education,
            "company_size": company_size,
            "company_type": company_type,
            "job_url": job_url,
        }

    def _parse_salary(self, salary_str):
        if not salary_str:
            return 0, 0, 0
        salary_str = salary_str.strip()
        pattern_k = re.compile(r'(\d+)[~-]?(\d+)\s*[Kk万]')
        pattern_yuan = re.compile(r'(\d+)[~-]?(\d+)\s*元')
        match = pattern_k.search(salary_str)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            if '万' in salary_str:
                low *= 10
                high *= 10
            months = 12
            month_match = re.search(r'·(\d+)薪', salary_str)
            if month_match:
                months = int(month_match.group(1))
            avg = (low + high) / 2 * months / 12
            return low, high, round(avg, 1)
        match = pattern_yuan.search(salary_str)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            avg = (low + high) / 2 / 1000
            return round(low / 1000, 1), round(high / 1000, 1), round(avg, 1)
        return 0, 0, 0
