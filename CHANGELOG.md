# Changelog

## 1.1.0 — 2026-10-27

### HSEG16

- 私有区全宽小写重做：`b` `d` `h` `j` `n` `u` 六个字形按新段码重建
  （`b`=e f g h r u、`d`=c d e f p t、`h`=f g h s u、`j`=d e f p、
  `n`=d p s u、`u`=e f g s），advance 与常规小写一致（816）。
- 常规 `j` 保持 `e s` 不变。
- 预览器字符表与字体编码全量同步。

### HSEG7

- `A`/`C`/`H`/`X`/`M`/`W` 重编码：A=1110111、C=1101110、H=0110111、
  X=0110110、M=1010101、W=0101011。
- `I`=0000110、`(`=1001110、`)`=1111000。
- `?`=1100101、`!`=0110000，均叠加 period 点（平移到 `x[754,878]`）。
- 小写 `a`–`z` 与大写 `A`–`Z` 完全同形（624 个字形复制）。

### 兼容性

- 码位不变，仅字形与段码调整。
- HSEG7 的 `?`/`!` 点属于字形，无 dp 位可解析；HSEG16 仍为 17 位含 dp。

## 1.0.0 — 2026-10-26

首个正式版本，为安卓 APP「时分秒(HoMiSe)」显示适配调整、更符合本地习惯。

### HSEG16（16 段）

- 24 个字体（Classic / Classic Mini / Modern / Modern Mini × Light / Light Italic / Regular / Italic / Bold / Bold Italic）
- ASCII 32–126 全覆盖，数字、大写、小写、符号均按固定亮段编码
- 补齐 DSEG14 缺失的 `#`、`;`、`[`、`]`、`{`、`}`、`¥`
- `~` 为十六段全亮；`!`、`?` 含小数点（dp）点；`period` 跨原点、`colon` 圆角并带斜体倾斜
- 私有区 `U+E000–U+E019` 提供等宽小写（advance 816，与原 `a`–`z` 同宽，仅亮段不同）
- 顶/底横保留模板分段缝隙（不做粘连修正）

### HSEG7（7 段）

- 24 个字体，7 段数字字形
- 家族名、PostScript 名、vendor、panose、name8–19 与 HSEG16 对齐

### 元信息

- `achVendID = HSEG`
- `panose = [2, 11, <weight>, 3, 2, 2, 2, 2, 2, 3]`（weight：Light 3 / Regular 4 / Bold 7）
- 斜体 `italicAngle = -5`
- name8 `HoMiSe APP`、name9 设计者署名、name10 派生说明、name11 项目地址、name12 原作者地址

### 已知限制

- HSEG7 的字符覆盖沿用 DSEG7（83 个），不含 HSEG16 新增的部分符号
- 小写字母的等宽版本仅在 HSEG16 的 PUA 码位提供
