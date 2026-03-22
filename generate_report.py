# -*- coding: utf-8 -*-
"""
韭研公社 A股/美股 每日舆情汇总报告生成器
适配 GitHub Actions 运行环境
支持 Markdown 和 HTML 两种格式
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger()


class ReportGenerator:
    """舆情汇总报告生成器"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def load_latest(self) -> List[Dict]:
        """加载最新数据"""
        if not os.path.exists(self.data_dir):
            return []
        files = sorted([f for f in os.listdir(self.data_dir)
                        if f.startswith("jiuyan_raw_") and f.endswith(".json")])
        if not files:
            return []
        with open(os.path.join(self.data_dir, files[-1]), "r", encoding="utf-8") as f:
            return json.load(f)

    def _top_keywords(self, articles: List[Dict], top_n: int = 15) -> list:
        """提取热门关键词"""
        kw_count = {}
        for a in articles:
            for kw in a.get("keywords", []):
                kw_count[kw] = kw_count.get(kw, 0) + 1
        return sorted(kw_count.items(), key=lambda x: -x[1])[:top_n]

    def generate_markdown(self, articles: List[Dict]) -> str:
        """生成 Markdown 报告"""
        now = datetime.now()
        today_str = now.strftime("%Y年%m月%d日")
        time_str = now.strftime("%H:%M")

        zh = [a for a in articles if a["type"] == "A股"]
        us = [a for a in articles if a["type"] == "美股"]
        all_kw = self._top_keywords(articles)

        lines = [
            f"# 韭研公社 每日舆情汇总",
            f"",
            f"> **{today_str} {time_str}** | 数据来源: 韭研公社 jiuyangongshe.com",
            f"",
            f"---",
            f"",
        ]

        if all_kw:
            lines.append(f"## 今日热词")
            lines.append(f"")
            kw_str = " | ".join([f"**{kw}**({cnt})" for kw, cnt in all_kw])
            lines.append(kw_str)
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")

        lines.append(f"## A股相关 ({len(zh)} 篇)")
        lines.append(f"")
        if zh:
            zh_kw = self._top_keywords(zh, 10)
            lines.append(f"### A股热词")
            for kw, cnt in zh_kw:
                bar = "█" * cnt
                lines.append(f"- {bar} **{kw}** ({cnt})")
            lines.append(f"")
            lines.append(f"### 文章详情")
            lines.append(f"")
            for i, a in enumerate(zh, 1):
                lines.append(f"**{i}. {a['title']}**")
                src = a.get("source", "")
                kws = ", ".join(a.get("keywords", []))
                lines.append(f"- 来源: {src} | 关键词: {kws}")
                lines.append(f"- [查看原文]({a['url']})")
                lines.append(f"")

        lines.append(f"---")
        lines.append(f"")
        lines.append(f"## 美股相关 ({len(us)} 篇)")
        lines.append(f"")
        if us:
            us_kw = self._top_keywords(us, 10)
            lines.append(f"### 美股热词")
            for kw, cnt in us_kw:
                bar = "█" * cnt
                lines.append(f"- {bar} **{kw}** ({cnt})")
            lines.append(f"")
            lines.append(f"### 文章详情")
            lines.append(f"")
            for i, a in enumerate(us, 1):
                lines.append(f"**{i}. {a['title']}**")
                src = a.get("source", "")
                kws = ", ".join(a.get("keywords", []))
                lines.append(f"- 来源: {src} | 关键词: {kws}")
                lines.append(f"- [查看原文]({a['url']})")
                lines.append(f"")

        lines.append(f"---")
        lines.append(f"")
        lines.append(f"*本报告由 GitHub Actions 自动生成，内容为系统自动筛选，仅供参考。*")

        return "\n".join(lines)

    def generate_html(self, articles: List[Dict]) -> str:
        """生成 HTML 报告"""
        now = datetime.now()
        today_str = now.strftime("%Y年%m月%d日")
        time_str = now.strftime("%H:%M")

        zh = [a for a in articles if a["type"] == "A股"]
        us = [a for a in articles if a["type"] == "美股"]
        all_kw = self._top_keywords(articles, 20)
        zh_kw = self._top_keywords(zh, 10)
        us_kw = self._top_keywords(us, 10)

        def esc(t):
            return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

        def render_articles(list_articles, color_accent):
            if not list_articles:
                return '<div class="empty">暂无相关内容</div>'
            h = ""
            for i, a in enumerate(list_articles, 1):
                kw_tags = "".join([f'<span class="kw">{esc(kw)}</span>' for kw in a.get("keywords",[])[:4]])
                h += f"""<div class="card">
                    <div class="card-num">{i}</div>
                    <div class="card-body">
                        <h3>{esc(a['title'])}</h3>
                        <div class="card-meta"><span class="src">{esc(a.get('source',''))}</span>{kw_tags}</div>
                        <a href="{a['url']}" target="_blank" class="card-link">查看原文 &rarr;</a>
                    </div></div>"""
            return h

        def render_tags(kw_list):
            if not kw_list:
                return ""
            mx = kw_list[0][1] if kw_list else 1
            return "\n".join([f'<span class="tag" style="font-size:{max(0.8,c/mx*1.6)}rem">{esc(k)}<sup>{c}</sup></span>' for k,c in kw_list])

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>韭研公社 舆情日报 {today_str}</title>
<style>
:root {{ --red:#e74c3c;--red-bg:#fff5f5;--blue:#2980b9;--blue-bg:#f0f8ff;--bg:#f5f6fa;--card:#fff;--text:#2c3e50;--text2:#7f8c8d;--border:#e8e8e8;--radius:12px; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
.container {{ max-width:960px; margin:0 auto; padding:20px 16px; }}
.header {{ background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%); color:#fff; border-radius:var(--radius); padding:32px 28px; margin-bottom:24px; text-align:center; }}
.header h1 {{ font-size:26px; margin-bottom:6px; font-weight:700; }}
.header .sub {{ font-size:14px; opacity:.7; }}
.stats {{ display:flex; justify-content:center; gap:24px; margin-top:20px; }}
.stat {{ padding:12px 28px; border-radius:10px; text-align:center; min-width:120px; }}
.stat.zh {{ background:rgba(231,76,60,.2); border:1px solid rgba(231,76,60,.3); }}
.stat.us {{ background:rgba(41,128,185,.2); border:1px solid rgba(41,128,185,.3); }}
.stat .num {{ font-size:28px; font-weight:800; }}
.stat .num.zh {{ color:#ff6b6b; }}
.stat .num.us {{ color:#74b9ff; }}
.stat .label {{ font-size:13px; opacity:.8; margin-top:2px; }}
.tag-cloud {{ background:var(--card); border-radius:var(--radius); padding:20px 24px; margin-bottom:24px; border:1px solid var(--border); }}
.tag-cloud h2 {{ font-size:16px; margin-bottom:12px; color:var(--text2); }}
.tag {{ display:inline-block; background:#f0f0f0; padding:4px 10px; margin:3px; border-radius:6px; color:var(--text); font-weight:500; }}
.tag sup {{ font-size:10px; color:var(--text2); margin-left:2px; }}
.section {{ background:var(--card); border-radius:var(--radius); padding:24px; margin-bottom:24px; border:1px solid var(--border); }}
.section-title {{ font-size:20px; font-weight:700; margin-bottom:16px; padding-bottom:12px; border-bottom:2px solid var(--border); display:flex; align-items:center; gap:10px; }}
.section-title .icon {{ font-size:24px; }}
.section-title .count {{ font-size:13px; background:#f0f0f0; padding:2px 10px; border-radius:12px; font-weight:400; color:var(--text2); }}
.card {{ display:flex; gap:14px; padding:16px; margin-bottom:12px; border-radius:10px; transition:all .2s; border:1px solid transparent; }}
.card:hover {{ background:#fafafa; border-color:var(--border); transform:translateX(3px); }}
.card-num {{ flex-shrink:0; width:28px; height:28px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; color:#fff; margin-top:2px; }}
.zh .card-num {{ background:var(--red); }}
.us .card-num {{ background:var(--blue); }}
.card-body {{ flex:1; min-width:0; }}
.card-body h3 {{ font-size:15px; font-weight:600; margin-bottom:6px; line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.card-meta {{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; margin-bottom:6px; }}
.src {{ font-size:12px; color:var(--text2); background:#f0f0f0; padding:1px 8px; border-radius:4px; }}
.kw {{ font-size:11px; color:var(--blue); background:var(--blue-bg); padding:1px 6px; border-radius:4px; }}
.zh .kw {{ color:var(--red); background:var(--red-bg); }}
.card-link {{ font-size:13px; color:var(--text2); text-decoration:none; }}
.card-link:hover {{ color:var(--blue); text-decoration:underline; }}
.empty {{ text-align:center; color:var(--text2); padding:40px; font-size:15px; }}
.footer {{ text-align:center; color:var(--text2); font-size:12px; padding:16px; }}
@media(max-width:640px) {{ .container {{ padding:12px; }} .header {{ padding:24px 16px; }} .header h1 {{ font-size:20px; }} .stats {{ flex-direction:column; gap:12px; align-items:center; }} .section {{ padding:16px; }} .card {{ padding:12px; }} }}
</style>
</head>
<body>
<div class="container">
<div class="header">
    <h1>韭研公社 每日舆情汇总</h1>
    <p class="sub">{today_str} {time_str} | jiuyangongshe.com</p>
    <div class="stats">
        <div class="stat zh"><div class="num zh">{len(zh)}</div><div class="label">A股相关</div></div>
        <div class="stat us"><div class="num us">{len(us)}</div><div class="label">美股相关</div></div>
    </div>
</div>
{f'<div class="tag-cloud"><h2>今日热词</h2>{render_tags(all_kw)}</div>' if all_kw else ''}
<div class="section zh">
    <div class="section-title"><span class="icon">📈</span> A股相关 <span class="count">{len(zh)} 篇</span></div>
    {f'<div class="tag-cloud" style="margin-bottom:16px"><h2>A股热词</h2>{render_tags(zh_kw)}</div>' if zh_kw else ''}
    {render_articles(zh, 'zh')}
</div>
<div class="section us">
    <div class="section-title"><span class="icon">🌎</span> 美股相关 <span class="count">{len(us)} 篇</span></div>
    {f'<div class="tag-cloud" style="margin-bottom:16px"><h2>美股热词</h2>{render_tags(us_kw)}</div>' if us_kw else ''}
    {render_articles(us, 'us')}
</div>
<div class="footer">由 GitHub Actions 自动生成 | 内容仅供参考，不构成投资建议</div>
</div>
</body>
</html>"""
        return html

    def generate(self, articles: List[Dict]):
        """生成所有报告"""
        if not articles:
            logger.warning("没有数据可生成报告")
            return None, None
        today = datetime.now().strftime("%Y%m%d")
        os.makedirs(self.data_dir, exist_ok=True)
        md = self.generate_markdown(articles)
        md_path = os.path.join(self.data_dir, f"舆情日报_{today}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        logger.info(f"Markdown 报告: {md_path}")
        html = self.generate_html(articles)
        html_path = os.path.join(self.data_dir, f"舆情日报_{today}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"HTML 报告: {html_path}")
        return md_path, html_path
