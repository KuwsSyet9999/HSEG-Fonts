# -*- coding: utf-8 -*-
"""导出 HSEG16 正式 TTC 到 release/。

命名：HSEG16_<版本>_<14位时间>_<sha256 前16>.ttc + 同名 .sha256
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\DSHin\HoMiSe")
TOOLS = ROOT / "font-source" / "tools"
TTF_DIR = ROOT / "font-source" / "build" / "hseg16-ttf"
TTF_DIR_MONO = ROOT / "font-source" / "build" / "hseg16-ttf-mono"
TTC = ROOT / "font-source" / "build" / "HSEG16.ttc"
TTC_MONO = ROOT / "font-source" / "build" / "HSEG16Mono.ttc"
RELEASE = ROOT / "release"
VERSION = "1.0.0"
ITER_FILE = ROOT / "font-source" / "build" / "hseg16-iter.txt"


def strip_internal_iter(ttc_path: Path, version: str) -> None:
    """把内部迭代版本 0.1.0.<n> 改回正式版本（去掉第 4 位）。"""
    from fontTools.ttLib import TTCollection
    out = ttc_path.with_suffix(".final.ttc")
    c = TTCollection(str(ttc_path))
    for f in c.fonts:
        nt = f["name"]
        for rec in nt.names:
            if rec.nameID == 5:
                rec.string = f"Version {version}"
            elif rec.nameID == 3:
                s = rec.toUnicode()
                head, sep, _ = s.rpartition(";")
                if sep:
                    rec.string = f"{head};{version}"
    c.save(str(out))
    c.close()
    out.replace(ttc_path)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mono", action="store_true")
    args = ap.parse_args()
    ttf_dir = TTF_DIR_MONO if args.mono else TTF_DIR
    ttc = TTC_MONO if args.mono else TTC
    prefix = "HSEG16Mono" if args.mono else "HSEG16"
    py = sys.executable
    subprocess.run([py, str(TOOLS / "build_ttc.py"),
                    "--ttf-dir", str(ttf_dir), "--out", str(ttc)], check=True)

    # 在临时副本上剥离内部迭代位，build/ 下的 TTC 保留 0.1.0.<n>
    tmp = ttc.with_suffix(".release.ttc")
    shutil.copy2(ttc, tmp)
    strip_internal_iter(tmp, VERSION)
    data = tmp.read_bytes()
    tmp.unlink()
    from fontTools.ttLib import TTCollection
    _c = TTCollection(str(ttc))
    _ver = _c.fonts[0]["name"].getDebugName(5)
    _c.close()
    parts = _ver.split(".")
    iter_n = parts[3] if len(parts) > 3 else "0"
    digest = hashlib.sha256(data).hexdigest()[:16]
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    RELEASE.mkdir(exist_ok=True)
    name = f"{prefix}_{VERSION}_{stamp}_{digest}.ttc"
    final = RELEASE / name
    final.write_bytes(data)
    (final.with_suffix(".ttc.sha256")).write_text(
        f"{digest}  {name}\n", encoding="utf-8", newline="\n"
    )

    print(f"导出: {final}")
    print(f"大小: {len(data):,} B")
    print(f"SHA-256: {digest}")
    print(f"校验文件: {final.with_suffix('.ttc.sha256')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
