import re
import logging

logger = logging.getLogger(__name__)


def parse_salary(salary_str):
    if not salary_str:
        return 0, 0, 0
    salary_str = salary_str.strip()

    pattern_k = re.compile(r'(\d+)[.\s]*[~-—]\s*(\d+)\s*[Kk万]')
    pattern_yuan = re.compile(r'(\d+)[.\s]*[~-—]\s*(\d+)\s*元[/每]?月?')

    match = pattern_k.search(salary_str)
    if match:
        low, high = int(match.group(1)), int(match.group(2))
        if '万' in salary_str:
            low *= 10
            high *= 10
        months = 12
        month_match = re.search(r'[·.]\s*(\d+)\s*薪', salary_str)
        if month_match:
            months = int(month_match.group(1))
        avg = round((low + high) / 2 * months / 12, 1)
        return low, high, avg

    match = pattern_yuan.search(salary_str)
    if match:
        low, high = int(match.group(1)), int(match.group(2))
        avg = round((low + high) / 2 / 1000, 1)
        return round(low / 1000, 1), round(high / 1000, 1), avg

    single_k = re.compile(r'(\d+)\s*[Kk万]')
    match = single_k.search(salary_str)
    if match:
        val = int(match.group(1))
        if '万' in salary_str:
            val *= 10
        return val, val, val

    return 0, 0, 0


def enrich_salary(jobs):
    for job in jobs:
        if job.get("salary_avg", 0) == 0:
            salary_raw = job.get("salary_raw", "")
            s_min, s_max, s_avg = parse_salary(salary_raw)
            job["salary_min"] = s_min
            job["salary_max"] = s_max
            job["salary_avg"] = s_avg
    return jobs
