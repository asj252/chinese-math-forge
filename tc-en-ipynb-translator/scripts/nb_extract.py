#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""nb_extract.py — 把 Jupyter Notebook 逐格 dump 成純文字，供審查或翻譯時完整閱讀。

只依賴標準庫（json），不需要 nbformat。

用法:
    python <本 skill 的目錄>/scripts/nb_extract.py <input.ipynb> [output.txt] [--range A:B]

輸出格式（每格一區塊）:
    ===== CELL 0 | markdown | lines=12 =====
    <原始 source 文字>
    ===== CELL 1 | code | lines=30 | outputs=0 =====
    ...

若省略 output.txt，直接印到 stdout。
--range 0:20 只輸出第 0..19 格（分段閱讀時用）。
"""
import json
import sys


class RangeError(Exception):
    pass


def extract(nb_path, lo=None, hi=None):
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    cells = nb.get("cells", [])
    lo = 0 if lo is None else lo
    if (hi is not None and lo > hi) or lo > len(cells):  # 倒序，或起點超出格數；合法的空範圍（如 0:0、6:）照常輸出零格
        raise RangeError("%s:%s" % (lo, hi))
    hi = len(cells) if hi is None else min(hi, len(cells))
    chunks = ["# NOTEBOOK: %s\n# TOTAL CELLS: %d\n# SHOWING: %d..%d\n"
              % (nb_path, len(cells), lo, hi - 1)]
    for i in range(lo, hi):
        c = cells[i]
        src = c.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        head = "===== CELL %d | %s | lines=%d" % (
            i, c.get("cell_type", "?"), len(src.splitlines()))
        if c.get("cell_type") == "code":
            head += " | outputs=%d" % len(c.get("outputs", []))
        head += " ====="
        chunks.append(head)
        chunks.append(src)
        chunks.append("")
    return "\n".join(chunks)


def usage():
    sys.stderr.write(__doc__)
    sys.exit(2)


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows 的管道或非 UTF-8 主控台下也能印中文
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    args = list(sys.argv[1:])
    lo = hi = None
    if "--range" in args:
        k = args.index("--range")
        if k + 1 >= len(args):
            usage()
        a, sep, b = args[k + 1].partition(":")
        if not sep or (a and not a.isdigit()) or (b and not b.isdigit()):
            usage()
        lo = int(a) if a else None
        hi = int(b) if b else None
        del args[k:k + 2]
    if not args or len(args) > 2:
        usage()
    try:
        text = extract(args[0], lo, hi)
    except RangeError:
        usage()
    except (OSError, ValueError) as e:  # 讀不到、不是 UTF-8 或不是合法 JSON
        sys.stderr.write("無法讀取 %s：%s\n" % (args[0], e))
        sys.exit(1)
    if len(args) > 1:
        with open(args[1], "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote %s (%d chars)" % (args[1], len(text)))
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
