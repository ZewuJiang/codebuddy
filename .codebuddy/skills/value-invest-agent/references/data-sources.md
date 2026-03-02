# 数据源优先级与获取路径（v6全球六市场覆盖）

---

## ⚠️⚠️ 一手财报获取路径矩阵（最高优先级 — 铁律#19）

> **核心原则**：优先去找一手的官方财报 → 也可以找对应证监会的公开文件材料 → 实在找不到用网页搜索或Google Finance

| 市场 | 一级：公司官方IR | 二级：监管机构公开文件 | 三级：三方平台（兜底） |
|------|----------------|---------------------|---------------------|
| 🇺🇸 美股 | `investor.{company}.com` | **SEC EDGAR** — 10-K/10-Q/8-K/20-F | StockAnalysis.com / Yahoo Finance / Google Finance |
| 🇭🇰 港股 | 公司官网IR页 | **港交所披露易** (hkexnews.hk) | 富途牛牛 / 东方财富港股 / AAStocks |
| 🇨🇳 A股 | 公司官网IR页 | **巨潮资讯** (cninfo.com.cn) + 上交所/深交所 | 东方财富 / 同花顺 / 雪球 |
| 🇯🇵 日股 | 公司官网IR页 | **EDINET** + **TDnet** — 決算短信 | Yahoo Finance Japan / Google Finance |
| 🇰🇷 韩股 | 公司官网IR页 | **DART** (dart.fss.or.kr) — 事業報告書 | Naver Finance / Google Finance |
| 🇪🇺 欧股 | 公司官网IR页 | 各国交易所+监管机构 / **ESMA** | Google Finance / Bloomberg |

---

## 市场数据源路由（按目标公司市场自动选择）

| 数据类型 | 🇺🇸 美股 | 🇭🇰 港股 | 🇨🇳 A股 | 🇯🇵 日股 | 🇰🇷 韩股 | 🇪🇺 欧股 |
|----------|---------|---------|---------|---------|---------|---------|
| **市值排名** | companiesmarketcap.com | companiesmarketcap.com | 东方财富A股市值排名 | companiesmarketcap.com | companiesmarketcap.com | companiesmarketcap.com |
| **股价/估值** | StockAnalysis / Yahoo Finance | 富途 / AAStocks / Google Finance | 东方财富 / 同花顺 | Yahoo Finance JP | Naver Finance | Google Finance |
| **PE/PB/ROE** | StockAnalysis | 富途 / AAStocks | 东方财富 / 同花顺 | Yahoo Finance JP | Naver Finance | Google Finance |
| **长周期财务** | Macrotrends / StockAnalysis | Google Finance / web_search | 同花顺iFind / 东方财富 | Macrotrends | web_search | Macrotrends |
| **分析师预期** | TipRanks / MarketBeat / Seeking Alpha | 富途 / Bloomberg | 万得一致预期 | Bloomberg | Naver Finance | Bloomberg / TipRanks |
| **技术面** | TradingView / StockAnalysis | TradingView / 富途 | TradingView / 同花顺 | TradingView | TradingView | TradingView |
| **公告/事件** | SEC EDGAR | 港交所披露易 | 巨潮资讯 | EDINET / TDnet | DART | 各国交易所 |
| **新闻动态** | web_search | web_search | web_search | web_search | web_search | web_search |
| **微信相关** | https://mp.weixin.qq.com/ | https://mp.weixin.qq.com/ | https://mp.weixin.qq.com/ | — | — | — |

---

## 各市场特殊注意事项

### 🇭🇰 港股特殊规则
- 货币：港元(HK$)，与人民币竞对对比时标注汇率
- 财报：中期报（半年报）+ 年报为主，季报非强制
- 注意：H股/红筹/中概回港等不同上市结构差异
- 沪深港通持股比例是重要指标
- **港交所披露易** (hkexnews.hk) 是必查一手来源
- ⚠️ Non-IFRS调整项为必备（铁律#35）
- ⚠️ SOTP估值为多元化公司必备（铁律#40）
- ⚠️ D&A精确拆解从年报附注获取（铁律#36）

### 🇨🇳 A股特殊规则
- 货币：人民币(¥/CNY)
- 财报：季报(Q1/Q3简要)+半年报+年报，会计准则CAS
- 重要指标：扣非净利润、商誉减值风险、质押比例、北向资金
- **巨潮资讯** (cninfo.com.cn) 是首选一手来源
- 区分：归母净利润 vs 扣非归母净利润
- 行业对比关注申万行业分类

### 🇯🇵 日股特殊规则
- 货币：日元(¥/JPY)，建议全文用"日元"或"JPY"
- 财年：多为4月-3月
- 财报：決算短信发布快，有価証券報告書详细
- **EDINET** 和 **TDnet** 是一手来源
- 交叉持股(Cross-shareholding)影响实际流通市值

### 🇰🇷 韩股特殊规则
- 货币：韩元(₩/KRW)，单位"亿韩元"或"兆韩元"
- 会计准则：K-IFRS
- **DART** (dart.fss.or.kr) 是一手披露平台
- 财阀集团(Chaebol)结构复杂，区分合并vs单体
- 优先股/普通股双轨制常见

### 🇪🇺 欧股特殊规则
- 货币：欧元(€)为主，英国英镑(£)，瑞士瑞郎(CHF)
- 会计准则：IFRS（欧盟强制）
- 注意欧洲企业分红税制差异大

---

## 信息采集批次详解

### 批次0：全球市值排名与竞对基准（⚠️ 最先执行）
- 从 companiesmarketcap.com 获取全球市值排名
- 记录目标公司及所有主要竞对的精确市值和排名
- 获取后立即检查数值大小与排名顺序是否一致

### 批次1：市场数据与长周期财务
1. **股价与估值数据** → 按市场路由选择数据源
   - 当前股价、市值、PE(TTM)、PB、PS、股息率
   - ⚠️⚠️ 涨跌幅必须从Finviz.com直接获取（铁律#27）
   - 52周最高/最低价、PE/PB历史分位数
2. **长周期财务（5-10年）** → 一手来源优先
   - 营收/净利润/毛利率/净利率/ROE/ROIC/FCF/CapEx趋势
3. **近期季度财务（4-8个季度）** → 一手来源优先
   - 逐季数据+现金流健康度
4. **行业对比数据**

### 批次2：基本面深度
5. **最新财报深度拆解** → 一手来源
   - 含Non-IFRS调整项逐项采集（铁律#35）
   - 含D&A三大分项精确拆解（铁律#36）
   - 含多口径指标校准（铁律#37）
6. **主营业务深度**
7. **行业与竞争格局**

### 批次3：定性信息与前瞻
8. **管理层与治理**（含ESG+薪酬）
9. **最新动态、公告与新闻**
10. **风险因素**
11. **消息前瞻（7-30天）**
12. **技术面数据**

### 批次4：资产负债表深度
13. **资产负债结构深度**
14. **需警惕事项**

### 批次5：市场一致预期
15. **一致预期数据** + 合理性验证

### 批次6：历史财报PDF系统化获取（v9新增）
16. **逐年历史财报PDF提取** — 按优先级获取：
    - ① 公司IR网站年报下载页
    - ② 监管机构文件库
    - ③ web_search + web_fetch获取PDF URL
17. **季度财报精确数据补全** — 从业绩公告获取
