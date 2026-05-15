import logging

logger = logging.getLogger(__name__)


def deduplicate(jobs):
    seen = set()
    unique_jobs = []
    duplicates = 0
    for job in jobs:
        key = _make_dedup_key(job)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique_jobs.append(job)
    logger.info(f"去重: {len(jobs)} → {len(unique_jobs)} 条 (去除 {duplicates} 条重复)")
    return unique_jobs


def _make_dedup_key(job):
    title = job.get("job_title", "").lower().strip()
    company = job.get("company", "").lower().strip()
    location = job.get("location", "").lower().strip()
    salary = job.get("salary_raw", "").strip()
    return f"{title}|{company}|{location}|{salary}"
