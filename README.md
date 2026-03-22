# 韭研公社 每日舆情汇总

自动抓取 [韭研公社](https://www.jiuyangongshe.com) 的 A股/美股 相关文章，生成每日舆情日报。

## 功能

- 每天北京时间 **8:30** 自动运行（仅工作日）
- 抓取来源：首页、研究优选、热门、异动页面
- 自动分类：A股 / 美股
- 输出格式：Markdown + HTML 精美报告
- 自动部署到 GitHub Pages，在线查看

## 在线查看报告

部署成功后，访问 `https://Areak777.github.io/jiuyan-crawler/` 查看所有历史报告。

## 手动触发

在 GitHub 仓库页面，点击 **Actions** → **韭研公社每日舆情汇总** → **Run workflow** 即可手动运行。

## 免费额度

GitHub Actions 每月提供 **2000 分钟**免费运行时间。本脚本每次运行约 1-2 分钟，按工作日每天一次计算，每月约 100 分钟，完全够用。

## 技术栈

- Python 3.12
- requests + BeautifulSoup
- GitHub Actions
- GitHub Pages
