import re
import logging
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class ZhilianScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.platform_name = "智联招聘"
        self.base_url = "https://www.zhaopin.com"

    def search(self, keyword, city="", max_pages=5, progress_callback=None):
        jobs = []
        city_code = self._get_city_code(city)
        for page in range(1, max_pages + 1):
            if progress_callback:
                progress_callback(f"[智联招聘] 正在爬取第 {page}/{max_pages} 页")
            url = f"{self.base_url}/sou/j{city_code}-{quote(keyword)}/{page}.html"
            html = self._fetch_page(url)
            if not html:
                logger.warning(f"[智联招聘] 第{page}页请求失败，跳过")
                break
            page_jobs = self._parse_list_page(html)
            if not page_jobs:
                logger.info(f"[智联招聘] 第{page}页无数据，停止翻页")
                break
            jobs.extend(page_jobs)
            logger.info(f"[智联招聘] 第{page}页获取 {len(page_jobs)} 条岗位")
            if page < max_pages:
                self._random_delay()
        return [self._normalize_job(j) for j in jobs]

    def _get_city_code(self, city):
        city_map = {
            "北京": "530", "上海": "538", "广州": "763", "深圳": "765",
            "杭州": "653", "成都": "801", "武汉": "736", "南京": "635",
            "苏州": "636", "西安": "854", "长沙": "749", "重庆": "854",
            "天津": "531", "郑州": "719", "东莞": "767",
        }
        return city_map.get(city, "530")

    def _parse_list_page(self, html):
        jobs = []
        try:
            soup = BeautifulSoup(html, "lxml")
            job_cards = soup.select(".joblist-box .joblist-box__item")
            if not job_cards:
                job_cards = soup.select(".soup .positionlist .iteminfo__top")
            if not job_cards:
                job_cards = soup.select("[class*='job-item']")
            for card in job_cards:
                try:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"[智联招聘] 解析单条岗位失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"[智联招聘] 解析列表页失败: {e}")
        return jobs

    def _parse_job_card(self, card):
        title_el = card.select_one(".iteminfo__line1__jobname a") or card.select_one(".job__title a") or card.select_one("a[class*='job-name']")
        if not title_el:
            return None
        job_title = title_el.get_text(strip=True)
        job_url = title_el.get("href", "")
        if job_url and not job_url.startswith("http"):
            job_url = urljoin(self.base_url, job_url)

        salary_el = card.select_one(".iteminfo__line1__jobname .job__money") or card.select_one(".job__salary") or card.select_one("[class*='salary']")
        salary_raw = salary_el.get_text(strip=True) if salary_el else ""
        salary_min, salary_max, salary_avg = self._parse_salary(salary_raw)

        company_el = card.select_one(".iteminfo__line1__companyname a") or card.select_one(".company__title a") or card.select_one("[class*='company-name'] a")
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(".iteminfo__line2__jobdesc .job__area") or card.select_one(".job__area") or card.select_one("[class*='area']")
        location = location_el.get_text(strip=True) if location_el else ""

        tag_els = card.select(".iteminfo__line2__jobdesc .job__demand span") or card.select(".job__detail span")
        experience = tag_els[0].get_text(strip=True) if len(tag_els) > 0 else ""
        education = tag_els[1].get_text(strip=True) if len(tag_els) > 1 else ""

        size_el = card.select_one(".iteminfo__line2__companydesc .company__tag") or card.select_one(".company__tag")
        company_size = size_el.get_text(strip=True) if size_el else ""

        type_el = card.select_one(".iteminfo__line2__companydesc .company__industry") or card.select_one(".company__industry")
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
