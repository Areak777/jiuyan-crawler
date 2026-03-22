# Setup Instructions

## GitHub Actions 工作流文件

请手动完成以下步骤：

1. 打开 https://github.com/Areak777/jiuyan-crawler
2. 点击 Add file -> Create new file
3. 文件名输入: `.github/workflows/jiuyan-crawler.yml`
4. 粘贴以下内容:

```yaml
name: 韭研公社每日舆情汇总

# 每天北京时间 8:30 自动运行（仅工作日）
on:
  schedule:
    # UTC 0:30 = 北京时间 8:30
    # cron 时区为 UTC，周一到周五
    - cron: '30 0 * * 1-5'
  # 支持手动触发
  workflow_dispatch:

jobs:
  crawl:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      # 1. 检出代码
      - name: 检出代码
        uses: actions/checkout@v4

      # 2. 设置 Python 环境
      - name: 设置 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # 3. 安装依赖
      - name: 安装依赖
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      # 4. 运行爬虫 + 生成报告
      - name: 运行抓取
        run: python run.py

      # 5. 上传报告为 Artifact（保留 30 天）
      - name: 上传报告
        uses: actions/upload-artifact@v4
        with:
          name: 舆情日报_${{ github.run_number }}
          path: data/
          retention-days: 30

      # 6. 将 HTML 报告部署到 GitHub Pages
      - name: 部署到 GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./data
          destination_dir: ./reports
          keep_files: true

```

5. 点击 Commit changes

完成后，Actions 就会自动运行了。
