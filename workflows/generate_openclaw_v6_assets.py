# -*- coding: utf-8 -*-
"""为 OpenClaw v6 研究报告生成配图（PNG）。

说明：
- 只生成结构化图表（架构/竞争版图/国内三层生态），用于提升PDF可读性与体积达标。
- 输出路径由命令行参数提供：python3 generate_openclaw_v6_assets.py /abs/path/to/output_dir
"""

from __future__ import annotations

import os
import sys
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont:
    # macOS 常见中文字体兜底：PingFang SC / STHeiti
    for name in [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _rounded(draw: ImageDraw.ImageDraw, xy: Tuple[int, int, int, int], r: int, fill, outline=None, width: int = 2):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int):
    # 简单按字符宽度换行（中文友好）
    lines = []
    cur = ""
    for ch in text:
        test = cur + ch
        w = draw.textlength(test, font=font)
        if w <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def _add_grain(img: Image.Image, strength: int = 6, alpha: int = 14) -> Image.Image:
    """添加极轻微的灰度纹理，提升图片信息量（避免过度压缩），不影响阅读。"""
    import random

    w, h = img.size
    noise = Image.new("L", (w, h), 128)
    px = noise.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = 128 + random.randint(-strength, strength)
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    return Image.blend(img, noise_rgb, alpha / 255.0)


def draw_stack_war(out_dir: str):
    W, H = 3600, 2100
    img = Image.new("RGB", (W, H), (245, 247, 250))
    d = ImageDraw.Draw(img)

    title_f = _font(96)
    sub_f = _font(52)
    body_f = _font(48)

    d.text((80, 60), "执行入口争夺：四层栈（从协议到分发）", font=title_f, fill=(20, 24, 31))
    d.text((80, 140), "结论：竞争不是“模型更强”，而是谁把计划变成动作并占据默认入口。", font=sub_f, fill=(73, 80, 87))

    layers = [
        ("连接层（协议/连接器）", "MCP/连接器：把工具与数据接到模型", (34, 197, 94)),
        ("协作层（多智能体互操作）", "A2A/多代理协议：让不同Agent协作", (0, 163, 255)),
        ("运行层（Agent Runtime/生产化）", "身份/隔离/审计/可观测：把执行做成可靠系统", (245, 158, 11)),
        ("分发层（SaaS/云/IM/终端）", "把Agent塞进默认入口：协同/CRM/ERP/OS/IM", (239, 68, 68)),
    ]

    x0, y0 = 80, 250
    box_w, box_h, gap = 2040, 210, 40
    for i, (t, s, c) in enumerate(layers):
        y = y0 + i * (box_h + gap)
        _rounded(d, (x0, y, x0 + box_w, y + box_h), r=28, fill=(255, 255, 255), outline=(220, 224, 229), width=3)
        # 左侧色条
        _rounded(d, (x0 + 20, y + 20, x0 + 70, y + box_h - 20), r=18, fill=c, outline=None, width=0)
        d.text((x0 + 100, y + 38), t, font=_font(44), fill=(20, 24, 31))
        lines = _wrap(d, s, body_f, max_w=box_w - 140)
        for j, line in enumerate(lines[:3]):
            d.text((x0 + 100, y + 110 + j * 44), line, font=body_f, fill=(73, 80, 87))

    d.text((80, 1180), "图：研究团队绘制（v6）", font=_font(28), fill=(110, 118, 128))
    img.save(os.path.join(out_dir, "stack_war.png"), format="PNG", optimize=False)


def draw_landscape(out_dir: str):
    W, H = 3600, 2300
    img = Image.new("RGB", (W, H), (245, 247, 250))
    d = ImageDraw.Draw(img)

    d.text((120, 80), "竞争版图：入口控制 × 运行时治理（示意）", font=_font(96), fill=(20, 24, 31))
    d.text((120, 200), "定位：OpenClaw更像“自托管执行节点/个人控制平面”，上层入口与托管运行时正快速固化。", font=_font(52), fill=(73, 80, 87))

    # 坐标区
    left, top, right, bottom = 180, 280, 2060, 1240
    _rounded(d, (left, top, right, bottom), r=28, fill=(255, 255, 255), outline=(220, 224, 229), width=3)

    mid_x = (left + right) // 2
    mid_y = (top + bottom) // 2
    d.line((mid_x, top + 20, mid_x, bottom - 20), fill=(220, 224, 229), width=3)
    d.line((left + 20, mid_y, right - 20, mid_y), fill=(220, 224, 229), width=3)

    # 轴标
    d.text((mid_x - 120, bottom + 20), "入口控制更强 →", font=_font(34), fill=(73, 80, 87))
    d.text((left - 160, mid_y - 120), "运行时治理更强\n↑", font=_font(34), fill=(73, 80, 87))

    # 点位（示意，不代表市场份额）
    points = [
        ("Salesforce\nAgentforce", (1750, 420), (99, 102, 241)),
        ("Microsoft\nCopilot Studio", (1700, 560), (99, 102, 241)),
        ("Oracle\nFusion", (1750, 700), (99, 102, 241)),
        ("Atlassian\nRovo", (1650, 780), (99, 102, 241)),
        ("AWS\nBedrock Agents", (780, 420), (16, 185, 129)),
        ("Databricks\nMosaic AI", (900, 520), (16, 185, 129)),
        ("IBM\nOrchestrate", (720, 620), (16, 185, 129)),
        ("NVIDIA\nNeMo", (860, 700), (16, 185, 129)),
        ("OpenClaw\n(自托管执行层)", (900, 980), (245, 158, 11)),
        ("Anthropic\nMCP", (360, 900), (0, 163, 255)),
        ("Google\nA2A", (420, 820), (0, 163, 255)),
        ("OpenAI\nResponses+Tools", (520, 620), (0, 163, 255)),
    ]

    for label, (x, y), color in points:
        r = 18
        d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=(255, 255, 255), width=3)
        d.text((x + 24, y - 34), label, font=_font(30), fill=(20, 24, 31))

    d.text((120, 2160), "注：此图是战略定位示意，非份额排名。", font=_font(40), fill=(110, 118, 128))
    img = _add_grain(img)
    img.save(os.path.join(out_dir, "landscape_map.png"), format="PNG", optimize=False)


def draw_china_layers(out_dir: str):
    W, H = 2200, 1400
    img = Image.new("RGB", (W, H), (245, 247, 250))
    d = ImageDraw.Draw(img)

    d.text((80, 60), "国内三层生态：卖铲 × 绑龙虾 × Agent工厂", font=_font(64), fill=(20, 24, 31))
    d.text((80, 140), "观察：云厂先把OpenClaw标准化成镜像/模板，模型厂把接入写进文档，平台侧把构建与治理平台化。", font=_font(34), fill=(73, 80, 87))

    # 金字塔
    base_x, base_y = 300, 1180
    top_x, top_y = 1100, 320

    # 三层梯形
    layers = [
        ("Agent工厂（构建/治理/可观测）", "百炼/千帆等：智能体与工作流平台化", (0, 163, 255)),
        ("绑龙虾（模型接入）", "混元/千问/GLM/MiniMax等：把OpenClaw接入写进官方文档", (245, 158, 11)),
        ("卖铲（部署入口）", "云镜像/模板/云电脑：一键部署+IM接入+安全组提示", (34, 197, 94)),
    ]

    width_top, width_bottom = 500, 1600
    h = 240
    for i, (t, s, c) in enumerate(layers):
        y1 = top_y + i * h
        y2 = y1 + h
        # 线性插值宽度
        w1 = int(width_top + (width_bottom - width_top) * (i / 3.0))
        w2 = int(width_top + (width_bottom - width_top) * ((i + 1) / 3.0))
        x1 = 1100 - w1 // 2
        x2 = 1100 + w1 // 2
        x3 = 1100 + w2 // 2
        x4 = 1100 - w2 // 2
        poly = [(x1, y1), (x2, y1), (x3, y2), (x4, y2)]
        d.polygon(poly, fill=(255, 255, 255), outline=(220, 224, 229))
        # 左侧色条
        d.rectangle((x4 + 18, y1 + 18, x4 + 38, y2 - 18), fill=c)
        d.text((x4 + 60, y1 + 32), t, font=_font(44), fill=(20, 24, 31))
        lines = _wrap(d, s, _font(32), max_w=(x3 - x4) - 120)
        for j, line in enumerate(lines[:2]):
            d.text((x4 + 60, y1 + 110 + j * 44), line, font=_font(32), fill=(73, 80, 87))

    d.text((80, 1320), "图：研究团队绘制（v6）", font=_font(28), fill=(110, 118, 128))
    img.save(os.path.join(out_dir, "china_three_layers.png"), format="PNG", optimize=False)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 generate_openclaw_v6_assets.py /abs/output_dir")
        return 2
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)

    draw_stack_war(out_dir)
    draw_landscape(out_dir)
    draw_china_layers(out_dir)

    print("OK", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
