# HSEG Fonts

HSEG（**H**oMiSe **Seg**ment）是一套为安卓 APP「时分秒(HoMiSe)」显示**优化调整**、更符合本地习惯的段码字体，
派生自 [keshikan](https://www.keshikan.net) 的 **DSEG**（v0.46），保留其 OFL 1.1 版权与许可。

本项目提供两个系列，每个系列 24 个字重（4 族 × 6 字重）：

| 系列 | 段数 | 家族名 | 文件 |
| --- | --- | --- | --- |
| HSEG16 | 16 段 | `HSEG 16 Classic / Classic Mini / Modern / Modern Mini` | `release/HSEG16_1.0.0_*.ttc` |
| HSEG7 | 7 段 | `HSEG 7 Classic / Classic Mini / Modern / Modern Mini` | `release/HSEG7_1.0.0_*.ttc` |

每个 TTC 内含 24 个字体（Light、Light Italic、Regular、Italic、Bold、Bold Italic）。

## 特性

- **HSEG16**：16 段几何（`HSSeg16-avg.svg` 派生），ASCII 32–126 全覆盖，
  含 DSEG14 原本缺失的 `# ; [ ] { }`；`~` 为十六段全亮；`!` `?` 含小数点（dp）点。
- **HSEG7**：7 段数字字体，保留 DSEG7 的字符覆盖。
- **PUA 等宽小写**：HSEG16 在 `U+E000–U+E019` 提供一套等宽小写（`a`–`z` 的 Mono 变体），
  与原 `a`–`z`（U+0061–U+007A，advance 816）同宽，仅亮段不同，供应用按需切换。
- 元信息完整：`achVendID = HSEG`、`panose` 按字重、斜体 `italicAngle = -5`。

## 字符表

- [HSEG16 字符表（SVG）](docs/hseg16-charset.svg)
- [HSEG7 字符表（SVG）](docs/hseg7-charset.svg)
- 全字重预览：[HSEG16](docs/hseg16-all-weights.png) / [HSEG7](docs/hseg7-all-weights.png)

## 安装

1. 从 [`release/`](release/) 下载对应 `.ttc`；
2. Windows：右键 → 安装（或复制到 `C:\Windows\Fonts`）；
   macOS：双击用「字体册」安装；
   Linux：复制到 `~/.local/share/fonts/` 后 `fc-cache -f`；
3. 在应用中以家族名 `HSEG 16 Classic` 等选用。

每个 `.ttc` 旁附 `.sha256` 校验文件，可用 `sha256sum -c` 核对。

## 构建

`tools/` 下是构建脚本（路径为项目内绝对路径，公开仓库中需按需调整）：

- `build_hseg16_from_svg.py`：从 DSEG14 的 SFD + `HSSeg16-avg.svg` 生成 HSEG16 的 24 个 TTF；
- `build_ttc.py`：把 TTF 目录打包成 TTC；
- `export_hseg16.py`：导出带版本/哈希的正式 TTC；
- `sfd_curves.py`：SFD 曲线解析（保留三次贝塞尔）。

依赖：Python 3.11+、`fontTools`、`Pillow`。

## 许可证

本项目字体遵循 **SIL Open Font License 1.1**，见 [LICENSE.txt](LICENSE.txt)。

- 原始设计：Copyright (c) 2017, keshikan (<https://www.keshikan.net>)，保留字体名 `DSEG`；
- 修改部分：Copyright (c) 2026, HoMiSe APP。

HSEG 的家族名不含 `DSEG`，属于 OFL 允许的改名发布方式。再分发时请保留本许可与上述版权声明。

## English

HSEG is a family of segmented display fonts designed specifically for the Android app
**"时分秒 (HoMiSe)"**, derived from [DSEG](https://www.keshikan.net) v0.46 by keshikan and
released under the SIL Open Font License 1.1. It ships two series — **HSEG16** (16-segment)
and **HSEG7** (7-segment) — each with 24 weights (4 families × 6 weights) packed as TTC files.
HSEG16 includes a monospaced lowercase set in the Private Use Area (`U+E000–U+E019`)
alongside the normal `a`–`z`.
