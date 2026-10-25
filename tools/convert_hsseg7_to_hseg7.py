# -*- coding: utf-8 -*-
"""把 HSSeg7 的 24 个 TTF 改名为 HSEG7，并同步 HSEG16 的字体信息规范。"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools.ttLib import TTFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\DSHin\HoMiSe")
SRC = ROOT / "font-source" / "build" / "ttf7"
OUT = ROOT / "font-source" / "build" / "ttf7-hseg7"
VERSION = "1.0.0"
ITER_FILE = ROOT / "font-source" / "build" / "hseg7-iter.txt"

FAM_DISPLAY = {"Classic": "Classic", "ClassicMini": "Classic Mini",
               "Modern": "Modern", "ModernMini": "Modern Mini"}
STYLE_DISPLAY = {"Light": "Light", "LightItalic": "Light Italic", "Regular": "Regular",
                 "Italic": "Italic", "Bold": "Bold", "BoldItalic": "Bold Italic"}
WEIGHT = {"Light": 3, "LightItalic": 3, "Regular": 4, "Italic": 4,
          "Bold": 7, "BoldItalic": 7}


def next_iter() -> int:
    n = int(ITER_FILE.read_text(encoding="utf-8").strip()) + 1 if ITER_FILE.exists() else 1
    ITER_FILE.write_text(str(n), encoding="utf-8")
    return n


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    n = next_iter()
    internal = f"{VERSION}.{n}"
    count = 0
    for p in sorted(SRC.glob("HSSeg7*.ttf")):
        f = TTFont(str(p))
        nt = f["name"]
        fam = p.stem.replace("HSSeg7", "")
        fam_name, _, style = fam.partition("-")
        disp_fam = FAM_DISPLAY[fam_name]
        disp_style = STYLE_DISPLAY[style]
        family = f"HSEG 7 {disp_fam}"
        ps = f"HSEG7{fam_name}-{style}"
        values = {
            1: family,
            2: disp_style,
            3: f"{ps};2026;{internal}",
            4: f"{family} {disp_style}",
            5: f"Version {internal}",
            6: ps,
            8: "HoMiSe APP",
            9: "keshikan (original design); HoMiSe APP (modifications)",
            10: "HSEG7 is a 7-segment derivative of DSEG v0.46 for the HoMiSe clock app.",
            11: "https://github.com/KuwsSyet9999/HSEG-Fonts",
            12: "https://www.keshikan.net",
            16: family,
            17: disp_style,
            19: "HSEG7 12:34",
        }
        for rec in nt.names:
            if rec.nameID in values:
                rec.string = values[rec.nameID]
        # 旧记录里 name16/17/19 可能不存在，补上
        existing = {rec.nameID for rec in nt.names}
        for nid, val in values.items():
            if nid not in existing:
                nt.setName(val, nid, 3, 1, 0x409)
        os2 = f["OS/2"]
        os2.achVendID = "HSEG"
        pa = os2.panose
        pa.bFamilyType = 2
        pa.bSerifStyle = 11
        pa.bWeight = WEIGHT[style]
        pa.bProportion = 3
        pa.bContrast = 2
        pa.bStrokeVariation = 2
        pa.bArmStyle = 2
        pa.bLetterForm = 2
        pa.bMidline = 2
        pa.bXHeight = 3
        out = OUT / f"HSEG7{fam_name}-{style}.ttf"
        f.save(str(out))
        f.close()
        count += 1
    print(f"converted {count} -> {OUT} (internal {internal})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
