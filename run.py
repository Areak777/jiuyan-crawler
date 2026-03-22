# -*- coding: utf-8 -*-
"""
韭研公社 每日舆情抓取 - 主运行脚本
适配 GitHub Actions 环境，串联执行爬取 + 报告生成 + 邮件推送
"""

import os
import json
import logging
from datetime import datetime
from jiuyangongshe_crawler import JiuyanCrawler
from generate_report import ReportGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger()


def send_email(to_email: str, subject: str, html_content: str):
    """通过 Resend API 发送邮件"""
    import requests

    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        logger.warning("未设置 RESEND_API_KEY，跳过邮件发送")
        return

    # Resend 免费版需要先验证发件域名
    # 使用 onboarding 域名发送
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "from": "Jiuyan Report <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        },
        timeout=30,
    )

    if resp.status_code == 200:
        logger.info("邮件发送成功!")
    else:
        logger.error(f"邮件发送失败: {resp.status_code} {resp.text}")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("韭研公社 每日舆情汇总")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 数据目录（GitHub Actions 使用相对路径）
    data_dir = os.environ.get("DATA_DIR", "data")
    os.makedirs(data_dir, exist_ok=True)

    # 第一步：抓取数据
    logger.info("[1/3] 正在抓取韭研公社数据...")
    try:
        crawler = JiuyanCrawler()
        articles = crawler.crawl_all()
        logger.info(f"抓取完成，共 {len(articles)} 篇文章")

        # 保存原始数据
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_file = os.path.join(data_dir, f"jiuyan_raw_{ts}.json")
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"原始数据已保存: {raw_file}")
    except Exception as e:
        logger.error(f"抓取失败: {e}")
        raise

    # 第二步：生成报告
    logger.info("[2/3] 正在生成汇总报告...")
    try:
        gen = ReportGenerator(data_dir)
        md_path, html_path = gen.generate(articles)
        if md_path and html_path:
            logger.info(f"报告生成完成!")
    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        raise

    # 第三步：发送邮件
    logger.info("[3/3] 正在发送邮件推送...")
    try:
        to_email = os.environ.get("EMAIL_TO", "")
        if to_email:
            today_str = datetime.now().strftime("%Y年%m月%d日")
            email_html = gen.generate_email_html(articles)
            send_email(
                to_email=to_email,
                subject=f"韭研公社舆情日报 {today_str}",
                html_content=email_html,
            )
        else:
            logger.warning("未设置 EMAIL_TO，跳过邮件发送")
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        # 邮件失败不影响整体任务

    logger.info("=" * 60)
    logger.info("任务完成!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
