# -*- coding: utf-8 -*-
"""
韭研公社 每日舆情抓取 - 主运行脚本
适配 GitHub Actions 环境，串联执行爬取 + 报告生成
"""

import os
import json
import logging
from datetime import datetime
from jiuyangongshe_crawler import JiuyanCrawler
from generate_report import ReportGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger()


def main():
    logger.info("=" * 60)
    logger.info("韭研公社 每日舆情汇总")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    data_dir = os.environ.get("DATA_DIR", "data")
    os.makedirs(data_dir, exist_ok=True)

    logger.info("[1/2] 正在抓取韭研公社数据...")
    try:
        crawler = JiuyanCrawler()
        articles = crawler.crawl_all()
        logger.info(f"抓取完成，共 {len(articles)} 篇文章")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_file = os.path.join(data_dir, f"jiuyan_raw_{ts}.json")
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"原始数据已保存: {raw_file}")
    except Exception as e:
        logger.error(f"抓取失败: {e}")
        raise

    logger.info("[2/2] 正在生成汇总报告...")
    try:
        gen = ReportGenerator(data_dir)
        md_path, html_path = gen.generate(articles)
        if md_path and html_path:
            logger.info(f"报告生成完成!")
    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        raise

    logger.info("=" * 60)
    logger.info("任务完成!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
