import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRAPERS = {
    "boss": {
        "name": "Boss直聘",
        "base_url": "https://www.zhipin.com",
        "enabled": True,
    },
    "zhilian": {
        "name": "智联招聘",
        "base_url": "https://www.zhaopin.com",
        "enabled": True,
    },
    "liepin": {
        "name": "猎聘",
        "base_url": "https://www.liepin.com",
        "enabled": True,
    },
    "job51": {
        "name": "前程无忧",
        "base_url": "https://www.51job.com",
        "enabled": True,
    },
    "lagou": {
        "name": "拉勾",
        "base_url": "https://www.lagou.com",
        "enabled": True,
    },
    "maimai": {
        "name": "脉脉",
        "base_url": "https://maimai.cn",
        "enabled": True,
    },
}

REQUEST_DELAY_MIN = 2
REQUEST_DELAY_MAX = 5
MAX_PAGES = 5
PAGE_SIZE = 30

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]

CITY_COST_INDEX = {
    "北京": 1.0,
    "上海": 0.95,
    "深圳": 0.90,
    "广州": 0.75,
    "杭州": 0.80,
    "成都": 0.55,
    "武汉": 0.50,
    "南京": 0.65,
    "苏州": 0.65,
    "西安": 0.45,
    "长沙": 0.45,
    "重庆": 0.48,
    "天津": 0.60,
    "郑州": 0.42,
    "东莞": 0.58,
    "沈阳": 0.42,
    "青岛": 0.52,
    "合肥": 0.48,
    "佛山": 0.55,
    "昆明": 0.40,
    "大连": 0.50,
    "厦门": 0.62,
    "福州": 0.55,
    "哈尔滨": 0.38,
    "济南": 0.48,
    "温州": 0.55,
    "南宁": 0.40,
    "长春": 0.38,
    "石家庄": 0.40,
    "贵阳": 0.38,
    "珠海": 0.65,
    "无锡": 0.60,
    "常州": 0.52,
    "惠州": 0.50,
}

OUTPUT_DIR = os.path.join(BASE_DIR, "output")

DEMO_DATA_FILE = os.path.join(BASE_DIR, "demo_data.json")

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True
