import re
import logging

logger = logging.getLogger(__name__)


def clean_jobs(jobs):
    cleaned = []
    for job in jobs:
        cleaned_job = {}
        for key, value in job.items():
            if isinstance(value, str):
                value = _clean_text(value)
            cleaned_job[key] = value
        if cleaned_job.get("job_title") and cleaned_job.get("company"):
            cleaned.append(cleaned_job)
    logger.info(f"数据清洗: {len(jobs)} → {len(cleaned)} 条")
    return cleaned


def _clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    text = text.replace('\xa0', ' ').replace('\u3000', ' ')
    text = text.replace('\r', '').replace('\n', '')
    return text
