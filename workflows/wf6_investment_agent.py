#!/usr/bin/env python3
"""
工作流 6：投资Agent - 每日分析结论与预测 v3.3
频率：每日（交易日，北京时间早8点运行）
架构：知识库(6层) → 数据源(多源聚合) → 新闻采集 → 决策框架(10 Skill) → 综合分析 → PDF报告

数据源架构 v3.3:
  主数据源: Alpha Vantage (全球行情/ETF/加密/汇率/基本面)
  宏观数据: FRED API (利率/CPI/GDP/就业/净流动性/收益率曲线)
  中国市场: AkShare (北向/南向资金/AH溢价/融资融券/SHIBOR/人民币中间价)
  降级备用: yfinance (AV不支持的指数ticker)
  情绪数据: CNN Fear & Greed Index
  实时新闻: Google News RSS (10个Skill领域 × 中英双语 × 24小时)

10-Skill 全球资本市场分析体系:
  Skill 1:  公司估值与质量评级（ROE/DCF/PE/PEG/DuPont/护城河）
  Skill 2:  加密货币周期与抄底模型（BTC/ETH/SOL, MVRV）
  Skill 3:  全球市场情绪监控（F&G/VIX结构/Put-Call/SPY RSI/QQQ RSI）
  Skill 4:  宏观流动性与央行监控（净流动性/TLT/IEF/DXY/MOVE/日元/HYG/LQD）
  Skill 5:  全球市场联动与资金流向（跨市场相关性/板块轮动/货币三角）
  Skill 6:  信贷市场与私募信用监控（HY利差/IG利差/BKLN/KRE/CLO）
  Skill 7:  贵金属与大宗商品周期（金/银/铜/油/农产品/金铜比）
  Skill 8:  收益率曲线与利率分析（2s10s/3m10s/期限溢价/利率冲击）
  Skill 9:  波动率微观结构（VIX期限结构/VVIX/Skew/Gamma/0DTE）
  Skill 10: 港股与A股专项分析（恒指估值/AH溢价/CNY/政策周期/资金流向）
"""
import sys
import os
import json
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from mbb_report_engine import *
from data_source_manager import DataSourceManager, get_manager, reset_manager, INDEX_TO_ETF, INDEX_TO_AKSHARE_GLOBAL
from news_fetcher import get_all_news, format_news_for_skill, format_news_for_markdown, NewsItem

# ═══════════════════════════════════════════════════════════
# 常量与配置
# ═══════════════════════════════════════════════════════════

DATE = datetime.now().strftime("%Y%m%d")
DATE_DISPLAY = datetime.now().strftime("%Y.%m.%d")
DATA_DIR = os.path.join(os.path.dirname(__file__), "investment_agent_data")
SKILL_DELAY = 3  # Skill间API限流间隔(秒)

# 投资Agent专属配色
INV_GREEN = HexColor('#06d6a0')   # 看多/加仓
INV_RED = HexColor('#ef476f')     # 看空/减仓
INV_BLUE = HexColor('#118ab2')    # 中性/持有
INV_GOLD = HexColor('#ffd166')    # 关注/预警
INV_PURPLE = HexColor('#7b2cbf')  # BTC/加密
INV_TEAL = HexColor('#2ec4b6')    # 全球市场
INV_ORANGE = HexColor('#f4845f')  # 信贷
INV_PINK = HexColor('#e07a5f')    # 商品
INV_DARK = HexColor('#3d405b')    # 收益率曲线
INV_CYAN = HexColor('#81b29a')    # 港股A股

# 10个Skill的对应颜色
SKILL_COLORS = [INV_BLUE, INV_PURPLE, INV_GOLD, INV_GREEN, INV_TEAL,
                INV_ORANGE, INV_PINK, INV_DARK, INV_RED, INV_CYAN]


# ═══════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class Signal:
    """单个信号"""
    name: str
    value: float
    threshold: float
    triggered: bool
    detail: str = ""

@dataclass
class SkillResult:
    """单个Skill的分析结果"""
    skill_name: str
    rating: str
    score: float          # -1.0(极度看空) ~ 1.0(极度看多)
    signals: list = field(default_factory=list)
    action: str = "持有"
    detail: str = ""
    confidence: float = 0.5
    error: str = ""
    news_highlights: list = field(default_factory=list)  # 关联的新闻 [NewsItem]

@dataclass
class StockRating:
    """单只股票的价值投资评级"""
    ticker: str
    name: str
    rating: str           # A/B/C/D
    roe: float = 0.0
    debt_ratio: float = 0.0
    fcf_ratio: float = 0.0
    moat_count: int = 0
    price: float = 0.0
    change_pct: float = 0.0
    pe_ratio: float = 0.0
    market_cap: float = 0.0
    detail: str = ""

@dataclass
class DailyAnalysis:
    """每日综合分析结果"""
    date: str = ""
    overnight_summary: dict = field(default_factory=dict)
    skill_results: list = field(default_factory=list)
    stock_ratings: list = field(default_factory=list)
    overall_rating: str = "中性"
    overall_score: float = 0.0
    overall_action: str = "持有"
    key_warnings: list = field(default_factory=list)
    upcoming_events: list = field(default_factory=list)
    pattern_matches: list = field(default_factory=list)
    prediction: str = ""
    cross_validation: list = field(default_factory=list)
    contradictions: list = field(default_factory=list)
    risk_exposures: list = field(default_factory=list)
    investment_narrative: str = ""
    news_themes: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════
# 知识库加载（v2.0 三层知识库架构）
# ═══════════════════════════════════════════════════════════

def _load_json(filename):
    """通用JSON加载"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_config():
    """加载投资配置"""
    return _load_json("investment_config.json")

def load_important_dates():
    """加载重要日期日历"""
    return _load_json("important_dates.json")

def load_historical_patterns():
    """加载历史模式库"""
    return _load_json("historical_patterns.json")

def load_historical_database():
    """加载历史数据库（宏观数据源、Top50公司、重大事件复盘）"""
    try:
        return _load_json("historical_database.json")
    except FileNotFoundError:
        return {}

def load_indicators_and_news():
    """加载重要指标与新闻（媒体渠道、Twitter账号、宏观指标体系、行业追踪）"""
    try:
        return _load_json("indicators_and_news.json")
    except FileNotFoundError:
        return {}

def load_personal_experience():
    """加载个人经验库（决策记录、复盘、个人规则）"""
    try:
        return _load_json("personal_experience.json")
    except FileNotFoundError:
        return {}


# ═══════════════════════════════════════════════════════════
# 数据采集层（通过DataSourceManager统一管理）
# ═══════════════════════════════════════════════════════════

def safe_download(tickers, period="1mo", interval="1d", max_retries=3):
    """兼容旧版: 通过全局DataSourceManager下载"""
    dm = get_manager()
    return dm.download_prices(tickers, period=period, interval=interval, max_retries=max_retries)

def get_ticker_info(ticker, max_retries=3):
    """兼容旧版: 通过全局DataSourceManager获取ticker info"""
    dm = get_manager()
    return dm.get_ticker_info(ticker, max_retries=max_retries)

def get_fear_greed_index():
    """兼容旧版: 通过全局DataSourceManager获取F&G"""
    dm = get_manager()
    return dm.get_fear_greed_index()

def calc_rsi(prices, period=14):
    """兼容旧版: 调用DataSourceManager的RSI计算"""
    return DataSourceManager.calc_rsi(prices, period)

def calc_ma(prices, period):
    """兼容旧版: 调用DataSourceManager的MA计算"""
    return DataSourceManager.calc_ma(prices, period)

def _get_closes(data, ticker):
    """兼容旧版: 通过全局DataSourceManager提取收盘价"""
    dm = get_manager()
    return dm.get_closes(data, ticker)

def _weekly_change(closes):
    """兼容旧版: 调用DataSourceManager的周变化率"""
    return DataSourceManager.weekly_change(closes)

def _daily_change(closes):
    """兼容旧版: 调用DataSourceManager的日变化率"""
    return DataSourceManager.daily_change(closes)


# ═══════════════════════════════════════════════════════════
# Skill 1: 公司估值与质量评级
# ═══════════════════════════════════════════════════════════

def skill1_value_investing(config):
    """
    公司估值与质量评级 v3.0
    ROE/PE/PEG/DuPont分析/负债率/自由现金流/7项护城河因子
    """
    print("  📊 Skill 1: 公司估值与质量评级...")
    result = SkillResult(skill_name="公司估值与质量评级", rating="", score=0.0)
    stock_ratings = []

    thresholds = config.get('skill1_value_investing', {})
    roe_min = thresholds.get('roe_threshold', 0.15)
    roe_premium = thresholds.get('roe_premium', 0.25)
    debt_max = thresholds.get('debt_ratio_max', 0.50)
    fcf_min = thresholds.get('fcf_to_income_min', 0.80)
    val_cfg = thresholds.get('valuation_metrics', {})
    dupont_cfg = thresholds.get('dupont_analysis', {})

    watchlist = config.get('watchlist', {}).get('us_stocks', [])

    # 批量获取所有股票info（反限流: 分批+随机延迟）
    all_tickers = [stock['ticker'] for stock in watchlist]
    dm = get_manager()
    if dm:
        print(f"    📊 批量获取{len(all_tickers)}只股票info...")
        all_info = dm.batch_get_ticker_info(all_tickers, batch_size=5)
    else:
        all_info = {}

    for idx, stock in enumerate(watchlist):
        ticker = stock['ticker']
        name = stock['name']
        try:
            info = all_info.get(ticker, {})
            if not info:
                stock_ratings.append(StockRating(ticker=ticker, name=name, rating="N/A", detail="数据获取失败"))
                continue

            # 检查info来源：缓存降级(cache_fallback/akshare)仅有价格，无基本面
            info_source = info.get('_source', '')
            has_fundamentals = info_source not in ('cache_fallback', 'alpha_vantage_quote_only') and (
                info.get('returnOnEquity', 0) or info.get('forwardPE', 0) or info.get('profitMargins', 0)
            )

            roe = info.get('returnOnEquity', 0) or 0
            debt_ratio = (info.get('debtToEquity', 0) or 0) / 100
            fcf = info.get('freeCashflow', 0) or 0
            net_income = info.get('netIncomeToCommon', 0) or 0
            fcf_ratio = (fcf / net_income) if net_income > 0 else 0
            price = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0) or 0
            prev_close = info.get('regularMarketPreviousClose', 0) or 0

            # 数据质量检测：价格异常校验
            from data_source_manager import DataSourceManager
            if ticker in DataSourceManager.PRICE_SANITY and price > 0:
                lo, hi = DataSourceManager.PRICE_SANITY[ticker]
                if price < lo * 0.5 or price > hi * 2:
                    # 价格严重异常（如NFLX $78.7），标记并跳过
                    stock_ratings.append(StockRating(
                        ticker=ticker, name=name, rating="N/A",
                        detail=f"价格异常 ${price:,.1f} (预期范围${lo}-${hi})，数据源错误"
                    ))
                    continue

            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 and price > 0 else 0
            market_cap = info.get('marketCap', 0) or 0
            profit_margin = info.get('profitMargins', 0) or 0
            forward_pe = info.get('forwardPE', 0) or 0
            peg = info.get('pegRatio', 0) or 0

            # 缓存降级模式：只有价格数据，无法评估基本面
            if not has_fundamentals:
                if price <= 0:
                    # 连价格都没有，标记为无数据
                    stock_ratings.append(StockRating(ticker=ticker, name=name, rating="N/A", detail="数据获取失败"))
                    continue
                rating = "C"  # 给予中性评级而非D（数据不足不等于差）
                detail = f"价格=${price:,.1f} 变化={change_pct:+.1f}% (基本面数据待补充)"
                stock_ratings.append(StockRating(
                    ticker=ticker, name=name, rating=rating,
                    price=price, change_pct=change_pct,
                    detail=detail
                ))
                continue

            # 7项护城河评估
            moat_count = 0
            if market_cap > 100e9:
                moat_count += 1  # 规模经济
            if profit_margin > 0.20:
                moat_count += 1  # 品牌/定价权
            if roe > 0.20:
                moat_count += 1  # 竞争优势
            if info.get('sector') == 'Technology':
                moat_count += 1  # 网络效应/转换成本
            if info.get('operatingMargins', 0) and info['operatingMargins'] > 0.30:
                moat_count += 1  # 高运营利润率=成本优势
            if market_cap > 500e9:
                moat_count += 1  # 超大规模壁垒
            if info.get('heldPercentInstitutions', 0) and info['heldPercentInstitutions'] > 0.70:
                moat_count += 1  # 机构高度认可

            # 综合评分（含估值因子）
            score_items = 0
            if roe > roe_premium:
                score_items += 2
            elif roe > roe_min:
                score_items += 1
            if debt_ratio < 0.30:
                score_items += 2
            elif debt_ratio < debt_max:
                score_items += 1
            if fcf_ratio > 1.2:
                score_items += 2
            elif fcf_ratio > fcf_min:
                score_items += 1
            if moat_count >= 4:
                score_items += 2
            elif moat_count >= 2:
                score_items += 1
            # PE/PEG估值奖惩
            pe_cheap = val_cfg.get('forward_pe_cheap', 15)
            pe_exp = val_cfg.get('forward_pe_expensive', 35)
            if 0 < forward_pe < pe_cheap:
                score_items += 1
            elif forward_pe > pe_exp:
                score_items -= 1
            if 0 < peg < val_cfg.get('peg_cheap', 1.0):
                score_items += 1
            elif peg > val_cfg.get('peg_expensive', 2.0):
                score_items -= 1
            # DuPont杠杆预警
            equity_mult = (1 / (1 - debt_ratio)) if debt_ratio < 1 else 5
            if equity_mult > dupont_cfg.get('leverage_warning', 3.0):
                score_items -= 1

            if score_items >= 8:
                rating = "A"
            elif score_items >= 5:
                rating = "B"
            elif score_items >= 3:
                rating = "C"
            else:
                rating = "D"

            detail = f"ROE={roe:.1%} PE={forward_pe:.1f} PEG={peg:.1f} 负债={debt_ratio:.1%} 护城河={moat_count}项"
            stock_ratings.append(StockRating(
                ticker=ticker, name=name, rating=rating,
                roe=roe, debt_ratio=debt_ratio, fcf_ratio=fcf_ratio,
                moat_count=moat_count, price=price, change_pct=change_pct,
                pe_ratio=forward_pe, market_cap=market_cap, detail=detail
            ))
        except Exception as e:
            stock_ratings.append(StockRating(ticker=ticker, name=name, rating="N/A", detail=f"分析失败: {str(e)[:50]}"))

    rated = [s for s in stock_ratings if s.rating in ('A', 'B', 'C', 'D')]
    a_count = sum(1 for s in rated if s.rating == 'A')
    b_count = sum(1 for s in rated if s.rating == 'B')
    c_count = sum(1 for s in rated if s.rating == 'C')
    d_count = sum(1 for s in rated if s.rating == 'D')
    na_count = sum(1 for s in stock_ratings if s.rating == 'N/A')

    if a_count >= 3:
        result.rating = "优质持仓"
        result.score = 0.6
        result.action = "持有/加仓A级标的"
    elif b_count >= 5:
        result.rating = "持仓健康"
        result.score = 0.3
        result.action = "持有"
    elif d_count >= 3:
        result.rating = "持仓偏弱"
        result.score = -0.3
        result.action = "关注D级标的，考虑置换"
    else:
        result.rating = "持仓中性"
        result.score = 0.0
        result.action = "持有"

    # 构建详情：包含完整ABCD评级分布
    a_tickers = ', '.join(s.ticker for s in rated if s.rating == 'A')
    b_tickers = ', '.join(s.ticker for s in rated if s.rating == 'B')
    d_tickers = ', '.join(s.ticker for s in rated if s.rating == 'D')
    detail_parts = [f"共分析{len(rated)}只"]
    if a_count > 0:
        detail_parts.append(f"A级={a_count}({a_tickers})")
    else:
        detail_parts.append(f"A级={a_count}")
    if b_count > 0:
        detail_parts.append(f"B级={b_count}({b_tickers})")
    else:
        detail_parts.append(f"B级={b_count}")
    detail_parts.append(f"C级={c_count}")
    if d_count > 0:
        detail_parts.append(f"D级={d_count}({d_tickers})")
    else:
        detail_parts.append(f"D级={d_count}")
    if na_count > 0:
        detail_parts.append(f"无数据={na_count}")
    result.detail = ' | '.join(detail_parts)
    result.confidence = min(len(rated) / len(watchlist), 1.0) if watchlist else 0.5
    print(f"    → {result.rating} ({result.detail})")
    return result, stock_ratings


# ═══════════════════════════════════════════════════════════
# Skill 2: 加密货币周期与抄底模型
# ═══════════════════════════════════════════════════════════

def skill2_crypto_signal(config):
    """
    加密货币周期与抄底模型 v3.0
    BTC+ETH多资产、RSI/MA200/F&G/成交量/ETH-BTC比率/超买检测
    """
    print("  ₿ Skill 2: 加密货币周期与抄底模型...")
    result = SkillResult(skill_name="加密货币周期与抄底", rating="", score=0.0)

    skill_cfg = config.get('skill2_crypto_signal', {})
    btc_cfg = skill_cfg.get('btc', skill_cfg)  # 兼容旧格式
    eth_cfg = skill_cfg.get('eth', {})
    signals_triggered = 0
    signals_list = []

    try:
        import numpy as np
        # BTC + ETH 数据
        crypto_data = safe_download("BTC-USD ETH-USD", period="1y", interval="1d")
        if crypto_data is None or crypto_data.empty:
            result.error = "加密货币数据获取失败"
            result.rating = "数据不可用"
            return result

        btc_closes = _get_closes(crypto_data, 'BTC-USD')
        eth_closes = _get_closes(crypto_data, 'ETH-USD')

        if btc_closes is None or len(btc_closes) < 20:
            result.error = "BTC数据不足"
            result.rating = "数据不可用"
            return result

        btc_price = float(btc_closes[-1])

        # BTC RSI(14) 超卖
        rsi = calc_rsi(btc_closes, 14)
        rsi_th = btc_cfg.get('rsi_oversold', 30)
        sig = Signal("BTC RSI超卖", rsi, rsi_th, rsi < rsi_th, f"RSI={rsi:.1f}，阈值<{rsi_th}")
        signals_list.append(sig)
        if sig.triggered:
            signals_triggered += 1

        # BTC MA200偏离
        ma200 = calc_ma(btc_closes.tolist(), 200)
        dev = (btc_price - ma200) / ma200 if ma200 > 0 else 0
        dev_th = btc_cfg.get('ma200_deviation_threshold', -0.20)
        sig = Signal("BTC MA200偏离", dev, dev_th, dev < dev_th, f"偏离={dev:.1%}，阈值<{dev_th:.0%}")
        signals_list.append(sig)
        if sig.triggered:
            signals_triggered += 1

        # 成交量萎缩
        if 'Volume' in crypto_data.columns.get_level_values(0):
            try:
                vols = crypto_data['Volume']['BTC-USD'].dropna().values
                if len(vols) >= 20:
                    vol_5d = float(np.mean(vols[-5:]))
                    vol_20d = float(np.mean(vols[-20:]))
                    vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1
                    vol_th = btc_cfg.get('volume_shrink_threshold', 0.5)
                    sig = Signal("BTC成交量萎缩", vol_ratio, vol_th, vol_ratio < vol_th, f"5d/20d量比={vol_ratio:.2f}")
                    signals_list.append(sig)
                    if sig.triggered:
                        signals_triggered += 1
            except Exception:
                pass

        # 恐惧贪婪指数
        fgi = get_fear_greed_index()
        fgi_value = fgi['value']
        fgi_th = btc_cfg.get('fear_greed_extreme_fear', 25)
        sig = Signal("恐惧贪婪指数", fgi_value, fgi_th, fgi_value < fgi_th, f"F&G={fgi_value:.0f}({fgi['description']})")
        signals_list.append(sig)
        if sig.triggered:
            signals_triggered += 1

        # 接近年内低点
        yearly_low = float(np.min(btc_closes[-252:])) if len(btc_closes) >= 252 else float(np.min(btc_closes))
        low_dist = (btc_price - yearly_low) / yearly_low if yearly_low > 0 else 1
        low_th = btc_cfg.get('price_vs_yearly_low_threshold', 0.15)
        sig = Signal("接近年内低点", low_dist, low_th, low_dist < low_th, f"距低点={low_dist:.1%}")
        signals_list.append(sig)
        if sig.triggered:
            signals_triggered += 1

        # 周RSI(模拟)
        if len(btc_closes) >= 70:
            weekly_closes = btc_closes[::5]
            weekly_rsi = calc_rsi(weekly_closes, 14)
            w_rsi_th = btc_cfg.get('weekly_rsi_oversold', 35)
            sig = Signal("BTC周RSI超卖", weekly_rsi, w_rsi_th, weekly_rsi < w_rsi_th, f"周RSI={weekly_rsi:.1f}")
            signals_list.append(sig)
            if sig.triggered:
                signals_triggered += 1

        # ETH/BTC 比率信号
        if eth_closes is not None and len(eth_closes) > 0:
            eth_price = float(eth_closes[-1])
            eth_btc = eth_price / btc_price if btc_price > 0 else 0
            eth_floor = eth_cfg.get('eth_btc_ratio_floor', 0.03)
            sig = Signal("ETH/BTC极低", eth_btc, eth_floor, eth_btc < eth_floor, f"ETH/BTC={eth_btc:.4f}")
            signals_list.append(sig)
            if sig.triggered:
                signals_triggered += 1

        # 超买检测（反向减分）
        overbought = False
        if rsi > 80 and fgi_value > 80 and dev > 1.0:
            overbought = True
            signals_list.append(Signal("BTC超买预警", rsi, 80, True, f"RSI={rsi:.0f}+F&G={fgi_value:.0f}+偏离MA200={dev:.0%}"))

        # 评级
        result.signals = signals_list
        if overbought:
            result.rating = "超买减仓信号"
            result.score = -0.6
            result.action = "分批减仓加密仓位"
        elif signals_triggered >= 5:
            result.rating = "强烈买入信号"
            result.score = 0.9
            result.action = "重仓抄底(30%仓位)"
        elif signals_triggered >= 4:
            result.rating = "买入信号"
            result.score = 0.6
            result.action = "分批建仓(15%仓位)"
        elif signals_triggered >= 2:
            result.rating = "关注信号"
            result.score = 0.2
            result.action = "密切关注,准备资金"
        else:
            result.rating = "无信号"
            result.score = 0.0
            result.action = "观望"

        result.detail = f"BTC=${btc_price:,.0f} | RSI={rsi:.1f} | F&G={fgi_value:.0f} | 触发{signals_triggered}/{len(signals_list)}信号"
        result.confidence = 0.7
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Skill 3: 市场情绪监控
# ═══════════════════════════════════════════════════════════

def skill3_sentiment(config):
    """
    全球市场情绪监控 v3.0
    F&G + VIX结构 + SPY RSI + QQQ RSI + 5维评分
    """
    print("  🎭 Skill 3: 全球市场情绪监控...")
    result = SkillResult(skill_name="全球市场情绪监控", rating="", score=0.0)
    signals_list = []
    thresholds = config.get('skill3_sentiment', {})

    try:
        market_data = safe_download("^VIX ^VIX9D SPY QQQ", period="3mo", interval="1d")

        # 1. 恐惧贪婪指数
        fgi = get_fear_greed_index()
        fgi_value = fgi['value']
        if fgi_value >= thresholds.get('fear_greed_extreme_greed', 80):
            fgi_signal, fgi_score = "极度贪婪", -0.8
        elif fgi_value >= thresholds.get('fear_greed_greed', 60):
            fgi_signal, fgi_score = "贪婪", -0.4
        elif fgi_value >= thresholds.get('fear_greed_fear', 40):
            fgi_signal, fgi_score = "中性", 0.0
        elif fgi_value >= thresholds.get('fear_greed_extreme_fear', 20):
            fgi_signal, fgi_score = "恐慌", 0.4
        else:
            fgi_signal, fgi_score = "极度恐慌", 0.8
        signals_list.append(Signal("恐惧贪婪指数", fgi_value, 50, fgi_value < 40 or fgi_value > 60, f"F&G={fgi_value:.0f} → {fgi_signal}"))

        # 2. VIX 水平与期限结构（含VIXY降级）
        vix_score = 0.0
        vix_closes = _get_closes(market_data, '^VIX') if market_data is not None else None
        vix_proxy_mode = False
        if vix_closes is None or len(vix_closes) < 2:
            # ^VIX不可用，用VIXY ETF代理
            vixy_data = safe_download("VIXY", period="3mo", interval="1d")
            if vixy_data is not None:
                vixy_closes = _get_closes(vixy_data, 'VIXY')
                if vixy_closes is not None and len(vixy_closes) >= 5:
                    vix_closes = vixy_closes
                    vix_proxy_mode = True

        if vix_closes is not None and len(vix_closes) > 0:
            if vix_proxy_mode:
                # VIXY代理模式：用变化率估算VIX水平
                import numpy as np
                vix_5d = float(vix_closes[-5]) if len(vix_closes) >= 5 else float(vix_closes[0])
                pulse = (float(vix_closes[-1]) - vix_5d) / vix_5d if vix_5d > 0 else 0
                vix_current = 18.0
                if pulse > 0.20: vix_current = 28.0
                elif pulse > 0.10: vix_current = 22.0
                elif pulse < -0.15: vix_current = 13.0
                elif pulse < -0.05: vix_current = 16.0
            else:
                vix_current = float(vix_closes[-1])

            if vix_current > thresholds.get('vix_panic_threshold', 30):
                vix_signal, vix_score = "恐慌水平", 0.6
            elif vix_current < thresholds.get('vix_complacency_threshold', 12):
                vix_signal, vix_score = "过度自满", -0.6
            else:
                vix_signal, vix_score = "正常区间", 0.0
            proxy_tag = "(VIXY代理)" if vix_proxy_mode else ""
            signals_list.append(Signal("VIX恐慌指数", vix_current, 20, vix_current > 25 or vix_current < 13, f"VIX={vix_current:.1f}{proxy_tag} → {vix_signal}"))

            # VIX期限结构（仅在非代理模式下可用）
            if not vix_proxy_mode:
                vix9d_closes = _get_closes(market_data, '^VIX9D') if market_data is not None else None
                if vix9d_closes is not None and len(vix9d_closes) > 0:
                    vix9d_current = float(vix9d_closes[-1])
                    term_str = vix9d_current / vix_current if vix_current > 0 else 1
                    inverted = term_str > 1.1
                    signals_list.append(Signal("VIX期限结构", term_str, 1.1, inverted, f"9日/标准={term_str:.2f} {'⚠️倒挂' if inverted else '正常'}"))
                    if inverted:
                        vix_score += 0.3

        # 3. SPY RSI
        spy_score = 0.0
        spy_closes = _get_closes(market_data, 'SPY') if market_data is not None else None
        if spy_closes is not None and len(spy_closes) > 14:
            spy_rsi = calc_rsi(spy_closes, 14)
            if spy_rsi > thresholds.get('spy_rsi_overbought', 70):
                spy_signal, spy_score = "超买", -0.5
            elif spy_rsi < thresholds.get('spy_rsi_oversold', 30):
                spy_signal, spy_score = "超卖", 0.5
            else:
                spy_signal, spy_score = "中性", 0.0
            signals_list.append(Signal("SPY RSI", spy_rsi, 50, spy_rsi > 70 or spy_rsi < 30, f"RSI={spy_rsi:.1f} → {spy_signal}"))

        # 4. QQQ RSI（新增）
        qqq_score = 0.0
        qqq_closes = _get_closes(market_data, 'QQQ') if market_data is not None else None
        if qqq_closes is not None and len(qqq_closes) > 14:
            qqq_rsi = calc_rsi(qqq_closes, 14)
            if qqq_rsi > thresholds.get('qqq_rsi_overbought', 75):
                qqq_signal, qqq_score = "科技超买", -0.5
            elif qqq_rsi < thresholds.get('qqq_rsi_oversold', 25):
                qqq_signal, qqq_score = "科技超卖", 0.5
            else:
                qqq_signal, qqq_score = "科技中性", 0.0
            signals_list.append(Signal("QQQ RSI", qqq_rsi, 50, qqq_rsi > 75 or qqq_rsi < 25, f"QQQ RSI={qqq_rsi:.1f} → {qqq_signal}"))

        # 综合情绪评级（5维均值）
        components = [fgi_score, vix_score, spy_score, qqq_score]
        avg_score = sum(components) / len(components)
        result.score = avg_score
        result.signals = signals_list

        if avg_score > 0.5:
            result.rating, result.action = "极度恐慌", "满仓抄底(90%+)"
        elif avg_score > 0.2:
            result.rating, result.action = "恐慌", "加仓至80%"
        elif avg_score > -0.2:
            result.rating, result.action = "中性", "维持当前仓位"
        elif avg_score > -0.5:
            result.rating, result.action = "贪婪", "减仓至65%"
        else:
            result.rating, result.action = "极度贪婪", "减仓至50%以下"

        result.detail = f"F&G={fgi_value:.0f}({fgi_signal}) | 综合得分={avg_score:.2f}"
        result.confidence = 0.75
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Skill 4: 宏观流动性监控
# ═══════════════════════════════════════════════════════════

def skill4_liquidity(config):
    """
    宏观流动性与央行监控 v3.2
    数据源: FRED真实宏观数据(主) + Alpha Vantage ETF代理(降级)
    FRED: 净流动性/2s10s/HY利差/联邦基金利率/SOFR
    ETF代理: TLT/IEF/SHY/UUP/FXY/HYG/LQD/GLD (via Alpha Vantage)
    """
    print("  💧 Skill 4: 宏观流动性与央行监控...")
    result = SkillResult(skill_name="宏观流动性与央行监控", rating="", score=0.0)
    signals_list = []
    thresholds = config.get('skill4_macro_liquidity', config.get('skill4_liquidity', {}))
    dm = get_manager()

    try:
        # ═══ 第一层: FRED真实宏观数据 ═══
        macro = dm.fetch_macro_data()
        fred_warning = 0
        fred_available = macro.source == "FRED"

        if fred_available:
            # 净流动性趋势
            if macro.net_liquidity is not None:
                nl_trend = dm.get_net_liquidity_trend(weeks=4)
                if nl_trend and len(nl_trend) >= 2:
                    nl_now = nl_trend[-1]['net_liquidity']
                    nl_prev = nl_trend[-2]['net_liquidity']
                    nl_change = (nl_now - nl_prev) / abs(nl_prev) if nl_prev != 0 else 0
                    nl_th = thresholds.get('net_liquidity_weekly_decline_warning', -0.05)
                    triggered = nl_change < nl_th
                    signals_list.append(Signal("净流动性(WALCL-TGA-RRP)", nl_change, nl_th, triggered,
                        f"净流动性={nl_now:,.0f}B | 周变化={nl_change:+.2%}"))
                    if triggered:
                        fred_warning += 1

            # 2s10s利差
            if macro.us2s10s_spread is not None:
                inverted = macro.us2s10s_spread < 0
                signals_list.append(Signal("2s10s收益率利差(FRED)", macro.us2s10s_spread, 0, inverted,
                    f"2s10s={macro.us2s10s_spread:+.2f}% {'⚠️倒挂' if inverted else '正常'}"))
                if inverted:
                    fred_warning += 1

            # 高收益债利差
            if macro.hy_spread is not None:
                hy_th = thresholds.get('hy_spread_widening_warning', 500)
                # FRED数据单位是百分比点(如5.0=500bp)
                hy_bp = macro.hy_spread * 100  # 转为bp
                triggered = hy_bp > hy_th
                signals_list.append(Signal("高收益债利差(FRED)", hy_bp, hy_th, triggered,
                    f"HY利差={hy_bp:.0f}bp {'⚠️高风险' if triggered else ''}"))
                if triggered:
                    fred_warning += 1

            # SOFR
            if macro.sofr is not None:
                sofr_th = thresholds.get('sofr_stress_threshold', 5.50)
                triggered = macro.sofr > sofr_th
                signals_list.append(Signal("SOFR融资利率(FRED)", macro.sofr, sofr_th, triggered,
                    f"SOFR={macro.sofr:.2f}% {'⚠️资金紧张' if triggered else ''}"))
                if triggered:
                    fred_warning += 1

            # 联邦基金利率
            if macro.fed_funds_rate is not None:
                signals_list.append(Signal("联邦基金利率(FRED)", macro.fed_funds_rate, 5.0, macro.fed_funds_rate > 5.0,
                    f"Fed Funds={macro.fed_funds_rate:.2f}%"))

        # ═══ 第二层: yfinance ETF代理数据(始终获取) ═══
        data = safe_download("TLT IEF SHY UUP FXY HYG LQD GLD", period="3mo", interval="1d")
        if data is None or data.empty:
            if not fred_available:
                result.error = "流动性数据获取失败"
                result.rating = "数据不可用"
                return result

        import numpy as np
        etf_warning = 0

        def analyze_proxy(ticker, name, weekly_th, is_inverse=False):
            nonlocal etf_warning
            closes = _get_closes(data, ticker)
            if closes is None or len(closes) < 5:
                return None
            wc = _weekly_change(closes)
            triggered = wc < weekly_th if not is_inverse else wc > abs(weekly_th)
            sig = Signal(name, wc, weekly_th, triggered, f"{name}: 周变化={wc:+.2%} (当前={float(closes[-1]):.2f})")
            signals_list.append(sig)
            if triggered:
                etf_warning += 1
            return wc

        if data is not None:
            tlt_ch = analyze_proxy("TLT", "20+年美债(TLT)", thresholds.get('tlt_weekly_drop_warning', -0.03))
            analyze_proxy("IEF", "7-10年美债(IEF)", thresholds.get('lqd_weekly_drop_warning', -0.015))
            analyze_proxy("UUP", "美元指数(UUP)", thresholds.get('dxy_strength_warning', 0.02), is_inverse=True)
            analyze_proxy("FXY", "日元(FXY)", thresholds.get('yen_carry_unwind_threshold', 0.03), is_inverse=True)
            analyze_proxy("HYG", "高收益债(HYG)", thresholds.get('hyg_spread_widening_warning', -0.02))
            analyze_proxy("LQD", "投资级债(LQD)", thresholds.get('lqd_weekly_drop_warning', -0.015))
            analyze_proxy("GLD", "黄金(GLD)", thresholds.get('gold_safe_haven_signal', 0.02), is_inverse=True)
            analyze_proxy("SHY", "短债(SHY)", thresholds.get('shy_yield_spike_warning', -0.01))
        else:
            tlt_ch = None

        # ═══ 综合评级（FRED权重更高）═══
        total_warning = fred_warning * 2 + etf_warning  # FRED双倍权重
        result.signals = signals_list

        if total_warning >= 8:
            result.rating, result.score, result.action = "流动性危机", -0.9, "立即减仓至50%以下"
        elif total_warning >= 6:
            result.rating, result.score, result.action = "流动性严重收紧", -0.7, "减仓至60%"
        elif total_warning >= 4:
            result.rating, result.score, result.action = "流动性收紧", -0.5, "减仓至70%"
        elif total_warning >= 2:
            result.rating, result.score, result.action = "流动性偏紧", -0.2, "关注变化，准备减仓"
        elif total_warning <= 0:
            result.rating, result.score, result.action = "流动性充裕", 0.5, "可适度加仓"
        else:
            result.rating, result.score, result.action = "流动性中性", 0.0, "维持仓位"

        data_src = f"FRED({fred_warning}项预警)" if fred_available else "ETF代理"
        result.detail = (f"数据源: {data_src}+ETF({etf_warning}项预警) | 综合预警: {total_warning}" +
                        (f" | TLT周变化={tlt_ch:+.2%}" if tlt_ch else ""))
        result.confidence = 0.9 if fred_available else 0.7
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Skill 5: 全球市场联动与资金流向
# ═══════════════════════════════════════════════════════════

def skill5_global_markets(config):
    """
    全球市场联动与资金流向
    跨市场共振、NDX vs RUT板块轮动、货币信号
    """
    print("  🌍 Skill 5: 全球市场联动与资金流向...")
    result = SkillResult(skill_name="全球市场联动与资金流向", rating="", score=0.0)
    signals_list = []
    cfg = config.get('skill5_global_markets', {})

    try:
        tickers = cfg.get('cross_market_tickers', "^GSPC ^IXIC ^RUT ^HSI ^N225 ^FTSE ^GDAXI ^STOXX50E")
        currency_tickers = cfg.get('currency_tickers', "UUP FXY FXE")
        data = safe_download(f"{tickers} {currency_tickers}", period="3mo", interval="1d")
        if data is None or data.empty:
            result.error = "全球市场数据获取失败"
            result.rating = "数据不可用"
            return result

        import numpy as np
        # 各指数周度变化
        index_changes = {}
        for t in tickers.split():
            closes = _get_closes(data, t)
            if closes is not None:
                index_changes[t] = _weekly_change(closes)

        # 板块轮动：NDX vs RUT
        ndx_ch = index_changes.get('^IXIC', 0)
        rut_ch = index_changes.get('^RUT', 0)
        rotation_signal = ndx_ch - rut_ch
        if rotation_signal > 0.03:
            rot_text, rot_score = "成长>价值（Risk-On偏科技）", 0.2
        elif rotation_signal < -0.03:
            rot_text, rot_score = "价值>成长（风险偏好下降）", -0.2
        else:
            rot_text, rot_score = "均衡", 0.0
        signals_list.append(Signal("板块轮动NDX-RUT", rotation_signal, 0.03, abs(rotation_signal) > 0.03, f"NDX-RUT={rotation_signal:+.2%} → {rot_text}"))

        # 美股vs非美分歧
        sp_ch = index_changes.get('^GSPC', 0)
        non_us = [index_changes.get(t, 0) for t in ['^HSI', '^N225', '^FTSE', '^GDAXI', '^STOXX50E'] if t in index_changes]
        non_us_avg = np.mean(non_us) if non_us else 0
        divergence = sp_ch - non_us_avg
        div_th = cfg.get('divergence_threshold', 0.05)
        div_triggered = abs(divergence) > div_th
        signals_list.append(Signal("美股vs非美分歧", divergence, div_th, div_triggered, f"SP500-非美={divergence:+.2%}"))

        # 货币信号
        uup_closes = _get_closes(data, 'UUP')
        fxy_closes = _get_closes(data, 'FXY')
        currency_score = 0.0
        if uup_closes is not None:
            uup_wc = _weekly_change(uup_closes)
            if uup_wc > 0.02:
                currency_score -= 0.3
                signals_list.append(Signal("美元走强", uup_wc, 0.02, True, f"UUP周变化={uup_wc:+.2%} → 流动性偏紧"))
        if fxy_closes is not None:
            fxy_wc = _weekly_change(fxy_closes)
            if fxy_wc > 0.03:
                currency_score -= 0.3
                signals_list.append(Signal("日元走强(套利风险)", fxy_wc, 0.03, True, f"FXY周变化={fxy_wc:+.2%} → 套利平仓风险"))

        # 全球同步下跌检测
        neg_count = sum(1 for ch in index_changes.values() if ch < -0.02)
        if neg_count >= 5:
            signals_list.append(Signal("全球同步下跌", neg_count, 5, True, f"{neg_count}个市场周跌>2% → 系统性风险"))
            currency_score -= 0.3

        avg_score = rot_score + currency_score + (0.3 if divergence > div_th else (-0.3 if divergence < -div_th else 0))
        result.score = max(-1, min(1, avg_score))
        result.signals = signals_list

        if result.score > 0.3:
            result.rating, result.action = "全球Risk-On", "增配风险资产"
        elif result.score < -0.3:
            result.rating, result.action = "全球Risk-Off", "减配风险资产，增加防御"
        else:
            result.rating, result.action = "全球中性", "维持全球配置"

        result.detail = f"NDX-RUT={rotation_signal:+.2%} | 美股-非美={divergence:+.2%} | 周跌市场={neg_count}"
        result.confidence = 0.65
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Skill 6: 信贷市场与私募信用监控
# ═══════════════════════════════════════════════════════════

def skill6_credit(config):
    """
    信贷市场与私募信用监控
    HYG/LQD/BKLN/KRE + HYG/LQD比率 + 信用分层
    """
    print("  🏦 Skill 6: 信贷市场与私募信用监控...")
    result = SkillResult(skill_name="信贷市场与私募信用监控", rating="", score=0.0)
    signals_list = []
    cfg = config.get('skill6_credit_private', {})

    try:
        data = safe_download("HYG LQD BKLN KRE", period="3mo", interval="1d")
        if data is None or data.empty:
            result.error = "信贷数据获取失败"
            result.rating = "数据不可用"
            return result

        warning_count = 0

        hyg_closes = _get_closes(data, 'HYG')
        lqd_closes = _get_closes(data, 'LQD')
        bkln_closes = _get_closes(data, 'BKLN')
        kre_closes = _get_closes(data, 'KRE')

        # HYG 高收益债
        if hyg_closes is not None:
            hyg_wc = _weekly_change(hyg_closes)
            triggered = hyg_wc < cfg.get('hyg_spread_widening_warning', -0.02)
            signals_list.append(Signal("高收益债(HYG)", hyg_wc, -0.02, triggered, f"HYG周变化={hyg_wc:+.2%}"))
            if triggered:
                warning_count += 1

        # LQD 投资级
        if lqd_closes is not None:
            lqd_wc = _weekly_change(lqd_closes)
            triggered = lqd_wc < -0.015
            signals_list.append(Signal("投资级债(LQD)", lqd_wc, -0.015, triggered, f"LQD周变化={lqd_wc:+.2%}"))
            if triggered:
                warning_count += 1

        # HYG/LQD 比率（信用分层）
        if hyg_closes is not None and lqd_closes is not None and len(hyg_closes) >= 5 and len(lqd_closes) >= 5:
            ratio_now = float(hyg_closes[-1]) / float(lqd_closes[-1]) if float(lqd_closes[-1]) > 0 else 0
            ratio_5d = float(hyg_closes[-5]) / float(lqd_closes[-5]) if float(lqd_closes[-5]) > 0 else 0
            ratio_ch = (ratio_now - ratio_5d) / ratio_5d if ratio_5d > 0 else 0
            triggered = ratio_ch < -0.01
            signals_list.append(Signal("HYG/LQD信用分层", ratio_ch, -0.01, triggered, f"HYG/LQD比率变化={ratio_ch:+.2%}"))
            if triggered:
                warning_count += 1

        # BKLN 浮动利率贷款
        if bkln_closes is not None:
            bkln_wc = _weekly_change(bkln_closes)
            triggered = bkln_wc < cfg.get('bkln_weekly_drop_warning', -0.02)
            signals_list.append(Signal("浮动利率贷款(BKLN)", bkln_wc, -0.02, triggered, f"BKLN周变化={bkln_wc:+.2%}"))
            if triggered:
                warning_count += 1

        # KRE 区域银行
        if kre_closes is not None:
            kre_wc = _weekly_change(kre_closes)
            triggered = kre_wc < cfg.get('kre_weekly_drop_warning', -0.05)
            signals_list.append(Signal("区域银行(KRE)", kre_wc, -0.05, triggered, f"KRE周变化={kre_wc:+.2%}"))
            if triggered:
                warning_count += 1

        result.signals = signals_list
        if warning_count >= 4:
            result.rating, result.score, result.action = "信贷危机预警", -0.9, "清仓高风险信用资产"
        elif warning_count >= 3:
            result.rating, result.score, result.action = "信贷恶化", -0.6, "减持高收益债，增持国债"
        elif warning_count >= 1:
            result.rating, result.score, result.action = "信贷偏紧", -0.2, "关注信用事件"
        else:
            result.rating, result.score, result.action = "信贷稳健", 0.3, "可持有信用资产"

        result.detail = f"信贷预警: {warning_count}/{len(signals_list)}"
        result.confidence = 0.7
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Skill 7: 贵金属与大宗商品周期
# ═══════════════════════════════════════════════════════════

def skill7_commodities(config):
    """
    贵金属与大宗商品周期
    金/银/GDX/铜/油/农产品 + 金铜比 + GDX/GLD比
    """
    print("  🪙 Skill 7: 贵金属与大宗商品周期...")
    result = SkillResult(skill_name="贵金属与大宗商品周期", rating="", score=0.0)
    signals_list = []
    cfg = config.get('skill7_precious_metals_commodities', {})

    try:
        data = safe_download("GLD SLV GDX USO CPER DBA PDBC", period="3mo", interval="1d")
        if data is None or data.empty:
            result.error = "商品数据获取失败"
            result.rating = "数据不可用"
            return result

        import numpy as np
        bullish = 0
        bearish = 0

        # 黄金周涨幅（降低阈值: 1.5%即有意义）
        gld_closes = _get_closes(data, 'GLD')
        if gld_closes is not None:
            gld_wc = _weekly_change(gld_closes)
            surge_th = cfg.get('gold_weekly_surge_signal', 0.03)
            mild_th = surge_th * 0.5  # 温和上涨阈值=1.5%
            if gld_wc > surge_th:
                bullish += 2  # 强信号加2
                signals_list.append(Signal("黄金强势上涨(避险)", gld_wc, surge_th, True, f"GLD周涨={gld_wc:+.2%} → 强烈避险信号"))
            elif gld_wc > mild_th:
                bullish += 1
                signals_list.append(Signal("黄金温和上涨", gld_wc, mild_th, True, f"GLD周涨={gld_wc:+.2%} → 避险需求上升"))
            elif gld_wc < -0.02:
                bearish += 1
                signals_list.append(Signal("黄金走弱", gld_wc, -0.02, True, f"GLD周跌={gld_wc:+.2%}"))

        # 白银周涨幅（新增独立分析）
        slv_closes = _get_closes(data, 'SLV')
        if slv_closes is not None:
            slv_wc = _weekly_change(slv_closes)
            if slv_wc > 0.03:
                bullish += 1
                signals_list.append(Signal("白银上涨(工业+贵金属)", slv_wc, 0.03, True, f"SLV周涨={slv_wc:+.2%} → 工业需求+避险"))
            elif slv_wc < -0.03:
                bearish += 1
                signals_list.append(Signal("白银走弱", slv_wc, -0.03, True, f"SLV周跌={slv_wc:+.2%}"))

        # GDX/GLD比率
        gdx_closes = _get_closes(data, 'GDX')
        if gld_closes is not None and gdx_closes is not None and len(gld_closes) >= 5 and len(gdx_closes) >= 5:
            ratio_now = float(gdx_closes[-1]) / float(gld_closes[-1]) if float(gld_closes[-1]) > 0 else 0
            ratio_prev = float(gdx_closes[-5]) / float(gld_closes[-5]) if float(gld_closes[-5]) > 0 else 0
            ratio_ch = ratio_now - ratio_prev
            if ratio_ch > 0.005:
                bullish += 1
                signals_list.append(Signal("GDX/GLD上升(牛市确认)", ratio_ch, 0.005, True, f"矿股跑赢金价 → 黄金牛市确认"))

        # 铜（经济晴雨表，降低阈值至2%）
        cper_closes = _get_closes(data, 'CPER')
        if cper_closes is not None:
            cper_wc = _weekly_change(cper_closes)
            if cper_wc > 0.02:
                bullish += 1
                signals_list.append(Signal("铜价上涨(经济扩张)", cper_wc, 0.02, True, f"CPER周涨={cper_wc:+.2%} → Dr.Copper看多"))
            elif cper_wc < -0.02:
                bearish += 1
                signals_list.append(Signal("铜价下跌(衰退信号)", cper_wc, -0.02, True, f"CPER周跌={cper_wc:+.2%} → 工业需求走弱"))

        # 金铜比
        if gld_closes is not None and cper_closes is not None:
            gc_ratio = float(gld_closes[-1]) / float(cper_closes[-1]) if float(cper_closes[-1]) > 0 else 0
            gc_ratio_prev = float(gld_closes[-5]) / float(cper_closes[-5]) if len(gld_closes) >= 5 and len(cper_closes) >= 5 and float(cper_closes[-5]) > 0 else gc_ratio
            gc_ch = (gc_ratio - gc_ratio_prev) / gc_ratio_prev if gc_ratio_prev > 0 else 0
            if gc_ch > 0.02:
                bearish += 1
                signals_list.append(Signal("金铜比上升(衰退预警)", gc_ch, 0.02, True, f"金铜比变化={gc_ch:+.2%} → 经济下行"))
            elif gc_ch < -0.02:
                bullish += 1
                signals_list.append(Signal("金铜比下降(经济向好)", gc_ch, -0.02, True, f"金铜比变化={gc_ch:+.2%}"))

        # 油价（降低阈值至5%，增加温和信号）
        uso_closes = _get_closes(data, 'USO')
        if uso_closes is not None:
            uso_wc = _weekly_change(uso_closes)
            if uso_wc > 0.05:
                bullish += 1
                signals_list.append(Signal("油价上涨(通胀/地缘)", uso_wc, 0.05, True, f"USO周涨={uso_wc:+.2%} → 能源通胀风险"))
            elif uso_wc < -0.05:
                bearish += 1
                signals_list.append(Signal("油价下跌(需求疲弱)", uso_wc, -0.05, True, f"USO周跌={uso_wc:+.2%} → 经济放缓信号"))

        # 农产品ETF
        dba_closes = _get_closes(data, 'DBA')
        if dba_closes is not None:
            dba_wc = _weekly_change(dba_closes)
            if dba_wc > 0.02:
                bullish += 1
                signals_list.append(Signal("农产品上涨(食品通胀)", dba_wc, 0.02, True, f"DBA周涨={dba_wc:+.2%} → 食品通胀升温"))
            elif dba_wc < -0.02:
                bearish += 1
                signals_list.append(Signal("农产品走弱", dba_wc, -0.02, True, f"DBA周跌={dba_wc:+.2%}"))

        # 多元商品ETF（总体趋势）
        pdbc_closes = _get_closes(data, 'PDBC')
        if pdbc_closes is not None:
            pdbc_wc = _weekly_change(pdbc_closes)
            if pdbc_wc > 0.02:
                bullish += 1
                signals_list.append(Signal("商品指数上涨", pdbc_wc, 0.02, True, f"PDBC周涨={pdbc_wc:+.2%} → 大宗商品趋势向上"))
            elif pdbc_wc < -0.02:
                bearish += 1
                signals_list.append(Signal("商品指数走弱", pdbc_wc, -0.02, True, f"PDBC周跌={pdbc_wc:+.2%}"))

        result.signals = signals_list
        net = bullish - bearish
        if net >= 3:
            result.rating, result.score, result.action = "商品超级周期信号", 0.6, "增配实物资产(金/铜/能源)"
        elif net >= 1:
            result.rating, result.score, result.action = "商品偏多", 0.2, "维持商品配置"
        elif net <= -2:
            result.rating, result.score, result.action = "商品走弱(通缩风险)", -0.4, "减持商品，增持债券"
        else:
            result.rating, result.score, result.action = "商品中性", 0.0, "观望"

        result.detail = f"多头信号={bullish} 空头信号={bearish} 净={net}"
        result.confidence = 0.6
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Skill 8: 收益率曲线与利率分析
# ═══════════════════════════════════════════════════════════

def skill8_yield_curve(config):
    """
    收益率曲线与利率分析 v3.2
    数据源: FRED真实利差(主) + Alpha Vantage TLT/SHY (降级)
    FRED: DGS10/DGS2/T10Y2Y/T10Y3M/FEDFUNDS
    """
    print("  📉 Skill 8: 收益率曲线与利率分析...")
    result = SkillResult(skill_name="收益率曲线与利率分析", rating="", score=0.0)
    signals_list = []
    cfg = config.get('skill8_yield_curve', {})
    rate_cfg = cfg.get('rate_change_thresholds', {})
    dm = get_manager()

    try:
        # ═══ 第一层: FRED真实收益率数据 ═══
        macro = dm.fetch_macro_data()
        fred_available = macro.source == "FRED"
        warning_count = 0

        if fred_available:
            # 2s10s利差（FRED直接提供）
            if macro.us2s10s_spread is not None:
                curve_cfg = cfg.get('curve_thresholds', {})
                deep_inv = curve_cfg.get('2s10s_deep_inversion', -0.50)
                if macro.us2s10s_spread < deep_inv:
                    warning_count += 2
                    signals_list.append(Signal("2s10s深度倒挂(FRED)", macro.us2s10s_spread, deep_inv, True,
                        f"2s10s={macro.us2s10s_spread:+.2f}% → 衰退概率极高"))
                elif macro.us2s10s_spread < 0:
                    warning_count += 1
                    signals_list.append(Signal("2s10s倒挂(FRED)", macro.us2s10s_spread, 0, True,
                        f"2s10s={macro.us2s10s_spread:+.2f}% → 衰退预警"))
                else:
                    signals_list.append(Signal("2s10s正常(FRED)", macro.us2s10s_spread, 0, False,
                        f"2s10s={macro.us2s10s_spread:+.2f}%"))

            # 3m10s利差
            if macro.us3m10s_spread is not None:
                if macro.us3m10s_spread < 0:
                    warning_count += 1
                    signals_list.append(Signal("3m10s倒挂(FRED)", macro.us3m10s_spread, 0, True,
                        f"3m10s={macro.us3m10s_spread:+.2f}% → 更准确的衰退指标"))

            # 10Y收益率水平
            if macro.us10y_yield is not None:
                if macro.us10y_yield > 5.0:
                    warning_count += 1
                    signals_list.append(Signal("10Y极高(FRED)", macro.us10y_yield, 5.0, True,
                        f"10Y={macro.us10y_yield:.2f}% → 压制估值"))
                # 获取历史趋势判断周变化
                y10_hist = dm.fetch_fred_series('DGS10', limit=10)
                if y10_hist and len(y10_hist) >= 5:
                    y10_now = y10_hist[-1]['value']
                    y10_5d = y10_hist[-5]['value']
                    y10_wc = y10_now - y10_5d
                    spike_th = rate_cfg.get('10y_weekly_spike', 0.20)
                    if abs(y10_wc) > spike_th:
                        warning_count += 1
                        direction = "飙升" if y10_wc > 0 else "骤降"
                        signals_list.append(Signal(f"10Y利率{direction}(FRED)", y10_wc, spike_th, True,
                            f"10Y 5日变化={y10_wc:+.2f}%"))

        # ═══ 第二层: yfinance代理数据(始终获取) ═══
        data = safe_download("^TNX TLT SHY IEF", period="3mo", interval="1d")

        if data is not None:
            import numpy as np
            # ^TNX (yfinance代理，作为FRED的补充/降级)
            tnx_closes = _get_closes(data, '^TNX')
            if tnx_closes is not None and len(tnx_closes) >= 5 and not fred_available:
                y10_now = float(tnx_closes[-1])
                y10_5d = float(tnx_closes[-5])
                y10_wc = y10_now - y10_5d
                spike_th = rate_cfg.get('10y_weekly_spike', 0.20)
                if y10_wc > spike_th:
                    warning_count += 1
                    signals_list.append(Signal("10Y利率飙升", y10_wc, spike_th, True, f"10Y变化={y10_wc:+.2f}% → 利率冲击"))
                elif y10_wc < -spike_th:
                    signals_list.append(Signal("10Y利率骤降", y10_wc, -spike_th, True, f"10Y变化={y10_wc:+.2f}% → 避险需求上升"))
                else:
                    signals_list.append(Signal("10Y利率", y10_wc, spike_th, False, f"10Y={y10_now:.2f}% 周变化={y10_wc:+.2f}%"))

                if y10_now > 5.0:
                    warning_count += 1
                    signals_list.append(Signal("10Y利率极高", y10_now, 5.0, True, f"10Y={y10_now:.2f}% → 高利率压制估值"))

            # TLT/SHY曲线代理
            tlt_closes = _get_closes(data, 'TLT')
            shy_closes = _get_closes(data, 'SHY')
            if tlt_closes is not None and shy_closes is not None and len(tlt_closes) >= 20 and len(shy_closes) >= 20:
                ratio_now = float(tlt_closes[-1]) / float(shy_closes[-1]) if float(shy_closes[-1]) > 0 else 0
                ratio_20d = float(tlt_closes[-20]) / float(shy_closes[-20]) if float(shy_closes[-20]) > 0 else 0
                curve_trend = (ratio_now - ratio_20d) / ratio_20d if ratio_20d > 0 else 0
                if curve_trend < -0.03:
                    warning_count += 1
                    signals_list.append(Signal("曲线趋平/倒挂加深", curve_trend, -0.03, True, f"TLT/SHY 20日变化={curve_trend:+.2%}"))
                elif curve_trend > 0.03:
                    signals_list.append(Signal("曲线变陡", curve_trend, 0.03, True, f"TLT/SHY 20日变化={curve_trend:+.2%} → 可能衰退临近"))

            # 利率冲击检测
            rate_shock_th = 0.25
            if tnx_closes is not None and len(tnx_closes) >= 5:
                weekly_abs_change = abs(float(tnx_closes[-1]) - float(tnx_closes[-5]))
                if weekly_abs_change > rate_shock_th:
                    warning_count += 1
                    signals_list.append(Signal("利率冲击", weekly_abs_change, rate_shock_th, True, f"10Y周绝对变化={weekly_abs_change:.2f}% → 利率冲击"))

        result.signals = signals_list
        if warning_count >= 4:
            result.rating, result.score, result.action = "利率危机", -0.8, "大幅减持长久期资产"
        elif warning_count >= 3:
            result.rating, result.score, result.action = "利率严重压力", -0.6, "减持长久期，增持现金"
        elif warning_count >= 2:
            result.rating, result.score, result.action = "利率压力", -0.4, "减持长久期，增持浮动利率"
        elif warning_count >= 1:
            result.rating, result.score, result.action = "利率偏高", -0.2, "关注利率走势"
        else:
            result.rating, result.score, result.action = "利率平稳", 0.2, "可持有久期资产"

        data_src = "FRED+ETF" if fred_available else "ETF代理"
        result.detail = f"数据源: {data_src} | 利率预警: {warning_count}/{len(signals_list)}"
        result.confidence = 0.85 if fred_available else 0.7
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Skill 9: 波动率微观结构
# ═══════════════════════════════════════════════════════════

def skill9_volatility(config):
    """
    波动率微观结构
    VIX水平/脉冲/持续性 + 期限结构分析
    """
    print("  🌪️ Skill 9: 波动率微观结构...")
    result = SkillResult(skill_name="波动率微观结构", rating="", score=0.0)
    signals_list = []
    cfg = config.get('skill9_volatility_structure', {})
    vix_levels = cfg.get('vix_levels', {})
    term_cfg = cfg.get('term_structure', {})

    try:
        # 优先获取VIX指数，同时准备VIXY ETF作为降级代理
        data = safe_download("^VIX ^VIX9D", period="3mo", interval="1d")

        import numpy as np

        vix_closes = _get_closes(data, '^VIX') if data is not None else None

        # VIX降级：^VIX获取失败时用VIXY ETF代理
        vixy_proxy = False
        if vix_closes is None or len(vix_closes) < 5:
            print("    ⚠️ VIX指数不可用，尝试VIXY ETF代理...")
            vixy_data = safe_download("VIXY", period="3mo", interval="1d")
            if vixy_data is not None:
                vixy_closes = _get_closes(vixy_data, 'VIXY')
                if vixy_closes is not None and len(vixy_closes) >= 5:
                    # VIXY价格趋势可近似反映VIX走势（非精确数值）
                    # 用VIXY的变化率估算VIX水平：基准VIX=18，用VIXY变化率调整
                    vix_closes = vixy_closes
                    vixy_proxy = True
                    print(f"    ✅ 使用VIXY ETF代理 ({len(vixy_closes)}天数据)")

        if vix_closes is None or len(vix_closes) < 5:
            result.error = "VIX及VIXY代理数据均不可用"
            result.rating = "数据不可用"
            return result

        if vixy_proxy:
            # VIXY是ETF价格（美元），不是VIX点位
            # 用最新价格和历史波动率相对变化来分析趋势
            vix_now_raw = float(vix_closes[-1])
            vix_5d_raw = float(vix_closes[-5])
            vix_20d_raw = float(np.mean(vix_closes[-20:])) if len(vix_closes) >= 20 else vix_now_raw
            # 用比率分析（比率不受绝对值影响）
            vix_pulse = (vix_now_raw - vix_5d_raw) / vix_5d_raw if vix_5d_raw > 0 else 0
            persistence = vix_now_raw / vix_20d_raw if vix_20d_raw > 0 else 1
            # 估算VIX水平：根据VIXY走势判断区间
            # VIXY上涨→VIX上升，VIXY下跌→VIX下降
            vix_now = 18.0  # 基准中性
            if vix_pulse > 0.20:
                vix_now = 28.0
            elif vix_pulse > 0.10:
                vix_now = 22.0
            elif vix_pulse < -0.15:
                vix_now = 13.0
            elif vix_pulse < -0.05:
                vix_now = 16.0
            result.detail = f"VIX≈{vix_now:.0f}(VIXY代理) | 脉冲={vix_pulse:+.0%} | 持续性={persistence:.2f}"
        else:
            vix_now = float(vix_closes[-1])
            vix_5d = float(vix_closes[-5])
            vix_20d_avg = float(np.mean(vix_closes[-20:])) if len(vix_closes) >= 20 else vix_now
            vix_pulse = (vix_now - vix_5d) / vix_5d if vix_5d > 0 else 0
            persistence = vix_now / vix_20d_avg if vix_20d_avg > 0 else 1
            result.detail = f"VIX={vix_now:.1f} | 脉冲={vix_pulse:+.0%} | 持续性={persistence:.2f}"

        # VIX水平判断
        if vix_now < vix_levels.get('complacency', {}).get('max', 12):
            level_signal, level_score = "过度自满", -0.5
        elif vix_now < vix_levels.get('normal', {}).get('max', 20):
            level_signal, level_score = "正常区间", 0.0
        elif vix_now < vix_levels.get('elevated', {}).get('max', 30):
            level_signal, level_score = "波动率升高", -0.3
        elif vix_now < vix_levels.get('panic', {}).get('max', 50):
            level_signal, level_score = "恐慌", 0.4
        else:
            level_signal, level_score = "系统性危机", 0.6
        proxy_tag = "(VIXY代理)" if vixy_proxy else ""
        signals_list.append(Signal("VIX水平", vix_now, 20, vix_now > 25 or vix_now < 12, f"VIX={vix_now:.1f}{proxy_tag} → {level_signal}"))

        # VIX脉冲（5日变化）
        pulse_score = 0.0
        if vix_pulse > 0.30:
            pulse_score = 0.4
            signals_list.append(Signal("VIX脉冲飙升", vix_pulse, 0.30, True, f"VIX 5日涨幅={vix_pulse:+.0%} → 恐慌脉冲"))
        elif vix_pulse < -0.20:
            pulse_score = -0.2
            signals_list.append(Signal("VIX快速回落", vix_pulse, -0.20, True, f"VIX 5日降幅={vix_pulse:+.0%}"))

        # VIX持续性（当前vs20日均值）
        persist_score = 0.0
        if persistence > 1.3:
            persist_score = 0.2
            signals_list.append(Signal("VIX持续偏高", persistence, 1.3, True, f"VIX/20日均值={persistence:.2f} → 持续紧张"))
        elif persistence < 0.7:
            persist_score = -0.2
            signals_list.append(Signal("VIX持续偏低", persistence, 0.7, True, f"VIX/20日均值={persistence:.2f} → 过度自满"))

        # VIX期限结构
        vix9d_closes = _get_closes(data, '^VIX9D') if data is not None else None
        term_score = 0.0
        if vix9d_closes is not None and len(vix9d_closes) > 0:
            vix9d_now = float(vix9d_closes[-1])
            ratio = vix9d_now / vix_now if vix_now > 0 else 1
            inv_th = term_cfg.get('inversion_ratio_threshold', 1.10)
            deep_inv = term_cfg.get('deep_inversion', 1.25)
            if ratio > deep_inv:
                term_score = 0.5
                signals_list.append(Signal("VIX深度倒挂", ratio, deep_inv, True, f"9日/标准={ratio:.2f} → 短期极度恐慌"))
            elif ratio > inv_th:
                term_score = 0.3
                signals_list.append(Signal("VIX倒挂", ratio, inv_th, True, f"9日/标准={ratio:.2f} → 短期恐慌高于长期"))
            else:
                signals_list.append(Signal("VIX正常期限结构", ratio, inv_th, False, f"9日/标准={ratio:.2f} → Contango正常"))
        elif vixy_proxy:
            signals_list.append(Signal("VIX期限结构", 0, 0, False, "VIX9D不可用(使用VIXY代理模式)"))

        avg_score = (level_score + pulse_score + persist_score + term_score) / 4
        result.score = max(-1, min(1, avg_score))
        result.signals = signals_list

        if result.score > 0.3:
            result.rating, result.action = "波动率极端(可能反转买点)", "关注政策干预信号，准备反转建仓"
        elif result.score < -0.3:
            result.rating, result.action = "波动率过低(自满风险)", "买入廉价保护(看跌期权)"
        else:
            result.rating, result.action = "波动率正常", "维持当前仓位"

        if not result.detail:
            result.detail = f"VIX={vix_now:.1f} | 脉冲={vix_pulse:+.0%} | 持续性={persistence:.2f}"
        result.confidence = 0.55 if vixy_proxy else 0.65
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Skill 10: 港股与A股专项分析
# ═══════════════════════════════════════════════════════════

def skill10_hk_a_shares(config):
    """
    港股与A股专项分析 v3.2
    数据源: AkShare(主) + Alpha Vantage(降级)
    AkShare: 北向/南向资金流 + AH溢价指数 + 融资融券 + SHIBOR + 人民币中间价
    Alpha Vantage: KWEB/FXI/MCHI/EWH(^HSI代理)/CNY=X
    """
    print("  🇨🇳 Skill 10: 港股与A股专项分析...")
    result = SkillResult(skill_name="港股与A股专项分析", rating="", score=0.0)
    signals_list = []
    cfg = config.get('skill10_hk_a_shares', {})
    cny_cfg = cfg.get('cny_thresholds', {})
    dm = get_manager()

    try:
        # ═══ 第一层: AkShare中国市场真实数据 ═══
        china = dm.fetch_china_market_data()
        akshare_available = china.source == "AkShare"
        bullish = 0
        bearish = 0

        if akshare_available:
            # 北向资金(沪深港通)
            if china.northbound_flow is not None:
                fund_cfg = cfg.get('fund_flow', {})
                if china.northbound_flow > 100:
                    bullish += 2
                    signals_list.append(Signal("北向资金大幅买入(AkShare)", china.northbound_flow, 100, True,
                        f"北向净买入={china.northbound_flow:+.0f}亿元 → 强烈做多A股"))
                elif china.northbound_flow > 30:
                    bullish += 1
                    signals_list.append(Signal("北向资金流入(AkShare)", china.northbound_flow, 30, True,
                        f"北向净买入={china.northbound_flow:+.0f}亿元"))
                elif china.northbound_flow < -50:
                    bearish += 1
                    signals_list.append(Signal("北向资金流出(AkShare)", china.northbound_flow, -50, True,
                        f"北向净卖出={china.northbound_flow:+.0f}亿元 → A股风险"))
                else:
                    signals_list.append(Signal("北向资金(AkShare)", china.northbound_flow, 50, False,
                        f"北向={china.northbound_flow:+.0f}亿元"))

            # 南向资金
            if china.southbound_flow is not None:
                if china.southbound_flow > 100:
                    bullish += 1
                    signals_list.append(Signal("南向资金大量流入港股(AkShare)", china.southbound_flow, 100, True,
                        f"南向净买入={china.southbound_flow:+.0f}亿港元 → 做多港股"))
                elif china.southbound_flow < -30:
                    bearish += 1
                    signals_list.append(Signal("南向资金流出港股(AkShare)", china.southbound_flow, -30, True,
                        f"南向净卖出={china.southbound_flow:+.0f}亿港元"))

            # AH溢价指数
            if china.ah_premium_index is not None:
                ah_cfg = cfg.get('ah_premium_index', {})
                extreme_cheap_hk = ah_cfg.get('extreme_cheap_hk', 150)
                extreme_cheap_a = ah_cfg.get('extreme_cheap_a', 110)
                if china.ah_premium_index > extreme_cheap_hk:
                    bullish += 1  # 港股极度低估
                    signals_list.append(Signal("AH溢价极高(港股低估)(AkShare)", china.ah_premium_index, extreme_cheap_hk, True,
                        f"AH溢价={china.ah_premium_index:.0f} → 港股相对A股极度低估"))
                elif china.ah_premium_index < extreme_cheap_a:
                    bearish += 1
                    signals_list.append(Signal("AH溢价极低(A股低估)(AkShare)", china.ah_premium_index, extreme_cheap_a, True,
                        f"AH溢价={china.ah_premium_index:.0f} → A股相对港股低估"))
                else:
                    signals_list.append(Signal("AH溢价指数(AkShare)", china.ah_premium_index, 130, False,
                        f"AH溢价={china.ah_premium_index:.0f}"))

            # 融资融券余额变化
            if china.margin_balance is not None:
                signals_list.append(Signal("融资融券余额(AkShare)", china.margin_balance, 0, False,
                    f"两融余额={china.margin_balance:,.0f}亿元"))

            # 人民币中间价(AkShare更准确)
            if china.cny_usd is not None:
                cny_now = china.cny_usd
                dep_warning = cny_cfg.get('depreciation_warning', 7.30)
                dep_crisis = cny_cfg.get('depreciation_crisis', 7.50)
                app_signal = cny_cfg.get('appreciation_signal', 7.00)

                if cny_now > dep_crisis:
                    bearish += 2
                    signals_list.append(Signal("人民币危机贬值(AkShare)", cny_now, dep_crisis, True,
                        f"CNY中间价={cny_now:.4f} → 严重贬值"))
                elif cny_now > dep_warning:
                    bearish += 1
                    signals_list.append(Signal("人民币贬值预警(AkShare)", cny_now, dep_warning, True,
                        f"CNY中间价={cny_now:.4f} → 贬值压力"))
                elif cny_now < app_signal:
                    bullish += 1
                    signals_list.append(Signal("人民币升值(AkShare)", cny_now, app_signal, True,
                        f"CNY中间价={cny_now:.4f} → 利好中国资产"))
                else:
                    signals_list.append(Signal("人民币汇率(AkShare)", cny_now, dep_warning, False,
                        f"CNY中间价={cny_now:.4f}"))

        # ═══ 第二层: yfinance ETF代理(始终获取) ═══
        tickers = "KWEB FXI MCHI ^HSI ^HSTECH"
        cny_ticker = cny_cfg.get('ticker', 'CNY=X')
        data = safe_download(f"{tickers} {cny_ticker}", period="3mo", interval="1d")

        if data is not None:
            import numpy as np
            # KWEB 中概互联网周度表现
            kweb_closes = _get_closes(data, 'KWEB')
            if kweb_closes is not None:
                kweb_wc = _weekly_change(kweb_closes)
                if kweb_wc > 0.05:
                    bullish += 1
                    signals_list.append(Signal("中概互联网强势", kweb_wc, 0.05, True, f"KWEB周涨={kweb_wc:+.2%}"))
                elif kweb_wc < -0.05:
                    bearish += 1
                    signals_list.append(Signal("中概互联网走弱", kweb_wc, -0.05, True, f"KWEB周跌={kweb_wc:+.2%}"))
                else:
                    signals_list.append(Signal("中概互联网", kweb_wc, 0.05, False, f"KWEB周变化={kweb_wc:+.2%}"))

            # 恒生指数
            hsi_closes = _get_closes(data, '^HSI')
            if hsi_closes is not None:
                hsi_wc = _weekly_change(hsi_closes)
                if hsi_wc > 0.03:
                    bullish += 1
                elif hsi_wc < -0.03:
                    bearish += 1
                signals_list.append(Signal("恒生指数", hsi_wc, 0.03, abs(hsi_wc) > 0.03, f"HSI周变化={hsi_wc:+.2%}"))

            # 恒生科技
            hstech_closes = _get_closes(data, '^HSTECH')
            if hstech_closes is not None:
                hstech_wc = _weekly_change(hstech_closes)
                if hstech_wc > 0.04:
                    bullish += 1
                elif hstech_wc < -0.04:
                    bearish += 1
                signals_list.append(Signal("恒生科技", hstech_wc, 0.04, abs(hstech_wc) > 0.04, f"HSTECH周变化={hstech_wc:+.2%}"))

            # FXI 中国大盘
            fxi_closes = _get_closes(data, 'FXI')
            if fxi_closes is not None:
                fxi_wc = _weekly_change(fxi_closes)
                if fxi_wc > 0.04:
                    bullish += 1
                elif fxi_wc < -0.04:
                    bearish += 1
                signals_list.append(Signal("中国大盘(FXI)", fxi_wc, 0.04, abs(fxi_wc) > 0.04, f"FXI周变化={fxi_wc:+.2%}"))

            # 人民币汇率(yfinance降级,如果AkShare没拿到)
            if not akshare_available or china.cny_usd is None:
                cny_closes = _get_closes(data, cny_ticker)
                if cny_closes is not None and len(cny_closes) > 0:
                    cny_now = float(cny_closes[-1])
                    dep_warning = cny_cfg.get('depreciation_warning', 7.30)
                    dep_crisis = cny_cfg.get('depreciation_crisis', 7.50)
                    if cny_now > dep_crisis:
                        bearish += 2
                        signals_list.append(Signal("人民币危机贬值", cny_now, dep_crisis, True, f"CNY={cny_now:.4f}"))
                    elif cny_now > dep_warning:
                        bearish += 1
                        signals_list.append(Signal("人民币贬值预警", cny_now, dep_warning, True, f"CNY={cny_now:.4f}"))

        result.signals = signals_list
        net = bullish - bearish
        if net >= 3:
            result.rating, result.score, result.action = "强烈做多中国资产", 0.8, "大幅增配港股/A股/中概"
        elif net >= 2:
            result.rating, result.score, result.action = "做多中国资产", 0.5, "增配港股/A股/中概"
        elif net >= 1:
            result.rating, result.score, result.action = "中国资产偏多", 0.2, "维持中国资产配置"
        elif net <= -3:
            result.rating, result.score, result.action = "中国资产高风险", -0.8, "清仓中国资产，避险"
        elif net <= -2:
            result.rating, result.score, result.action = "中国资产风险", -0.5, "减持中国资产"
        elif net <= -1:
            result.rating, result.score, result.action = "中国资产偏弱", -0.2, "谨慎，关注政策变化"
        else:
            result.rating, result.score, result.action = "中国资产中性", 0.0, "维持现有配置"

        data_src = "AkShare+ETF" if akshare_available else "ETF代理"
        result.detail = f"数据源: {data_src} | 多头={bullish} 空头={bearish} 净={net}"
        result.confidence = 0.8 if akshare_available else 0.6
        print(f"    → {result.rating} ({result.detail})")

    except Exception as e:
        result.error = str(e)
        result.rating = "分析异常"
        result.detail = f"错误: {str(e)[:80]}"
        print(f"    ❌ {result.detail}")

    return result


# ═══════════════════════════════════════════════════════════
# Overnight市场摘要采集
# ═══════════════════════════════════════════════════════════

def collect_overnight_summary(config):
    """采集隔夜市场数据，生成摘要（v3.1: 全球指数优先用AkShare真实点位）"""
    print("  🌙 采集Overnight市场摘要...")
    summary = {'indices': [], 'crypto': [], 'commodities': [], 'key_moves': []}

    try:
        # 兼容v2(market_indices)和v3(global_indices)
        indices_key = 'global_indices' if 'global_indices' in config['watchlist'] else 'market_indices'
        crypto_tickers = [t['ticker'] for t in config['watchlist'].get('crypto', [])]
        macro_tickers = [t['ticker'] for t in config['watchlist'].get('macro_proxies', [])]
        commodity_tickers = [t['ticker'] for t in config['watchlist'].get('commodities', [])]

        # ═══ 第一步: 获取全球指数真实点位（AkShare东方财富 index_global_spot_em）═══
        mgr = get_manager()
        global_index_data = mgr.get_global_index_spot()

        index_items = config['watchlist'].get(indices_key, [])
        covered_indices = set()  # 已用真实数据覆盖的指数ticker

        for item in index_items:
            ticker, name = item['ticker'], item['name']
            if ticker in global_index_data:
                idx_info = global_index_data[ticker]
                price = idx_info['price']
                change = idx_info['change']
                summary['indices'].append({
                    'name': name, 'price': price, 'change': change,
                    'is_etf_proxy': False
                })
                covered_indices.add(ticker)
                if abs(change) > 1.5:
                    direction = "暴涨" if change > 0 else "暴跌"
                    summary['key_moves'].append(f"{name}{direction}{abs(change):.1f}%")

        # ═══ 第二步: 未覆盖的指数 + 加密货币 + 宏观/商品 → yfinance ETF代理 ═══
        uncovered_index_items = [t for t in index_items if t['ticker'] not in covered_indices]
        uncovered_index_tickers = [t['ticker'] for t in uncovered_index_items]
        all_yf_tickers = uncovered_index_tickers + crypto_tickers + macro_tickers + commodity_tickers

        data = None
        if all_yf_tickers:
            data = safe_download(" ".join(all_yf_tickers), period="5d", interval="1d")

        def process_items(items, category, threshold, mark_etf_proxy=False):
            if data is None or data.empty:
                return
            for item in items:
                ticker, name = item['ticker'], item['name']
                closes = _get_closes(data, ticker)
                if closes is not None and len(closes) >= 2:
                    current = float(closes[-1])
                    prev = float(closes[-2])
                    change = (current - prev) / prev * 100 if prev > 0 else 0
                    is_etf_proxy = mark_etf_proxy and ticker.startswith('^') and ticker in INDEX_TO_ETF
                    summary[category].append({
                        'name': name, 'price': current, 'change': change,
                        'is_etf_proxy': is_etf_proxy
                    })
                    if abs(change) > threshold:
                        direction = "暴涨" if change > 0 else "暴跌"
                        summary['key_moves'].append(f"{name}{direction}{abs(change):.1f}%")

        # 未覆盖指数走ETF代理（标记）
        process_items(uncovered_index_items, 'indices', 1.5, mark_etf_proxy=True)
        # 加密货币不标记
        process_items(config['watchlist'].get('crypto', []), 'crypto', 3.0)

        # ═══ 第三步: 宏观/商品 → 优先新浪真实外汇/商品数据，降级到ETF ═══
        forex_commodity_real = mgr.get_forex_commodity_realtime()
        realtime_replaced = set()  # 已用真实数据替代的ETF ticker

        # 先用真实数据替代 macro_proxies 和 commodities 中对应的ETF
        for category_items in [config['watchlist'].get('macro_proxies', []),
                               config['watchlist'].get('commodities', [])]:
            for item in category_items:
                ticker = item['ticker']
                if ticker in forex_commodity_real and ticker not in realtime_replaced:
                    real = forex_commodity_real[ticker]
                    display_name = real['name']
                    if real.get('unit'):
                        display_name = f"{real['name']}({real['unit']})"
                    summary['commodities'].append({
                        'name': display_name,
                        'price': real['price'],
                        'change': real['change'],
                        'is_realtime': True,
                    })
                    realtime_replaced.add(ticker)
                    if abs(real['change']) > 2.0:
                        direction = "暴涨" if real['change'] > 0 else "暴跌"
                        summary['key_moves'].append(f"{display_name}{direction}{abs(real['change']):.1f}%")

        # 剩余未替代的走ETF代理
        remaining_macro = [item for item in config['watchlist'].get('macro_proxies', [])
                           if item['ticker'] not in realtime_replaced]
        remaining_commodities = [item for item in config['watchlist'].get('commodities', [])
                                  if item['ticker'] not in realtime_replaced]
        process_items(remaining_macro, 'commodities', 2.0)
        process_items(remaining_commodities, 'commodities', 2.0)

        real_count = len(covered_indices)
        etf_count = len(summary['indices']) - real_count
        realtime_count = len(realtime_replaced)
        print(f"    → 指数{len(summary['indices'])}个(真实{real_count}+ETF代理{etf_count}) | 加密{len(summary['crypto'])}个 | 宏观/商品{len(summary['commodities'])}个(实时{realtime_count}个)")

    except Exception as e:
        print(f"    ⚠️ 采集失败: {e}")
        import traceback
        traceback.print_exc()

    return summary


# ═══════════════════════════════════════════════════════════
# 综合分析引擎
# ═══════════════════════════════════════════════════════════

def check_upcoming_events(dates_config, indicators_news=None):
    """检查未来7天的重要事件（支持v2.0多层知识库）"""
    today = datetime.now().date()
    events = []

    # 1. 检查FOMC会议
    for meeting in dates_config.get('fomc_meetings_2026', []):
        try:
            meeting_date = datetime.strptime(meeting['date'], '%Y-%m-%d').date()
            days_until = (meeting_date - today).days
            if 0 <= days_until <= 7:
                events.append({
                    'date': meeting['date'],
                    'type': meeting['type'],
                    'note': meeting.get('note', ''),
                    'days_until': days_until,
                    'impact': '高'
                })
        except Exception:
            continue

    # 2. 检查FOMC黑静期（美联储官员禁止公开发言）
    for blackout in dates_config.get('fomc_blackout_2026', []):
        try:
            start = datetime.strptime(blackout['start'], '%Y-%m-%d').date()
            end = datetime.strptime(blackout['end'], '%Y-%m-%d').date()
            if start <= today <= end:
                events.append({
                    'date': blackout['start'],
                    'type': 'FOMC黑静期',
                    'note': f"美联储官员禁止公开发言期（至{blackout['end']}）",
                    'days_until': 0,
                    'impact': '中'
                })
            elif 0 < (start - today).days <= 3:
                events.append({
                    'date': blackout['start'],
                    'type': 'FOMC黑静期即将开始',
                    'note': f"黑静期 {blackout['start']} 至 {blackout['end']}",
                    'days_until': (start - today).days,
                    'impact': '中'
                })
        except Exception:
            continue

    # 3. 检查财报日（important_dates.json 中的平铺列表）
    for earning in dates_config.get('earnings_calendar_2026_q1', []):
        try:
            earn_date = datetime.strptime(earning['date'], '%Y-%m-%d').date()
            days_until = (earn_date - today).days
            if 0 <= days_until <= 7:
                events.append({
                    'date': earning['date'],
                    'type': f"{earning['name']}({earning['company']})财报",
                    'note': earning.get('quarter', ''),
                    'days_until': days_until,
                    'impact': '高'
                })
        except Exception:
            continue

    # 4. 从 indicators_news 读取更完整的多季度财报日历
    if indicators_news:
        earnings_cal = indicators_news.get('earnings_calendar_2026', {})
        for quarter_key, quarter_data in earnings_cal.items():
            if quarter_key.startswith('_'):
                continue
            reports = quarter_data.get('reports', []) if isinstance(quarter_data, dict) else []
            for report in reports:
                try:
                    rpt_date = datetime.strptime(report['date'], '%Y-%m-%d').date()
                    days_until = (rpt_date - today).days
                    if 0 <= days_until <= 7:
                        event_type = f"{report['name']}({report['ticker']})财报"
                        # 去重：避免与 important_dates 重复
                        if not any(e['date'] == report['date'] and report['ticker'] in e['type'] for e in events):
                            events.append({
                                'date': report['date'],
                                'type': event_type,
                                'note': f"{report.get('quarter', '')} {report.get('timing', '')}",
                                'days_until': days_until,
                                'impact': '高'
                            })
                except Exception:
                    continue

        # 5. 从 indicators_news 读取期权到期日
        opex_data = indicators_news.get('options_expiry_2026', {})
        for opex in opex_data.get('monthly_expiry', []):
            try:
                opex_date = datetime.strptime(opex['date'], '%Y-%m-%d').date()
                days_until = (opex_date - today).days
                if 0 <= days_until <= 3:
                    if not any(e['date'] == opex['date'] and '期权' in e['type'] for e in events):
                        events.append({
                            'date': opex['date'],
                            'type': opex['type'],
                            'note': opex.get('note', ''),
                            'days_until': days_until,
                            'impact': '中'
                        })
            except Exception:
                continue

    # 6. 检查期权到期日（important_dates.json）
    for opex in dates_config.get('options_expiry_2026', []):
        try:
            opex_date = datetime.strptime(opex['date'], '%Y-%m-%d').date()
            days_until = (opex_date - today).days
            if 0 <= days_until <= 3:
                if not any(e['date'] == opex['date'] and '期权' in e['type'] for e in events):
                    events.append({
                        'date': opex['date'],
                        'type': opex['type'],
                        'note': opex.get('note', ''),
                        'days_until': days_until,
                        'impact': '中'
                    })
        except Exception:
            continue

    return sorted(events, key=lambda x: x['days_until'])

def match_patterns(skill_results, patterns_config, historical_db=None):
    """历史模式匹配（v2.0: 支持 historical_patterns + historical_database 双源匹配）"""
    matches = []

    # 提取当前信号特征
    current_signals = set()
    current_keywords = set()
    for sr in skill_results:
        if sr.score < -0.5:
            current_signals.add("risk_off")
            current_keywords.add("危机")
        if sr.score > 0.5:
            current_signals.add("risk_on")
        if sr.score < -0.3:
            current_keywords.add("收紧")
        for sig in sr.signals:
            if isinstance(sig, Signal) and sig.triggered:
                current_signals.add(sig.name.lower())
                for kw in ['vix', '流动性', '日元', '套利', '恐慌', '美债', '黄金', '超卖', '超买', '信用']:
                    if kw in sig.name.lower() or kw in sig.detail.lower():
                        current_keywords.add(kw)

    # 源1: historical_patterns.json（原有6个模式）
    patterns = patterns_config.get('patterns', [])
    for pattern in patterns:
        pattern_keywords = set()
        for ts in pattern.get('trigger_signals', []):
            for keyword in ['vix', '流动性', '日元', '套利', '恐慌', '美债', '黄金', '信用', '超卖']:
                if keyword in ts.lower() or keyword in ts:
                    pattern_keywords.add(keyword)
        overlap = len(current_keywords & pattern_keywords)
        if overlap >= 1:
            matches.append({
                'pattern_name': pattern['name'],
                'date': pattern['date'],
                'lesson': pattern['lesson'],
                'match_score': overlap,
                'resolution': pattern['resolution']
            })

    # 源2: historical_database.json（10个重大事件复盘）
    if historical_db:
        events = historical_db.get('major_market_events', {}).get('events', [])
        for event in events:
            event_keywords = set()
            # 从事件的 key_lessons 和 key_data_points 提取关键词
            for lesson in event.get('key_lessons', []):
                for kw in ['流动性', '恐慌', '美联储', 'vix', '信用', '杠杆', '日元', '套利', '黄金', '美债']:
                    if kw in lesson.lower():
                        event_keywords.add(kw)
            for dp in event.get('key_data_points', []):
                for kw in ['vix', '流动性', '信用', '恐慌', '美债']:
                    if kw in dp.lower():
                        event_keywords.add(kw)

            overlap = len(current_keywords & event_keywords)
            if overlap >= 1:
                lessons = event.get('key_lessons', [])
                lesson_text = lessons[0] if lessons else event.get('description', '')
                matches.append({
                    'pattern_name': f"{event.get('name', '未知事件')} ({event.get('date_range', '')})",
                    'date': event.get('date_range', ''),
                    'lesson': lesson_text[:80] if lesson_text else '',
                    'match_score': overlap,
                    'resolution': '; '.join(lessons[:2]) if len(lessons) > 1 else lesson_text
                })

    return sorted(matches, key=lambda x: x['match_score'], reverse=True)[:3]

def synthesize_analysis(skill_results, stock_ratings, overnight, upcoming_events, pattern_matches, config=None):
    """综合分析：汇总10个Skill结果，动态权重+交叉验证+投资逻辑链生成最终投资建议"""
    analysis = DailyAnalysis()
    analysis.date = DATE_DISPLAY
    analysis.overnight_summary = overnight
    analysis.skill_results = skill_results
    analysis.stock_ratings = stock_ratings
    analysis.upcoming_events = upcoming_events
    analysis.pattern_matches = pattern_matches

    # 从配置读取权重，否则使用默认均匀权重
    skill_weight_keys = [
        'skill1_value_investing', 'skill2_crypto_signal', 'skill3_sentiment',
        'skill4_macro_liquidity', 'skill5_global_markets', 'skill6_credit_private',
        'skill7_precious_metals', 'skill8_yield_curve', 'skill9_volatility', 'skill10_hk_a_shares'
    ]
    if config:
        sw = config.get('skill_weights', {})
        weights = [sw.get(k, 0.10) for k in skill_weight_keys]
    else:
        weights = [0.10] * 10

    # ═══ 动态权重调整（市场状态自适应）═══
    # 当某些信号极端时，提升其权重影响
    for i, sr in enumerate(skill_results):
        if sr.error or i >= len(weights):
            continue
        # 极端信号加权（|score|>0.5时权重提升50%）
        if abs(sr.score) > 0.5:
            weights[i] *= 1.5
        # 高置信度加权
        if sr.confidence > 0.8:
            weights[i] *= 1.2

    # 只取有效的Skill结果
    valid_scores = []
    for i, sr in enumerate(skill_results):
        w = weights[i] if i < len(weights) else 0.10
        if not sr.error:
            valid_scores.append((sr.score, w, sr))

    if valid_scores:
        total_weight = sum(w for _, w, _ in valid_scores)
        analysis.overall_score = sum(s * w for s, w, _ in valid_scores) / total_weight if total_weight > 0 else 0
    else:
        analysis.overall_score = 0

    # ═══ 交叉验证 & 核心矛盾识别 ═══
    cross_validation = []
    contradictions = []

    # 流动性(4) vs 信贷(6) 交叉验证
    s4 = skill_results[3] if len(skill_results) > 3 and not skill_results[3].error else None
    s6 = skill_results[5] if len(skill_results) > 5 and not skill_results[5].error else None
    if s4 and s6:
        if (s4.score > 0.2 and s6.score > 0.2):
            cross_validation.append("流动性充裕+信贷宽松 → 双重确认风险偏好环境，利好权益资产")
        elif (s4.score < -0.2 and s6.score < -0.2):
            cross_validation.append("流动性收紧+信贷恶化 → 双重确认防御环境，建议降低风险敞口")
        elif abs(s4.score - s6.score) > 0.4:
            contradictions.append(f"流动性({s4.score:+.2f})与信贷({s6.score:+.2f})信号分歧 → 市场处于转折点，需密切监控")

    # 情绪(3) vs 波动率(9) 交叉验证
    s3 = skill_results[2] if len(skill_results) > 2 and not skill_results[2].error else None
    s9 = skill_results[8] if len(skill_results) > 8 and not skill_results[8].error else None
    if s3 and s9:
        if s3.score < -0.3 and s9.score < -0.3:
            cross_validation.append("极度恐慌+波动率飙升 → 可能接近市场底部，关注反转信号")
        elif s3.score > 0.3 and s9.score > 0.3:
            contradictions.append("贪婪情绪+波动率自满 → 逆向指标预警，市场可能过度乐观")

    # 全球联动(5) vs 港股A股(10) 区域验证
    s5 = skill_results[4] if len(skill_results) > 4 and not skill_results[4].error else None
    s10 = skill_results[9] if len(skill_results) > 9 and not skill_results[9].error else None
    if s5 and s10:
        if s5.score > 0.2 and s10.score < -0.2:
            contradictions.append("全球Risk-On但中国资产走弱 → 关注中国特有风险因素(政策/汇率/地缘)")
        elif s5.score < -0.2 and s10.score > 0.2:
            cross_validation.append("全球Risk-Off但中国资产逆势走强 → 中国资产独立行情，政策利好驱动")

    # 商品(7) vs 收益率(8) 通胀验证
    s7 = skill_results[6] if len(skill_results) > 6 and not skill_results[6].error else None
    s8 = skill_results[7] if len(skill_results) > 7 and not skill_results[7].error else None
    if s7 and s8:
        if s7.score > 0.2 and s8.score < -0.2:
            cross_validation.append("商品走强+收益率上行 → 再通胀交易确认，利好实物资产和周期股")

    analysis.cross_validation = cross_validation
    analysis.contradictions = contradictions

    # ═══ 风险暴露分析 ═══
    risk_exposures = []
    bullish_skills = [sr for sr in skill_results if not sr.error and sr.score > 0.2]
    bearish_skills = [sr for sr in skill_results if not sr.error and sr.score < -0.2]
    neutral_skills = [sr for sr in skill_results if not sr.error and -0.2 <= sr.score <= 0.2]

    if len(bearish_skills) >= 3:
        risk_exposures.append(f"⚠️ {len(bearish_skills)}个Skill发出看空信号，系统性风险升高")
    if len(bullish_skills) >= 7:
        risk_exposures.append("⚠️ 大面积看多，需警惕一致性预期反转")
    if len(neutral_skills) >= 6:
        risk_exposures.append("市场方向不明，多数指标中性，建议观望等待催化剂")

    analysis.risk_exposures = risk_exposures

    # ═══ 新闻热点摘要（从Skill新闻中提取跨领域主题）═══
    news_themes = []
    all_news_titles = []
    for sr in skill_results:
        if hasattr(sr, 'news_highlights') and sr.news_highlights:
            for n in sr.news_highlights:
                all_news_titles.append(n.title.lower())

    # 关键主题检测
    theme_keywords = {
        '关税/贸易战': ['tariff', 'trade war', 'tariffs', '关税', '贸易战'],
        '私募信贷风险': ['private credit', 'blue owl', 'obdc', 'clo', '私募信贷', 'leveraged loan'],
        'AI/科技冲击': ['ai ', 'artificial intelligence', 'saas', 'chatgpt', 'ai冲击'],
        '地缘政治': ['geopolitical', 'ukraine', 'russia', 'iran', 'taiwan', '地缘'],
        '银行/金融风险': ['bank failure', 'bank crisis', 'banking', 'svb', '银行'],
        '通胀再升温': ['inflation', 'cpi', 'pce', '通胀', '物价'],
        '衰退担忧': ['recession', 'downturn', 'layoffs', '衰退', '裁员'],
        '加密货币暴跌': ['crypto crash', 'bitcoin crash', '加密货币 暴跌', '比特币 暴跌'],
    }

    for theme, keywords in theme_keywords.items():
        count = sum(1 for title in all_news_titles if any(kw in title for kw in keywords))
        if count >= 2:  # 至少2条相关新闻才算主题
            news_themes.append(f"📰 {theme}（{count}条相关报道）")

    analysis.news_themes = news_themes

    # ═══ 投资逻辑链叙事 ═══
    narrative_parts = []
    score = analysis.overall_score

    # 宏观环境定调
    if s4 and not s4.error:
        if s4.score > 0.2:
            narrative_parts.append("当前宏观流动性环境偏宽松，支撑风险资产估值")
        elif s4.score < -0.2:
            narrative_parts.append("宏观流动性趋紧，对风险资产构成压力")
        else:
            narrative_parts.append("宏观流动性维持中性，边际变化需关注")

    # 信贷&信用验证
    if s6 and not s6.error:
        if s6.score < -0.3:
            narrative_parts.append("信贷市场出现压力信号，需警惕尾部风险传导")

    # 市场结构判断
    if s3 and not s3.error:
        if s3.score < -0.3:
            narrative_parts.append("市场情绪处于恐慌区间，历史上往往酝酿反弹机会")
        elif s3.score > 0.3:
            narrative_parts.append("市场情绪偏贪婪，短期回调风险累积")

    analysis.investment_narrative = "。".join(narrative_parts) + "。" if narrative_parts else ""

    # 生成综合评级和操作建议
    if score > 0.5:
        analysis.overall_rating = "强烈看多"
        analysis.overall_action = "积极加仓，提高权益仓位至85%+"
    elif score > 0.2:
        analysis.overall_rating = "偏多"
        analysis.overall_action = "适度加仓，维持75%权益仓位"
    elif score > -0.2:
        analysis.overall_rating = "中性"
        analysis.overall_action = "维持当前仓位，关注边际变化"
    elif score > -0.5:
        analysis.overall_rating = "偏空"
        analysis.overall_action = "适度减仓，降至65%权益仓位"
    else:
        analysis.overall_rating = "强烈看空"
        analysis.overall_action = "大幅减仓至50%以下，增加现金和避险资产"

    # 关键风险预警
    warnings = []
    for sr in skill_results:
        if sr.score < -0.5:
            warnings.append(f"⚠️ {sr.skill_name}: {sr.rating} — {sr.action}")
        if sr.error:
            warnings.append(f"⚠️ {sr.skill_name}数据异常: {sr.error[:50]}")

    # 新增：矛盾信号预警
    for c in contradictions:
        warnings.append(f"🔀 {c}")

    if upcoming_events:
        for evt in upcoming_events[:3]:
            warnings.append(f"📅 {evt['days_until']}天后: {evt['type']} ({evt['date']})")

    if pattern_matches:
        for pm in pattern_matches[:2]:
            warnings.append(f"🔍 历史模式匹配: {pm['pattern_name']} — {pm['lesson'][:50]}")

    analysis.key_warnings = warnings

    # 每日预测（增加叙事）
    skill_actions = [sr.action for sr in skill_results if not sr.error]
    prediction_parts = [
        f"综合评分: {score:.2f}/1.0 → {analysis.overall_rating}",
        f"操作建议: {analysis.overall_action}",
    ]
    if analysis.investment_narrative:
        prediction_parts.append(f"逻辑链: {analysis.investment_narrative[:80]}")
    if pattern_matches:
        prediction_parts.append(f"历史参照: {pattern_matches[0]['pattern_name']} → {pattern_matches[0]['lesson'][:60]}")
    if upcoming_events:
        prediction_parts.append(f"近期关注: {upcoming_events[0]['type']} (T-{upcoming_events[0]['days_until']}天)")

    analysis.prediction_parts = prediction_parts
    analysis.prediction = " | ".join(prediction_parts)

    return analysis


# ═══════════════════════════════════════════════════════════
# PDF报告渲染
# ═══════════════════════════════════════════════════════════

def render_pdf(analysis: DailyAnalysis):
    """渲染MBB风格投资分析报告PDF（v3.0: 10-Skill架构）"""
    filename = os.path.join(os.path.dirname(__file__),
                           f"投资Agent-每日分析-{DATE}.pdf")

    if analysis.overall_score > 0.2:
        accent = INV_GREEN
    elif analysis.overall_score < -0.2:
        accent = INV_RED
    else:
        accent = INV_BLUE

    r = MBBReportEngine(
        filename,
        title="投资Agent · 每日分析与预测 v3.3",
        subtitle=f"6层知识库 · 10维决策框架 · 全球资本市场  |  {DATE_DISPLAY}",
        accent_color=accent,
        page_scale=16.0  # 10个Skill需要更长页面
    )

    r.draw_header()

    # ═══ 综合结论 ═══
    r.draw_section_title("📊 今日综合结论", accent)
    score = analysis.overall_score
    score_color = INV_GREEN if score > 0.2 else (INV_RED if score < -0.2 else INV_BLUE)
    r.draw_insight_card({
        'category': f"综合评级: {analysis.overall_rating}",
        'priority': max(1, min(5, int(abs(score) * 5) + 1)),
        'color': score_color,
        'thesis': f"综合评分 {score:.2f}/1.0 — {analysis.overall_action}",
        'detail': analysis.prediction,
        'impact': " | ".join([f"{sr.skill_name}:{sr.action}" for sr in analysis.skill_results[:5] if not sr.error]),
        'action': analysis.overall_action
    })

    if analysis.key_warnings:
        warning_items = [(w[:60], "", "", INV_GOLD) for w in analysis.key_warnings[:8]]
        r.draw_info_card("⚠️ 关键预警与提醒", warning_items, INV_RED)

    # ═══ Overnight市场摘要 ═══
    r.draw_section_title("🌙 隔夜市场摘要", NAVY)
    overnight = analysis.overnight_summary
    if overnight.get('indices'):
        index_items = []
        for idx in overnight['indices']:
            ch = f"{idx['change']:+.2f}%"
            ch_color = INV_GREEN if idx['change'] > 0 else INV_RED
            if idx.get('is_etf_proxy'):
                price_str = "(ETF代理)"
            else:
                price_str = f"{idx['price']:,.2f}" if idx['price'] < 100000 else f"{idx['price']:,.0f}"
            index_items.append((idx['name'], price_str, ch, ch_color))
        r.draw_info_card("全球主要指数", index_items, INV_BLUE)

    if overnight.get('crypto'):
        crypto_items = [(c['name'], f"${c['price']:,.0f}", f"{c['change']:+.2f}%",
                        INV_GREEN if c['change'] > 0 else INV_RED) for c in overnight['crypto']]
        r.draw_info_card("加密货币", crypto_items, INV_PURPLE)

    if overnight.get('commodities'):
        comm_items = []
        for c in overnight['commodities']:
            price = c['price']
            price_str = f"{price:,.2f}" if price >= 1000 else (f"{price:.2f}" if price >= 10 else f"{price:.4f}")
            comm_items.append((c['name'][:15], price_str, f"{c['change']:+.2f}%",
                              INV_GREEN if c['change'] > 0 else INV_RED))
        r.draw_info_card("宏观/商品指标", comm_items, INV_GOLD)

    # ═══ 10个Skill逐一渲染 ═══
    skill_icons = ["📈", "₿", "🎭", "💧", "🌍", "🏦", "🪙", "📉", "🌪️", "🇨🇳"]
    for i, sr in enumerate(analysis.skill_results):
        sname = sr.skill_name
        icon = skill_icons[i] if i < len(skill_icons) else "📊"
        sr_color = SKILL_COLORS[i] if i < len(SKILL_COLORS) else INV_BLUE

        r.draw_section_title(f"{icon} Skill {i+1}: {sname}", sr_color)

        if sr.error:
            r.draw_insight_card({
                'category': f'Skill {i+1} 异常', 'priority': 1, 'color': GRAY_LIGHT,
                'thesis': sr.error or "数据获取失败",
                'detail': f'{sname}暂时不可用', 'impact': '无', 'action': '等待数据恢复'
            })
            continue

        signal_detail = " | ".join([
            f"{'✅' if s.triggered else '❌'} {s.detail}"
            for s in sr.signals if isinstance(s, Signal)
        ][:6])  # 最多显示6个信号

        r.draw_insight_card({
            'category': f"{sname}: {sr.rating}",
            'priority': max(1, min(5, int(abs(sr.score) * 5) + 1)),
            'color': sr_color,
            'thesis': sr.detail,
            'detail': signal_detail,
            'impact': f"得分: {sr.score:.2f} | 置信度: {sr.confidence:.0%}",
            'action': sr.action
        })

        # PDF新闻摘要（每个Skill最多展示3条）
        if hasattr(sr, 'news_highlights') and sr.news_highlights:
            news_items = [(
                f"{'🇨🇳' if n.language == 'zh' else '🇺🇸'} [{n.source[:12]}]",
                n.title[:55] + ('...' if len(n.title) > 55 else ''),
                n.published[:16] if n.published else '',
                sr_color
            ) for n in sr.news_highlights[:3]]
            r.draw_info_card(f"📰 Skill {i+1} 关联新闻", news_items, sr_color)

    # ═══ Skill 1 股票评级详情（特殊处理）═══
    if analysis.stock_ratings:
        r.draw_section_title("📋 股票评级明细", INV_BLUE)
        a_stocks = [(f"[A] {s.ticker} {s.name}", f"${s.price:,.1f}", f"{s.change_pct:+.1f}%", INV_GREEN)
                    for s in analysis.stock_ratings if s.rating == 'A']
        b_stocks = [(f"[B] {s.ticker} {s.name}", f"${s.price:,.1f}", f"{s.change_pct:+.1f}%", INV_BLUE)
                    for s in analysis.stock_ratings if s.rating == 'B']
        cd_stocks = [(f"[{s.rating}] {s.ticker} {s.name}", f"${s.price:,.1f}", f"{s.change_pct:+.1f}%",
                     INV_RED if s.rating == 'D' else GRAY_LIGHT) for s in analysis.stock_ratings if s.rating in ('C', 'D')]

        if a_stocks:
            r.draw_info_card("A级标的（优秀）— 持有/加仓", a_stocks, INV_GREEN)
        if b_stocks:
            r.draw_info_card("B级标的（良好）— 持有", b_stocks, INV_BLUE)
        if cd_stocks:
            r.draw_info_card("C/D级标的（待优化）", cd_stocks, INV_RED)

        detail_items = [(f"{s.ticker}", f"ROE={s.roe:.0%} PE={s.pe_ratio:.1f}",
                        f"负债={s.debt_ratio:.0%} 护城河={s.moat_count}项",
                        INV_GREEN if s.rating == 'A' else (INV_BLUE if s.rating == 'B' else INV_RED))
                       for s in analysis.stock_ratings if s.rating in ('A', 'B', 'C', 'D')]
        if detail_items:
            r.draw_info_card("财务指标明细", detail_items, NAVY)

    # ═══ 历史模式匹配 ═══
    if analysis.pattern_matches:
        r.draw_section_title("🔍 历史模式匹配参照", NAVY)
        for pm in analysis.pattern_matches:
            r.draw_insight_card({
                'category': pm['pattern_name'],
                'priority': min(5, pm['match_score'] + 2),
                'color': INV_GOLD,
                'thesis': f"历史日期: {pm['date']}",
                'detail': pm.get('resolution', ''),
                'impact': f"匹配度: {pm['match_score']}个关键信号重合",
                'action': pm['lesson']
            })

    # ═══ 近期重要事件 ═══
    if analysis.upcoming_events:
        r.draw_section_title("📅 近期重要事件", INV_GOLD)
        event_timeline = []
        for evt in analysis.upcoming_events[:6]:
            evt_color = INV_RED if evt['impact'] == '高' else INV_GOLD
            event_timeline.append((f"T-{evt['days_until']}天", evt['type'], evt.get('note', ''), evt['date'], evt_color))
        if event_timeline:
            r.draw_timeline(event_timeline)

    # ═══ 今日操作清单 ═══
    r.draw_section_title("🎯 今日操作建议", accent)
    actions = [("P0", analysis.overall_action, "投资决策", "当日", accent)]
    for sr in analysis.skill_results:
        if not sr.error and abs(sr.score) > 0.3:
            priority = "P1" if abs(sr.score) > 0.5 else "P2"
            p_color = INV_RED if sr.score < -0.3 else INV_GREEN
            actions.append((priority, f"{sr.skill_name}: {sr.action}", "Agent建议", "当日", p_color))
    if analysis.upcoming_events:
        evt = analysis.upcoming_events[0]
        actions.append(("P1", f"关注: {evt['type']} (T-{evt['days_until']}天)", "事件提醒", evt['date'], INV_GOLD))
    r.draw_actions(actions[:10])

    # ═══ 页脚 ═══
    r.draw_footer(f"数据: Alpha Vantage + FRED + AkShare + F&G + Google News  |  框架: 6层知识库→10Skill决策→综合预测  |  投资Agent v3.3 · {DATE_DISPLAY}")
    r.save()

    return filename


# ═══════════════════════════════════════════════════════════
# Markdown报告渲染（MBB风格结构化分析）
# ═══════════════════════════════════════════════════════════

def render_markdown(analysis: DailyAnalysis) -> str:
    """渲染MBB风格投资分析报告Markdown"""
    dm = get_manager()
    macro = dm.fetch_macro_data() if dm else None
    lines = []
    a = lines.append

    # ═══ 标题与元数据 ═══
    a(f"# 投资Agent每日分析报告")
    a(f"")
    a(f"**日期**: {DATE_DISPLAY}（{datetime.now().strftime('%A')}）")
    a(f"**版本**: 投资Agent v3.3 · 10-Skill全球资本市场分析架构 + 实时新闻")
    a(f"**数据源**: Alpha Vantage + FRED + AkShare + CNN Fear & Greed + Google News RSS")
    a(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    a(f"")

    # ═══ Executive Summary ═══
    a(f"---")
    a(f"")
    a(f"## 📊 Executive Summary")
    a(f"")
    score = analysis.overall_score
    score_bar = "🟢" if score > 0.2 else ("🔴" if score < -0.2 else "🟡")
    a(f"| 维度 | 结论 |")
    a(f"|------|------|")
    a(f"| **综合评级** | {score_bar} **{analysis.overall_rating}** |")
    a(f"| **综合评分** | `{score:+.2f}` / 1.0 |")
    a(f"| **操作建议** | {analysis.overall_action} |")
    a(f"| **Skill覆盖** | {sum(1 for s in analysis.skill_results if not s.error)}/10 成功 |")
    a(f"")

    if analysis.prediction:
        parts = getattr(analysis, 'prediction_parts', None)
        if parts:
            a(f"> **今日预测**:")
            a(f">")
            for part in parts:
                a(f"> - {part}")
        else:
            a(f"> **今日预测**: {analysis.prediction}")
        a(f"")

    # ═══ 今日新闻热点主题 ═══
    if hasattr(analysis, 'news_themes') and analysis.news_themes:
        a(f"### 📰 今日新闻热点主题")
        a(f"")
        for theme in analysis.news_themes:
            a(f"- {theme}")
        a(f"")

    # ═══ 关键预警 ═══
    if analysis.key_warnings:
        a(f"### ⚠️ 关键预警")
        a(f"")
        for w in analysis.key_warnings:
            a(f"- {w}")
        a(f"")

    # ═══ 投资逻辑链（专业叙事）═══
    if hasattr(analysis, 'investment_narrative') and analysis.investment_narrative:
        a(f"### 🧠 投资逻辑链")
        a(f"")
        a(f"> {analysis.investment_narrative}")
        a(f"")

    # ═══ 交叉验证 & 矛盾分析 ═══
    has_cv = hasattr(analysis, 'cross_validation') and analysis.cross_validation
    has_ct = hasattr(analysis, 'contradictions') and analysis.contradictions
    if has_cv or has_ct:
        a(f"### 🔗 Skill间交叉验证")
        a(f"")
        if has_cv:
            for cv in analysis.cross_validation:
                a(f"- ✅ **确认**: {cv}")
        if has_ct:
            for ct in analysis.contradictions:
                a(f"- 🔀 **分歧**: {ct}")
        a(f"")

    # ═══ 风险暴露分析 ═══
    if hasattr(analysis, 'risk_exposures') and analysis.risk_exposures:
        a(f"### 📊 风险暴露分析")
        a(f"")
        for re_item in analysis.risk_exposures:
            a(f"- {re_item}")
        a(f"")

    # ═══ 隔夜市场速览 ═══
    a(f"---")
    a(f"")
    a(f"## 🌙 隔夜市场速览")
    a(f"")
    overnight = analysis.overnight_summary

    if overnight.get('indices'):
        a(f"### 全球主要指数")
        a(f"")
        a(f"| 指数 | 价格 | 日变化 | 趋势 |")
        a(f"|------|------|--------|------|")
        for idx in overnight['indices']:
            ch = idx['change']
            trend = "📈" if ch > 0 else ("📉" if ch < 0 else "➡️")
            # ETF代理：绝对价格无参考意义，仅标注为代理
            if idx.get('is_etf_proxy'):
                price_str = f"*(ETF代理)*"
            else:
                price_str = f"{idx['price']:,.2f}" if idx['price'] < 100000 else f"{idx['price']:,.0f}"
            a(f"| {idx['name']} | {price_str} | {ch:+.2f}% | {trend} |")
        a(f"")

    if overnight.get('crypto'):
        a(f"### 加密货币")
        a(f"")
        a(f"| 资产 | 价格 | 日变化 | 趋势 |")
        a(f"|------|------|--------|------|")
        for c in overnight['crypto']:
            ch = c['change']
            trend = "📈" if ch > 0 else ("📉" if ch < 0 else "➡️")
            a(f"| {c['name']} | ${c['price']:,.0f} | {ch:+.2f}% | {trend} |")
        a(f"")

    if overnight.get('commodities'):
        a(f"### 宏观/商品指标")
        a(f"")
        a(f"| 品种 | 价格 | 日变化 | 趋势 |")
        a(f"|------|------|--------|------|")
        for c in overnight['commodities']:
            ch = c['change']
            trend = "📈" if ch > 0 else ("📉" if ch < 0 else "➡️")
            price = c['price']
            # 根据价格量级智能格式化
            if price >= 1000:
                price_str = f"{price:,.2f}"
            elif price >= 10:
                price_str = f"{price:.2f}"
            else:
                price_str = f"{price:.4f}"
            a(f"| {c['name']} | {price_str} | {ch:+.2f}% | {trend} |")
        a(f"")

    # ═══ FRED宏观数据仪表盘 ═══
    if macro and macro.source == "FRED":
        a(f"---")
        a(f"")
        a(f"## 📡 宏观经济仪表盘（FRED实时数据）")
        a(f"")
        a(f"| 指标 | 最新值 | 说明 |")
        a(f"|------|--------|------|")
        if macro.fed_funds_rate is not None:
            a(f"| 联邦基金利率 | **{macro.fed_funds_rate:.2f}%** | Fed政策利率 |")
        if macro.us10y_yield is not None:
            a(f"| 10Y国债收益率 | **{macro.us10y_yield:.2f}%** | 长端利率基准 |")
        if macro.us2y_yield is not None:
            a(f"| 2Y国债收益率 | **{macro.us2y_yield:.2f}%** | 短端利率 |")
        if macro.us2s10s_spread is not None:
            inv_mark = " ⚠️倒挂" if macro.us2s10s_spread < 0 else ""
            a(f"| 2s10s利差 | **{macro.us2s10s_spread:+.2f}%** | {inv_mark}收益率曲线 |")
        if macro.us3m10s_spread is not None:
            a(f"| 3m10s利差 | **{macro.us3m10s_spread:+.2f}%** | 更准确衰退指标 |")
        if macro.hy_spread is not None:
            a(f"| 高收益债利差 | **{macro.hy_spread:.2f}%** | 信用风险度量 |")
        if macro.sofr is not None:
            a(f"| SOFR | **{macro.sofr:.2f}%** | 隔夜融资利率 |")
        if macro.cpi_yoy is not None:
            a(f"| CPI YoY（粘性） | **{macro.cpi_yoy:.2f}%** | 通胀趋势 |")
        if macro.core_pce is not None:
            a(f"| Core PCE YoY | **{macro.core_pce:.2f}%** | Fed首选通胀指标 |")
        if macro.unemployment is not None:
            a(f"| 失业率 | **{macro.unemployment:.1f}%** | 劳动力市场 |")
        if macro.net_liquidity is not None:
            a(f"| 净流动性 | **{macro.net_liquidity:,.0f}B** ({macro.net_liquidity/1000:.2f}万亿) | WALCL-TGA-RRP |")
        if macro.fed_balance_sheet is not None:
            a(f"| Fed资产负债表 | **{macro.fed_balance_sheet/1e6:.2f}万亿** | WALCL |")
        if macro.m2_supply is not None:
            a(f"| M2货币供应 | **{macro.m2_supply:,.0f}B** | 广义货币 |")
        a(f"")

    # ═══ 10个Skill逐一详析 ═══
    a(f"---")
    a(f"")
    a(f"## 🧠 10-Skill决策框架详析")
    a(f"")
    skill_icons = ["📈", "₿", "🎭", "💧", "🌍", "🏦", "🪙", "📉", "🌪️", "🇨🇳"]

    # Skill总览表格
    a(f"### Skill总览")
    a(f"")
    a(f"| # | Skill | 评级 | 评分 | 置信度 | 操作建议 |")
    a(f"|---|-------|------|------|--------|----------|")
    for i, sr in enumerate(analysis.skill_results):
        icon = skill_icons[i] if i < len(skill_icons) else "📊"
        if sr.error:
            a(f"| {i+1} | {icon} {sr.skill_name} | ❌ 异常 | - | - | {sr.error[:30]} |")
        else:
            score_icon = "🟢" if sr.score > 0.2 else ("🔴" if sr.score < -0.2 else "🟡")
            a(f"| {i+1} | {icon} {sr.skill_name} | {score_icon} {sr.rating} | `{sr.score:+.2f}` | {sr.confidence:.0%} | {sr.action} |")
    a(f"")

    # 各Skill详细分析
    for i, sr in enumerate(analysis.skill_results):
        icon = skill_icons[i] if i < len(skill_icons) else "📊"
        a(f"### {icon} Skill {i+1}: {sr.skill_name}")
        a(f"")

        if sr.error:
            a(f"> ❌ **异常**: {sr.error}")
            a(f"")
            continue

        score_icon = "🟢" if sr.score > 0.2 else ("🔴" if sr.score < -0.2 else "🟡")
        a(f"- **评级**: {score_icon} {sr.rating}")
        a(f"- **评分**: `{sr.score:+.2f}` / 1.0")
        a(f"- **置信度**: {sr.confidence:.0%}")
        a(f"- **操作建议**: {sr.action}")
        if sr.detail:
            a(f"- **详情**: {sr.detail}")
        a(f"")

        # Skill 1 特殊处理：展示个股评级分布摘要
        if i == 0 and analysis.stock_ratings:
            a(f"**个股评级分布**:")
            a(f"")
            a(f"| 评级 | 数量 | 标的 |")
            a(f"|------|------|------|")
            for grade, grade_icon in [("A", "🟢"), ("B", "🔵"), ("C", "🟡"), ("D", "🔴")]:
                grade_stocks = [s for s in analysis.stock_ratings if s.rating == grade]
                if grade_stocks:
                    tickers = ', '.join(s.ticker for s in grade_stocks)
                    a(f"| {grade_icon} {grade}级 | {len(grade_stocks)}只 | {tickers} |")
            na_stocks = [s for s in analysis.stock_ratings if s.rating == 'N/A']
            if na_stocks:
                tickers = ', '.join(s.ticker for s in na_stocks)
                a(f"| ⚪ 无数据 | {len(na_stocks)}只 | {tickers} |")
            a(f"")
            # A级标的亮点
            a_stocks = [s for s in analysis.stock_ratings if s.rating == 'A']
            if a_stocks:
                a(f"**A级标的亮点**:")
                a(f"")
                for s in a_stocks:
                    has_fund = s.roe != 0 or s.pe_ratio != 0
                    if has_fund:
                        a(f"- **{s.ticker}**({s.name}): ROE={s.roe:.0%}, PE={s.pe_ratio:.1f}, 负债率={s.debt_ratio:.0%}, 护城河={s.moat_count}项")
                    else:
                        a(f"- **{s.ticker}**({s.name}): ${s.price:,.1f} ({s.change_pct:+.1f}%)")
                a(f"")
            # D级标的预警
            d_stocks = [s for s in analysis.stock_ratings if s.rating == 'D']
            if d_stocks:
                a(f"**D级标的预警**:")
                a(f"")
                for s in d_stocks:
                    has_fund = s.roe != 0 or s.pe_ratio != 0
                    if has_fund:
                        a(f"- ⚠️ **{s.ticker}**({s.name}): ROE={s.roe:.0%}, PE={s.pe_ratio:.1f}, 负债率={s.debt_ratio:.0%}, 护城河={s.moat_count}项")
                    else:
                        a(f"- ⚠️ **{s.ticker}**({s.name}): ${s.price:,.1f} ({s.change_pct:+.1f}%)")
                a(f"")

        # 信号明细
        if sr.signals:
            a(f"**信号明细**:")
            a(f"")
            a(f"| 状态 | 信号 | 详情 |")
            a(f"|------|------|------|")
            for s in sr.signals:
                if isinstance(s, Signal):
                    status = "✅触发" if s.triggered else "❌未触发"
                    a(f"| {status} | {s.name} | {s.detail} |")
            a(f"")

        # 关联新闻资讯
        if hasattr(sr, 'news_highlights') and sr.news_highlights:
            a(f"**📰 关联新闻资讯** (过去24小时):")
            a(f"")
            a(f"| 语言 | 来源 | 标题 | 时间 |")
            a(f"|------|------|------|------|")
            news_rows = format_news_for_markdown(sr.news_highlights, max_display=5)
            for row in news_rows:
                a(row)
            a(f"")

    # ═══ 股票评级明细 ═══
    if analysis.stock_ratings:
        a(f"---")
        a(f"")
        a(f"## 📋 个股评级明细")
        a(f"")
        a(f"| 评级 | Ticker | 公司 | 价格 | 日涨跌 | ROE | PE | 负债率 | 护城河 |")
        a(f"|------|--------|------|------|--------|-----|-----|--------|--------|")
        for s in sorted(analysis.stock_ratings, key=lambda x: x.rating):
            grade_icon = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}.get(s.rating, "⚪")
            # 缓存降级时（ROE/PE全0）显示"-"而非0
            has_fundamentals = s.roe != 0 or s.pe_ratio != 0
            roe_str = f"{s.roe:.0%}" if has_fundamentals else "-"
            pe_str = f"{s.pe_ratio:.1f}" if has_fundamentals else "-"
            debt_str = f"{s.debt_ratio:.0%}" if has_fundamentals else "-"
            moat_str = f"{s.moat_count}项" if has_fundamentals else "-"
            price_str = f"${s.price:,.1f}" if s.price > 0 else "N/A"
            change_str = f"{s.change_pct:+.1f}%" if s.price > 0 else "-"
            # N/A评级特殊标注
            rating_label = f"{grade_icon} {s.rating}"
            if s.rating == 'N/A':
                rating_label = "⚪ 无数据"
            elif s.rating == 'C' and not has_fundamentals:
                rating_label = f"{grade_icon} C(仅价格)"
            a(f"| {rating_label} | {s.ticker} | {s.name[:12]} | {price_str} | {change_str} | {roe_str} | {pe_str} | {debt_str} | {moat_str} |")
        a(f"")

    # ═══ 历史模式匹配 ═══
    if analysis.pattern_matches:
        a(f"---")
        a(f"")
        a(f"## 🔍 历史模式匹配")
        a(f"")
        for pm in analysis.pattern_matches:
            a(f"### {pm['pattern_name']}")
            a(f"")
            a(f"- **历史日期**: {pm['date']}")
            a(f"- **匹配度**: {pm['match_score']}个关键信号重合")
            if pm.get('resolution'):
                a(f"- **历史结果**: {pm['resolution']}")
            a(f"- **经验教训**: {pm['lesson']}")
            a(f"")

    # ═══ 近期重要事件 ═══
    if analysis.upcoming_events:
        a(f"---")
        a(f"")
        a(f"## 📅 近期重要事件")
        a(f"")
        a(f"| 时间 | 类型 | 日期 | 影响 | 备注 |")
        a(f"|------|------|------|------|------|")
        for evt in analysis.upcoming_events[:8]:
            impact_icon = "🔴" if evt['impact'] == '高' else "🟡"
            a(f"| T-{evt['days_until']}天 | {evt['type']} | {evt['date']} | {impact_icon} {evt['impact']} | {evt.get('note', '')} |")
        a(f"")

    # ═══ 今日操作清单 ═══
    a(f"---")
    a(f"")
    a(f"## 🎯 今日操作清单")
    a(f"")
    a(f"| 优先级 | 操作 | 来源 | 时效 |")
    a(f"|--------|------|------|------|")
    a(f"| **P0** | {analysis.overall_action} | 综合决策 | 当日 |")
    for sr in analysis.skill_results:
        if not sr.error and abs(sr.score) > 0.3:
            priority = "P1" if abs(sr.score) > 0.5 else "P2"
            a(f"| **{priority}** | {sr.skill_name}: {sr.action} | Agent建议 | 当日 |")
    if analysis.upcoming_events:
        evt = analysis.upcoming_events[0]
        a(f"| **P1** | 关注: {evt['type']} (T-{evt['days_until']}天) | 事件提醒 | {evt['date']} |")
    a(f"")

    # ═══ 数据源诊断 ═══
    a(f"---")
    a(f"")
    a(f"## 📡 数据源状态")
    a(f"")
    if dm:
        stats = dm.get_stats()
        a(f"| 数据源 | 状态 | 说明 |")
        a(f"|--------|------|------|")
        src_desc = {
            'alpha_vantage': 'Alpha Vantage（主数据源：全球行情/ETF/加密/基本面）',
            'fred': 'FRED联储数据（利率/CPI/GDP/净流动性）',
            'akshare': 'AkShare（北向资金/AH溢价/融资融券）',
            'yfinance': 'Yahoo Finance（降级备用：AV不支持的指数）',
            'fear_and_greed': 'CNN恐惧贪婪指数',
        }
        for src, status in stats['data_sources'].items():
            icon = '✅' if status == 'active' else ('⚠️' if status in ('not_installed', 'fallback', 'rate_limited') else '❌')
            desc = src_desc.get(src, src)
            a(f"| {icon} {src} | {status} | {desc} |")

        # 新闻数据源统计
        news_total = sum(len(sr.news_highlights) for sr in analysis.skill_results if hasattr(sr, 'news_highlights'))
        news_skills = sum(1 for sr in analysis.skill_results if hasattr(sr, 'news_highlights') and sr.news_highlights)
        if news_total > 0:
            a(f"| ✅ google_news | active | Google News RSS（{news_total}条新闻覆盖{news_skills}/10个Skill） |")
        else:
            a(f"| ⚠️ google_news | no_data | Google News RSS（未获取到新闻） |")
        a(f"")

    # ═══ 页脚 ═══
    a(f"---")
    a(f"")
    a(f"*数据: Alpha Vantage + FRED + AkShare + F&G + Google News | 框架: 6层知识库→10Skill决策→综合预测 | 投资Agent v3.3 · {DATE_DISPLAY}*")
    a(f"")
    a(f"*⚠️ 免责声明: 本报告由AI系统自动生成，仅供参考，不构成投资建议。投资有风险，决策需谨慎。*")

    # 写入文件
    md_filename = os.path.join(os.path.dirname(__file__),
        f"投资Agent-每日分析-{datetime.now().strftime('%Y%m%d')}.md")
    content = "\n".join(lines)
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✅ MD报告: {os.path.basename(md_filename)} ({len(lines)}行)")
    return md_filename


# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════

def generate(news_data=None):
    """投资Agent主入口 v3.3（10-Skill全球资本市场分析 + 实时新闻 + 多源数据）"""
    print(f"\n{'='*60}")
    print(f"  🤖 投资Agent v3.3 - 每日分析与预测")
    print(f"  📅 {DATE_DISPLAY}")
    print(f"  🏗️ 10-Skill全球资本市场分析架构")
    print(f"  📡 多源数据: Alpha Vantage + FRED + AkShare + yfinance + Google News")
    print(f"{'='*60}\n")

    # 0. 初始化DataSourceManager（全局单例）
    reset_manager()  # 每次运行重置缓存
    config_early = load_config()
    dm = get_manager(config_early)
    print("📡 初始化数据源管理器...")
    stats = dm.get_stats()
    for src, status in stats['data_sources'].items():
        icon = '✅' if status == 'active' else ('⚠️' if status in ('not_installed', 'fallback', 'rate_limited') else '❌')
        print(f"  {icon} {src}: {status}")
    print()

    # 1. 加载六层知识库
    print("📚 加载知识库（六层架构）...")
    config = config_early
    dates_config = load_important_dates()
    patterns_config = load_historical_patterns()
    historical_db = load_historical_database()
    indicators_news = load_indicators_and_news()
    personal_exp = load_personal_experience()
    kb_count = sum(1 for x in [config, dates_config, patterns_config, historical_db, indicators_news, personal_exp] if x)
    print(f"  ✅ {kb_count}/6 知识库加载完成")
    if historical_db:
        top50_count = len(historical_db.get('us_stock_top50', {}).get('companies', []))
        events_count = len(historical_db.get('major_market_events', {}).get('events', []))
        print(f"  📊 历史数据库: Top{top50_count}公司 | {events_count}重大事件")
    if indicators_news:
        twitter_count = sum(len(cat.get('accounts', [])) for cat in indicators_news.get('twitter_key_accounts', {}).values() if isinstance(cat, dict) and 'accounts' in cat)
        print(f"  🐦 信息源: {twitter_count}个Twitter关键账号")
    if personal_exp:
        decisions = len(personal_exp.get('decision_log', {}).get('records', []))
        print(f"  📝 个人经验: {decisions}条决策记录")
    print()

    # 1.5 预加载全局市场数据（减少后续API调用）
    dm.preload_all(period="3mo")
    print()

    # 1.6 采集实时财经新闻（10个Skill领域 × 双语）
    print("📰 采集实时财经新闻...")
    try:
        all_news = get_all_news(force_refresh=True)
    except Exception as e:
        print(f"  ⚠️ 新闻采集异常: {e}，继续执行...")
        all_news = {}
    print()

    # 2. 采集Overnight市场摘要
    overnight = collect_overnight_summary(config)
    print()

    # 3. 运行10个决策Skill（各Skill间间隔避免API限流）
    import time
    print("🧠 运行决策框架（10个Skill）...\n")

    def run_skill(name, func, *args):
        try:
            return func(*args)
        except Exception as e:
            print(f"  ❌ {name} 异常: {e}")
            traceback.print_exc()
            return SkillResult(skill_name=name, rating="异常", score=0, error=str(e))

    # Skill 1: 估值评级（返回 tuple）
    try:
        skill1_result, stock_ratings = skill1_value_investing(config)
    except Exception as e:
        print(f"  ❌ Skill 1 异常: {e}")
        traceback.print_exc()
        skill1_result = SkillResult(skill_name="公司估值与质量评级", rating="异常", score=0, error=str(e))
        stock_ratings = []
    time.sleep(SKILL_DELAY)

    # Skill 2-10
    skill2_result = run_skill("加密货币周期与抄底", skill2_crypto_signal, config)
    time.sleep(SKILL_DELAY)

    skill3_result = run_skill("全球市场情绪监控", skill3_sentiment, config)
    time.sleep(SKILL_DELAY)

    skill4_result = run_skill("宏观流动性与央行监控", skill4_liquidity, config)
    time.sleep(SKILL_DELAY)

    skill5_result = run_skill("全球市场联动与资金流向", skill5_global_markets, config)
    time.sleep(SKILL_DELAY)

    skill6_result = run_skill("信贷市场与私募信用监控", skill6_credit, config)
    time.sleep(SKILL_DELAY)

    skill7_result = run_skill("贵金属与大宗商品周期", skill7_commodities, config)
    time.sleep(SKILL_DELAY)

    skill8_result = run_skill("收益率曲线与利率分析", skill8_yield_curve, config)
    time.sleep(SKILL_DELAY)

    skill9_result = run_skill("波动率微观结构", skill9_volatility, config)
    time.sleep(SKILL_DELAY)

    skill10_result = run_skill("港股与A股专项分析", skill10_hk_a_shares, config)

    skill_results = [
        skill1_result, skill2_result, skill3_result, skill4_result, skill5_result,
        skill6_result, skill7_result, skill8_result, skill9_result, skill10_result
    ]

    # 3.5 注入新闻数据到每个Skill结果
    if all_news:
        for i, sr in enumerate(skill_results):
            skill_id = i + 1
            news_items = all_news.get(skill_id, [])
            if news_items:
                sr.news_highlights = news_items
        news_total = sum(len(sr.news_highlights) for sr in skill_results)
        print(f"  📰 新闻注入完成: {news_total}条新闻分配到10个Skill")

    # 4. 检查近期事件
    print("\n📅 检查近期重要事件...")
    upcoming_events = check_upcoming_events(dates_config, indicators_news)
    if upcoming_events:
        for evt in upcoming_events[:3]:
            print(f"  → T-{evt['days_until']}天: {evt['type']}")
    else:
        print("  → 近7天无重大事件")

    # 5. 历史模式匹配
    print("\n🔍 历史模式匹配...")
    pattern_matches = match_patterns(skill_results, patterns_config, historical_db)
    if pattern_matches:
        for pm in pattern_matches[:2]:
            print(f"  → 匹配: {pm['pattern_name']} (相似度: {pm['match_score']})")
    else:
        print("  → 未匹配到显著历史模式")

    # 6. 综合分析（传入config以读取skill_weights）
    print("\n🎯 综合分析与预测...")
    analysis = synthesize_analysis(
        skill_results, stock_ratings, overnight,
        upcoming_events, pattern_matches, config
    )
    print(f"  → 综合评级: {analysis.overall_rating} (评分: {analysis.overall_score:.2f})")
    print(f"  → 操作建议: {analysis.overall_action}")

    # 7. 生成PDF + MD报告
    print(f"\n📄 生成分析报告...")
    filename = render_pdf(analysis)
    md_filename = render_markdown(analysis)

    print(f"\n{'='*60}")
    print(f"  ✅ 投资Agent v3.3 分析完成")
    print(f"  📄 PDF报告: {filename}")
    print(f"  📝 MD报告: {md_filename}")
    print(f"  📊 综合评级: {analysis.overall_rating}")
    print(f"  💡 操作建议: {analysis.overall_action}")
    print(f"  🧠 10个Skill运行: {sum(1 for s in skill_results if not s.error)}/10 成功")

    # 8. 数据源诊断
    dm.print_diagnostics()
    print(f"{'='*60}")

    return os.path.basename(filename)


if __name__ == "__main__":
    f = generate()
    print(f"\n产出: {f}")
