# -*- coding: utf-8 -*-
"""
韭研公社 A股/美股 舆情爬虫 v3 - 多策略综合版
适配 GitHub Actions 运行环境

策略1: HTML直接解析（首页/研究优选/热门）
策略2: SSR数据提取（异动页面）
策略3: DuckDuckGo搜索补充（site:jiuyangongshe.com）
"""

import requests
import re
import json
import os
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger()

# ============================================================
# 配置
# ============================================================
BASE_URL = "https://www.jiuyangongshe.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# A股关键词
KEYWORDS_A = [
    "A股", "上证", "深证", "创业板", "科创板", "北交所", "沪指", "深指",
    "涨停", "跌停", "大盘", "指数", "蓝筹", "龙头", "央行", "证监会",
    "IPO", "注册制", "新能源", "半导体", "医药", "白酒", "银行", "券商",
    "基金", "外资", "北向", "龙虎榜", "主力", "游资", "机构",
    "行情", "收盘", "开盘", "牛股", "板块", "题材", "概念",
    "政策", "利好", "利空", "回购", "并购", "重组", "增发",
    "算力", "AI", "芯片", "光模块", "光通信", "氢能", "光伏",
    "机器人", "低空经济", "碳纤维", "储能", "充电桩", "锂电",
    "华为", "小米", "比亚迪", "宁德时代", "中芯国际",
]

# 美股关键词
KEYWORDS_US = [
    "美股", "纳斯达克", "道琼斯", "标普", "S&P", "NYSE",
    "苹果", "微软", "谷歌", "亚马逊", "特斯拉", "Meta",
    "英伟达", "AMD", "Intel", "美联储", "Fed", "鲍威尔",
    "CPI", "非农", "加息", "降息", "华尔街", "中概股",
    "财报", "季报", "科技股", "FAANG", "ChatGPT", "马斯克",
    "通胀", "失业率", "GDP", "SpaceX", "OpenAI", "TSLA",
    "半导体", "芯片", "AI", "算力",
]

# 排除关键词
EXCLUDE_KW = ["广告", "推广", "合作", "代写"]


class JiuyanCrawler:
    """韭研公社舆情爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.seen_urls: Set[str] = set()
        self.all_articles: List[Dict] = []

    def _delay(self):
        time.sleep(random.uniform(0.3, 0.8))

    def _classify(self, text: str) -> Optional[str]:
        """判断文本属于 A股/美股/None"""
        text_lower = text.lower()
        for kw in EXCLUDE_KW:
            if kw in text_lower:
                return None
        a_score = sum(1 for kw in KEYWORDS_A if kw in text)
        us_score = sum(1 for kw in KEYWORDS_US if kw in text)
        if a_score > 0 and a_score >= us_score:
            return "A股"
        elif us_score > 0:
            return "美股"
        return None

    def _add_article(self, title: str, url: str, source: str, content: str = ""):
        """添加文章（自动去重和分类）"""
        if url in self.seen_urls:
            return
        if not title or len(title) < 8:
            return

        stock_type = self._classify(title + " " + content)
        if not stock_type:
            return

        self.seen_urls.add(url)
        self.all_articles.append({
            "title": title.strip(),
            "url": url,
            "type": stock_type,
            "source": source,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "keywords": [kw for kw in (KEYWORDS_A if stock_type == "A股" else KEYWORDS_US) if kw in title + content][:5],
        })

    # --------------------------------------------------------
    # 策略1: HTML正则提取（首页/研究优选/热门）
    # --------------------------------------------------------
    def crawl_html_pages(self):
        """从可直接解析的页面提取文章"""
        pages = [
            (BASE_URL, "首页"),
            (f"{BASE_URL}/study_publish", "研究优选"),
            (f"{BASE_URL}/hot", "热门"),
        ]
        for url, name in pages:
            logger.info(f"[策略1] 抓取 {name}: {url}")
            try:
                self._delay()
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
                resp.encoding = 'utf-8'

                pattern = r'<a[^>]+href="(/a/[^"]+)"[^>]*>([^<]{8,})</a>'
                matches = re.findall(pattern, resp.text)

                count = 0
                for href, title in matches:
                    title = title.strip()
                    self._add_article(title, BASE_URL + href, name)
                    count += 1
                logger.info(f"  找到 {len(matches)} 个链接, 匹配 {count} 篇相关文章")

            except Exception as e:
                logger.error(f"  失败: {e}")

    # --------------------------------------------------------
    # 策略2: 异动页面SSR数据提取
    # --------------------------------------------------------
    def crawl_action_page(self):
        """从异动页面提取（SSR渲染）"""
        logger.info(f"[策略2] 抓取 异动页面")
        try:
            self._delay()
            resp = self.session.get(f"{BASE_URL}/action", timeout=15)
            resp.raise_for_status()
            resp.encoding = 'utf-8'

            links = re.findall(r'href="(/a/[^"]+)"', resp.text)
            logger.info(f"  异动页面找到 {len(links)} 个链接")

            for link in links:
                pattern = rf'([^<]{{10,80}})</a[^>]*href="{re.escape(link)}"'
                pattern2 = rf'href="{re.escape(link)}"[^>]*>[^<]*<[^>]*>([^<]{{10,100}})'

                match = re.search(pattern, resp.text)
                match2 = re.search(pattern2, resp.text)
                title = ""
                if match:
                    title = match.group(1).strip()
                elif match2:
                    title = match2.group(1).strip()

                self._add_article(title or f"异动分析-{link.split('/')[-1]}", BASE_URL + link, "异动")

            if BeautifulSoup:
                soup = BeautifulSoup(resp.text, 'html.parser')
                items = soup.select('.item-content')
                if items:
                    logger.info(f"  通过BS4找到 {len(items)} 个item-content")
                    for item in items:
                        a_tag = item.find('a', href=re.compile(r'/a/'))
                        if a_tag:
                            text = item.get_text(separator=' ', strip=True)[:200]
                            href = a_tag.get('href', '')
                            if href.startswith('/a/'):
                                self._add_article(text, BASE_URL + href, "异动")

        except Exception as e:
            logger.error(f"  异动页面失败: {e}")

    # --------------------------------------------------------
    # 策略3: DuckDuckGo 搜索补充
    # --------------------------------------------------------
    def crawl_duckduckgo(self):
        """通过 DuckDuckGo 搜索补充韭研公社最新内容"""
        logger.info(f"[策略3] DuckDuckGo 搜索补充")
        try:
            from ddgs import DDGS

            month_str = datetime.now().strftime('%Y-%m')
            queries = [
                f"jiuyangongshe.com stock market China A-share {month_str}",
                f"jiuyangongshe.com US stock Tesla Nvidia {month_str}",
                f"jiuyangongshe.com AI chip semiconductor",
                f"jiuyangongshe.com IPO policy central bank",
            ]

            count = 0
            ddgs = DDGS()
            for query in queries:
                try:
                    self._delay()
                    results = ddgs.text(query, max_results=10)
                    for r in results:
                        title = r.get("title", "")
                        href = r.get("href", "")
                        body = r.get("body", "")
                        if "jiuyangongshe" in href:
                            self._add_article(title, href, "DuckDuckGo", body)
                            count += 1
                except Exception as e:
                    logger.error(f"  搜索失败: {e}")
                    continue

            logger.info(f"  DuckDuckGo 补充 {count} 篇文章")

        except ImportError:
            logger.warning("  ddgs 未安装，跳过此策略")
        except Exception as e:
            logger.error(f"  DuckDuckGo 失败: {e}")

    # --------------------------------------------------------
    # 主入口
    # --------------------------------------------------------
    def crawl_all(self) -> List[Dict]:
        """执行全部抓取策略"""
        logger.info("=" * 60)
        logger.info(f"韭研公社舆情抓取 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        self.crawl_html_pages()
        self.crawl_action_page()
        self.crawl_duckduckgo()

        zh = [a for a in self.all_articles if a["type"] == "A股"]
        us = [a for a in self.all_articles if a["type"] == "美股"]

        logger.info(f"{'=' * 60}")
        logger.info(f"抓取完成！共 {len(self.all_articles)} 篇")
        logger.info(f"  A股: {len(zh)} 篇")
        logger.info(f"  美股: {len(us)} 篇")
        logger.info(f"{'=' * 60}")

        return self.all_articles
