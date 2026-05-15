import re
import logging
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class MaimaiScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.platform_name = "脉脉"
        self.base_url = "https://maimai.cn"

    def search(self, keyword, city="", max_pages=5, progress_callback=None):
        jobs = []
        for page in range(1, max_pages + 1):
            if progress_callback:
                progress_callback(f"[脉脉] 正在爬取第 {page}/{max_pages} 页")
            url = f"{self.base_url}/web/search/jobs"
            params = {"query": keyword, "page": page}
            html = self._fetch_page(url, params=params)
            if not html:
                logger.warning(f"[脉脉] 第{page}页请求失败，跳过")
                break
            page_jobs = self._parse_list_page(html)
            if not page_jobs:
                logger.info(f"[脉脉] 第{page}页无数据，停止翻页")
                break
            jobs.extend(page_jobs)
            logger.info(f"[脉脉] 第{page}页获取 {len(page_jobs)} 条岗位")
            if page < max_pages:
                self._random_delay()
        return [self._normalize_job(j) for j in jobs]

    def _parse_list_page(self, html):
        jobs = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            job_cards = soup.select(".search-job-list .job-item") or soup.select("[class*='job-card']")
            for card in job_cards:
                try:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"[脉脉] 解析单条岗位失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"[脉脉] 解析列表页失败: {e}")
        return jobs

    def _parse_job_card(self, card):
        title_el = card.select_one(".job-title a") or card.select_one("[class*='job-name'] a")
        if not title_el:
            return None
        job_title = title_el.get_text(strip=True)
        job_url = title_el.get("href", "")
        if job_url and not job_url.startswith("http"):
            job_url = urljoin(self.base_url, job_url)

        salary_el = card.select_one(".job-salary") or card.select_one("[class*='salary']")
        salary_raw = salary_el.get_text(strip=True) if salary_el else ""
        salary_min, salary_max, salary_avg = self._parse_salary(salary_raw)

        company_el = card.select_one(".company-name") or card.select_one("[class*='company']")
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(".job-area") or card.select_one("[class*='location']")
        location = location_el.get_text(strip=True) if location_el else ""

        tag_els = card.select(".job-tags span") or card.select("[class*='tag']")
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