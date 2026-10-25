# -*- coding: utf-8 -*-
"""解析 SFD 的 SplineSet，保留三次贝塞尔曲线（m/l/c），供重建使用。"""
from __future__ import annotations

import sys
from pathlib import Path


def parse_sfd_curves(path: Path):
    """返回 glyph 列表：{name, unicode, width, segments}。

    segments 每项：
      ("m", (x, y))
      ("l", (x, y))
      ("c", ((x1,y1), (x2,y2), (x3,y3)))
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    glyphs = []
    n = len(lines)
    i = 0
    while i < n:
        if not lines[i].startswith("StartChar:"):
            i += 1
            continue
        name = lines[i].split(":", 1)[1].strip()
        uni = None
        width = 0
        segs = []
        in_spline = False
        j = i + 1
        while j < n and not lines[j].startswith("EndChar"):
            l2 = lines[j]
            if l2.startswith("Encoding:"):
                parts = l2.split(":", 1)[1].split()
                if len(parts) >= 2 and parts[1].lstrip("-").isdigit():
                    uni = int(parts[1])
            elif l2.startswith("Width:"):
                try:
                    width = int(l2.split(":", 1)[1])
                except ValueError:
                    pass
            elif l2.startswith("SplineSet"):
                in_spline = True
            elif l2.startswith("EndSplineSet"):
                in_spline = False
            elif in_spline and l2.strip():
                parts = l2.split()
                flag = parts[-2] if len(parts) >= 2 else ""
                nums = parts[:-2]
                try:
                    vals = [float(v) for v in nums]
                except ValueError:
                    j += 1
                    continue
                if flag == "m" and len(vals) >= 2:
                    segs.append(("m", (vals[0], vals[1])))
                elif flag == "l" and len(vals) >= 2:
                    segs.append(("l", (vals[0], vals[1])))
                elif flag == "c" and len(vals) >= 6:
                    segs.append(("c", ((vals[0], vals[1]), (vals[2], vals[3]), (vals[4], vals[5]))))
            j += 1
        glyphs.append({"name": name, "unicode": uni, "width": width, "segments": segs})
        i = j + 1
    return glyphs


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    gs = parse_sfd_curves(Path(r"D:\DSHin\HoMiSe\font-source\DSEG-v0.46\src\DSEG14Modern-Regular.sfd"))
    seg_types = {}
    for g in gs:
        for s in g["segments"]:
            seg_types[s[0]] = seg_types.get(s[0], 0) + 1
    print("glyphs", len(gs), "seg types", seg_types)
