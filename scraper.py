#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用爬虫工具包 web-scraper-kit

开箱即用的爬虫脚手架：自动重试、请求间隔、分页抓取、导出 CSV/JSON。

用法：
    python scraper.py --url "https://example.com/page={page}" --pages 5 -o data.json
    python scraper.py --url "https://example.com/list" --selector ".item" -o out.csv

注意：请遵守目标网站的 robots.txt 与服务条款，控制请求频率，做个有礼貌的爬虫。
"""

import argparse
import csv
import json
import random
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class PoliteScraper:
    """有礼貌的爬虫：限速 + 重试 + 随机间隔。"""

    def __init__(self, delay=(1.0, 3.0), retries=3, timeout=15):
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def get(self, url: str) -> BeautifulSoup | None:
        """GET 请求并返回 BeautifulSoup，失败自动重试。"""
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding
                # 礼貌间隔
                time.sleep(random.uniform(*self.delay))
                return BeautifulSoup(resp.text, "html.parser")
            except requests.RequestException as e:
                print(f"  请求失败 ({attempt}/{self.retries})：{url} - {e}")
                time.sleep(2 * attempt)
        return None

    def crawl_pages(self, url_template: str, pages: int, item_selector: str) -> list:
        """
        分页抓取。url_template 中用 {page} 作为页码占位符。
        返回每页的 item 元素列表（跨页合并）。
        """
        items = []
        for page in range(1, pages + 1):
            url = url_template.format(page=page)
            print(f"正在抓取第 {page}/{pages} 页：{url}")
            soup = self.get(url)
            if soup is None:
                print("  跳过本页（请求失败）")
                continue
            found = soup.select(item_selector)
            print(f"  找到 {len(found)} 条")
            if not found:
                print("  本页无数据，提前结束。")
                break
            items.extend(found)
        return items


def extract_text(element, selector: str, default: str = "") -> str:
    """从元素中按选择器提取文本，找不到返回默认值。"""
    node = element.select_one(selector)
    return node.get_text(strip=True) if node else default


def extract_attr(element, selector: str, attr: str, base_url: str = "", default: str = "") -> str:
    """提取属性（如链接 href），base_url 不为空时转为绝对地址。"""
    node = element.select_one(selector)
    if not node or not node.has_attr(attr):
        return default
    value = node[attr]
    return urljoin(base_url, value) if base_url else value


def save(data: list | str | Path, output: str | Path):
    """按后缀导出 JSON 或 CSV。"""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".json":
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    elif output.suffix == ".csv":
        if not data:
            print("无数据可写。")
            return
        with open(output, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    else:
        raise ValueError("输出格式仅支持 .json / .csv")
    print(f"已保存 {len(data)} 条 -> {output}")


def main():
    parser = argparse.ArgumentParser(description="通用爬虫工具包")
    parser.add_argument("--url", required=True, help="目标 URL，分页用 {page} 占位")
    parser.add_argument("--pages", type=int, default=1, help="抓取页数（默认 1）")
    parser.add_argument("--selector", default="body", help="条目 CSS 选择器")
    parser.add_argument("--title", default="h1, h2, h3", help="标题 CSS 选择器")
    parser.add_argument("--link", default="a", help="链接 CSS 选择器")
    parser.add_argument("-o", "--output", default="data.json", help="输出文件 (.json/.csv)")
    parser.add_argument("--delay", type=float, default=2.0, help="请求间隔基准秒数")
    args = parser.parse_args()

    scraper = PoliteScraper(delay=(args.delay, args.delay + 1.5))
    items = scraper.crawl_pages(args.url, args.pages, args.selector)

    base = args.url.split("{page}")[0]
    data = [{
        "title": extract_text(el, args.title),
        "link": extract_attr(el, args.link, "href", base),
        "text": el.get_text(strip=True)[:200],
    } for el in items]

    save(data, Path(args.output))


if __name__ == "__main__":
    main()
