# JobAnalyzer - 多平台岗位情况分析工具

[![Release](https://img.shields.io/github/v/release/SimpleStar666/job-analyzer)](https://github.com/SimpleStar666/job-analyzer/releases)
[![License](https://img.shields.io/github/license/SimpleStar666/job-analyzer)](https://github.com/SimpleStar666/job-analyzer/blob/main/LICENSE)

多平台岗位情况分析工具 - 支持6大招聘平台数据采集、智能分析、可视化对比

## 🎯 功能特性

- **多平台支持**: Boss直聘、智联招聘、猎聘、前程无忧、拉勾、脉脉
- **反爬策略**: UA轮换、随机休眠、浏览器请求头伪装
- **智能分析**: 数据清洗去重、薪资标准化解析、性价比评分算法
- **可视化**: ECharts图表（薪资分布、城市分布、经验要求、行业分布、横向对比）
- **筛选功能**: 学历、薪资、经验多维度筛选
- **导出功能**: CSV、JSON、HTML报告导出
- **实时进度**: SSE实时进度推送（进度条+百分比+日志）

## 🚀 快速开始

### 方式一：一键安装

**Windows**: 下载 [install.bat](https://github.com/SimpleStar666/job-analyzer/releases/download/v1.0.0/install.bat) 双击运行

**Mac/Linux**:
```bash
curl -sSL https://github.com/SimpleStar666/job-analyzer/releases/download/v1.0.0/install.sh | bash
```

### 方式二：手动安装

```bash
# 克隆仓库
git clone https://github.com/SimpleStar666/job-analyzer.git
cd job-analyzer

# 安装依赖
pip install -r requirements.txt

# 运行演示
python cli.py demo

# 启动Web服务
python web/app.py
```

## 🖥️ CLI 使用

```bash
# 演示模式
python cli.py demo Python

# 搜索岗位
python cli.py search 前端 --city 北京

# 搜索并导出
python cli.py search Java --export

# 真实爬虫模式（较慢）
python cli.py search Python --live
```

## 🌐 Web 界面

启动服务后访问 http://localhost:5000

### 功能说明

1. **搜索面板**: 输入关键词、城市筛选、平台选择
2. **筛选条件**: 学历、薪资、经验多维度筛选
3. **实时进度**: 显示采集进度和日志
4. **可视化图表**: 薪资分布、城市分布、经验要求、行业分布、横向对比
5. **岗位列表**: 展示岗位详情、链接、性价比评分

## 📁 项目结构

```
job-analyzer/
├── cli.py              # 命令行工具
├── web/app.py          # Web服务
├── requirements.txt    # 依赖列表
├── demo_data.json      # 演示数据
├── scrapers/           # 爬虫模块
│   ├── base.py         # 爬虫基类
│   ├── boss.py         # Boss直聘
│   ├── zhilian.py      # 智联招聘
│   ├── liepin.py       # 猎聘
│   ├── job51.py        # 前程无忧
│   ├── lagou.py        # 拉勾
│   ├── maimai.py       # 脉脉
│   └── mock.py         # 模拟数据
├── processor/          # 数据处理
│   ├── cleaner.py      # 数据清洗
│   ├── deduplicator.py # 去重
│   ├── salary_parser.py # 薪资解析
│   └── analyzer.py     # 分析引擎
└── exporter/           # 数据导出
    └── exporter.py     # CSV/JSON/HTML导出
```

## 📱 手机访问

### 同一局域网

1. 电脑启动服务: `python web/app.py`
2. 查看电脑IP: `ifconfig` (Mac/Linux) 或 `ipconfig` (Windows)
3. 手机连接同一WiFi，访问: `http://电脑IP:5000`

### 内网穿透

```bash
# 使用 ngrok
ngrok http 5000
# 手机访问 ngrok 提供的 https 地址
```

## 📦 下载

- **Release**: https://github.com/SimpleStar666/job-analyzer/releases
- **源码包**: https://github.com/SimpleStar666/job-analyzer/archive/refs/tags/v1.0.0.zip

## 📝 License

MIT License
