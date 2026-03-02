#!/usr/bin/env python3
"""
数据源管理器 v2.0 — 投资Agent多源数据聚合层

架构:
┌─────────────────────────────────────────────────────────────┐
│                    DataSourceManager                         │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐              │
│  │ AlphaVantage  │  │  FRED    │  │ AkShare  │              │
│  │ (主数据源)    │  │(宏观数据) │  │(中国市场) │              │
│  └──────────────┘  └──────────┘  └──────────┘              │
│  ┌──────────┐                                                │
│  │ yfinance  │  ← 降级备用（AV失败时使用）                    │
│  └──────────┘                                                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              全局缓存层 (Session Cache)                 │ │
│  │     去重下载 · 跨Skill共享 · 失败降级 · 限流控制        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

数据源优先级:
  - 行情数据: Alpha Vantage (主) → yfinance (降级) → 缓存
  - 宏观数据: FRED (主)
  - A股/港股: AkShare (主)
  - 技术指标: 本地计算 (主) → Alpha Vantage API (备用)
"""

import os
import sys
import json
import time
import random
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple

# ═══════════════════════════════════════════════════════════
# SSL证书修复（macOS Python 3.x 常见问题）
# ═══════════════════════════════════════════════════════════
try:
    import certifi
    os.environ.setdefault('SSL_CERT_FILE', certifi.where())
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════
# Alpha Vantage 配置与核心请求层
# ═══════════════════════════════════════════════════════════

ALPHA_VANTAGE_KEY = os.environ.get('ALPHA_VANTAGE_KEY', '2DY8F4CY466WAT7U')
AV_BASE_URL = 'https://www.alphavantage.co/query'
AV_CALL_DELAY = 5.0  # 免费版限制：约25次/分钟，保守间隔5秒（避免触发限流）

# 指数 → ETF 映射（Alpha Vantage不支持指数ticker，用ETF代理）
INDEX_TO_ETF = {
    '^GSPC': 'SPY',    # S&P 500
    '^IXIC': 'QQQ',    # NASDAQ
    '^DJI': 'DIA',     # 道琼斯
    '^RUT': 'IWM',     # 罗素2000
    '^VIX': 'VIXY',    # VIX（近似）
    '^VIX9D': None,    # 无ETF代理
    '^HSI': 'EWH',     # 恒生
    '^HSTECH': None,   # 恒生科技无直接ETF
    '^N225': 'EWJ',    # 日经
    '^FTSE': 'EWU',    # 英国
    '^GDAXI': 'EWG',   # 德国
    '^STOXX50E': 'FEZ', # 欧洲
    '^TNX': None,       # 10Y收益率，用FRED替代
    '^FVX': None,       # 5Y收益率
    '^IRX': None,       # 3M收益率
}

# 指数ticker → AkShare东方财富全球指数代码（index_global_spot_em）
# 用于获取真实指数点位（而非ETF代理价格）
INDEX_TO_AKSHARE_GLOBAL = {
    '^GSPC': 'SPX',     # 标普500
    '^IXIC': 'NDX',     # 纳斯达克
    '^DJI': 'DJIA',     # 道琼斯
    '^HSI': 'HSI',      # 恒生指数
    '^N225': 'N225',    # 日经225
    '^FTSE': 'FTSE',    # 英国富时100
    '^GDAXI': 'GDAXI',  # 德国DAX30
    '^STOXX50E': 'SX5E', # 欧洲斯托克50
}

# 补充指数: AkShare全球指数列表中缺失的，通过Google Finance网页获取
# 格式: ticker → (Google Finance symbol, exchange)
INDEX_GOOGLE_FINANCE_FALLBACK = {
    '^RUT': ('RUT', 'INDEXRUSSELL'),   # 罗素2000
    '^VIX': ('VIX', 'INDEXCBOE'),      # VIX恐慌指数
}

# 加密货币 ticker 映射（yfinance格式 → AV格式）
CRYPTO_MAP = {
    'BTC-USD': 'BTC',
    'ETH-USD': 'ETH',
    'SOL-USD': 'SOL',
}

# 汇率 ticker 映射
FX_MAP = {
    'CNY=X': ('USD', 'CNY'),
}

# AkShare美股 ticker → 东方财富代码映射
# 格式: "105.XXX"(NASDAQ ETF/股票) "106.XXX"(美股正股) "107.XXX"(NYSE/ARCA ETF)
AKSHARE_US_PREFIX = {
    # ═══ ETF: NASDAQ上市 (105) ═══
    'QQQ': '105.QQQ', 'TLT': '105.TLT', 'IEF': '105.IEF', 'SHY': '105.SHY',
    'PDBC': '105.PDBC', 'MCHI': '105.MCHI',
    # ═══ ETF: NYSE/ARCA上市 (107) ═══
    'SPY': '107.SPY', 'DIA': '107.DIA', 'IWM': '107.IWM',
    'HYG': '107.HYG', 'LQD': '107.LQD', 'UUP': '107.UUP', 'GLD': '107.GLD',
    'SLV': '107.SLV', 'GDX': '107.GDX', 'USO': '107.USO', 'CPER': '107.CPER',
    'DBA': '107.DBA', 'BKLN': '107.BKLN', 'KRE': '107.KRE',
    'KWEB': '107.KWEB', 'FXI': '107.FXI', 'EWH': '107.EWH',
    'EWJ': '107.EWJ', 'EWU': '107.EWU', 'EWG': '107.EWG', 'FEZ': '107.FEZ',
    'VIXY': '107.VIXY', 'FXY': '107.FXY', 'FXE': '107.FXE',
    'USHY': '107.USHY', 'UNG': '107.UNG',
    # ═══ 美股正股 (106=东方财富美股正股前缀) ═══
    # NASDAQ上市个股
    'AAPL': '105.AAPL', 'MSFT': '105.MSFT', 'AMZN': '105.AMZN', 'GOOGL': '105.GOOGL',
    'META': '105.META', 'NVDA': '105.NVDA', 'TSLA': '105.TSLA', 'AMD': '105.AMD',
    'NFLX': '105.NFLX', 'AVGO': '105.AVGO', 'COST': '105.COST', 'ADBE': '105.ADBE',
    'INTC': '105.INTC', 'QCOM': '105.QCOM', 'PYPL': '105.PYPL',
    'TXN': '105.TXN', 'MU': '105.MU', 'AMAT': '105.AMAT', 'LRCX': '105.LRCX',
    'KLAC': '105.KLAC', 'MRVL': '105.MRVL', 'SNPS': '105.SNPS', 'CDNS': '105.CDNS',
    'PANW': '105.PANW', 'CRWD': '105.CRWD', 'ABNB': '105.ABNB', 'COIN': '105.COIN',
    'PDD': '105.PDD',
    # NYSE/其他交易所正股 → 用106前缀（东方财富美股正股标准格式）
    'JPM': '106.JPM', 'V': '106.V', 'MA': '106.MA', 'BAC': '106.BAC',
    'WMT': '106.WMT', 'JNJ': '106.JNJ', 'PG': '106.PG', 'UNH': '106.UNH',
    'HD': '106.HD', 'DIS': '106.DIS', 'BA': '106.BA', 'GS': '106.GS',
    'XOM': '106.XOM', 'CVX': '106.CVX',
    'BRK-B': '106.BRK_B',  # 东方财富用下划线替代横杠
    'TSM': '106.TSM', 'LLY': '106.LLY', 'NVO': '106.NVO',
    'BABA': '106.BABA', 'CRM': '106.CRM',
    # TCEHY(腾讯ADR) = OTC交易，东方财富无数据，需CoinGecko或其他源
}

# ═══════════════════════════════════════════════════════════
# 数据源配置
# ═══════════════════════════════════════════════════════════

FRED_API_KEY = os.environ.get('FRED_API_KEY', '78b890270efd7d6c2d9365b0c658adcc')

# 限流配置
FRED_CALL_DELAY = 0.5
AKSHARE_CALL_DELAY = 0.5
YFINANCE_BATCH_DELAY = 2.0
YFINANCE_TICKER_INFO_DELAY = 2.0


# ═══════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class DataPoint:
    """单个数据点"""
    source: str
    value: float
    timestamp: str
    unit: str = ""
    note: str = ""

@dataclass
class MacroData:
    """宏观经济数据包"""
    fed_funds_rate: Optional[float] = None
    cpi_yoy: Optional[float] = None
    core_pce: Optional[float] = None
    unemployment: Optional[float] = None
    gdp_growth: Optional[float] = None
    us10y_yield: Optional[float] = None
    us2y_yield: Optional[float] = None
    us2s10s_spread: Optional[float] = None
    us3m10s_spread: Optional[float] = None
    hy_spread: Optional[float] = None
    fed_balance_sheet: Optional[float] = None
    tga_balance: Optional[float] = None
    on_rrp: Optional[float] = None
    net_liquidity: Optional[float] = None
    m2_supply: Optional[float] = None
    mortgage_rate_30y: Optional[float] = None
    initial_claims: Optional[float] = None
    dxy_index: Optional[float] = None
    sofr: Optional[float] = None
    move_index: Optional[float] = None
    source: str = ""
    last_updated: str = ""
    raw_data: dict = field(default_factory=dict)

@dataclass
class ChinaMarketData:
    """中国市场数据包（AkShare）"""
    sh_index: Optional[float] = None
    sz_index: Optional[float] = None
    cyb_index: Optional[float] = None
    hs300: Optional[float] = None
    northbound_flow: Optional[float] = None
    southbound_flow: Optional[float] = None
    ah_premium_index: Optional[float] = None
    cny_usd: Optional[float] = None
    shibor_overnight: Optional[float] = None
    social_financing: Optional[float] = None
    margin_balance: Optional[float] = None
    source: str = ""
    last_updated: str = ""
    raw_data: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# 核心: DataSourceManager
# ═══════════════════════════════════════════════════════════

class DataSourceManager:
    """
    多源数据聚合管理器 v2.0 — Alpha Vantage 优先

    功能:
    1. Alpha Vantage 为主数据源（行情/基本面/加密/汇率）
    2. FRED 宏观数据（利率/CPI/GDP/净流动性）
    3. AkShare 中国市场数据
    4. yfinance 作为降级备用
    5. 全局缓存 + 限流控制
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._batch_cache: Dict[str, Any] = {}          # batch_key -> DataFrame
        self._info_cache: Dict[str, dict] = {}           # ticker -> info dict
        self._fred_cache: Dict[str, Any] = {}            # series_id -> value
        self._akshare_cache: Dict[str, Any] = {}         # data_key -> value
        self._av_cache: Dict[str, Any] = {}              # AV专用缓存
        self._macro_data: Optional[MacroData] = None
        self._china_data: Optional[ChinaMarketData] = None
        self._fear_greed: Optional[dict] = None
        self._last_api_call: Dict[str, float] = {}
        self._stats = {'av_calls': 0, 'av_cache_hits': 0,
                       'yf_downloads': 0, 'yf_cache_hits': 0,
                       'fred_calls': 0, 'akshare_calls': 0,
                       'errors': 0}
        self._av_rate_limited = False   # AV全局限流标记
        self._av_consecutive_limits = 0  # AV连续限流计数
        self._yf_available = None        # yfinance可用性（None=未检测, True/False）
        self._akshare_failures = {}      # AkShare失败记录

        # HTTP Session
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        })

        # 预定义需要预加载的ticker分组（覆盖所有10个Skill的核心需求）
        # AV免费版限制：25次/分钟，500次/天
        # AV限流后自动降级为yfinance批量获取
        self._preload_groups = {
            'indices': '^GSPC ^IXIC ^DJI ^VIX ^VIX9D ^HSI ^HSTECH ^RUT ^N225 ^FTSE ^GDAXI ^STOXX50E',
            'crypto': 'BTC-USD ETH-USD',
            'macro_bonds': 'TLT IEF SHY HYG LQD UUP FXY GLD',
            'commodities': 'USO SLV GDX CPER DBA PDBC',
            'credit': 'BKLN KRE',
            'china_etf': 'KWEB FXI MCHI EWH CNY=X',
            'market_etf': 'SPY QQQ',
        }

    # ─── 限流控制 ─────────────────────────────────────────
    def _rate_limit(self, api_name: str, min_interval: float):
        """确保API调用间隔不小于min_interval秒"""
        last = self._last_api_call.get(api_name, 0)
        elapsed = time.time() - last
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_api_call[api_name] = time.time()

    # ─── Alpha Vantage 核心请求 ───────────────────────────

    def _av_request(self, params: dict, max_retries: int = 3) -> Optional[dict]:
        """Alpha Vantage API 统一请求（带限流+重试+缓存+全局限流短路）"""
        if not ALPHA_VANTAGE_KEY:
            return None

        # 全局限流短路：连续3次限流后跳过AV
        if self._av_rate_limited:
            return None

        params['apikey'] = ALPHA_VANTAGE_KEY
        cache_key = json.dumps(params, sort_keys=True)

        if cache_key in self._av_cache:
            self._stats['av_cache_hits'] += 1
            return self._av_cache[cache_key]

        self._rate_limit('alpha_vantage', AV_CALL_DELAY)

        for attempt in range(max_retries):
            try:
                resp = self._session.get(AV_BASE_URL, params=params, timeout=20)
                data = resp.json()

                # 检查限流（Note字段 — 分钟级限流）
                if 'Note' in data and 'call frequency' in data.get('Note', '').lower():
                    self._av_consecutive_limits += 1
                    if self._av_consecutive_limits >= 2:
                        self._av_rate_limited = True
                        print(f"    🚫 AV连续{self._av_consecutive_limits}次限流，跳过所有AV请求")
                        return None
                    if attempt < max_retries - 1:
                        wait = 12 + random.uniform(1, 3)
                        print(f"    🚫 AV限流，退避{wait:.0f}秒...")
                        time.sleep(wait)
                        continue
                    else:
                        return None

                # 检查错误
                if 'Error Message' in data:
                    print(f"    ⚠️ AV错误: {data['Error Message'][:60]}")
                    return None

                # 检查空响应或信息消息（通常是限流）
                if 'Information' in data:
                    info_msg = data['Information']
                    if 'standard API rate limit' in info_msg or 'call frequency' in info_msg.lower():
                        # 日限额已用完，直接标记全局限流（不再重试）
                        self._av_rate_limited = True
                        print(f"    🚫 AV日限额已用完，跳过所有AV请求")
                        return None
                    print(f"    ⚠️ AV信息: {info_msg[:60]}")
                    return None

                # 成功获取数据，重置连续限流计数
                self._av_consecutive_limits = 0
                self._av_cache[cache_key] = data
                self._stats['av_calls'] += 1
                return data

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    print(f"    ❌ AV请求超时")
                    self._stats['errors'] += 1
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    print(f"    ❌ AV请求失败: {e}")
                    self._stats['errors'] += 1
        return None

    def _av_get_daily(self, symbol: str, outputsize: str = 'compact') -> Optional[dict]:
        """获取 TIME_SERIES_DAILY 数据"""
        return self._av_request({
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': outputsize,
        })

    def _av_get_crypto_daily(self, symbol: str) -> Optional[dict]:
        """获取 DIGITAL_CURRENCY_DAILY 数据"""
        return self._av_request({
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': symbol,
            'market': 'USD',
        })

    def _av_get_fx_daily(self, from_sym: str, to_sym: str) -> Optional[dict]:
        """获取 FX_DAILY 数据"""
        return self._av_request({
            'function': 'FX_DAILY',
            'from_symbol': from_sym,
            'to_symbol': to_sym,
            'outputsize': 'compact',
        })

    def _av_get_global_quote(self, symbol: str) -> Optional[dict]:
        """获取 GLOBAL_QUOTE (最新价)"""
        return self._av_request({
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
        })

    def _av_get_overview(self, symbol: str) -> Optional[dict]:
        """获取 OVERVIEW (公司基本面)"""
        return self._av_request({
            'function': 'OVERVIEW',
            'symbol': symbol,
        })

    # ─── Alpha Vantage → pandas DataFrame 转换 ───────────

    def _av_daily_to_df(self, data: dict, ticker: str) -> Any:
        """将AV TIME_SERIES_DAILY响应转为与yfinance兼容的pandas DataFrame"""
        import pandas as pd
        import numpy as np

        ts_key = 'Time Series (Daily)'
        if ts_key not in data:
            return None

        ts = data[ts_key]
        rows = []
        for date_str, vals in ts.items():
            rows.append({
                'Date': pd.Timestamp(date_str),
                'Open': float(vals.get('1. open', 0)),
                'High': float(vals.get('2. high', 0)),
                'Low': float(vals.get('3. low', 0)),
                'Close': float(vals.get('4. close', 0)),
                'Volume': int(float(vals.get('5. volume', 0))),
            })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        return df

    def _av_crypto_to_df(self, data: dict, ticker: str) -> Any:
        """将AV DIGITAL_CURRENCY_DAILY响应转为pandas DataFrame"""
        import pandas as pd

        ts_key = 'Time Series (Digital Currency Daily)'
        if ts_key not in data:
            return None

        ts = data[ts_key]
        rows = []
        for date_str, vals in ts.items():
            # AV加密货币字段名可能因版本不同而变化:
            # 旧版: '4. close'  新版: '4a. close (USD)'
            close_val = vals.get('4a. close (USD)') or vals.get('4. close') or 0
            open_val = vals.get('1a. open (USD)') or vals.get('1. open') or 0
            high_val = vals.get('2a. high (USD)') or vals.get('2. high') or 0
            low_val = vals.get('3a. low (USD)') or vals.get('3. low') or 0
            vol_val = vals.get('5. volume') or 0
            rows.append({
                'Date': pd.Timestamp(date_str),
                'Open': float(open_val),
                'High': float(high_val),
                'Low': float(low_val),
                'Close': float(close_val),
                'Volume': float(vol_val),
            })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        return df

    def _av_fx_to_df(self, data: dict, ticker: str) -> Any:
        """将AV FX_DAILY响应转为pandas DataFrame"""
        import pandas as pd

        ts_key = 'Time Series FX (Daily)'
        if ts_key not in data:
            return None

        ts = data[ts_key]
        rows = []
        for date_str, vals in ts.items():
            close = float(vals.get('4. close', 0))
            rows.append({
                'Date': pd.Timestamp(date_str),
                'Open': float(vals.get('1. open', 0)),
                'High': float(vals.get('2. high', 0)),
                'Low': float(vals.get('3. low', 0)),
                'Close': close,
                'Volume': 0,
            })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        return df

    # ─── 主要数据获取接口 ─────────────────────────────────

    def _fetch_single_ticker_av(self, ticker: str) -> Any:
        """用Alpha Vantage获取单个ticker的DataFrame"""
        # 加密货币
        if ticker in CRYPTO_MAP:
            av_symbol = CRYPTO_MAP[ticker]
            data = self._av_get_crypto_daily(av_symbol)
            if data:
                return self._av_crypto_to_df(data, ticker)
            return None

        # 汇率
        if ticker in FX_MAP:
            from_sym, to_sym = FX_MAP[ticker]
            data = self._av_get_fx_daily(from_sym, to_sym)
            if data:
                return self._av_fx_to_df(data, ticker)
            return None

        # 指数 → ETF代理
        av_symbol = ticker
        if ticker in INDEX_TO_ETF:
            etf = INDEX_TO_ETF[ticker]
            if etf is None:
                return None  # 无ETF代理
            av_symbol = etf

        # 普通股票/ETF
        data = self._av_get_daily(av_symbol)
        if data:
            return self._av_daily_to_df(data, ticker)
        return None

    def download_prices(self, tickers: str, period: str = "3mo",
                        interval: str = "1d", max_retries: int = 3) -> Any:
        """
        统一的价格下载接口（Alpha Vantage优先 → yfinance降级）

        兼容yfinance的调用格式，返回pandas DataFrame:
        - 单ticker: 返回带Date索引的DataFrame (Open/High/Low/Close/Volume)
        - 多ticker: 返回MultiIndex DataFrame
        """
        import pandas as pd

        ticker_list = sorted(tickers.strip().split())
        batch_key = f"{'|'.join(ticker_list)}|{period}|{interval}"

        # 精确匹配缓存
        if batch_key in self._batch_cache:
            self._stats['av_cache_hits'] += 1
            return self._batch_cache[batch_key]

        # 子集缓存命中
        ticker_set = set(ticker_list)
        for cached_key, cached_data in self._batch_cache.items():
            cached_parts = cached_key.rsplit('|', 2)
            if len(cached_parts) == 3 and cached_parts[1] == period and cached_parts[2] == interval:
                cached_tickers = set(cached_parts[0].split('|'))
                if ticker_set.issubset(cached_tickers):
                    try:
                        if isinstance(cached_data.columns, pd.MultiIndex):
                            available = set(cached_data.columns.get_level_values(1).unique())
                            found = ticker_set & available
                            if found:
                                if len(ticker_list) == 1:
                                    t = ticker_list[0]
                                    if t in available:
                                        subset = cached_data.xs(t, level=1, axis=1)
                                        self._batch_cache[batch_key] = subset
                                        self._stats['av_cache_hits'] += 1
                                        return subset
                                else:
                                    subset = cached_data.loc[:, cached_data.columns.get_level_values(1).isin(found)]
                                    if not subset.empty:
                                        self._batch_cache[batch_key] = subset
                                        self._stats['av_cache_hits'] += 1
                                        return subset
                        else:
                            if len(ticker_list) == 1:
                                self._stats['av_cache_hits'] += 1
                                return cached_data
                    except Exception:
                        pass

        # 单独ticker直接缓存查找
        if len(ticker_list) == 1:
            single_key = f"{ticker_list[0]}|single"
            if single_key in self._batch_cache:
                self._stats['av_cache_hits'] += 1
                return self._batch_cache[single_key]

        # ════ Alpha Vantage 获取（主数据源）════
        # 根据period计算需要多少天数据
        period_days = self._period_to_days(period)
        all_dfs = {}
        av_failed_tickers = []

        for ticker in ticker_list:
            # 检查单ticker缓存（preload或之前的请求可能已缓存）
            single_key = f"{ticker}|single"
            if single_key in self._batch_cache:
                df = self._batch_cache[single_key]
                if df is not None and len(df) > 0:
                    all_dfs[ticker] = df
                    self._stats['av_cache_hits'] += 1
                    continue

            # 跳过无法通过AV获取的ticker
            if ticker in INDEX_TO_ETF and INDEX_TO_ETF[ticker] is None:
                av_failed_tickers.append(ticker)
                continue

            # AV已限流时，直接跳到yfinance降级
            if self._av_rate_limited:
                av_failed_tickers.append(ticker)
                continue

            df = self._fetch_single_ticker_av(ticker)
            if df is not None and not df.empty:
                # 按period截取
                if period_days > 0 and len(df) > period_days:
                    df = df.iloc[-period_days:]
                all_dfs[ticker] = df
                self._batch_cache[single_key] = df
            else:
                av_failed_tickers.append(ticker)

        # AV失败的ticker尝试yfinance降级（限流时批量降级更高效）
        still_failed = list(av_failed_tickers)
        if av_failed_tickers:
            yf_result = self._yfinance_fallback(av_failed_tickers, period, interval)
            if yf_result is not None:
                for t in av_failed_tickers:
                    yf_closes = self.get_closes(yf_result, t)
                    if yf_closes is not None:
                        # 从yfinance结果中提取单ticker的DF
                        try:
                            if isinstance(yf_result.columns, pd.MultiIndex):
                                if t in yf_result.columns.get_level_values(1):
                                    single_df = yf_result.xs(t, level=1, axis=1)
                                    all_dfs[t] = single_df
                                    self._batch_cache[f"{t}|single"] = single_df
                                    still_failed.remove(t) if t in still_failed else None
                            else:
                                all_dfs[t] = yf_result
                                self._batch_cache[f"{t}|single"] = yf_result
                                still_failed.remove(t) if t in still_failed else None
                        except Exception:
                            pass

        # 第三层降级：AkShare美股数据（当AV和yfinance都失败时）
        if still_failed:
            ak_results = self._akshare_us_fallback(still_failed, period)
            for t, df in ak_results.items():
                if df is not None and not df.empty:
                    all_dfs[t] = df
                    self._batch_cache[f"{t}|single"] = df

        if not all_dfs:
            return None

        # 组装结果
        if len(all_dfs) == 1:
            ticker = list(all_dfs.keys())[0]
            result = all_dfs[ticker]
        else:
            # 多ticker → MultiIndex DataFrame（与yfinance格式兼容）
            result = self._merge_to_multiindex(all_dfs)

        if result is not None and not result.empty:
            self._batch_cache[batch_key] = result
        return result

    def _merge_to_multiindex(self, dfs: Dict[str, Any]) -> Any:
        """将多个单ticker DataFrame合并为MultiIndex格式（兼容yfinance）"""
        import pandas as pd

        if not dfs:
            return None

        panels = {}
        for ticker, df in dfs.items():
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in df.columns:
                    if col not in panels:
                        panels[col] = {}
                    panels[col][ticker] = df[col]

        if not panels:
            return None

        # 构建MultiIndex
        combined_dfs = []
        for col, ticker_series in panels.items():
            panel_df = pd.DataFrame(ticker_series)
            panel_df.columns = pd.MultiIndex.from_product([[col], panel_df.columns])
            combined_dfs.append(panel_df)

        if combined_dfs:
            result = pd.concat(combined_dfs, axis=1)
            result.sort_index(inplace=True)
            return result
        return None

    def _period_to_days(self, period: str) -> int:
        """将yfinance风格的period转为天数"""
        period = period.lower().strip()
        if period.endswith('d'):
            return int(period[:-1])
        elif period.endswith('mo'):
            return int(period[:-2]) * 22  # 交易日
        elif period.endswith('y'):
            return int(period[:-1]) * 252
        return 66  # 默认3个月

    def _yfinance_fallback(self, tickers: list, period: str, interval: str) -> Any:
        """yfinance降级获取数据（含可用性短路）"""
        # 已探测到yfinance不可用时直接跳过
        if self._yf_available is False:
            return None
        try:
            import yfinance as yf
            ticker_str = ' '.join(tickers)
            self._rate_limit('yfinance', YFINANCE_BATCH_DELAY)

            data = yf.download(tickers=ticker_str, period=period, interval=interval,
                               progress=False, threads=True, timeout=10)
            if data is not None and not data.empty:
                self._stats['yf_downloads'] += 1
                if self._yf_available is None:
                    self._yf_available = True
                return data
            else:
                # 返回空结果也视为不可用
                if self._yf_available is None:
                    self._yf_available = False
                return None
        except Exception as e:
            print(f"    ⚠️ yfinance降级失败: {str(e)[:60]}")
            self._stats['errors'] += 1
            if self._yf_available is None:
                self._yf_available = False
        return None

    # ─── AkShare 美股降级层（第三层降级）────────────────────

    def _akshare_us_fallback(self, tickers: list, period: str = "3mo") -> Dict[str, Any]:
        """AkShare获取美股历史价格数据（当AV和yfinance都失败时的第三层降级）
        返回: {ticker: DataFrame} 字典，DataFrame包含 Open/High/Low/Close/Volume 列
        """
        import pandas as pd
        results = {}
        period_days = self._period_to_days(period)
        if period_days <= 0:
            period_days = 90  # 默认3个月

        for ticker in tickers:
            # 指数ticker → 通过ETF代理获取（用原始指数ticker作为key存储）
            if ticker.startswith('^'):
                etf = INDEX_TO_ETF.get(ticker)
                if not etf:
                    continue
                etf_code = self._get_akshare_us_code(etf)
                if not etf_code:
                    continue
                try:
                    import akshare as ak
                    self._rate_limit('akshare_us', 0.3)
                    df = ak.stock_us_hist(symbol=etf_code, period="daily", adjust="qfq")
                    if df is not None and len(df) > 0:
                        col_map = {'日期': 'Date', '开盘': 'Open', '收盘': 'Close',
                                   '最高': 'High', '最低': 'Low', '成交量': 'Volume'}
                        df = df.rename(columns=col_map)
                        df['Date'] = pd.to_datetime(df['Date'])
                        df = df.set_index('Date').sort_index()
                        keep_cols = [c for c in ['Open', 'High', 'Low', 'Close', 'Volume'] if c in df.columns]
                        df = df[keep_cols]
                        if period_days > 0 and len(df) > period_days:
                            df = df.iloc[-period_days:]
                        results[ticker] = df  # 用原始指数ticker作为key
                        self._stats['akshare_calls'] += 1
                except Exception:
                    pass
                continue
            # 加密货币用CoinGecko降级
            if ticker in CRYPTO_MAP or ticker in FX_MAP:
                crypto_df = self._coingecko_fallback(ticker, period_days)
                if crypto_df is not None:
                    results[ticker] = crypto_df
                continue

            ak_code = self._get_akshare_us_code(ticker)
            if not ak_code:
                continue

            try:
                import akshare as ak
                self._rate_limit('akshare_us', 0.3)
                df = ak.stock_us_hist(symbol=ak_code, period="daily", adjust="qfq")
                if df is not None and len(df) > 0:
                    # 转换列名为英文标准格式
                    col_map = {'日期': 'Date', '开盘': 'Open', '收盘': 'Close',
                               '最高': 'High', '最低': 'Low', '成交量': 'Volume'}
                    df = df.rename(columns=col_map)
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date').sort_index()
                    # 只保留需要的列
                    keep_cols = [c for c in ['Open', 'High', 'Low', 'Close', 'Volume'] if c in df.columns]
                    df = df[keep_cols]
                    # 按period截取
                    if period_days > 0 and len(df) > period_days:
                        df = df.iloc[-period_days:]
                    results[ticker] = df
                    self._stats['akshare_calls'] += 1
            except Exception as e:
                # 记录失败原因帮助诊断
                if hasattr(self, '_akshare_failures'):
                    self._akshare_failures[ticker] = str(e)[:60]

        return results

    def _get_akshare_us_code(self, ticker: str) -> str:
        """将标准ticker转换为AkShare东方财富美股代码"""
        # 先查静态映射
        if ticker in AKSHARE_US_PREFIX:
            return AKSHARE_US_PREFIX[ticker]

        # 动态尝试：依次尝试 106(正股) / 105(NASDAQ) / 107(NYSE ETF) 前缀
        for prefix in ['106', '105', '107']:
            code = f"{prefix}.{ticker}"
            try:
                import akshare as ak
                df = ak.stock_us_hist(symbol=code, period="daily", adjust="qfq")
                if df is not None and len(df) > 0:
                    AKSHARE_US_PREFIX[ticker] = code  # 缓存映射
                    return code
            except Exception:
                continue
        return ''

    def _akshare_batch_preload(self, tickers: list, period: str = "3mo"):
        """AkShare批量预加载美股价格数据到缓存"""
        results = self._akshare_us_fallback(tickers, period)
        loaded = 0
        for ticker, df in results.items():
            if df is not None and not df.empty:
                self._batch_cache[f"{ticker}|single"] = df
                loaded += 1
        if loaded > 0:
            print(f"    ✅ AkShare美股降级加载: {loaded}/{len(tickers)}个ticker")
        return loaded

    # ─── CoinGecko 加密货币降级层 ────────────────────────

    # CoinGecko ID映射
    COINGECKO_MAP = {
        'BTC-USD': 'bitcoin',
        'ETH-USD': 'ethereum',
        'SOL-USD': 'solana',
        'BNB-USD': 'binancecoin',
        'ADA-USD': 'cardano',
        'DOGE-USD': 'dogecoin',
        'XRP-USD': 'ripple',
        'AVAX-USD': 'avalanche-2',
    }

    # 法币汇率映射（CoinGecko支持法币对USD）
    FX_COINGECKO_MAP = {
        'CNY=X': ('usd', 'cny'),  # USD/CNY
    }

    def _coingecko_fallback(self, ticker: str, period_days: int = 90) -> Any:
        """CoinGecko降级获取加密货币/汇率价格数据
        返回标准DataFrame（Open/High/Low/Close/Volume列）
        """
        import pandas as pd

        # 加密货币
        coin_id = self.COINGECKO_MAP.get(ticker)
        if coin_id:
            return self._coingecko_fetch_coin(coin_id, ticker, period_days)

        # 汇率（CNY=X等）
        if ticker in self.FX_COINGECKO_MAP:
            return self._coingecko_fetch_fx(ticker, period_days)

        # 也检查全局CRYPTO_MAP（兼容）
        if ticker in CRYPTO_MAP:
            coin_id = ticker.replace('-USD', '').lower()
            # 常见简写映射
            simple_map = {'btc': 'bitcoin', 'eth': 'ethereum', 'sol': 'solana'}
            coin_id = simple_map.get(coin_id, coin_id)
            return self._coingecko_fetch_coin(coin_id, ticker, period_days)

        return None

    def _coingecko_fetch_coin(self, coin_id: str, ticker: str, period_days: int) -> Any:
        """从CoinGecko获取加密货币历史价格"""
        import pandas as pd

        try:
            self._rate_limit('coingecko', 1.5)  # CoinGecko免费版限流：10-30次/分钟
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {'vs_currency': 'usd', 'days': str(period_days), 'interval': 'daily'}
            resp = self._session.get(url, params=params, timeout=15)

            if resp.status_code == 429:
                print(f"      ⚠️ CoinGecko限流，跳过{ticker}")
                return None
            if resp.status_code != 200:
                return None

            data = resp.json()
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])

            if not prices or len(prices) < 2:
                return None

            # 构建DataFrame
            rows = []
            vol_dict = {int(v[0]): v[1] for v in volumes} if volumes else {}

            for i, (ts_ms, price) in enumerate(prices):
                dt = pd.Timestamp(ts_ms, unit='ms').normalize()
                vol = vol_dict.get(int(ts_ms), 0)

                # CoinGecko只提供收盘价，用相邻价格估算OHLC
                if i > 0:
                    prev_price = prices[i-1][1]
                    open_price = prev_price
                    high_price = max(price, prev_price)
                    low_price = min(price, prev_price)
                else:
                    open_price = price
                    high_price = price
                    low_price = price

                rows.append({
                    'Date': dt,
                    'Open': float(open_price),
                    'High': float(high_price),
                    'Low': float(low_price),
                    'Close': float(price),
                    'Volume': float(vol),
                })

            df = pd.DataFrame(rows)
            # 去重日期（CoinGecko有时返回同一天多个数据点）
            df = df.drop_duplicates(subset='Date', keep='last')
            df = df.set_index('Date').sort_index()

            if not df.empty:
                self._stats['akshare_calls'] += 1  # 复用统计字段
                print(f"      ✅ CoinGecko {ticker}: {len(df)}天数据, 最新${float(df['Close'].iloc[-1]):,.0f}")
            return df

        except Exception as e:
            print(f"      ⚠️ CoinGecko {ticker} 失败: {str(e)[:60]}")
            return None

    def _coingecko_fetch_fx(self, ticker: str, period_days: int) -> Any:
        """从CoinGecko获取法币汇率（通过BTC价格间接计算）
        原理：USD/CNY = BTC价格(CNY) / BTC价格(USD)
        """
        import pandas as pd

        base_cur, quote_cur = self.FX_COINGECKO_MAP[ticker]

        try:
            self._rate_limit('coingecko', 1.5)
            # 用稳定币USDT做代理获取汇率
            url = "https://api.coingecko.com/api/v3/coins/tether/market_chart"
            params = {'vs_currency': quote_cur.lower(), 'days': str(min(period_days, 365)), 'interval': 'daily'}
            resp = self._session.get(url, params=params, timeout=15)

            if resp.status_code != 200:
                return None

            data = resp.json()
            prices = data.get('prices', [])
            if not prices or len(prices) < 2:
                return None

            rows = []
            for ts_ms, price in prices:
                dt = pd.Timestamp(ts_ms, unit='ms').normalize()
                rows.append({
                    'Date': dt,
                    'Open': float(price),
                    'High': float(price),
                    'Low': float(price),
                    'Close': float(price),
                    'Volume': 0,
                })

            df = pd.DataFrame(rows)
            df = df.drop_duplicates(subset='Date', keep='last')
            df = df.set_index('Date').sort_index()

            if not df.empty:
                print(f"      ✅ CoinGecko {ticker}: {len(df)}天汇率数据")
            return df

        except Exception as e:
            print(f"      ⚠️ CoinGecko {ticker} 汇率失败: {str(e)[:60]}")
            return None

    # ─── Ticker Info（公司基本面）─────────────────────────

    def get_ticker_info(self, ticker: str, max_retries: int = 3) -> dict:
        """获取单只股票详细信息（Alpha Vantage OVERVIEW + GLOBAL_QUOTE）"""
        if ticker in self._info_cache:
            self._stats['av_cache_hits'] += 1
            return self._info_cache[ticker]

        info = {}

        # Alpha Vantage OVERVIEW
        overview = self._av_get_overview(ticker)
        if overview and 'Symbol' in overview:
            info = {
                'shortName': overview.get('Name', ticker),
                'symbol': overview.get('Symbol', ticker),
                'sector': overview.get('Sector', ''),
                'industry': overview.get('Industry', ''),
                'marketCap': self._safe_float(overview.get('MarketCapitalization', 0)),
                'currentPrice': 0,  # 后面用GLOBAL_QUOTE补充
                'forwardPE': self._safe_float(overview.get('ForwardPE', 0)),
                'trailingPE': self._safe_float(overview.get('PERatio', 0)),
                'pegRatio': self._safe_float(overview.get('PEGRatio', 0)),
                'returnOnEquity': self._safe_float(overview.get('ReturnOnEquityTTM', 0)),
                'profitMargins': self._safe_float(overview.get('ProfitMargin', 0)),
                'operatingMargins': self._safe_float(overview.get('OperatingMarginTTM', 0)),
                'debtToEquity': self._safe_float(overview.get('DebtToEquity', 0)) if overview.get('DebtToEquity') else 0,
                'freeCashflow': 0,  # AV OVERVIEW 没有直接提供
                'netIncomeToCommon': self._safe_float(overview.get('NetIncomeTTM', 0)) if overview.get('NetIncomeTTM') else 0,
                'beta': self._safe_float(overview.get('Beta', 0)),
                'dividendYield': self._safe_float(overview.get('DividendYield', 0)),
                'regularMarketPreviousClose': self._safe_float(overview.get('PreviousClose', 0)) if overview.get('PreviousClose') else 0,
                'heldPercentInstitutions': 0,  # AV没有
                '_source': 'alpha_vantage',
            }

        # Alpha Vantage GLOBAL_QUOTE（获取最新价格）
        quote = self._av_get_global_quote(ticker)
        if quote and 'Global Quote' in quote and quote['Global Quote']:
            gq = quote['Global Quote']
            price = self._safe_float(gq.get('05. price', 0))
            prev_close = self._safe_float(gq.get('08. previous close', 0))
            change_pct_str = gq.get('10. change percent', '0%').replace('%', '')
            change_pct = self._safe_float(change_pct_str)

            if info:
                info['currentPrice'] = price
                info['regularMarketPrice'] = price
                info['regularMarketPreviousClose'] = prev_close or info.get('regularMarketPreviousClose', 0)
                info['_change_pct'] = change_pct
            else:
                # 只有GLOBAL_QUOTE成功
                info = {
                    'shortName': ticker,
                    'symbol': ticker,
                    'currentPrice': price,
                    'regularMarketPrice': price,
                    'regularMarketPreviousClose': prev_close,
                    '_change_pct': change_pct,
                    '_source': 'alpha_vantage_quote_only',
                }

        if info and len(info) > 3:
            self._info_cache[ticker] = info
            return info

        # 从缓存价格数据构建最基本info（AV限流降级策略）
        cache_info = self._build_info_from_cache(ticker)
        if cache_info:
            return cache_info

        # 降级yfinance
        yf_info = self._yfinance_get_info_fallback(ticker)
        if yf_info:
            return yf_info

        # 第三层：AkShare获取价格后构建info
        ak_results = self._akshare_us_fallback([ticker], "3mo")
        if ticker in ak_results and ak_results[ticker] is not None:
            self._batch_cache[f"{ticker}|single"] = ak_results[ticker]
            return self._build_info_from_cache(ticker)

        return {}

    # 常见ticker → 公司名映射（用于缓存降级时提供可读名称）
    TICKER_NAMES = {
        'AAPL': '苹果', 'MSFT': '微软', 'GOOGL': '谷歌', 'NVDA': '英伟达',
        'META': 'Meta', 'AMZN': '亚马逊', 'TSLA': '特斯拉', 'AVGO': '博通',
        'TSM': '台积电', 'AMD': 'AMD', 'LLY': '礼来', 'JPM': '摩根大通',
        'BRK-B': '伯克希尔', 'V': 'Visa', 'UNH': '联合健康', 'NFLX': '奈飞',
        'CRM': 'Salesforce', 'COST': 'Costco', 'XOM': '埃克森美孚',
        'NVO': '诺和诺德', 'TCEHY': '腾讯ADR', 'BABA': '阿里巴巴', 'PDD': '拼多多',
    }

    # 已知价格合理范围（用于异常检测，基于2025-2026年市价区间）
    PRICE_SANITY = {
        'AAPL': (120, 400), 'MSFT': (250, 700), 'GOOGL': (100, 400), 'NVDA': (50, 300),
        'META': (300, 900), 'AMZN': (120, 350), 'TSLA': (100, 600), 'AVGO': (80, 500),
        'TSM': (100, 500), 'AMD': (60, 300), 'LLY': (400, 1500), 'JPM': (120, 400),
        'V': (180, 450), 'UNH': (200, 750), 'NFLX': (400, 1500), 'CRM': (120, 500),
        'COST': (500, 1500), 'XOM': (60, 200), 'NVO': (30, 250),
        'TCEHY': (25, 100), 'BABA': (40, 250), 'PDD': (50, 250), 'BRK-B': (300, 700),
    }

    def _build_info_from_cache(self, ticker: str) -> dict:
        """从已缓存的价格数据构建基本ticker info（AV限流时降级用）"""
        single_key = f"{ticker}|single"
        df = self._batch_cache.get(single_key)
        if df is None or df.empty:
            return {}

        try:
            if 'Close' not in df.columns:
                return {}
            closes = df['Close'].dropna()
            if len(closes) < 2:
                return {}

            price = float(closes.iloc[-1])
            prev_close = float(closes.iloc[-2])

            # 数据异常检测：价格合理性校验
            if ticker in self.PRICE_SANITY:
                lo, hi = self.PRICE_SANITY[ticker]
                if price < lo * 0.5 or price > hi * 2:
                    # 价格严重异常，尝试用5日均价修正
                    recent = closes.iloc[-5:] if len(closes) >= 5 else closes
                    median_price = float(recent.median())
                    if lo * 0.5 <= median_price <= hi * 2:
                        price = median_price
                        prev_close = float(closes.iloc[-6]) if len(closes) >= 6 else float(closes.iloc[-2])

            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            name = self.TICKER_NAMES.get(ticker, ticker)
            info = {
                'shortName': name,
                'symbol': ticker,
                'currentPrice': price,
                'regularMarketPrice': price,
                'regularMarketPreviousClose': prev_close,
                '_change_pct': change_pct,
                '_source': 'cache_fallback',
            }
            self._info_cache[ticker] = info
            return info
        except Exception:
            return {}

    def _yfinance_get_info_fallback(self, ticker: str) -> dict:
        """yfinance降级获取ticker info（含可用性短路）"""
        if self._yf_available is False:
            return {}
        try:
            import yfinance as yf
            self._rate_limit('yfinance_info', YFINANCE_TICKER_INFO_DELAY)
            t = yf.Ticker(ticker=ticker)
            info = t.info
            if info and len(info) > 5:
                self._info_cache[ticker] = info
                if self._yf_available is None:
                    self._yf_available = True
                return info
        except Exception as e:
            if self._yf_available is None:
                self._yf_available = False
        return {}

    def _fetch_stockanalysis_fundamentals(self, ticker: str) -> dict:
        """从stockanalysis.com网页抓取基本面数据（ROE/PE/负债率等）
        作为AV和yfinance都失败时的最终降级层"""
        import urllib.request
        import re
        import ssl

        # BRK-B 在 stockanalysis 上用 brk.b
        url_ticker = ticker.lower().replace('-', '.')
        url = f"https://stockanalysis.com/stocks/{url_ticker}/financials/ratios/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            self._rate_limit('stockanalysis', 1.5)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                html = resp.read().decode('utf-8', errors='ignore')

            result = {}

            # 解析 ROE — 查找 "Return on Equity (ROE)" 后的百分比数值
            m = re.search(r'Return on Equity.*?([0-9.-]+)%', html, re.DOTALL)
            if m:
                result['returnOnEquity'] = float(m.group(1)) / 100

            # 解析 PE Ratio
            m = re.search(r'PE Ratio.*?([0-9.,]+)', html, re.DOTALL)
            if m:
                result['forwardPE'] = float(m.group(1).replace(',', ''))

            # 解析 Debt/Equity
            m = re.search(r'Debt / Equity.*?([0-9.,]+)', html, re.DOTALL)
            if m:
                result['debtToEquity'] = float(m.group(1).replace(',', '')) * 100

            # 解析 Profit Margin (净利润率)
            # 可能在 ratios 页面没有，但 ROE/PE/Debt 已经足够
            if result.get('returnOnEquity') or result.get('forwardPE'):
                result['_source'] = 'stockanalysis_web'
                print(f"      🌐 {ticker}: ROE={result.get('returnOnEquity', 'N/A')} PE={result.get('forwardPE', 'N/A')} D/E={result.get('debtToEquity', 'N/A')}")
                return result

        except Exception as e:
            pass

        return {}

    def _enrich_cache_fallback_with_fundamentals(self, results: Dict[str, dict]) -> Dict[str, dict]:
        """对缓存降级(仅有价格)的结果，尝试从stockanalysis.com补充基本面数据"""
        need_enrich = [
            ticker for ticker, info in results.items()
            if info.get('_source') in ('cache_fallback', 'alpha_vantage_quote_only')
            and not info.get('returnOnEquity')
            and not info.get('forwardPE')
        ]
        if not need_enrich:
            return results

        print(f"    🌐 尝试从stockanalysis.com补充{len(need_enrich)}只股票基本面...")
        enriched = 0
        for ticker in need_enrich:
            fundamentals = self._fetch_stockanalysis_fundamentals(ticker)
            if fundamentals:
                info = results[ticker]
                info['returnOnEquity'] = fundamentals.get('returnOnEquity', 0)
                info['forwardPE'] = fundamentals.get('forwardPE', 0)
                info['debtToEquity'] = fundamentals.get('debtToEquity', 0)
                info['profitMargins'] = fundamentals.get('profitMargins', 0)
                info['_source'] = 'cache_plus_stockanalysis'
                results[ticker] = info
                self._info_cache[ticker] = info
                enriched += 1
        if enriched:
            print(f"    ✅ 成功补充{enriched}/{len(need_enrich)}只股票基本面数据")
        return results

    def batch_get_ticker_info(self, tickers: List[str], batch_size: int = 5) -> Dict[str, dict]:
        """分批获取多只股票信息（AV优先 → 缓存降级 → yfinance降级）"""
        results = {}
        uncached = [t for t in tickers if t not in self._info_cache]
        cached = {t: self._info_cache[t] for t in tickers if t in self._info_cache}
        results.update(cached)

        if cached:
            self._stats['av_cache_hits'] += len(cached)

        # AV全局限流时，先尝试yfinance/AkShare批量下载价格数据填充缓存
        if self._av_rate_limited and uncached:
            print(f"      ⚠️ AV限流中，尝试批量获取{len(uncached)}只股票价格...")
            self._preload_stock_prices_yf(uncached)
            # yfinance之后仍未缓存的，走AkShare
            still_need = [t for t in uncached if f"{t}|single" not in self._batch_cache]
            if still_need:
                self._akshare_batch_preload(still_need)

        for i in range(0, len(uncached), batch_size):
            batch = uncached[i:i + batch_size]
            for ticker in batch:
                info = self.get_ticker_info(ticker)
                if info:
                    results[ticker] = info
            if batch:
                print(f"      📊 Info批次 {i//batch_size + 1}: {len(batch)}只完成")

        # 最终降级层：对仅有价格的股票，从stockanalysis.com补充基本面
        results = self._enrich_cache_fallback_with_fundamentals(results)

        return results

    def _preload_stock_prices_yf(self, tickers: List[str]):
        """用yfinance批量预加载股票价格数据（供缓存降级使用）
        如果yfinance不可用（超时/限流），快速放弃让AkShare接管"""
        # 过滤掉已缓存的ticker
        need_load = [t for t in tickers if f"{t}|single" not in self._batch_cache]
        if not need_load:
            return

        # 先用一小批测试yfinance可用性（避免所有ticker都超时浪费时间）
        test_batch = need_load[:3]
        yf_data = self._yfinance_fallback(test_batch, "3mo", "1d")
        if yf_data is None:
            print(f"      ⚠️ yfinance不可用，跳过（将由AkShare接管）")
            return

        # yfinance可用，继续下载剩余
        import pandas as pd
        loaded = 0
        for t in test_batch:
            try:
                if isinstance(yf_data.columns, pd.MultiIndex):
                    if t in yf_data.columns.get_level_values(1):
                        single_df = yf_data.xs(t, level=1, axis=1)
                        self._batch_cache[f"{t}|single"] = single_df
                        loaded += 1
                else:
                    if len(test_batch) == 1:
                        self._batch_cache[f"{t}|single"] = yf_data
                        loaded += 1
            except Exception:
                pass

        remaining = [t for t in need_load[3:] if f"{t}|single" not in self._batch_cache]
        batch_size = 20
        for i in range(0, len(remaining), batch_size):
            batch = remaining[i:i + batch_size]
            yf_data = self._yfinance_fallback(batch, "3mo", "1d")
            if yf_data is not None:
                for t in batch:
                    try:
                        if isinstance(yf_data.columns, pd.MultiIndex):
                            if t in yf_data.columns.get_level_values(1):
                                single_df = yf_data.xs(t, level=1, axis=1)
                                self._batch_cache[f"{t}|single"] = single_df
                                loaded += 1
                        else:
                            if len(batch) == 1:
                                self._batch_cache[f"{t}|single"] = yf_data
                                loaded += 1
                    except Exception:
                        pass
        if loaded > 0:
            print(f"      📊 yfinance价格: {loaded}只成功")

    @staticmethod
    def _safe_float(val) -> float:
        """安全转换为float"""
        if val is None or val == '' or val == 'None' or val == '-':
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    # ─── 数据提取辅助 ─────────────────────────────────────

    def get_closes(self, data, ticker: str):
        """从批量下载结果中安全提取收盘价数组"""
        import numpy as np
        try:
            if data is None or data.empty:
                return None
            if isinstance(data.columns, __import__('pandas').MultiIndex):
                if 'Close' in data.columns.get_level_values(0):
                    level1_vals = data['Close'].columns.tolist()
                    if ticker in level1_vals:
                        arr = data['Close'][ticker].dropna().values
                    elif len(level1_vals) == 1:
                        arr = data['Close'].iloc[:, 0].dropna().values
                    else:
                        # 尝试ETF代理
                        etf = INDEX_TO_ETF.get(ticker)
                        if etf and etf in level1_vals:
                            arr = data['Close'][etf].dropna().values
                        else:
                            return None
                else:
                    return None
            else:
                if 'Close' in data.columns:
                    arr = data['Close'].dropna().values
                else:
                    return None
            return arr if len(arr) > 0 else None
        except Exception:
            return None

    def get_volumes(self, data, ticker: str):
        """从批量下载结果中安全提取成交量数组"""
        import numpy as np
        try:
            if data is None or data.empty:
                return None
            if isinstance(data.columns, __import__('pandas').MultiIndex):
                if 'Volume' in data.columns.get_level_values(0):
                    if ticker in data['Volume'].columns:
                        arr = data['Volume'][ticker].dropna().values
                        return arr if len(arr) > 0 else None
                    etf = INDEX_TO_ETF.get(ticker)
                    if etf and etf in data['Volume'].columns:
                        arr = data['Volume'][etf].dropna().values
                        return arr if len(arr) > 0 else None
            else:
                if 'Volume' in data.columns:
                    arr = data['Volume'].dropna().values
                    return arr if len(arr) > 0 else None
            return None
        except Exception:
            return None

    # ─── 预加载（一次性批量下载，跨Skill共享）─────────────

    def preload_all(self, period: str = "3mo"):
        """
        预加载所有常用ticker数据（Alpha Vantage优先）

        策略:
        - 对于AV支持的ticker逐个获取（带缓存）
        - AV不支持的（如指数^VIX9D等）走yfinance降级
        - 子集缓存让后续Skill请求直接从缓存提取
        """
        print("  📡 预加载全局市场数据（Alpha Vantage优先）...")
        t0 = time.time()

        # 收集所有需要的ticker（按组优先级排序，确保核心ticker先加载）
        # 优先级：market_etf > indices > crypto > macro_bonds > china_etf > commodities > credit
        priority_order = ['market_etf', 'indices', 'crypto', 'macro_bonds', 'china_etf', 'commodities', 'credit']
        all_tickers_ordered = []
        seen = set()
        for group in priority_order:
            if group in self._preload_groups:
                for t in self._preload_groups[group].split():
                    if t not in seen:
                        all_tickers_ordered.append(t)
                        seen.add(t)

        # 分类（保持优先级顺序）
        av_tickers = []   # AV可获取
        yf_tickers = []   # 需要yfinance

        for t in all_tickers_ordered:
            if t in CRYPTO_MAP or t in FX_MAP:
                av_tickers.append(t)
            elif t in INDEX_TO_ETF:
                etf = INDEX_TO_ETF[t]
                if etf:
                    av_tickers.append(t)
                else:
                    yf_tickers.append(t)
            elif t.startswith('^'):
                yf_tickers.append(t)
            else:
                av_tickers.append(t)

        print(f"    AV: {len(av_tickers)}个ticker | yfinance降级: {len(yf_tickers)}个")

        # AV批量获取
        loaded = 0
        for i, ticker in enumerate(av_tickers):
            single_key = f"{ticker}|single"
            if single_key in self._batch_cache:
                loaded += 1
                continue

            # AV已限流，将剩余ticker转入yfinance降级列表
            if self._av_rate_limited:
                yf_tickers.append(ticker)
                continue

            df = self._fetch_single_ticker_av(ticker)
            if df is not None and not df.empty:
                self._batch_cache[single_key] = df
                loaded += 1
            else:
                # AV获取失败，加入yfinance降级列表
                yf_tickers.append(ticker)
            if (i + 1) % 10 == 0:
                print(f"    📡 AV进度: {i+1}/{len(av_tickers)} ({loaded}成功)")

        print(f"    ✅ AV加载: {loaded}/{len(av_tickers)}个ticker"
              + (f" | {len(yf_tickers)}个转yfinance降级" if yf_tickers else ""))

        # yfinance降级获取（先用小批测试可用性，失败则跳过全部由AkShare接管）
        if yf_tickers:
            yf_tickers = list(set(yf_tickers))
            yf_loaded = 0

            # 先测试yfinance可用性（用3个ticker探测）
            test_batch = yf_tickers[:3]
            test_result = self._yfinance_fallback(test_batch, period, "1d")
            yf_available = test_result is not None and not test_result.empty

            if yf_available:
                import pandas as pd
                # 处理测试批结果
                for t in test_batch:
                    try:
                        if isinstance(test_result.columns, pd.MultiIndex):
                            if t in test_result.columns.get_level_values(1):
                                single_df = test_result.xs(t, level=1, axis=1)
                                self._batch_cache[f"{t}|single"] = single_df
                                yf_loaded += 1
                        else:
                            if len(test_batch) == 1:
                                self._batch_cache[f"{t}|single"] = test_result
                                yf_loaded += 1
                    except Exception:
                        pass

                # 下载剩余
                remaining = yf_tickers[3:]
                batch_size = 15
                for batch_start in range(0, len(remaining), batch_size):
                    batch = remaining[batch_start:batch_start + batch_size]
                    yf_data = self._yfinance_fallback(batch, period, "1d")
                    if yf_data is not None:
                        for t in batch:
                            try:
                                if isinstance(yf_data.columns, pd.MultiIndex):
                                    if t in yf_data.columns.get_level_values(1):
                                        single_df = yf_data.xs(t, level=1, axis=1)
                                        self._batch_cache[f"{t}|single"] = single_df
                                        yf_loaded += 1
                                else:
                                    if len(batch) == 1:
                                        self._batch_cache[f"{t}|single"] = yf_data
                                        yf_loaded += 1
                            except Exception:
                                pass
                print(f"    ✅ yfinance降级加载: {yf_loaded}/{len(yf_tickers)}个ticker")
            else:
                print(f"    ⚠️ yfinance不可用（超时/限流），跳过{len(yf_tickers)}个ticker → AkShare接管")
            loaded += yf_loaded

        # 第三层降级：AkShare美股 + CoinGecko加密货币（当AV和yfinance都失败时）
        still_missing = [t for t in all_tickers_ordered
                         if f"{t}|single" not in self._batch_cache
                         and not t.startswith('^')]
        if still_missing:
            # 分离：美股走AkShare，加密货币/汇率走CoinGecko
            ak_candidates = [t for t in still_missing if t not in CRYPTO_MAP and t not in FX_MAP]
            crypto_candidates = [t for t in still_missing if t in CRYPTO_MAP or t in FX_MAP]

            if ak_candidates:
                print(f"    📡 AkShare第三层降级: 尝试获取{len(ak_candidates)}个ticker...")
                ak_loaded = self._akshare_batch_preload(ak_candidates, period)
                loaded += ak_loaded

            if crypto_candidates:
                print(f"    📡 CoinGecko第三层降级: 尝试获取{len(crypto_candidates)}个加密/汇率ticker...")
                period_days = self._period_to_days(period)
                cg_loaded = 0
                for t in crypto_candidates:
                    df = self._coingecko_fallback(t, period_days)
                    if df is not None and not df.empty:
                        self._batch_cache[f"{t}|single"] = df
                        cg_loaded += 1
                if cg_loaded > 0:
                    print(f"    ✅ CoinGecko加载: {cg_loaded}/{len(crypto_candidates)}个ticker")
                loaded += cg_loaded

        # 构建分组缓存（让 download_prices 子集命中更高效）
        for group_name, group_tickers_str in self._preload_groups.items():
            group_tickers = group_tickers_str.split()
            group_dfs = {}
            for t in group_tickers:
                single_key = f"{t}|single"
                if single_key in self._batch_cache:
                    group_dfs[t] = self._batch_cache[single_key]
            if len(group_dfs) >= 2:
                merged = self._merge_to_multiindex(group_dfs)
                if merged is not None:
                    group_batch_key = f"{'|'.join(sorted(group_dfs.keys()))}|{period}|1d"
                    self._batch_cache[group_batch_key] = merged

        elapsed = time.time() - t0
        print(f"  📡 预加载完成 ({elapsed:.1f}秒) | "
              f"AV调用{self._stats['av_calls']}次 | "
              f"缓存命中{self._stats['av_cache_hits']}次")
        return loaded > 0

    # ─── FRED 宏观数据层 ────────────────────────────────

    def fetch_fred_series(self, series_id: str, observation_start: str = None,
                          limit: int = 10) -> Optional[List[Dict]]:
        """从FRED获取单个时间序列的最新数据"""
        if not FRED_API_KEY:
            return None

        fred_cache_key = f"{series_id}|{observation_start or ''}|{limit}"
        if fred_cache_key in self._fred_cache:
            return self._fred_cache[fred_cache_key]

        self._rate_limit('fred', FRED_CALL_DELAY)

        try:
            from fredapi import Fred
            fred = Fred(api_key=FRED_API_KEY)

            if observation_start:
                data = fred.get_series(series_id, observation_start=observation_start)
            else:
                start = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                data = fred.get_series(series_id, observation_start=start)

            if data is not None and not data.empty:
                result = []
                for date, value in data.dropna().items():
                    result.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'value': float(value)
                    })
                result = result[-limit:] if len(result) > limit else result
                self._fred_cache[fred_cache_key] = result
                self._stats['fred_calls'] += 1
                return result

        except ImportError:
            print("    ⚠️ fredapi未安装 (pip install fredapi)")
        except Exception as e:
            print(f"    ⚠️ FRED [{series_id}] 获取失败: {e}")
            self._stats['errors'] += 1
        return None

    def fetch_fred_latest(self, series_id: str) -> Optional[float]:
        """获取FRED序列的最新值"""
        data = self.fetch_fred_series(series_id, limit=1)
        if data and len(data) > 0:
            return data[-1]['value']
        return None

    def fetch_macro_data(self) -> MacroData:
        """获取完整宏观经济数据包（FRED优先）"""
        if self._macro_data is not None:
            return self._macro_data

        macro = MacroData(last_updated=datetime.now().strftime('%Y-%m-%d %H:%M'))

        if FRED_API_KEY:
            print("    📊 从FRED获取宏观数据...")
            macro.fed_funds_rate = self.fetch_fred_latest('FEDFUNDS')
            macro.us10y_yield = self.fetch_fred_latest('DGS10')
            macro.us2y_yield = self.fetch_fred_latest('DGS2')
            macro.us2s10s_spread = self.fetch_fred_latest('T10Y2Y')
            macro.us3m10s_spread = self.fetch_fred_latest('T10Y3M')
            macro.hy_spread = self.fetch_fred_latest('BAMLH0A0HYM2')
            macro.cpi_yoy = self.fetch_fred_latest('CORESTICKM159SFRBATL')

            pce_hist = self.fetch_fred_series('PCEPILFE', limit=15)
            if pce_hist and len(pce_hist) >= 13:
                pce_now = pce_hist[-1]['value']
                pce_yr_ago = pce_hist[-13]['value']
                if pce_yr_ago > 0:
                    macro.core_pce = (pce_now - pce_yr_ago) / pce_yr_ago * 100
            elif pce_hist and len(pce_hist) >= 2:
                macro.core_pce = macro.cpi_yoy

            macro.unemployment = self.fetch_fred_latest('UNRATE')
            macro.initial_claims = self.fetch_fred_latest('ICSA')
            macro.gdp_growth = self.fetch_fred_latest('A191RL1Q225SBEA')
            macro.fed_balance_sheet = self.fetch_fred_latest('WALCL')
            macro.tga_balance = self.fetch_fred_latest('WTREGEN')
            macro.on_rrp = self.fetch_fred_latest('RRPONTSYD')

            if all(v is not None for v in [macro.fed_balance_sheet, macro.tga_balance, macro.on_rrp]):
                # WALCL (百万美元) / 1000 → 十亿美元
                # WTREGEN (百万美元) / 1000 → 十亿美元
                # RRPONTSYD (十亿美元) → 已是十亿美元
                walcl_b = macro.fed_balance_sheet / 1000
                tga_b = macro.tga_balance / 1000
                rrp_b = macro.on_rrp
                macro.net_liquidity = walcl_b - tga_b - rrp_b

            macro.m2_supply = self.fetch_fred_latest('M2SL')
            macro.mortgage_rate_30y = self.fetch_fred_latest('MORTGAGE30US')
            macro.sofr = self.fetch_fred_latest('SOFR')
            macro.dxy_index = self.fetch_fred_latest('DTWEXBGS')

            macro.source = "FRED"

            fields = [macro.fed_funds_rate, macro.us10y_yield, macro.us2y_yield,
                      macro.us2s10s_spread, macro.hy_spread, macro.cpi_yoy,
                      macro.unemployment, macro.fed_balance_sheet, macro.net_liquidity]
            success = sum(1 for f in fields if f is not None)
            print(f"    ✅ FRED宏观数据: {success}/{len(fields)}项获取成功")
            macro.raw_data = {k: v for k, v in self._fred_cache.items()}
        else:
            print("    ⚠️ FRED_API_KEY未设置")
            macro.source = "unavailable"

        self._macro_data = macro
        return macro

    def fetch_fred_series_history(self, series_id: str, years: int = 1) -> Optional[List[Dict]]:
        """获取FRED序列的历史数据"""
        start = (datetime.now() - timedelta(days=years * 365)).strftime('%Y-%m-%d')
        return self.fetch_fred_series(series_id, observation_start=start, limit=500)

    def get_net_liquidity_trend(self, weeks: int = 12) -> Optional[List[Dict]]:
        """获取净流动性趋势"""
        if not FRED_API_KEY:
            return None

        start = (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
        walcl = self.fetch_fred_series('WALCL', observation_start=start, limit=50)
        tga = self.fetch_fred_series('WTREGEN', observation_start=start, limit=50)
        rrp = self.fetch_fred_series('RRPONTSYD', observation_start=start, limit=50)

        if not walcl:
            return None

        trend = []
        tga_dict = {d['date']: d['value'] for d in (tga or [])}
        rrp_dict = {d['date']: d['value'] for d in (rrp or [])}

        for w in walcl:
            date = w['date']
            w_val = w['value']
            t_val = tga_dict.get(date) or self._find_nearest(tga_dict, date)
            r_val = rrp_dict.get(date) or self._find_nearest(rrp_dict, date)
            if t_val is not None and r_val is not None:
                w_b = w_val / 1000
                t_b = t_val / 1000
                r_b = r_val
                net = w_b - t_b - r_b
                trend.append({'date': date, 'walcl': w_b, 'tga': t_b,
                              'rrp': r_b, 'net_liquidity': net})
        return trend if trend else None

    def _find_nearest(self, data_dict: dict, target_date: str) -> Optional[float]:
        """在日期字典中找最接近的值"""
        if not data_dict:
            return None
        target = datetime.strptime(target_date, '%Y-%m-%d')
        best_date, best_diff = None, timedelta(days=999)
        for d_str in data_dict:
            d = datetime.strptime(d_str, '%Y-%m-%d')
            diff = abs(d - target)
            if diff < best_diff:
                best_diff = diff
                best_date = d_str
        return data_dict.get(best_date) if best_diff <= timedelta(days=7) else None

    # ─── AkShare 中国市场数据层 ────────────────────────

    def fetch_china_market_data(self) -> ChinaMarketData:
        """获取中国市场数据"""
        if self._china_data is not None:
            return self._china_data

        china = ChinaMarketData(last_updated=datetime.now().strftime('%Y-%m-%d %H:%M'))

        try:
            import akshare as ak
            print("    🇨🇳 从AkShare获取中国市场数据...")

            try:
                self._rate_limit('akshare', AKSHARE_CALL_DELAY)
                flow_df = ak.stock_hsgt_fund_flow_summary_em()
                if flow_df is not None and not flow_df.empty:
                    north_rows = flow_df[flow_df['资金方向'] == '北向']
                    if not north_rows.empty:
                        china.northbound_flow = float(north_rows['成交净买额'].sum())
                        print(f"      北向资金: {china.northbound_flow:+.1f}亿元")
                    south_rows = flow_df[flow_df['资金方向'] == '南向']
                    if not south_rows.empty:
                        china.southbound_flow = float(south_rows['成交净买额'].sum())
                        print(f"      南向资金: {china.southbound_flow:+.1f}亿元")
                    china.raw_data['hsgt_flow'] = flow_df.to_dict('records')
            except Exception as e:
                print(f"      ⚠️ 沪深港通资金获取失败: {e}")

            try:
                self._rate_limit('akshare', AKSHARE_CALL_DELAY)
                ah_df = ak.stock_zh_ah_spot_em()
                if ah_df is not None and not ah_df.empty and '溢价' in ah_df.columns:
                    avg_premium = ah_df['溢价'].mean()
                    china.ah_premium_index = 100 + avg_premium
                    print(f"      AH溢价指数(估算): {china.ah_premium_index:.1f}")
            except Exception as e:
                print(f"      ⚠️ AH溢价指数获取失败: {e}")

            try:
                self._rate_limit('akshare', AKSHARE_CALL_DELAY)
                margin_df = ak.stock_margin_account_info()
                if margin_df is not None and not margin_df.empty:
                    latest = margin_df.iloc[-1]
                    for col in margin_df.columns:
                        if '余额' in str(col) and '融资' in str(col):
                            china.margin_balance = float(latest[col])
                            print(f"      两融余额: {china.margin_balance:,.0f}亿元")
                            break
            except Exception as e:
                print(f"      ⚠️ 融资融券数据获取失败: {e}")

            try:
                self._rate_limit('akshare', AKSHARE_CALL_DELAY)
                shibor_df = ak.macro_china_shibor_all()
                if shibor_df is not None and not shibor_df.empty:
                    latest = shibor_df.iloc[-1]
                    for col in shibor_df.columns:
                        if '隔夜' in str(col) or 'O/N' in str(col):
                            china.shibor_overnight = float(latest[col])
                            print(f"      SHIBOR隔夜: {china.shibor_overnight:.4f}%")
                            break
            except Exception as e:
                print(f"      ⚠️ SHIBOR获取失败: {e}")

            # 人民币汇率 — 优先用AV
            try:
                fx_data = self._av_get_fx_daily('USD', 'CNY')
                if fx_data:
                    fx_ts = fx_data.get('Time Series FX (Daily)', {})
                    if fx_ts:
                        latest_date = list(fx_ts.keys())[0]
                        china.cny_usd = float(fx_ts[latest_date]['4. close'])
                        print(f"      美元/人民币(AV): {china.cny_usd:.4f}")
            except Exception:
                pass

            china.source = "AkShare"
            success = sum(1 for v in [china.northbound_flow, china.southbound_flow,
                                       china.ah_premium_index, china.margin_balance,
                                       china.shibor_overnight, china.cny_usd] if v is not None)
            print(f"    ✅ AkShare中国市场: {success}/6项获取成功")

        except ImportError:
            print("    ⚠️ akshare未安装 (pip install akshare)")
            china.source = "unavailable"
        except Exception as e:
            print(f"    ⚠️ AkShare异常: {e}")
            china.source = "unavailable"

        self._china_data = china
        return china

    # ─── Alpha Vantage 技术指标 ──────────────────────

    def fetch_av_indicator(self, symbol: str, indicator: str = 'RSI',
                           interval: str = 'daily', time_period: int = 14) -> Optional[List[Dict]]:
        """从Alpha Vantage获取技术指标"""
        if not ALPHA_VANTAGE_KEY:
            return None

        cache_key = f"av_{symbol}_{indicator}_{time_period}"
        if cache_key in self._av_cache:
            return self._av_cache[cache_key]

        data = self._av_request({
            'function': indicator,
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': 'close',
        })

        if data:
            result_key = [k for k in data.keys() if 'Technical Analysis' in k]
            if result_key:
                ts = data[result_key[0]]
                result = []
                for date, values in list(ts.items())[:30]:
                    point = {'date': date}
                    point.update({k: float(v) for k, v in values.items()})
                    result.append(point)
                result.reverse()
                self._av_cache[cache_key] = result
                return result
        return None

    # ─── 全球指数实时数据（AkShare东方财富）────────────────

    def get_global_index_spot(self) -> dict:
        """
        获取全球主要指数的真实点位数据（非ETF代理）
        返回: {ticker: {'price': float, 'change': float, 'prev_close': float}} 
        """
        if hasattr(self, '_global_index_cache') and self._global_index_cache:
            return self._global_index_cache

        result = {}
        try:
            import akshare as ak
            self._rate_limit('akshare', AKSHARE_CALL_DELAY)
            df = ak.index_global_spot_em()
            if df is not None and not df.empty:
                # 建立 AkShare代码 → 行数据 的映射
                ak_data = {}
                for _, row in df.iterrows():
                    ak_data[str(row['代码'])] = row

                # 将 ticker → AkShare代码 映射转换为结果
                for ticker, ak_code in INDEX_TO_AKSHARE_GLOBAL.items():
                    if ak_code in ak_data:
                        row = ak_data[ak_code]
                        price = float(row['最新价']) if row['最新价'] else 0
                        prev_close = float(row['昨收价']) if row['昨收价'] else 0
                        change_pct = float(row['涨跌幅']) if row['涨跌幅'] else 0
                        if price > 0:
                            result[ticker] = {
                                'price': price,
                                'change': change_pct,
                                'prev_close': prev_close,
                            }

                print(f"    ✅ AkShare全球指数实时数据: {len(result)}/{len(INDEX_TO_AKSHARE_GLOBAL)}个")
        except Exception as e:
            print(f"    ⚠️ AkShare全球指数获取失败: {e}")

        # ═══ 补充: 通过Google Finance获取AkShare缺失的指数（罗素2000、VIX）═══
        for ticker, (gf_symbol, gf_exchange) in INDEX_GOOGLE_FINANCE_FALLBACK.items():
            if ticker not in result:
                try:
                    gf_data = self._fetch_google_finance_index(gf_symbol, gf_exchange)
                    if gf_data:
                        result[ticker] = gf_data
                        print(f"    ✅ Google Finance补充: {gf_symbol} = {gf_data['price']:.2f} ({gf_data['change']:+.2f}%)")
                except Exception as e:
                    print(f"    ⚠️ Google Finance获取{gf_symbol}失败: {e}")

        self._global_index_cache = result
        return result

    def _fetch_google_finance_index(self, symbol: str, exchange: str) -> dict:
        """
        从Google Finance网页抓取指数真实价格
        返回: {'price': float, 'change': float, 'prev_close': float} 或 None
        """
        import urllib.request
        import re
        import ssl

        url = f"https://www.google.com/finance/quote/{symbol}:{exchange}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        price = None
        prev_close = None

        # 方法1: data-last-price 属性（最可靠）
        m = re.search(r'data-last-price="([0-9.,]+)"', html)
        if m:
            price = float(m.group(1).replace(',', ''))

        # 方法2: YMlKec fxKbKc class（页面显示价格）
        if price is None:
            m = re.search(r'class="YMlKec fxKbKc"[^>]*>([0-9,]+\.?\d*)', html)
            if m:
                price = float(m.group(1).replace(',', ''))

        # 方法3: Previous close
        m = re.search(r'Previous close.*?([0-9,]+\.\d+)', html, re.DOTALL)
        if m:
            prev_close = float(m.group(1).replace(',', ''))

        if price and price > 0:
            change_pct = 0
            if prev_close and prev_close > 0:
                change_pct = (price - prev_close) / prev_close * 100
            else:
                prev_close = price
            return {
                'price': price,
                'change': change_pct,
                'prev_close': prev_close,
            }
        return None

    # ─── 新浪外汇/商品实时数据 ────────────────────────────

    # 新浪外汇/商品符号映射
    # ETF ticker → (新浪符号, 显示名称, 价格单位, 数据类型)
    # 数据类型: 'fx' = 外汇(字段格式不同于 'futures')
    SINA_REALTIME_MAP = {
        'UUP': ('DINIW', '美元指数', '', 'fx'),
        'FXY': ('USDJPY', '美元/日元', '', 'fx'),
        'FXE': ('EURUSD', '欧元/美元', '', 'fx'),
        'GLD': ('hf_GC', '黄金', '美元/盎司', 'futures'),
        'SLV': ('hf_SI', '白银', '美元/盎司', 'futures'),
    }

    def fetch_sina_realtime(self, symbols: list) -> dict:
        """
        从新浪财经获取外汇/商品实时数据
        Args:
            symbols: 新浪符号列表，如 ['DINIW', 'USDJPY', 'hf_GC']
        Returns:
            {symbol: {'price': float, 'change': float, 'prev_close': float, 'name': str}}
        """
        import urllib.request
        import ssl
        import re

        if not symbols:
            return {}

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        result = {}
        try:
            symbols_str = ','.join(symbols)
            url = f'https://hq.sinajs.cn/list={symbols_str}'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Referer': 'https://finance.sina.com.cn/',
            })
            resp = urllib.request.urlopen(req, context=ctx, timeout=10).read().decode('gbk', errors='ignore')

            for line in resp.strip().split('\n'):
                m = re.match(r'var hq_str_(\w+)="(.*)";', line)
                if not m or not m.group(2):
                    continue
                key = m.group(1)
                parts = m.group(2).split(',')

                try:
                    if key.startswith('hf_'):
                        # 外盘期货格式: 最新价,,卖1,买1,最高,最低,时间,前结算,开盘,...,日期,品名
                        price = float(parts[0])
                        prev_close = float(parts[7]) if parts[7] else 0
                        name = parts[13] if len(parts) > 13 else key
                    else:
                        # 外汇格式: 时间,买入价,卖出价,最新价,成交量,昨收,最高,最低,...,名称,日期
                        price = float(parts[1]) if parts[1] and float(parts[1]) > 0 else float(parts[3])
                        prev_close = float(parts[5]) if parts[5] else 0
                        name = parts[9] if len(parts) > 9 else key

                    if price > 0:
                        change_pct = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0
                        result[key] = {
                            'price': price,
                            'change': round(change_pct, 2),
                            'prev_close': prev_close,
                            'name': name,
                        }
                except (ValueError, IndexError):
                    continue

        except Exception as e:
            print(f"    ⚠️ 新浪外汇/商品数据获取失败: {e}")

        return result

    def get_forex_commodity_realtime(self) -> dict:
        """
        获取外汇和商品真实价格（替代ETF代理）
        Returns:
            {etf_ticker: {'price': float, 'change': float, 'name': str, 'unit': str}}
            例如: {'UUP': {'price': 97.61, 'change': -0.09, 'name': '美元指数', 'unit': ''}}
        """
        if hasattr(self, '_forex_commodity_cache') and self._forex_commodity_cache:
            return self._forex_commodity_cache

        # 收集需要查询的新浪符号
        sina_symbols = []
        etf_to_sina = {}
        for etf_ticker, (sina_sym, display_name, unit, dtype) in self.SINA_REALTIME_MAP.items():
            sina_symbols.append(sina_sym)
            etf_to_sina[etf_ticker] = (sina_sym, display_name, unit)

        sina_data = self.fetch_sina_realtime(sina_symbols)

        result = {}
        for etf_ticker, (sina_sym, display_name, unit) in etf_to_sina.items():
            if sina_sym in sina_data:
                d = sina_data[sina_sym]
                result[etf_ticker] = {
                    'price': d['price'],
                    'change': d['change'],
                    'name': display_name,
                    'unit': unit,
                }

        if result:
            print(f"    ✅ 新浪外汇/商品实时数据: {len(result)}/{len(self.SINA_REALTIME_MAP)}个")
        self._forex_commodity_cache = result
        return result

    # ─── Fear & Greed Index ────────────────────────────

    def get_fear_greed_index(self) -> dict:
        """获取恐惧贪婪指数"""
        if self._fear_greed is not None:
            return self._fear_greed

        try:
            import fear_and_greed
            fgi = fear_and_greed.get()
            self._fear_greed = {
                'value': fgi.value,
                'description': fgi.description,
            }
        except Exception as e:
            print(f"    ⚠️ 恐惧贪婪指数获取失败: {e}")
            self._fear_greed = {'value': 50, 'description': 'Neutral (获取失败)'}

        return self._fear_greed

    # ─── 技术指标计算（本地）─────────────────────────────

    @staticmethod
    def calc_rsi(prices, period: int = 14) -> float:
        import numpy as np
        if prices is None or len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def calc_ma(prices, period: int) -> float:
        if prices is None or len(prices) < period:
            return float(prices[-1]) if prices is not None and len(prices) > 0 else 0
        return sum(float(p) for p in prices[-period:]) / period

    @staticmethod
    def calc_ema(prices, period: int) -> float:
        import numpy as np
        if prices is None or len(prices) < period:
            return float(prices[-1]) if prices is not None and len(prices) > 0 else 0
        multiplier = 2 / (period + 1)
        ema = float(prices[0])
        for p in prices[1:]:
            ema = (float(p) - ema) * multiplier + ema
        return ema

    @staticmethod
    def calc_macd(prices, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        if prices is None or len(prices) < slow + signal:
            return 0.0, 0.0, 0.0

        def _ema(data, period):
            multiplier = 2 / (period + 1)
            ema_val = float(data[0])
            ema_arr = [ema_val]
            for p in data[1:]:
                ema_val = (float(p) - ema_val) * multiplier + ema_val
                ema_arr.append(ema_val)
            return ema_arr

        ema_fast = _ema(prices, fast)
        ema_slow = _ema(prices, slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = _ema(macd_line, signal)
        histogram = macd_line[-1] - signal_line[-1]
        return macd_line[-1], signal_line[-1], histogram

    @staticmethod
    def weekly_change(closes) -> float:
        if closes is None or len(closes) < 5:
            return 0.0
        curr, prev = float(closes[-1]), float(closes[-5])
        return (curr - prev) / prev if prev != 0 else 0.0

    @staticmethod
    def daily_change(closes) -> float:
        if closes is None or len(closes) < 2:
            return 0.0
        curr, prev = float(closes[-1]), float(closes[-2])
        return (curr - prev) / prev if prev != 0 else 0.0

    @staticmethod
    def monthly_change(closes) -> float:
        if closes is None or len(closes) < 21:
            return 0.0
        curr, prev = float(closes[-1]), float(closes[-21])
        return (curr - prev) / prev if prev != 0 else 0.0

    @staticmethod
    def calc_volatility(prices, period: int = 20) -> float:
        import numpy as np
        if prices is None or len(prices) < period + 1:
            return 0.0
        returns = np.diff(np.log(prices[-period-1:].astype(float)))
        return float(np.std(returns) * np.sqrt(252))

    @staticmethod
    def calc_drawdown(prices) -> float:
        import numpy as np
        if prices is None or len(prices) < 2:
            return 0.0
        peak = float(np.max(prices))
        current = float(prices[-1])
        return (current - peak) / peak if peak > 0 else 0.0

    # ─── 统计与诊断 ─────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            **self._stats,
            'av_rate_limited': self._av_rate_limited,
            'av_consecutive_limits': self._av_consecutive_limits,
            'cache_size': {
                'batch_cache': len(self._batch_cache),
                'info_cache': len(self._info_cache),
                'fred_cache': len(self._fred_cache),
                'av_cache': len(self._av_cache),
            },
            'data_sources': {
                'alpha_vantage': 'rate_limited' if self._av_rate_limited else ('active' if ALPHA_VANTAGE_KEY else 'inactive'),
                'fred': 'active' if FRED_API_KEY else 'inactive',
                'akshare': self._check_akshare_available(),
                'yfinance': 'unavailable' if self._yf_available is False else ('active' if self._yf_available else 'fallback'),
                'coingecko': 'active',
                'fear_and_greed': 'active',
            }
        }

    def _check_akshare_available(self) -> str:
        try:
            import akshare
            return 'active'
        except ImportError:
            return 'not_installed'

    def print_diagnostics(self):
        stats = self.get_stats()
        print(f"\n{'='*50}")
        print(f"  📊 数据源诊断报告")
        print(f"{'='*50}")
        print(f"  Alpha Vantage调用: {stats['av_calls']}次 | 缓存命中: {stats['av_cache_hits']}次")
        if stats.get('av_rate_limited'):
            print(f"  🚫 AV全局限流已触发（连续{stats['av_consecutive_limits']}次）")
        print(f"  yfinance降级调用: {stats['yf_downloads']}次")
        print(f"  FRED调用: {stats['fred_calls']}次")
        print(f"  AkShare调用: {stats['akshare_calls']}次")
        print(f"  错误总数: {stats['errors']}次")
        print(f"  缓存大小: batch={stats['cache_size']['batch_cache']} "
              f"info={stats['cache_size']['info_cache']} "
              f"fred={stats['cache_size']['fred_cache']} "
              f"av={stats['cache_size']['av_cache']}")
        print(f"\n  数据源状态:")
        for src, status in stats['data_sources'].items():
            icon = '✅' if status == 'active' else ('⚠️' if status in ('not_installed', 'fallback', 'rate_limited') else '❌')
            print(f"    {icon} {src}: {status}")
        print(f"{'='*50}\n")


# ═══════════════════════════════════════════════════════════
# 便捷函数（兼容旧版代码）
# ═══════════════════════════════════════════════════════════

_global_manager: Optional[DataSourceManager] = None

def get_manager(config: dict = None) -> DataSourceManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = DataSourceManager(config)
    return _global_manager

def reset_manager():
    global _global_manager
    _global_manager = None


# ═══════════════════════════════════════════════════════════
# 自测入口
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🔍 数据源管理器 v2.0 自测（Alpha Vantage优先）...\n")

    dm = DataSourceManager()

    print("--- 测试1: AV日线下载 ---")
    data = dm.download_prices("AAPL MSFT", period="5d")
    if data is not None:
        closes = dm.get_closes(data, 'AAPL')
        print(f"  AAPL最新收盘: ${float(closes[-1]):,.2f}" if closes is not None else "  AAPL: 无数据")
    else:
        print("  ❌ 下载失败")

    print("\n--- 测试2: 缓存验证 ---")
    data2 = dm.download_prices("AAPL MSFT", period="5d")
    print(f"  缓存命中: {dm._stats['av_cache_hits']}")

    print("\n--- 测试3: 加密货币 ---")
    btc_data = dm.download_prices("BTC-USD", period="5d")
    if btc_data is not None:
        btc_closes = dm.get_closes(btc_data, 'BTC-USD')
        print(f"  BTC最新: ${float(btc_closes[-1]):,.0f}" if btc_closes is not None else "  BTC: 无数据")

    print("\n--- 测试4: 公司基本面 ---")
    info = dm.get_ticker_info('AAPL')
    if info:
        print(f"  {info.get('shortName', '?')} PE={info.get('forwardPE', '?')} ROE={info.get('returnOnEquity', '?')}")

    print("\n--- 测试5: FRED宏观数据 ---")
    if FRED_API_KEY:
        macro = dm.fetch_macro_data()
        print(f"  联邦基金利率: {macro.fed_funds_rate}")
        print(f"  10年期收益率: {macro.us10y_yield}")

    print("\n--- 测试6: Fear & Greed ---")
    fgi = dm.get_fear_greed_index()
    print(f"  F&G: {fgi['value']} ({fgi['description']})")

    dm.print_diagnostics()
    print("✅ 自测完成")
