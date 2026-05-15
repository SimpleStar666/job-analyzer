import random
import time
import logging
from abc import ABC, abstractmethod

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENTS, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    def __init__(self):
        self.session = self._create_session()
        self.platform_name = ""
        self.base_url = ""

    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self._random_headers())
        return session

    def _random_headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

    def _rotate_ua(self):
        self.session.headers.update({"User-Agent": random.choice(USER_AGENTS)})

    def _random_delay(self):
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        logger.info(f"[{self.platform_name}] 休眠 {delay:.1f}s 模拟人工操作...")
        time.sleep(delay)

    def _fetch_page(self, url, params=None, encoding=None):
        self._rotate_ua()
        try:
            logger.info(f"[{self.platform_name}] 正在请求: {url}")
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            if encoding:
                resp.encoding = encoding
            else:
                resp.encoding = resp.apparent_encoding
            return resp.text
        except requests.RequestException as e:
            logger.error(f"[{self.platform_name}] 请求失败: {e}")
            return None

    @abstractmethod
    def search(self, keyword, city="", max_pages=5, progress_callback=None):
        pass

    @abstractmethod
    def _parse_list_page(self, html):
        pass

    def _normalize_job(self, raw_job):
        return {
            "job_title": raw_job.get("job_title", "").strip(),
            "company": raw_job.get("company", "").strip(),
            "location": raw_job.get("location", "").strip(),
            "salary_raw": raw_job.get("salary_raw", "").strip(),
            "salary_min": raw_job.get("salary_min", 0),
            "salary_max": raw_job.get("salary_max", 0),
            "salary_avg": raw_job.get("salary_avg", 0),
            "experience": raw_job.get("experience", "").strip(),
            "education": raw_job.get("education", "").strip(),
            "company_size": raw_job.get("company_size", "").strip(),
            "company_type": raw_job.get("company_type", "").strip(),
            "platform": self.platform_name,
            "job_url": raw_job.get("job_url", ""),
        }
