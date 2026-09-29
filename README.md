# web-scraper-kit 通用爬虫工具包

开箱即用的爬虫脚手架：自动重试、礼貌限速、分页抓取、一键导出 JSON/CSV。

## 功能

- `PoliteScraper` 类：请求间隔随机化 + 失败自动重试，直接 import 复用
- 分页抓取：URL 模板里用 `{page}` 做页码占位符
- CSS 选择器提取标题 / 链接 / 正文
- 导出 JSON 或 CSV（CSV 带 BOM，Excel 直接打开不乱码）
- 相对链接自动转绝对地址

## 安装

```bash
pip install -r requirements.txt
```

## 用法

```bash
# 抓取单页
python scraper.py --url "https://example.com/news" --selector ".news-item" -o news.json

# 分页抓取 5 页
python scraper.py --url "https://example.com/list?page={page}" --pages 5 \
    --selector ".item" --title ".item h2" --link ".item a" -o out.csv

# 自定义请求间隔（秒）
python scraper.py --url "https://example.com/list" --delay 3
```

## 在代码中复用

```python
from scraper import PoliteScraper, extract_text, save

s = PoliteScraper(delay=(1, 3), retries=3)
soup = s.get("https://example.com/page")
titles = [extract_text(el, "h2") for el in soup.select(".item")]
save([{"title": t} for t in titles], "out.json")
```

## 爬虫礼仪

请遵守目标网站的 `robots.txt` 与服务条款，控制请求频率，不要给别人的服务器造成负担。

## License

MIT
