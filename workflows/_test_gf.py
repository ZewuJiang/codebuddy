"""临时测试脚本: 验证Google Finance网页抓取"""
import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for symbol, exchange in [('RUT', 'INDEXRUSSELL'), ('VIX', 'INDEXCBOE')]:
    url = f'https://www.google.com/finance/quote/{symbol}:{exchange}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        print(f'\n=== {symbol}:{exchange} (html len={len(html)}) ===')

        # data-last-price
        m = re.search(r'data-last-price="([0-9.,]+)"', html)
        if m:
            print(f'  data-last-price: {m.group(1)}')
        else:
            print('  data-last-price: NOT FOUND')

        # YMlKec fxKbKc class
        m = re.search(r'class="YMlKec fxKbKc"[^>]*>([0-9,]+\.?\d*)', html)
        if m:
            print(f'  YMlKec: {m.group(1)}')

        # Previous close
        m = re.search(r'Previous close.*?([0-9,]+\.\d+)', html, re.DOTALL)
        if m:
            print(f'  Previous close: {m.group(1)}')

        # 百分比
        matches = re.findall(r'\(([+-]?\d+\.?\d*)%\)', html[:15000])
        if matches:
            print(f'  百分比: {matches[:5]}')

        # data属性中的数字
        data_attrs = re.findall(r'data-[a-z-]+="([0-9][0-9,.]+)"', html[:20000])
        if data_attrs:
            print(f'  data属性中的数字: {data_attrs[:10]}')

    except Exception as e:
        print(f'{symbol}: ERROR - {e}')
