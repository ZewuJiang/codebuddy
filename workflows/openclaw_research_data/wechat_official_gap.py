#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计 wechat_articles 现有结果里：各厂商官方号覆盖缺口与Top来源。

- 复用 wechat_fill_v2.py 里的 OFFICIAL_SOURCES / VENDOR_PREFIX / JSON_DIRS
- 输出：stdout + 生成一份 JSON 报告文件到最新一轮 wechat_articles 目录
"""

import json
import os
import runpy
from collections import Counter, defaultdict

FILL_SCRIPT = "/Users/zewujiang/Desktop/AICo/codebuddy/workflows/openclaw_research_data/wechat_fill_v2.py"
ctx = runpy.run_path(FILL_SCRIPT)

JSON_DIRS = ctx.get("JSON_DIRS") or []
OFFICIAL_SOURCES = ctx["OFFICIAL_SOURCES"]
VENDOR_PREFIX = ctx["VENDOR_PREFIX"]
ORDER = ctx["ORDER"]
BAD_KW = ctx["BAD_KW"]


def vendor_for_filename(fn: str) -> str:
    for prefix, v in VENDOR_PREFIX:
        if fn.startswith(prefix):
            return v
    return "其他"


def is_sensitive(text: str) -> bool:
    t = text or ""
    return any(k in t for k in BAD_KW)


def is_official(vendor: str, source: str) -> bool:
    return bool(source) and (source in OFFICIAL_SOURCES.get(vendor, set()))


def main():
    cnt = defaultdict(Counter)
    src_counter = defaultdict(Counter)

    for json_dir in [d for d in JSON_DIRS if os.path.isdir(d)]:
        for fn in os.listdir(json_dir):
            if not fn.endswith(".json"):
                continue
            vendor = vendor_for_filename(fn)
            try:
                obj = json.load(open(os.path.join(json_dir, fn), "r", encoding="utf-8"))
            except Exception:
                continue

            for a in obj.get("articles", []) or []:
                title = (a.get("title") or "").strip()
                if (not title) or ("��" in title) or is_sensitive(title):
                    continue
                src = (a.get("source") or "").strip() or "未知"
                src_counter[vendor][src] += 1
                cnt[vendor]["official" if is_official(vendor, src) else "third"] += 1

    summary = {}
    for v in ORDER:
        if v not in cnt:
            continue
        o = cnt[v]["official"]
        t = cnt[v]["third"]
        total = o + t
        if total <= 0:
            continue
        summary[v] = {
            "official": o,
            "third": t,
            "total": total,
            "official_ratio": round(o / total, 4),
            "top_sources": src_counter[v].most_common(15),
            "top_unofficial_sources": [
                (src, n)
                for (src, n) in src_counter[v].most_common(80)
                if src not in OFFICIAL_SOURCES.get(v, set())
            ][:15],
        }

    print("== 官方覆盖概览（按 wechat_fill_v2.py 的 OFFICIAL_SOURCES 白名单）==")
    for v in ORDER:
        if v not in summary:
            continue
        s = summary[v]
        print(f"- {v}: 官方 {s['official']} / 总 {s['total']}（{s['official_ratio']*100:.1f}%）")

    last_dir = None
    for d in JSON_DIRS:
        if os.path.isdir(d):
            last_dir = d
    if not last_dir:
        raise SystemExit("未找到可用 JSON_DIRS 目录")

    out_path = os.path.join(last_dir, "official_gap_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "json_dirs": JSON_DIRS,
                "summary": summary,
                "official_sources": {k: sorted(list(v)) for k, v in OFFICIAL_SOURCES.items()},
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\n已写入：{out_path}")


if __name__ == "__main__":
    main()
