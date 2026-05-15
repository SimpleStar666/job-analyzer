import re
import logging
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class LagouScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.platform_name = "拉勾"
        self.base_url = "https://www.lagou.com"

    def search(self, keyword, city="", max_pages=5, progress_callback=None):
        jobs = []
        for page in range(1, max_pages + 1):
            if progress_callback:
                progress_callback(f"[拉勾] 正在爬取第 {page}/{max_pages} 页")
            url = f"{self.base_url}/jobs/list_{quote(keyword)}"
            params = {"page": page}
            html = self._fetch_page(url, params=params)
            if not html:
                logger.warning(f"[拉勾] 第{page}页请求失败，跳过")
                break
            page_jobs = self._parse_list_page(html)
            if not page_jobs:
                logger.info(f"[拉勾] 第{page}页无数据，停止翻页")
                break
            jobs.extend(page_jobs)
            logger.info(f"[拉勾] 第{page}页获取 {len(page_jobs)} 条岗位")
            if page < max_pages:
                self._random_delay()
        return [self._normalize_job(j) for j in jobs]

    def _parse_list_page(self, html):
        jobs = []
        try:
            soup = BeautifulSoup(html, "lxml")
            job_cards = soup.select(".item__10RTO") or soup.select(".s_position_list .item_con_list li")
            for card in job_cards:
                try:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"[拉勾] 解析单条岗位失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"[拉勾] 解析列表页失败: {e}")
        return jobs

    def _parse_job_card(self, card):
        title_el = card.select_one(".p_top__3Q3wE a") or card.select_one(".position_link") or card.select_one("a[class*='position']")
        if not title_el:
            return None
        job_title = title_el.get_text(strip=True)
        job_url = title_el.get("href", "")
        if job_url and not job_url.startswith("http"):
            job_url = urljoin(self.base_url, job_url)

        salary_el = card.select_one(".money__3Lkgq") or card.select_one(".salary") or card.select_one("[class*='money']")
        salary_raw = salary_el.get_text(strip=True) if salary_el else ""
        salary_min, salary_max, salary_avg = self._parse_salary(salary_raw)

        company_el = card.select_one(".company_name a") or card.select_one(".company__2EsC8 a") or card.select_one("[class*='company'] a")
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(".add") or card.select_one("[class*='address']")
        location = location_el.get_text(strip=True) if location_el else ""

        tag_els = card.select(".li_b_l") or card.select(".list_item_bot span")
        experience = tag_els[0].get_text(strip=True) if len(tag_els) > 0 else ""
        education = tag_els[1].get_text(strip=True) if len(tag_els) > 1 else ""

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
            "company_size": "",
            "company_type": "",
            "job_url": job_url,
        }

    def _parse_salary(self, salary_str):
        if not salary_str:
            return 0, 0, 0
        pattern = re.compile(r'(\d+)[~-]?(\d+)\s*[Kk万]')
        match = pattern.search(salary_str)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            if '万' in salary_str:
                low *= 10
                high *= 10
            return low, high, round((low + high) / 2, 1)
        return 0, 0, 0