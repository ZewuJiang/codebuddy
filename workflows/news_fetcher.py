#!/usr/bin/env python3
"""
财经新闻采集引擎 v1.0
为投资Agent的10个Skill提供实时新闻数据（过去24小时）

数据源：Google News RSS（英文+中文双语采集）
架构：每个Skill定义专属搜索关键词 → 并行采集 → 去重 → 时效性过滤 → 返回结构化新闻列表
"""

import os
import time
import json
import hashlib
import requests
import feedparser
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════
# 新闻数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class NewsItem:
    """单条新闻"""
    title: str
    source: str
    published: str          # 发布时间字符串
    published_dt: Optional[datetime] = None  # 发布时间datetime（可能为None）
    url: str = ""
    language: str = "en"    # en / zh
    skill_tags: list = field(default_factory=list)  # 关联的Skill编号
    relevance: float = 1.0  # 相关性分数

    def to_dict(self):
        return {
            'title': self.title,
            'source': self.source,
            'published': self.published,
            'url': self.url,
            'language': self.language,
            'skill_tags': self.skill_tags,
        }


# ═══════════════════════════════════════════════════════════
# Skill搜索关键词定义（英文+中文）
# ═══════════════════════════════════════════════════════════

# 每个Skill的搜索查询（精简版：英文2条+中文1条，when:1d限制过去24小时）
SKILL_QUERIES = {
    1: {
        'name': '公司估值与质量评级',
        'en': [
            'NVDA AAPL MSFT TSLA META AMZN stock earnings valuation',
            'tech stock mega cap earnings P/E growth outlook',
        ],
        'zh': [
            '美股 科技股 财报 估值 英伟达 苹果',
        ],
    },
    2: {
        'name': '加密货币周期与抄底',
        'en': [
            'bitcoin ethereum crypto market price crash rally',
            'cryptocurrency SEC regulation ETF stablecoin',
        ],
        'zh': [
            '比特币 以太坊 加密货币 暴跌 暴涨',
        ],
    },
    3: {
        'name': '全球市场情绪监控',
        'en': [
            'market sentiment fear greed VIX crash correction',
            'investor sentiment put call ratio stock market rally',
        ],
        'zh': [
            '美股 市场情绪 恐慌 贪婪 大跌 大涨',
        ],
    },
    4: {
        'name': '宏观流动性与央行监控',
        'en': [
            'federal reserve interest rate monetary policy inflation',
            'ECB BOJ central bank rate decision QE QT liquidity',
        ],
        'zh': [
            '美联储 降息 加息 货币政策 通胀',
        ],
    },
    5: {
        'name': '全球市场联动与资金流向',
        'en': [
            'global stock market Asia Europe capital flow rotation',
            'emerging markets fund flow S&P 500 Nasdaq sector',
        ],
        'zh': [
            '全球股市 资金流向 板块轮动 新兴市场',
        ],
    },
    6: {
        'name': '信贷市场与私募信用监控',
        'en': [
            'private credit default high yield bond CLO leveraged loan',
            'Blue Owl Ares KKR TPG credit fund SaaS software debt',
        ],
        'zh': [
            '私募信贷 高收益债 违约 杠杆贷款 信用风险',
        ],
    },
    7: {
        'name': '贵金属与大宗商品周期',
        'en': [
            'gold silver copper oil price commodity',
            'OPEC crude WTI Brent supply demand inflation commodity',
        ],
        'zh': [
            '黄金 白银 原油 大宗商品 铜价',
        ],
    },
    8: {
        'name': '收益率曲线与利率分析',
        'en': [
            'treasury yield curve inversion 10 year bond rate',
            'mortgage rate spread housing interest rate',
        ],
        'zh': [
            '美债 收益率 利率 曲线倒挂 国债',
        ],
    },
    9: {
        'name': '波动率微观结构',
        'en': [
            'VIX volatility spike options expiration 0DTE gamma',
            'implied volatility skew term structure market',
        ],
        'zh': [
            'VIX 波动率 期权 市场波动',
        ],
    },
    10: {
        'name': '港股与A股专项分析',
        'en': [
            'Hong Kong stock Hang Seng China market A-share',
            'China policy stimulus southbound northbound tech property',
        ],
        'zh': [
            '港股 A股 恒指 南向资金 中概股 腾讯 阿里',
        ],
    },
}

# ═══════════════════════════════════════════════════════════
# Google News RSS 采集器
# ═══════════════════════════════════════════════════════════

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml',
}

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(__file__), "investment_agent_data", "news_cache")


def _parse_pub_date(entry) -> Optional[datetime]:
    """解析RSS条目的发布时间"""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            from calendar import timegm
            ts = timegm(entry.published_parsed)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        pass

    # 尝试解析published字符串
    pub_str = entry.get('published', '')
    for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S']:
        try:
            return datetime.strptime(pub_str, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def _extract_source(title: str) -> tuple:
    """从Google News标题中提取来源（格式：'标题 - 来源'）"""
    if ' - ' in title:
        parts = title.rsplit(' - ', 1)
        return parts[0].strip(), parts[1].strip()
    return title, 'Unknown'


def fetch_google_news(query: str, lang: str = 'en', max_results: int = 8) -> List[NewsItem]:
    """
    从Google News RSS获取新闻
    Args:
        query: 搜索关键词
        lang: 语言 ('en' 或 'zh')
        max_results: 最大返回数
    Returns:
        NewsItem列表
    """
    try:
        if lang == 'zh':
            params = 'hl=zh-CN&gl=CN&ceid=CN:zh-Hans'
        else:
            params = 'hl=en-US&gl=US&ceid=US:en'

        # 添加时间限制（when:1d = 过去24小时）
        q_encoded = quote(query + ' when:1d')
        url = f'https://news.google.com/rss/search?q={q_encoded}&{params}'

        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []

        feed = feedparser.parse(resp.text)
        items = []

        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc - timedelta(hours=36)  # 36小时窗口（宽松一点）

        for entry in feed.entries[:max_results * 2]:  # 多取一些用于过滤
            pub_dt = _parse_pub_date(entry)

            # 时效性过滤：如果能解析时间，只保留36小时内的
            if pub_dt and pub_dt < cutoff:
                continue

            raw_title = entry.get('title', '')
            title, source = _extract_source(raw_title)

            if not title or len(title) < 10:
                continue

            item = NewsItem(
                title=title,
                source=source,
                published=entry.get('published', ''),
                published_dt=pub_dt,
                url=entry.get('link', ''),
                language=lang,
            )
            items.append(item)

            if len(items) >= max_results:
                break

        return items

    except Exception as e:
        return []


# ═══════════════════════════════════════════════════════════
# Skill级新闻采集（并行）
# ═══════════════════════════════════════════════════════════

def fetch_skill_news(skill_id: int, max_per_query: int = 5) -> List[NewsItem]:
    """
    采集特定Skill的新闻
    Args:
        skill_id: Skill编号 (1-10)
        max_per_query: 每个查询最大返回数
    Returns:
        去重后的NewsItem列表
    """
    queries = SKILL_QUERIES.get(skill_id)
    if not queries:
        return []

    all_items = []
    seen_titles = set()

    # 英文查询
    for q in queries.get('en', []):
        items = fetch_google_news(q, lang='en', max_results=max_per_query)
        for item in items:
            # 标题去重（用标题前30字符的hash）
            key = hashlib.md5(item.title[:30].lower().encode()).hexdigest()
            if key not in seen_titles:
                seen_titles.add(key)
                item.skill_tags.append(skill_id)
                all_items.append(item)

    # 中文查询
    for q in queries.get('zh', []):
        items = fetch_google_news(q, lang='zh', max_results=max_per_query)
        for item in items:
            key = hashlib.md5(item.title[:30].lower().encode()).hexdigest()
            if key not in seen_titles:
                seen_titles.add(key)
                item.skill_tags.append(skill_id)
                all_items.append(item)

    # 按时间排序（最新优先）
    all_items.sort(key=lambda x: x.published_dt or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    return all_items


def fetch_all_skills_news(max_per_skill: int = 8, parallel: bool = True) -> Dict[int, List[NewsItem]]:
    """
    并行采集所有10个Skill的新闻
    Args:
        max_per_skill: 每个Skill最终保留的最大新闻数
        parallel: 是否并行采集
    Returns:
        {skill_id: [NewsItem, ...]} 字典
    """
    print("  📰 采集财经新闻（10个Skill领域 × 双语）...")
    start = time.time()
    results = {}

    if parallel:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            for skill_id in range(1, 11):
                future = executor.submit(fetch_skill_news, skill_id, max_per_skill)
                futures[future] = skill_id

            for future in as_completed(futures):
                skill_id = futures[future]
                try:
                    items = future.result(timeout=30)
                    results[skill_id] = items[:max_per_skill]
                except Exception:
                    results[skill_id] = []
    else:
        for skill_id in range(1, 11):
            items = fetch_skill_news(skill_id, max_per_skill)
            results[skill_id] = items[:max_per_skill]

    elapsed = time.time() - start
    total = sum(len(v) for v in results.values())
    skills_with_news = sum(1 for v in results.values() if v)
    print(f"  ✅ 新闻采集完成: {total}条新闻 覆盖{skills_with_news}/10个Skill ({elapsed:.1f}秒)")

    # 打印各Skill采集概况
    for sid in range(1, 11):
        items = results.get(sid, [])
        name = SKILL_QUERIES[sid]['name']
        if items:
            print(f"    Skill {sid:>2} {name}: {len(items)}条 | {items[0].title[:50]}...")
        else:
            print(f"    Skill {sid:>2} {name}: 0条")

    return results


def format_news_for_skill(news_items: List[NewsItem], max_display: int = 5) -> str:
    """将新闻列表格式化为Skill分析使用的摘要文本"""
    if not news_items:
        return ""

    lines = []
    for item in news_items[:max_display]:
        source_tag = f"[{item.source}]" if item.source != 'Unknown' else ""
        lang_tag = "🇨🇳" if item.language == 'zh' else "🇺🇸"
        lines.append(f"{lang_tag} {source_tag} {item.title}")

    return "\n".join(lines)


def format_news_for_markdown(news_items: List[NewsItem], max_display: int = 5) -> List[str]:
    """将新闻列表格式化为Markdown表格行"""
    rows = []
    for item in news_items[:max_display]:
        lang_tag = "🇨🇳" if item.language == 'zh' else "🇺🇸"
        source = item.source[:15] if item.source else '-'
        title = item.title[:60] + ('...' if len(item.title) > 60 else '')
        pub = item.published[:16] if item.published else '-'
        rows.append(f"| {lang_tag} | {source} | {title} | {pub} |")
    return rows


# ═══════════════════════════════════════════════════════════
# 新闻缓存（避免重复请求）
# ═══════════════════════════════════════════════════════════

def save_news_cache(all_news: Dict[int, List[NewsItem]]):
    """将新闻保存到缓存文件"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"news_{datetime.now().strftime('%Y%m%d_%H%M')}.json")

    cache_data = {}
    for skill_id, items in all_news.items():
        cache_data[str(skill_id)] = [item.to_dict() for item in items]

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    return cache_file


def load_latest_cache() -> Optional[Dict[int, List[NewsItem]]]:
    """加载最近6小时内的缓存（如果存在）"""
    if not os.path.exists(CACHE_DIR):
        return None

    files = sorted([f for f in os.listdir(CACHE_DIR) if f.startswith('news_') and f.endswith('.json')], reverse=True)
    if not files:
        return None

    latest = files[0]
    # 检查时效性（6小时以内有效）
    try:
        ts_str = latest.replace('news_', '').replace('.json', '')
        cache_time = datetime.strptime(ts_str, '%Y%m%d_%H%M')
        if datetime.now() - cache_time > timedelta(hours=6):
            return None
    except Exception:
        return None

    try:
        with open(os.path.join(CACHE_DIR, latest), 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = {}
        for skill_id_str, items in data.items():
            skill_id = int(skill_id_str)
            results[skill_id] = [
                NewsItem(
                    title=item['title'],
                    source=item['source'],
                    published=item['published'],
                    url=item.get('url', ''),
                    language=item.get('language', 'en'),
                    skill_tags=item.get('skill_tags', []),
                )
                for item in items
            ]
        return results
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════

def get_all_news(force_refresh: bool = False) -> Dict[int, List[NewsItem]]:
    """
    获取所有Skill的新闻（带缓存）
    Args:
        force_refresh: 是否强制刷新（忽略缓存）
    Returns:
        {skill_id: [NewsItem, ...]}
    """
    if not force_refresh:
        cached = load_latest_cache()
        if cached:
            total = sum(len(v) for v in cached.values())
            print(f"  📰 使用缓存新闻: {total}条")
            return cached

    all_news = fetch_all_skills_news(max_per_skill=8, parallel=True)
    save_news_cache(all_news)
    return all_news


# 测试
if __name__ == "__main__":
    news = get_all_news(force_refresh=True)
    print(f"\n{'='*60}")
    for sid in range(1, 11):
        items = news.get(sid, [])
        print(f"\n--- Skill {sid}: {SKILL_QUERIES[sid]['name']} ({len(items)}条) ---")
        for item in items[:3]:
            lang = '🇨🇳' if item.language == 'zh' else '🇺🇸'
            print(f"  {lang} [{item.source}] {item.title[:70]}")
