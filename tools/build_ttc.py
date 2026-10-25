# -*- coding: utf-8 -*-
"""把多个 TTF 合并成一个 TTC（TrueType Collection）。

不共享表数据，按字体内表目录重新布局；保留各字体原有表内容与校验和。

用法：
  python build_ttc.py --ttf-dir build/ttf7 --out build/HSSeg7.ttc
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def checksum(data: bytes) -> int:
    s = 0
    for i in range(0, len(data), 4):
        chunk = data[i:i + 4]
        if len(chunk) < 4:
            chunk += b"\0" * (4 - len(chunk))
        s = (s + struct.unpack(">I", chunk)[0]) & 0xFFFFFFFF
    return s


def read_tables(path: Path):
    data = path.read_bytes()
    num = struct.unpack_from(">H", data, 4)[0]
    tables = {}
    for i in range(num):
        off = 12 + i * 16
        tag = data[off:off + 4].decode("latin-1")
        _, toff, tlen = struct.unpack_from(">III", data, off + 4)
        tables[tag] = data[toff:toff + tlen]
    return tables


def build(paths, out: Path):
    fonts = [read_tables(p) for p in paths]
    header_size = 12 + 4 * len(fonts)
    cur = header_size
    offsets = []
    body = bytearray()

    for tables in fonts:
        offsets.append(cur)
        n = len(tables)
        p = 2 ** int(math.log2(n))
        search_range = p * 16
        entry_selector = int(math.log2(p))
        range_shift = n * 16 - search_range

        dir_size = 12 + 16 * n
        data_off = cur + dir_size
        entries = []
        table_data = bytearray()
        for tag in sorted(tables):
            d = tables[tag]
            entries.append((tag, checksum(d), data_off + len(table_data), len(d)))
            table_data += d
            table_data += b"\0" * ((-len(d)) % 4)

        directory = struct.pack(">IHHHH", 0x00010000, n, search_range, entry_selector, range_shift)
        for tag, cs, off, ln in entries:
            directory += tag.encode("latin-1") + struct.pack(">III", cs, off, ln)
        body += directory + table_data
        cur += dir_size + len(table_data)

    header = b"ttcf" + struct.pack(">II", 0x00010000, len(fonts))
    header += b"".join(struct.pack(">I", o) for o in offsets)
    out.write_bytes(header + body)
    return len(fonts)


def font_order(p: Path):
    """Classic → Classic Mini → Modern → Modern Mini；每族 Light → … → BoldItalic。

    TTF 文件名形如 `HSSeg7Classic-Bold.ttf` / `HSSeg16ModernMini-Italic.ttf`，
    族名前缀随系列不同，这里统一剥掉再做排序。
    """
    fam, _, style = p.stem.partition("-")
    for pre in ("HSSeg16", "HSSeg7", "HSEG16", "HSEG7", "DSEG14"):
        if fam.startswith(pre):
            fam = fam[len(pre):]
            break
    fam_order = {"Classic": 0, "ClassicMini": 1, "Modern": 2, "ModernMini": 3}
    style_order = {"Light": 0, "LightItalic": 1, "Regular": 2,
                   "Italic": 3, "Bold": 4, "BoldItalic": 5}
    return (fam_order.get(fam, 9), style_order.get(style, 9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttf-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ttf_dir = Path(args.ttf_dir)
    paths = sorted(ttf_dir.glob("*.ttf"), key=font_order)
    if not paths:
        raise SystemExit(f"没有 TTF: {ttf_dir}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = build(paths, out)
    print(f"写好 {out}（{n} 个字体，{out.stat().st_size:,} B）")


if __name__ == "__main__":
    raise SystemExit(main())
