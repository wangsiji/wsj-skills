#!/usr/bin/env python3
"""
微信读书教练 - 数据抓取脚本
支持两种认证方式：
1. Playwright 扫码登录（首次设置时用 --visible）
2. 从浏览器导入手动 cookie（推荐，永久有效）

用法：
  # 首次扫码登录（需要图形界面）
  python3 weread_coach.py --login

  # 导入手动 cookie（推荐）
  python3 weread_coach.py --cookie-file /path/to/cookies.json

  # 抓取数据
  python3 weread_coach.py --days 1
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
import urllib.request
from urllib.parse import urlencode

# 尝试导入 playwright
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    playwright_available = True
except ImportError:
    playwright_available = False

COOKIE_FILE = os.path.expanduser("~/.hermes/.weread_cookies")
DATA_DIR = os.path.expanduser("~/.hermes/weread_data")


def save_cookies(cookies):
    """保存 cookies 到文件"""
    os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
    with open(COOKIE_FILE, 'w') as f:
        json.dump(cookies, f, ensure_ascii=False)


def load_cookies():
    """从文件加载 cookies"""
    if not os.path.exists(COOKIE_FILE):
        return None
    try:
        with open(COOKIE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def get_cookie_dict(cookies):
    """将 cookies 列表转为 dict"""
    return {c['name']: c['value'] for c in cookies}


def get_user_vid(cookies):
    """从 cookie 中提取 userVid"""
    cookie_dict = {c['name']: c for c in cookies}

    if 'wr_sid' in cookie_dict:
        val = cookie_dict['wr_sid']['value']
        return val.split('_')[0] if '_' in val else val

    if 'wr_vid' in cookie_dict:
        return cookie_dict['wr_vid']['value']

    return None


def rebuild_wr_sid(cookies):
    """重建 wr_sid cookie（如果缺失）"""
    cookie_dict = {c['name']: c for c in cookies}
    if 'wr_sid' in cookie_dict:
        return

    if 'wr_vid' in cookie_dict and 'wr_rt' in cookie_dict:
        import urllib.parse
        user_vid = cookie_dict['wr_vid']['value']
        session_id = urllib.parse.unquote(cookie_dict['wr_rt']['value'])
        wr_sid_value = f"{user_vid}_{session_id}"
        cookies.append({
            'name': 'wr_sid',
            'value': wr_sid_value,
            'domain': '.weread.qq.com',
            'path': '/',
        })


def make_request(url, cookies, params=None):
    """发送 HTTP 请求"""
    import gzip

    cookie_dict = get_cookie_dict(cookies)
    cookie_str = '; '.join(f"{k}={v}" for k, v in cookie_dict.items())

    if params:
        query = urlencode(params)
        full_url = f"{url}?{query}"
    else:
        full_url = url

    req = urllib.request.Request(full_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cookie': cookie_str,
        'Referer': 'https://weread.qq.com/',
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if resp.headers.get('Content-Encoding') == 'gzip':
                data = gzip.decompress(data)
            return json.loads(data.decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def fetch_bookshelf(cookies):
    """获取书架数据"""
    url = "https://weread.qq.com/api/user/notebook"
    return make_request(url, cookies)


def parse_books(data):
    """解析书架数据，返回书籍列表"""
    if not data or 'books' not in data:
        return []

    books = []
    for item in data.get('books', []):
        book = item.get('book', {})
        books.append({
            'bookId': book.get('bookId', ''),
            'title': book.get('title', ''),
            'author': book.get('author', ''),
            'cover': book.get('cover', ''),
            'readingProgress': item.get('readingProgress', 0),
            'noteCount': item.get('noteCount', 0),
            'reviewCount': item.get('reviewCount', 0),
            'isFinish': item.get('isFinish', 0),
            'lastReadTimestamp': item.get('sort', 0),  # sort 是时间戳
        })
    return books


def get_recent_books(books, days=1):
    """获取最近 days 天有阅读的书籍"""
    cutoff = time.time() - days * 86400
    return [b for b in books if b.get('lastReadTimestamp', 0) >= cutoff]


def generate_report(data, days=1):
    """生成阅读报告"""
    books = parse_books(data)
    recent = get_recent_books(books, days)

    # 转换时间戳为日期
    for b in books:
        if b.get('lastReadTimestamp'):
            b['lastReadDate'] = datetime.fromtimestamp(b['lastReadTimestamp']).strftime('%Y-%m-%d')

    for b in recent:
        if b.get('lastReadTimestamp'):
            b['lastReadDate'] = datetime.fromtimestamp(b['lastReadTimestamp']).strftime('%Y-%m-%d')

    total_finished = sum(1 for b in books if b.get('isFinish') == 1)

    return {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_books': len(books),
        'total_finished': total_finished,
        'all_books': books,
        'recent_books': recent,
        'recent_count': len(recent),
    }


def save_data(data, prefix='weread'):
    """保存数据到本地"""
    os.makedirs(DATA_DIR, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    filepath = os.path.join(DATA_DIR, f'{prefix}_{date_str}.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


def login_with_qrcode(playwright, visible=True):
    """使用 Playwright 扫码登录微信读书"""
    headless = not visible
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()

    print("正在打开微信读书登录页...")
    page.goto("https://weread.qq.com/", timeout=30000)

    try:
        login_btn = page.wait_for_selector('.header_login_btn', timeout=5000)
        login_btn.click()
    except Exception:
        pass

    print("等待扫码登录（请使用微信扫描页面二维码）...")
    try:
        page.wait_for_selector('.user_info', timeout=120000)
        print("登录成功！")
    except PlaywrightTimeout:
        print("登录超时，请重试")
        browser.close()
        sys.exit(1)

    cookies = context.cookies()
    browser.close()
    return cookies


def main():
    parser = argparse.ArgumentParser(description='微信读书数据抓取')
    parser.add_argument('--days', type=int, default=1, help='获取最近N天的阅读数据')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--force-login', action='store_true', help='强制重新扫码登录')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    parser.add_argument('--cookie-file', type=str, help='从文件导入 cookie')
    parser.add_argument('--import', dest='import_cookies', action='store_true', help='导入 cookie')
    args = parser.parse_args()

    cookies = None

    # 从文件导入 cookie
    if args.cookie_file:
        with open(args.cookie_file, 'r') as f:
            cookie_data = json.load(f)
        if isinstance(cookie_data, list):
            cookies = cookie_data
        elif isinstance(cookie_data, dict) and 'cookies' in cookie_data:
            cookies = cookie_data['cookies']
        else:
            print("无法解析 cookie 文件格式")
            sys.exit(1)
        rebuild_wr_sid(cookies)
        save_cookies(cookies)
        print("Cookie 已导入并保存")

    if not cookies and not args.cookie_file:
        cookies = load_cookies()

    if not cookies:
        if not playwright_available:
            print("ERROR: playwright not installed and no cookies found.")
            print("请先导入 Cookie：python3 weread_coach.py --cookie-file /path/to/cookies.json")
            sys.exit(1)
        print("未找到保存的登录态，需要扫码登录...")
        with sync_playwright() as p:
            cookies = login_with_qrcode(p, visible=args.visible)
        save_cookies(cookies)
        print("登录态已保存")
    else:
        rebuild_wr_sid(cookies)
        save_cookies(cookies)

    print("正在抓取阅读数据...")
    data = fetch_bookshelf(cookies)

    if not data:
        print("获取数据失败，请尝试 --force-login 重新导入 Cookie")
        sys.exit(1)

    filepath = save_data(data)
    print(f"数据已保存到: {filepath}")

    report = generate_report(data, args.days)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"报告已保存到: {args.output}")
    else:
        print(f"\n=== 每日阅读报告 ===")
        print(f"总书籍数: {report['total_books']}（已读 {report['total_finished']} 本）")
        print(f"最近 {args.days} 天阅读: {report['recent_count']} 本")
        for book in report['recent_books']:
            title = book.get('title', '未知')
            author = book.get('author', '未知')
            progress = book.get('readingProgress', 0)
            last_read = book.get('lastReadDate', '未知')
            print(f"  - {title} ({author}) - 进度 {progress}% - 最后阅读 {last_read}")

    return report


if __name__ == '__main__':
    main()
