# -*- coding: utf-8 -*-
"""HSEG16 新思路：用 SVG 的 16 段 + 原字形交叠，反推每个字符保留哪些段，
只替换 glyf 轮廓，其它表一律不动。先在 Classic-Regular 上验证。

用法：python build_hseg16_from_svg.py --style Classic-Regular [--all]
"""
from __future__ import annotations

import argparse
import json
import string
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(r"D:\DSHin\HoMiSe")
sys.path.insert(0, str(ROOT / "font-source" / "build" / "_test"))
sys.path.insert(0, str(ROOT / "font-source" / "tools"))
from expand_svg_paths import parse_path  # noqa: E402
from sfd_curves import parse_sfd_curves  # noqa: E402

SVG = ROOT / "HSSeg16-avg.svg"
D14SFD = ROOT / "font-source" / "DSEG-v0.46" / "src"
D14 = ROOT / "app" / "src" / "main" / "res" / "font"
OUTDIR = ROOT / "font-source" / "build" / "hseg16-ttf"
MONO_OUTDIR = ROOT / "font-source" / "build" / "hseg16-ttf-mono"
NS = "{http://www.w3.org/2000/svg}"

GLYPHS_JSON = ROOT / "font-source" / "build" / "hsseg16-glyphs.json"

# 内部迭代版本：0.1.0.<n>，正式导出时由 export_hseg16.py 去掉第 4 位
VERSION_BASE = "1.0.0"
ITER_FILE = ROOT / "font-source" / "build" / "hseg16-iter.txt"


def _next_iter() -> int:
    n = int(ITER_FILE.read_text(encoding="utf-8").strip()) + 1 if ITER_FILE.exists() else 1
    ITER_FILE.parent.mkdir(parents=True, exist_ok=True)
    ITER_FILE.write_text(str(n), encoding="utf-8")
    return n


INTERNAL_VERSION = f"{VERSION_BASE}.{_next_iter()}"

# 0-9 的亮段（来自用户图反推；0 无中横，斜线移到 O/o）
DIGIT_GLYPH = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
               "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"}
DIGIT_CODES = {
    "0": "a b c d e f g h",
    "1": "c d",
    "2": "a b c e f g u p",
    "3": "a b c d e f u p",
    "4": "c d h u p",
    "5": "a b d e f h u p",
    "6": "a b d e f g h u p",
    "7": "a b c d",
    "8": "a b c d e f g h u p",
    "9": "a b c d e f h u p",
}

# A-Z 的亮段（来自用户 7×4 图反推）
LETTER_CODES = {
    "A": "a b c d g h u p",
    "B": "a b e f g h u n r",
    "C": "a b c e f g h",
    "D": "a b c d e f m s",
    "E": "a b e f g h u p",
    "F": "a b g h u p",
    "G": "a b d e f g h p",
    "H": "c d g h u p",
    "I": "a b e f m s",
    "J": "a b c d e f g",
    "K": "g h u n r",
    "L": "e f g h",
    "M": "c d g h k n s",
    "N": "c d g h k r",
    "O": "a b c d e f g h t n",
    "P": "a b c g h u p",
    "Q": "a b c d e f g h r",
    "R": "a b c g h u p r",
    "S": "a b e f k r",
    "T": "a b m s",
    "U": "c d e f g h",
    "V": "g h t n",
    "W": "c d g h t r m",
    "X": "k t n r",
    "Y": "k n s",
    "Z": "a b e f t n",
}

# 符号固定编码（用户逐字符给图反推）；SFD 缺失的字符也会按此新增
SYMBOL_CODES = {
    "@": "a b c d f g u t s",
    "#": "c d e f u p m s",
    "&": "a b c e f g u p k r",
    "$": "a b d e f h u p m s",
    "(": "n r",
    ")": "k t",
    "%": "a d f h u p t n m s",
    "¥": "u p k n s",
    "[": "b f m s",
    "]": "a e m s",
    "{": "b f u m s",
    "|": "m s",
    "}": "a e p m s",
    '"': "c h",
    "+": "u p m s",
    "'": "m",
    "-": "u p",
    "`": "a b",
    "<": "u n r",
    "^": "a b c h",
    ">": "p k t",
    "_": "e f",
    "=": "e f u p",
    ";": "t m",
    "/": "t n",
    "*": "u p k t n r m s",
    "\\": "k r",
    ",": "t",
}
GLYPH_SYMBOL = {"at": "@", "numbersign": "#", "ampersand": "&", "dollar": "$",
                "parenleft": "(", "parenright": ")", "percent": "%",
                "bar": "|", "quotedbl": '"', "plus": "+", "quotesingle": "'",
                "hyphen": "-", "grave": "`", "less": "<", "asciicircum": "^",
                "greater": ">", "underscore": "_", "exclam": "!", "question": "?",
                "equal": "=", "semicolon": ";", "slash": "/", "asterisk": "*",
                "backslash": "\\", "yen": "¥"}

# 含 dp 点（与 "1." 的效果一致：period 画在字符右侧 816 处）
DP_DOT = [[878, 74], [878, 50], [868, 26], [852, 10], [828, 0], [804, 0], [780, 10],
          [764, 26], [754, 50], [754, 74], [764, 98], [780, 114], [804, 124],
          [828, 124], [852, 114], [868, 98]]
DP_SYMBOLS = {
    "!": "c d",
    "?": "b c p r",
}

# a-z 的亮段（来自用户 7×4 小写图反推）
LOWER_CODES = {
    "a": "g u t s",
    "b": "e g h u s",
    "c": "e g u",
    "d": "e g u m s",
    "e": "e g u t",
    "f": "b m s u p",
    "g": "d e f p r",
    "h": "g h u s",
    "i": "s",
    "j": "e s",
    "k": "p r m s",
    "l": "a f m s",
    "m": "d g u p s",
    "n": "g u s",
    "o": "e g u t s",
    "p": "g u t",
    "q": "d p r",
    "r": "g u",
    "s": "f p r",
    "t": "f u p m s",
    "u": "e g s",
    "v": "g t",
    "w": "d g t r",
    "x": "u p t r",
    "y": "d e f r",
    "z": "e u t",
}

# Mono 变体的小写字母（用户等宽图反推）
MONO_LOWER_CODES = {
    "a": "e g u f s",
    "b": "d e f g h u p",
    "c": "e f g u p",
    "d": "c d e f g u p",
    "e": "e f g u t",
    "f": "b u p m s",
    "g": "d e f p r",
    "h": "d g h u p",
    "i": "e f u p s",
    "j": "d e f",
    "k": "a p r m s",
    "l": "a f m s",
    "m": "d g u p s",
    "n": "d g u p",
    "o": "d e f g u p s",
    "p": "e f r s",
    "q": "e f t s",
    "r": "p t s",
    "s": "e f p r",
    "t": "f u p m s",
    "u": "d e f g",
    "v": "g p t",
    "w": "d g t r",
    "x": "u p t r",
    "y": "d e f r",
    "z": "e f u t",
}

FAM_DISPLAY = {"Classic": "Classic", "ClassicMini": "Classic Mini",
               "Modern": "Modern", "ModernMini": "Modern Mini"}
STYLE_DISPLAY = {"Light": "Light", "LightItalic": "Light Italic", "Regular": "Regular",
                 "Italic": "Italic", "Bold": "Bold", "BoldItalic": "Bold Italic"}

STYLES = ["Light", "LightItalic", "Regular", "Italic", "Bold", "BoldItalic"]
FAMS = {"classic": "Classic", "classic_mini": "ClassicMini",
        "modern": "Modern", "modern_mini": "ModernMini"}
STYLE_FILE = {"Light": "light", "LightItalic": "light_italic", "Regular": "regular",
              "Italic": "italic", "Bold": "bold", "BoldItalic": "bold_italic"}
# 4 行 × 6 列，与之前匹配结果一致
ROW_START = {"Classic": 12, "ClassicMini": 18, "Modern": 0, "ModernMini": 6}

X0, X1, H = 99.0, 717.0, 1000.0
THRESHOLD = 0.3


def bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def group_polys(g):
    polys = []
    for el in g:
        tag = el.tag.replace(NS, "")
        if tag == "path":
            polys.extend(parse_path(el.get("d", "")))
        elif tag == "polygon":
            pts = []
            for pair in el.get("points", "").split():
                try:
                    x, y = pair.split(",")
                    pts.append((float(x), float(y)))
                except ValueError:
                    pass
            if len(pts) >= 3:
                polys.append(pts)
    return polys


def normalize(polys, target=None):
    """SVG 坐标 -> 字体坐标：默认 x 99..717、y 0..1000，可传入该字重字形的实际 bbox。"""
    allpts = [p for poly in polys for p in poly]
    x0, y0, x1, y1 = bbox(allpts)
    if target is None:
        tx0, ty0, tx1, ty1 = X0, 0.0, X1, H
    else:
        tx0, ty0, tx1, ty1 = target
    sx = (tx1 - tx0) / (x1 - x0)
    sy = (ty1 - ty0) / (y1 - y0)
    return [[(tx0 + (p[0] - x0) * sx, ty1 - (p[1] - y0) * sy) for p in poly] for poly in polys]


def point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xin = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xin:
                inside = not inside
    return inside


def coverage(seg, glyph_polys, n=7):
    x0, y0, x1, y1 = bbox(seg)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    inside_seg = 0
    inside_both = 0
    for i in range(n):
        for j in range(n):
            px = x0 + (i + 0.5) / n * (x1 - x0)
            py = y0 + (j + 0.5) / n * (y1 - y0)
            if point_in_poly((px, py), seg):
                inside_seg += 1
                if any(point_in_poly((px, py), gp) for gp in glyph_polys):
                    inside_both += 1
    return inside_both / inside_seg if inside_seg else 0.0


def center_inside(seg, glyph_polys):
    x0, y0, x1, y1 = bbox(seg)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return any(point_in_poly((cx, cy), gp) for gp in glyph_polys)


def glyph_polys_from_ttf(glyf, gname):
    g = glyf[gname]
    coords, ends, flags = g.getCoordinates(glyf)
    polys, start = [], 0
    for e in ends:
        polys.append([(float(coords[i][0]), float(coords[i][1])) for i in range(start, e + 1)])
        start = e + 1
    return polys


def period_from_official(fam: str, style: str):
    """从 DSEG14 官方 TTF 取 period 轮廓（斜体各字重补偿量不同）。"""
    fam_key = next((k for k, v in FAMS.items() if v == fam), None)
    if fam_key is None:
        return []
    p = ROOT / "font-source" / "build" / f"dseg_14_{fam_key}_{STYLE_FILE[style]}.ttf"
    if not p.exists():
        return []
    f = TTFont(str(p))
    cm = f.getBestCmap()
    if ord(".") not in cm:
        f.close()
        return []
    g = f["glyf"][cm[ord(".")]]
    coords, ends, _ = g.getCoordinates(f["glyf"])
    polys, st = [], 0
    for e in ends:
        polys.append([(float(coords[i][0]), float(coords[i][1])) for i in range(st, e + 1)])
        st = e + 1
    f.close()
    return polys


def make_glyph(polys):
    pen = TTGlyphPen(None)
    for c in polys:
        if len(c) < 3:
            continue
        # 统一方向（非零环绕）
        s = 0.0
        n = len(c)
        for i in range(n):
            x0, y0 = c[i]
            x1, y1 = c[(i + 1) % n]
            s += x0 * y1 - x1 * y0
        if s < 0:
            c = list(reversed(c))
        pen.moveTo(c[0])
        for p in c[1:]:
            pen.lineTo(p)
        pen.closePath()
    return pen.glyph()


PERIOD_POLY = [[62, 74], [62, 50], [52, 26], [36, 10], [12, 0], [-12, 0], [-36, 10],
               [-52, 26], [-62, 50], [-62, 74], [-52, 98], [-36, 114], [-12, 124],
               [12, 124], [36, 114], [52, 98]]
COLON_POLYS = [
    [[162, 705], [162, 681], [152, 657], [136, 641], [112, 631], [88, 631], [64, 641],
     [48, 657], [38, 681], [38, 705], [43, 717], [48, 728], [56, 736], [66, 745],
     [76, 750], [85, 754], [115, 754], [124, 750], [135, 745], [144, 736], [152, 728], [157, 717]],
    [[162, 293], [162, 269], [152, 245], [136, 229], [112, 219], [88, 219], [64, 229],
     [48, 245], [38, 269], [38, 293], [43, 305], [48, 316], [56, 324], [66, 334],
     [76, 338], [85, 342], [115, 342], [124, 338], [135, 334], [144, 324], [152, 316], [157, 305]],
]


def segments_to_polys(segs, samples=8):
    """SFD 的 m/l/c 段 -> 多边形（曲线采样）。"""
    polys, cur = [], None
    for s in segs:
        if s[0] == "m":
            if cur and len(cur) >= 3:
                polys.append(cur)
            cur = [s[1]]
        elif s[0] == "l":
            if cur is not None:
                cur.append(s[1])
        elif s[0] == "c" and cur:
            (x1, y1), (x2, y2), (x3, y3) = s[1]
            x0, y0 = cur[-1]
            for k in range(1, samples + 1):
                t = k / samples
                mt = 1 - t
                cur.append((mt**3 * x0 + 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t**3 * x3,
                            mt**3 * y0 + 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t**3 * y3))
    if cur and len(cur) >= 3:
        polys.append(cur)
    return polys


def fix_horizontal_gaps(segs, target=-4.0):
    """把顶/底横的左右两截拉到重叠（gap <= target），只水平拉伸横段。"""
    for top in (True, False):
        cand = []
        for i, s in enumerate(segs):
            x0, y0, x1, y1 = bbox(s)
            if (y1 - y0) < 200 and ((y0 >= 880) if top else (y1 <= 120)):
                cand.append(i)
        if len(cand) != 2:
            continue
        cand.sort(key=lambda i: bbox(segs[i])[0])
        L, R = cand
        lx0, lx1 = bbox(segs[L])[0], bbox(segs[L])[2]
        rx0, rx1 = bbox(segs[R])[0], bbox(segs[R])[2]
        gap = rx0 - lx1
        if gap <= target:
            continue
        d = (gap - target) / 2
        if lx1 > lx0:
            segs[L] = [(lx0 + (x - lx0) * (lx1 + d - lx0) / (lx1 - lx0), y) for x, y in segs[L]]
        if rx1 > rx0:
            segs[R] = [((rx0 - d) + (x - rx0) * (rx1 - (rx0 - d)) / (rx1 - rx0), y) for x, y in segs[R]]
    return segs


def build_style(fam: str, style: str, groups, mono: bool = False):
    sfd = D14SFD / f"DSEG14{fam}-{style}.sfd"
    if not sfd.exists():
        sfd = D14SFD / f"DSEG14{fam}--{style}.sfd"
    s = parse_sfd_curves(sfd)
    items = [{"name": g["name"], "unicode": g["unicode"], "width": g["width"],
              "polys": segments_to_polys(g["segments"])} for g in s]
    gi = ROW_START[fam] + STYLES.index(style)
    # 用数字 0 的 bbox 作为段归一化基准（它覆盖整个字形框）
    zero = next((it for it in items if it["name"] == "zero"), None)
    flat = [p for poly in (zero["polys"] if zero and zero["polys"] else []) for p in poly]
    target = bbox(flat) if flat else None
    segs = normalize(group_polys(groups[gi]), target)
    assert len(segs) == 16, len(segs)
    # 保留 SVG 模板顶/底横的原始分段缝隙，不做重叠修正
    # segs = fix_horizontal_gaps(segs)

    # 用该字重的模板（命名段）把 segs 的索引映射到 a..u，供数字固定编码使用
    tpl = json.loads(GLYPHS_JSON.read_text(encoding="utf-8"))[f"{fam}-{style}"]
    seg_bbox = [bbox(s) for s in segs]
    name_to_idx = {}
    for nm, poly in tpl.items():
        tb = bbox([(float(p[0]), float(p[1])) for p in poly])
        name_to_idx[nm] = min(range(16), key=lambda i: sum(abs(a - b) for a, b in zip(seg_bbox[i], tb)))

    glyph_order = [".notdef"] + [it["name"] for it in items]
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (816, 0)}
    cmap = {}
    replaced = 0

    for it in items:
        polys = it["polys"]
        name = it["name"]
        digit = DIGIT_GLYPH.get(name)
        if digit:
            keep = [segs[name_to_idx[s]] for s in DIGIT_CODES[digit].split()]
            glyphs[name] = make_glyph(keep)
            replaced += 1
        elif name in LETTER_CODES:
            keep = [segs[name_to_idx[s]] for s in LETTER_CODES[name].split()]
            glyphs[name] = make_glyph(keep)
            replaced += 1
        elif name in (MONO_LOWER_CODES if mono else LOWER_CODES):
            lower = MONO_LOWER_CODES if mono else LOWER_CODES
            keep = [segs[name_to_idx[s]] for s in lower[name].split()]
            glyphs[name] = make_glyph(keep)
            replaced += 1
        elif name in GLYPH_SYMBOL and GLYPH_SYMBOL[name] in SYMBOL_CODES:
            keep = [segs[name_to_idx[s]] for s in SYMBOL_CODES[GLYPH_SYMBOL[name]].split()]
            glyphs[name] = make_glyph(keep)
            replaced += 1
        elif name in GLYPH_SYMBOL and GLYPH_SYMBOL[name] in DP_SYMBOLS:
            keep = [segs[name_to_idx[s]] for s in DP_SYMBOLS[GLYPH_SYMBOL[name]].split()]
            keep.append([(x, y) for x, y in DP_DOT])
            glyphs[name] = make_glyph(keep)
            replaced += 1
        elif name == "period":
            # 零宽字符：正体跨原点；斜体需左移补偿。DSEG14 的 ClassicMini-BoldItalic
            # 本身漏了补偿（center 0），这里统一左移 44（= DSEG14 其它斜体的补偿量）
            if "Italic" in style:
                glyphs[name] = make_glyph([[(x - 44.0, y) for x, y in PERIOD_POLY]])
            else:
                glyphs[name] = make_glyph([PERIOD_POLY])
            replaced += 1
        elif name == "colon":
            # 斜体：上点右移、下点左移，偏移量相反且相等（DSEG14 为 18）
            d = 18.0 if "Italic" in style else 0.0
            cols = [[(x + d, y) for x, y in COLON_POLYS[0]],
                    [(x - d, y) for x, y in COLON_POLYS[1]]]
            glyphs[name] = make_glyph(cols)
            replaced += 1
        elif it["unicode"] and 32 <= it["unicode"] < 127 and polys:
            # 稀疏字形（单列）在低阈值下容易多留段；直立字重收紧到 0.5
            th = 0.3 if "Italic" in style else 0.5
            keep = [seg for seg in segs
                    if coverage(seg, polys) >= th or center_inside(seg, polys)]
            if keep:
                glyphs[name] = make_glyph(keep)
                replaced += 1
            else:
                glyphs[name] = make_glyph(polys)
        else:
            glyphs[name] = make_glyph(polys) if polys else TTGlyphPen(None).glyph()
        metrics[name] = (it["width"], 0)
        if it["unicode"]:
            cmap[it["unicode"]] = name

    # SFD 缺失但已有固定编码的符号（如 #）追加为新字形
    existing = set(cmap)
    for ch, codes in SYMBOL_CODES.items():
        if ord(ch) in existing:
            continue
        gn = f"uni{ord(ch):04X}"
        glyph_order.append(gn)
        keep = [segs[name_to_idx[s]] for s in codes.split()]
        glyphs[gn] = make_glyph(keep)
        metrics[gn] = (816, 0)
        cmap[ord(ch)] = gn
        replaced += 1

    # Mono 字形并入同一字体：U+E000..U+E019，advance 408、水平居中，
    # 原 a-z 保持 LOWER_CODES（advance 816）不动
    # PUA 码位沿用 Mono 的亮段，宽度/advance 与原 a-z 相同（816），不压缩不居中
    for i, ch in enumerate(string.ascii_lowercase):
        codes = MONO_LOWER_CODES[ch].split()
        polys = [[(x, y) for x, y in segs[name_to_idx[s]]] for s in codes]
        gn = f"uni{0xE000 + i:04X}"
        glyph_order.append(gn)
        glyphs[gn] = make_glyph(polys)
        metrics[gn] = (816, 0)
        cmap[0xE000 + i] = gn

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    # lsb 必须等于字形 xMin，否则 FreeType 会把整字左移（1 显示靠左的根因）
    glyf_table = fb.font["glyf"]
    for name, g in glyphs.items():
        if getattr(g, "numberOfContours", 0):
            g.recalcBounds(glyf_table)
            metrics[name] = (metrics[name][0], g.xMin)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=1000, descent=0)
    fam_label = f"HSEG 16 Mono {FAM_DISPLAY[fam]}" if mono else f"HSEG 16 {FAM_DISPLAY[fam]}"
    ps_name = f"HSEG16Mono{fam}-{style}" if mono else f"HSEG16{fam}-{style}"
    fb.setupNameTable({
        "familyName": fam_label,
        "styleName": STYLE_DISPLAY[style],
        "uniqueFontIdentifier": f"{ps_name};2026;{INTERNAL_VERSION}",
        "fullName": f"{fam_label} {STYLE_DISPLAY[style]}",
        "psName": ps_name,
        "version": f"Version {INTERNAL_VERSION}",
        "copyright": "Copyright (c) 2017, keshikan (http://www.keshikan.net), with Reserved "
                     "Font Name DSEG. Modifications copyright (c) 2026, HoMiSe APP.",
        "licenseDescription": "SIL Open Font License 1.1. See DSEG-LICENSE.txt.",
        "licenseInfoURL": "https://scripts.sil.org/OFL",
        "manufacturer": "HoMiSe APP",
        "designer": "keshikan (original design); HoMiSe APP (modifications)",
        "description": "HSEG16 is a 16-segment derivative of DSEG v0.46 for the HoMiSe clock app.",
        "vendorURL": "https://github.com/KuwsSyet9999/HSEG-Fonts",
        "designerURL": "https://www.keshikan.net",
        "typographicFamily": (f"HSEG 16 Mono {FAM_DISPLAY[fam]}" if mono else f"HSEG 16 {FAM_DISPLAY[fam]}"),
        "typographicSubfamily": STYLE_DISPLAY[style],
        "sampleText": "HSEG16 12:34",
    })
    fb.setupOS2(sTypoAscender=1000, sTypoDescender=0, sTypoLineGap=0,
                usWinAscent=1000, usWinDescent=0)
    _os2 = fb.font["OS/2"]
    _os2.achVendID = "HSEG"
    _wt = {"Light": 3, "LightItalic": 3, "Regular": 4, "Italic": 4,
           "Bold": 7, "BoldItalic": 7}[style]
    _p = _os2.panose
    _p.bFamilyType = 2      # Latin Text
    _p.bSerifStyle = 11     # Normal Sans
    _p.bWeight = _wt
    _p.bProportion = 3      # Modern
    _p.bContrast = 2        # None
    _p.bStrokeVariation = 2
    _p.bArmStyle = 2
    _p.bLetterForm = 2
    _p.bMidline = 2
    _p.bXHeight = 3
    fb.setupPost()
    # 斜体字重标注真实倾斜角（DSEG14 的 Classic-Italic 为 -5）
    fb.font["post"].italicAngle = -5.0 if "Italic" in style else 0.0
    fb.setupMaxp()
    weight = {"Light": 300, "LightItalic": 300, "Regular": 400,
              "Italic": 400, "Bold": 700, "BoldItalic": 700}[style]
    italic = "Italic" in style
    bold = style.startswith("Bold")
    os2 = fb.font["OS/2"]
    os2.usWeightClass = weight
    fs = os2.fsSelection
    fs = (fs | 0x01) if italic else (fs & ~0x01)
    fs = (fs | 0x20) if bold else (fs & ~0x20)
    fs = (fs & ~0x40) if (italic or bold) else (fs | 0x40)
    os2.fsSelection = fs
    fb.font["head"].macStyle = (0x01 if bold else 0) | (0x02 if italic else 0)

    out_dir = MONO_OUTDIR if mono else OUTDIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (f"HSEG16Mono{fam}-{style}.ttf" if mono
                     else f"HSEG16{fam}-{style}.ttf")
    fb.save(str(out))
    print(f"{'Mono ' if mono else ''}{fam}-{style}: 原字形 {len(items)}，替换 {replaced} -> {out.name}")
    return out, {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fam", default="Classic")
    ap.add_argument("--style", default="Regular")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--mono", action="store_true")
    args = ap.parse_args()
    root = ET.parse(SVG).getroot()
    groups = [el for el in root.iter() if el.tag == NS + "g"]
    if args.all:
        for fam in FAMS.values():
            for style in STYLES:
                build_style(fam, style, groups, mono=args.mono)
        return 0
    out, codes = build_style(args.fam, args.style, groups, mono=args.mono)
    for ch in "0185:A":
        if ch in codes:
            print(ch, codes[ch])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
