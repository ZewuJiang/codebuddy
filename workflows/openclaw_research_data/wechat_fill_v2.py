#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 wechat-article-search 的 JSON 输出补齐 OpenClaw 厂商扫描文档的公众号文章章节。

- 输入：v1 扫描文档 + wechat_articles 目录下的若干 JSON（支持多个目录合并）
- 输出：扫描文档新版本（不覆盖旧版）

注意：会过滤明显的政治/地缘/冲突类标题，避免把无关敏感话题带入报告。
"""

import json
import os
import re
from datetime import datetime

V1_PATH = "/Users/zewujiang/Desktop/AICo/codebuddy/OpenclawAIco/OpenClaw-中国厂商布局全量扫描-202603051710-v1.md"
OUT_PATH = "/Users/zewujiang/Desktop/AICo/codebuddy/OpenclawAIco/OpenClaw-中国厂商布局全量扫描-202603052030-v7.md"

# 合并多个检索批次：先旧批次（覆盖面广），再官方定向批次（官方命中更高），最后矩阵号扩展批次（尽量挖全官方号）
JSON_DIRS = [
    "/Users/zewujiang/Desktop/AICo/codebuddy/workflows/wechat_articles/202603051717",
    "/Users/zewujiang/Desktop/AICo/codebuddy/workflows/wechat_articles/202603051902_official",
    "/Users/zewujiang/Desktop/AICo/codebuddy/workflows/wechat_articles/202603051931_matrix",
    "/Users/zewujiang/Desktop/AICo/codebuddy/workflows/wechat_articles/202603051958_matrix2",
    "/Users/zewujiang/Desktop/AICo/codebuddy/workflows/wechat_articles/202603052030_final",
]

BAD_KW = [
    "伊朗",
    "美以",
    "选举",
    "总统",
    "战争",
    "内战",
    "地缘",
    "封杀",
    "指控",
    "政变",
    "党",
    "政府",
    "制裁",
    "冲突",
]

# 说明：这里的“官方”=我们明确认为属于该厂商体系的公众号名称白名单。
# 目标是尽量减少第三方内容占比；后续可按 official_gap_report.json 继续扩充。
OFFICIAL_SOURCES = {
    "腾讯云": {
        "腾讯云",
        "腾讯云服务器",
        "腾讯云智能",
        "腾讯云开发者",
        "腾讯云开发者社区",
    },
    "阿里云": {
        "阿里云",
        "阿里云开发者",
        "阿里云云栖号",
        "阿里云云栖社区",
    },
    "百度智能云": {
        "百度智能云",
        "百度开发者中心",
    },
    "华为云": {
        "华为云",
        "华为云开发者联盟",
        "华为云云商店",
        "华为云行业创新LAB",
    },
    "火山引擎": {
        "火山引擎",
        "火山引擎开发者",
        "火山引擎开发者社区",
    },
    "天翼云": {"天翼云", "中国电信", "中国电信上海公司", "天翼云开发者", "天翼云科技", "电信风尚"},
    "腾讯混元": {"腾讯混元", "腾讯混元大模型", "混元大模型", "腾讯AI", "腾讯混元助手"},
    "智谱": {"智谱AI", "智谱", "Z.ai", "GLM大模型", "智谱清言", "ChatGLM"},
    "Moonshot": {"Moonshot", "Moonshot AI", "月之暗面", "Kimi智能助手"},
    "MiniMax": {"MiniMax", "稀宇科技", "MiniMax 稀宇科技"},
    "百川智能": {"百川智能", "Baichuan", "百川大模型"},
    "DeepSeek": {"DeepSeek", "深度求索", "DeepSeek AI"},
    "科大讯飞": {"科大讯飞", "讯飞", "讯飞开放平台", "讯飞星火", "星火大模型"},
    "商汤科技": {"商汤科技", "商汤", "SenseTime", "日日新"},
    "01.AI": {"01万物", "零一万物", "01.AI", "Yi大模型"},
}

# 仅用于“厂商相关”标签：名字包含厂商关键字，但未入官方白名单
VENDOR_RELATED_KW = {
    "腾讯云": ["腾讯"],
    "阿里云": ["阿里", "云栖"],
    "百度智能云": ["百度"],
    "华为云": ["华为"],
    "火山引擎": ["火山", "字节"],
    "天翼云": ["天翼", "电信"],
    "腾讯混元": ["混元"],
    "智谱": ["智谱", "Z.ai", "清言", "GLM"],
    "Moonshot": ["月之暗面", "Moonshot", "Kimi"],
    "MiniMax": ["MiniMax", "稀宇"],
    "百川智能": ["百川", "Baichuan"],
    "DeepSeek": ["DeepSeek", "深度求索"],
    "科大讯飞": ["讯飞", "星火"],
    "商汤科技": ["商汤", "SenseTime", "日日新", "SenseNova"],
    "01.AI": ["01万物", "零一万物", "01.AI", "Yi"],
}

VENDOR_PREFIX = [
    ("tencentcloud", "腾讯云"),
    ("hunyuan", "腾讯混元"),
    ("tencent_hunyuan", "腾讯混元"),
    ("aliyun", "阿里云"),
    ("baidu", "百度智能云"),
    ("huaweicloud", "华为云"),
    ("volcengine", "火山引擎"),
    ("ctyun", "天翼云"),
    ("zhipu", "智谱"),
    ("moonshot", "Moonshot"),
    ("kimi", "Moonshot"),
    ("minimax", "MiniMax"),
    ("baichuan", "百川智能"),
    ("deepseek", "DeepSeek"),
    ("iflytek", "科大讯飞"),
    ("sensetime", "商汤科技"),
    ("01ai", "01.AI"),
    ("channel_", "渠道/通用"),
]

ORDER = [
    "腾讯云",
    "阿里云",
    "百度智能云",
    "华为云",
    "火山引擎",
    "天翼云",
    "腾讯混元",
    "智谱",
    "Moonshot",
    "MiniMax",
    "百川智能",
    "DeepSeek",
    "科大讯飞",
    "商汤科技",
    "01.AI",
    "渠道/通用",
    "其他",
]


def norm_title(t: str) -> str:
    if not t:
        return ""
    if "��" in t:
        return ""
    return re.sub(r"\s+", " ", t).strip()


def parse_dt(s: str):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def keypoint(title: str, summary: str) -> str:
    text = f"{title} {summary or ''}"
    if any(x in text for x in ("一键", "镜像", "模板")):
        return "强调一键部署/镜像/模板的快速上手路径。"
    if any(x in text for x in ("Lighthouse", "轻量", "LS", "SAS", "Flexus")):
        return "围绕轻量应用服务器/弹性算力（如 Lighthouse/LS/SAS/Flexus）部署与配置。"
    if "云市场" in text or "镜像市场" in text:
        return "涉及云市场/镜像市场入口或上架/选型信息。"
    if "飞书" in text:
        return "给出接入飞书机器人的步骤与注意事项。"
    if "企业微信" in text or "企微" in text:
        return "给出接入企业微信/企微的步骤与注意事项。"
    if "钉钉" in text:
        return "给出接入钉钉的步骤与注意事项。"
    if re.search(r"\bQQ\b", text) or "QQ群" in text:
        return "给出接入 QQ/QQ群 的步骤与注意事项。"
    if "百炼" in text or "DashScope" in text:
        return "涉及百炼（DashScope）/Coding Plan 的密钥与配置。"
    if "千帆" in text:
        return "涉及千帆平台的模型接入或部署联动。"
    if any(x in text for x in ("安全", "风控", "权限", "鉴权")):
        return "围绕部署安全/权限控制/风险防护的说明或方案。"
    if any(x in text for x in ("上架", "云商店", "KooGallery")):
        return "涉及云商店/上架入口与购买/计费信息。"
    return "围绕 OpenClaw 的部署、配置或官方活动/能力说明。"


def vendor_for_filename(fn: str) -> str:
    for prefix, v in VENDOR_PREFIX:
        if fn.startswith(prefix):
            return v
    return "其他"


def is_sensitive(text: str) -> bool:
    return any(k in (text or "") for k in BAD_KW)


def is_official(vendor: str, source: str) -> bool:
    if not source:
        return False
    return source in OFFICIAL_SOURCES.get(vendor, set())


def is_vendor_related(vendor: str, source: str) -> bool:
    if not source:
        return False
    for kw in VENDOR_RELATED_KW.get(vendor, []):
        if kw and kw in source:
            return True
    return False


def tag_for(vendor: str, source: str) -> str:
    if is_official(vendor, source):
        return "官方"
    if is_vendor_related(vendor, source):
        return "厂商相关"
    return "非官方/第三方"


def load_items() -> dict:
    data: dict = {}

    for json_dir in JSON_DIRS:
        if not os.path.isdir(json_dir):
            continue
        for fn in os.listdir(json_dir):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(json_dir, fn)
            try:
                obj = json.load(open(path, "r", encoding="utf-8"))
            except Exception:
                continue

            vendor = vendor_for_filename(fn)
            for a in obj.get("articles", []) or []:
                title = norm_title(a.get("title", "") or "")
                if not title or is_sensitive(title):
                    continue

                summary = (a.get("summary", "") or "").strip()
                if is_sensitive(summary):
                    summary = ""

                data.setdefault(vendor, []).append(
                    {
                        "title": title,
                        "url": a.get("url", "") or "",
                        "source": (a.get("source", "") or "").strip(),
                        "dt": parse_dt(a.get("datetime", "") or ""),
                        "date_text": a.get("date_text") or a.get("date_description") or "",
                        "url_resolved": a.get("url_resolved", None),
                        "keypoint": keypoint(title, summary),
                    }
                )

    # 去重（同标题优先保留“官方”版本；若无官方则保留“厂商相关”；最后才是第三方；同等级再选最新）
    def _rank(vendor: str, it: dict) -> int:
        src = it.get("source") or ""
        if is_official(vendor, src):
            return 2
        if is_vendor_related(vendor, src):
            return 1
        return 0

    for vendor, items in list(data.items()):
        best_by_title = {}
        for it in items:
            t = it.get("title") or ""
            if not t:
                continue
            cur = best_by_title.get(t)
            if not cur:
                best_by_title[t] = it
                continue

            r_new = _rank(vendor, it)
            r_old = _rank(vendor, cur)
            if r_new > r_old:
                best_by_title[t] = it
                continue
            if r_new < r_old:
                continue

            dt_new = it.get("dt") or datetime.min
            dt_old = cur.get("dt") or datetime.min
            if dt_new > dt_old:
                best_by_title[t] = it

        dedup = sorted(best_by_title.values(), key=lambda x: (x.get("dt") or datetime.min), reverse=True)
        data[vendor] = dedup

    return data


def render_md(vendor_data: dict) -> str:
    out = []
    out.append("### 4.1 说明")
    out.append("")
    out.append(
        "- **数据来源**：使用 `wechat-article-search` 在微信生态的公开索引中检索（底层为搜狗微信检索页），并开启 `-r` 尽量解析为可直接打开的 `mp.weixin.qq.com` 文章链接。"
    )
    out.append(
        "- **优先级策略**：本版优先收敛到**厂商官方公众号**（白名单判定），不足部分才保留少量“厂商相关/第三方”作参考。"
    )
    out.append(
        "- **阅读方式**：每条只给 **一句话要点**，你点开链接即可逐篇核验细节。"
    )
    out.append("")

    out.append("### 4.2 官方号优先汇总（尽量全量）")
    out.append("")

    for vendor in ORDER:
        items = vendor_data.get(vendor) or []
        if not items:
            continue

        out.append(f"#### {vendor}")
        out.append("")

        official_items = [it for it in items if is_official(vendor, it.get("source", ""))]
        related_items = [it for it in items if (not is_official(vendor, it.get("source", ""))) and is_vendor_related(vendor, it.get("source", ""))]
        third_items = [it for it in items if (it not in official_items and it not in related_items)]

        out.append("##### 官方号（尽量全量）")
        out.append("")
        if not official_items:
            out.append("- 暂未检索到该厂商官方公众号文章（以当前公开索引为准）。")
            if vendor in ("阿里云", "智谱", "Moonshot", "MiniMax"):
                out.append("- 建议：后续可继续尝试该厂商在微信侧的**其它官方/矩阵号名称**（如“开发者/云商店/研究院/技术号”等）做定向检索。")
            out.append("")
        else:
            for it in official_items[:25]:
                resolved = it.get("url_resolved", None)
                resolved_text = "直链" if resolved else ("中转" if resolved is False else "未知")
                out.append(
                    f"- [{it['title']}]({it['url']}) — **来源**：{it.get('source') or '未知'}（官方）— **时间**：{it.get('date_text') or '未知'} — **链接**：{resolved_text} — **要点**：{it.get('keypoint')}"
                )
            out.append("")

        out.append("##### 其他来源（供参考，已大幅压缩）")
        out.append("")
        picked_other = (related_items[:4] + third_items[:6])[:8]
        for it in picked_other:
            tag = tag_for(vendor, it.get("source", ""))
            resolved = it.get("url_resolved", None)
            resolved_text = "直链" if resolved else ("中转" if resolved is False else "未知")
            out.append(
                f"- [{it['title']}]({it['url']}) — **来源**：{it.get('source') or '未知'}（{tag}）— **时间**：{it.get('date_text') or '未知'} — **链接**：{resolved_text} — **要点**：{it.get('keypoint')}"
            )
        out.append("")

    return "\n".join(out).strip() + "\n"


def main():
    base = open(V1_PATH, "r", encoding="utf-8").read()

    # 修正 v1 中“缺少工具”的描述
    base = base.replace(
        "## 4）“公众号文章”扫描结果与补齐建议",
        "## 4）微信公众号文章扫描（已使用 wechat-article-search 补齐直链）",
    )
    base = re.sub(
        r"\n- \*\*微信公众号文章\*\*：.*?(?=\n\n---\n\n## 1）扫描范围)",
        "\n- **微信公众号文章**：已通过 `wechat-article-search`（基于搜狗微信索引）批量检索并尽量解析为 `mp.weixin.qq.com` 直链；每条给出**一句话要点**便于你快速判断是否值得点开深读。",
        base,
        flags=re.S,
    )

    vendor_data = load_items()
    wechat_section = render_md(vendor_data)

    pattern = r"## 4）微信公众号文章扫描（已使用 wechat-article-search 补齐直链）[\s\S]*?(?=\n\n---\n\n## 5）下一步)"
    repl = "## 4）微信公众号文章扫描（已使用 wechat-article-search 补齐直链）\n\n" + wechat_section + "\n\n---\n\n"

    new_text, n = re.subn(pattern, repl, base)
    if n == 0:
        new_text = base + "\n\n---\n\n## 4）微信公众号文章扫描（已使用 wechat-article-search 补齐直链）\n\n" + wechat_section

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(new_text)

    print(OUT_PATH)


if __name__ == "__main__":
    main()
