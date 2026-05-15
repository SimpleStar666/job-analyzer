import logging
from collections import Counter

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CITY_COST_INDEX

logger = logging.getLogger(__name__)


def analyze(jobs):
    if not jobs:
        return {
            "jobs": [],
            "summary": {},
            "salary_distribution": [],
            "location_distribution": [],
            "experience_distribution": [],
            "platform_distribution": [],
            "company_type_distribution": [],
        }

    jobs_sorted = sorted(jobs, key=lambda j: j.get("salary_avg", 0))
    jobs_with_score = _add_value_score(jobs_sorted)
    summary = _generate_summary(jobs_with_score)
    salary_dist = _salary_distribution(jobs_with_score)
    location_dist = _location_distribution(jobs_with_score)
    experience_dist = _experience_distribution(jobs_with_score)
    platform_dist = _platform_distribution(jobs_with_score)
    company_type_dist = _company_type_distribution(jobs_with_score)

    return {
        "jobs": jobs_with_score,
        "summary": summary,
        "salary_distribution": salary_dist,
        "location_distribution": location_dist,
        "experience_distribution": experience_dist,
        "platform_distribution": platform_dist,
        "company_type_distribution": company_type_dist,
    }


def _add_value_score(jobs):
    for job in jobs:
        score = _calc_value_score(job)
        job["value_score"] = score
        job["recommendation"] = ""
        if score >= 80:
            job["recommendation"] = "⭐ 高性价比"
        elif score >= 60:
            job["recommendation"] = "👍 性价比不错"
        elif score <= 30:
            job["recommendation"] = "⚠️ 性价比偏低"
    return jobs


def _calc_value_score(job):
    salary_avg = job.get("salary_avg", 0)
    if salary_avg <= 0:
        return 0

    salary_score = _salary_score(salary_avg, job)

    location = job.get("location", "")
    cost_index = CITY_COST_INDEX.get(location, 0.5)
    adjusted_salary = salary_avg / cost_index
    cost_score = min(adjusted_salary / 60 * 40, 40)

    size_score = _size_score(job.get("company_size", ""))

    total = salary_score + cost_score + size_score
    return round(min(total, 100), 1)


def _salary_score(salary_avg, job):
    exp = job.get("experience", "")
    exp_multipliers = {
        "应届生": 1.5,
        "1年以下": 1.3,
        "1-3年": 1.0,
        "3-5年": 0.85,
        "5-10年": 0.7,
        "10年以上": 0.6,
        "不限": 1.0,
    }
    multiplier = exp_multipliers.get(exp, 1.0)
    adjusted = salary_avg * multiplier
    return min(adjusted / 50 * 40, 40)


def _size_score(size_str):
    if not size_str:
        return 10
    if "10000" in size_str:
        return 20
    if "5000" in size_str:
        return 18
    if "1000" in size_str:
        return 15
    if "500" in size_str:
        return 12
    if "100" in size_str:
        return 10
    if "50" in size_str:
        return 8
    return 10


def _generate_summary(jobs):
    salaries = [j.get("salary_avg", 0) for j in jobs if j.get("salary_avg", 0) > 0]
    if not salaries:
        return {}
    return {
        "total_jobs": len(jobs),
        "salary_min": min(salaries),
        "salary_max": max(salaries),
        "salary_avg": round(sum(salaries) / len(salaries), 1),
        "salary_median": _median(salaries),
        "top_cities": _top_n(jobs, "location", 5),
        "top_experience": _top_n(jobs, "experience", 3),
        "top_education": _top_n(jobs, "education", 3),
    }


def _median(lst):
    s = sorted(lst)
    n = len(s)
    if n % 2 == 0:
        return round((s[n // 2 - 1] + s[n // 2]) / 2, 1)
    return round(s[n // 2], 1)


def _top_n(jobs, key, n):
    counter = Counter(j.get(key, "未知") for j in jobs)
    return counter.most_common(n)


def _salary_distribution(jobs):
    ranges = [
        ("0-10K", 0, 10),
        ("10-15K", 10, 15),
        ("15-20K", 15, 20),
        ("20-25K", 20, 25),
        ("25-30K", 25, 30),
        ("30-40K", 30, 40),
        ("40-50K", 40, 50),
        ("50K+", 50, 999),
    ]
    result = []
    for label, low, high in ranges:
        count = sum(1 for j in jobs if low <= j.get("salary_avg", 0) < high)
        result.append({"range": label, "count": count})
    return result


def _location_distribution(jobs):
    counter = Counter(j.get("location", "未知") for j in jobs)
    return [{"city": k, "count": v} for k, v in counter.most_common(15)]


def _experience_distribution(jobs):
    counter = Counter(j.get("experience", "未知") for j in jobs)
    return [{"experience": k, "count": v} for k, v in counter.most_common()]


def _platform_distribution(jobs):
    counter = Counter(j.get("platform", "未知") for j in jobs)
    return [{"platform": k, "count": v} for k, v in counter.most_common()]


def _company_type_distribution(jobs):
    counter = Counter(j.get("company_type", "未知") for j in jobs)
    return [{"type": k, "count": v} for k, v in counter.most_common(10)]
