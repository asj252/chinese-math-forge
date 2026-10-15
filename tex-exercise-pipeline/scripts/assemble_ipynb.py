#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""assemble_ipynb.py — 把习题 Markdown 与验算 Notebook 交错组合成一份 .ipynb。

只依赖标准库（json）。不执行 notebook；验算 notebook 里已有的执行输出原样带过来。

用法:
    python <本 skill 的目录>/scripts/assemble_ipynb.py <习题.md> <验算.ipynb> <mapping.json> <输出.ipynb>

输入:
    习题.md       阶段 A 的产物。习题是 `::::{exercise}` 块（冒号数不限，至少 3 个；块内嵌套的 directive 冒号要更少）。
                  冒号 directive 与代码围栏的开头、结尾可以缩进 0–3 格；缩进 4 格以上的行是普通内容（缩进代码），
                  不当成开头或结尾。反引号写法的 directive、引用块或列表里的 directive 不支持。
                  习题之间的 `### 子节标题` 变成单独的 markdown cell；`---` 分隔线略过（cell 本身已经分开）；
                  其他文字原样成为 markdown cell；习题之外的 directive 或孤立的冒号结尾报错。
    验算.ipynb    阶段 B 的产物。第一个 code cell 是全局设置与辅助函数；之后每段以一个只有一行 `## ` 标题的
                  markdown cell 起头，到下一个 `## ` 之前的所有 cell（一个或多个 code cell、说明用的 markdown cell）算一个代码段。
                  开头可以有一个只有一行 `# ` 标题的 cell。标题 cell 里若还有别的文字就停下（不会悄悄丢掉）。
    mapping.json  {"title": "习题标题", "ex_to_code": {"0": 0, "1": null, ...}, "intro": "可选的说明", "outro": "可选的结尾"}
                  ex_to_code 必须为每一道习题（0-based，键写成不带前导零的数字字符串）给出代码段编号（0-based）或 null；
                  多道题可以指向同一段（只在第一次出现时放入）。每一段代码都必须被用到。

任何对不上的地方（习题块没有结尾、映射缺题或越界、代码段没被用到、验算 notebook 有无法归属的 cell）都停下报错，
不会静默丢弃内容。输出文件已存在时停下，不覆盖（检查与改名之间若有别的程序同时写同一个文件，不在保护范围内）。

结束码：0 成功；1 内容对不上或读写失败（不写出任何东西）；2 用法错误。
"""
import json
import os
import re
import sys
import tempfile

OPEN = re.compile(r"^ {0,3}(:{3,})\{([A-Za-z][\w:-]*)\}")
CLOSE = re.compile(r"^ {0,3}(:{3,})\s*$")
TICKS = re.compile(r"^ {0,3}(`{3,}|~{3,})")


class Stop(Exception):
    pass


def lines_of(text):
    return text.splitlines(keepends=True)


def parse_exercises(text):
    """回传项目清单：('exercise', 文字, label) 或 ('md', 文字)。"""
    items, buf, block, stack, fence = [], [], None, [], None
    label = None

    def flush():
        t = "".join(buf).strip("\n")
        if t.strip():
            items.append(("md", t + "\n"))
        buf.clear()

    for no, line in enumerate(text.splitlines(keepends=True), 1):
        st = line.rstrip("\n")
        if fence:  # 反引号或波浪号围栏里的内容不解析
            (block if block is not None else buf).append(line)
            m_end = TICKS.match(st)
            if m_end and m_end.group(1)[0] == fence[0] and len(m_end.group(1)) >= len(fence) and st.strip() == m_end.group(1):
                fence = None
            continue
        m_t = TICKS.match(st)
        if m_t:
            fence = m_t.group(1)
            (block if block is not None else buf).append(line)
            continue
        m_open, m_close = OPEN.match(st), CLOSE.match(st)
        if block is None:
            if m_open and m_open.group(2) == "exercise":
                flush()
                block, stack, label = [line], [len(m_open.group(1))], None
            elif m_open:
                raise Stop("第 %d 行：习题之外有 {%s} directive，脚本不知道它属于哪道题" % (no, m_open.group(2)))
            elif m_close:
                raise Stop("第 %d 行：习题之外有孤立的冒号结尾 %s" % (no, st.strip()))
            elif st.strip() == "---":
                flush()
            elif st.startswith("### "):
                flush()
                items.append(("md", st + "\n"))
            else:
                buf.append(line)
            continue
        block.append(line)
        if m_open:
            n = len(m_open.group(1))
            if n >= stack[-1]:
                raise Stop("第 %d 行：嵌套的 {%s} 用了 %d 个冒号，外层只有 %d 个（嵌套的要更少）" % (no, m_open.group(2), n, stack[-1]))
            stack.append(n)
        elif m_close:
            n = len(m_close.group(1))
            if n != stack[-1]:
                raise Stop("第 %d 行：结尾的冒号数 %d 与开头 %d 对不上" % (no, n, stack[-1]))
            stack.pop()
            if not stack:
                items.append(("exercise", "".join(block).rstrip("\n") + "\n", label))
                block = None
        elif len(stack) == 1 and label is None:
            m = re.match(r"^ {0,3}:label:\s*(\S+)", st)
            if m:
                label = m.group(1)
    if block is not None:
        raise Stop("习题块没有结尾（开头 %s）" % block[0].strip())
    if fence:
        raise Stop("有没结尾的代码围栏 %s" % fence)
    flush()
    return items


def text_of(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def only_heading(text, what):
    if len([x for x in text.split("\n") if x.strip()]) != 1:
        raise Stop("%s只能有一行标题；说明请放进单独的 markdown cell" % what)


def parse_verify(nb):
    cells = nb.get("cells")
    if not isinstance(cells, list):
        raise Stop("验算 notebook 没有 cells 清单")
    setup, pairs, i = None, [], 0
    if i < len(cells) and cells[i].get("cell_type") == "markdown" and text_of(cells[i]).lstrip().startswith("# "):
        only_heading(text_of(cells[i]), "开头的标题 cell")
        i += 1
    if i < len(cells) and cells[i].get("cell_type") == "code":
        setup = cells[i]
        i += 1
    else:
        raise Stop("验算 notebook 的第一个 code cell（全局设置与辅助函数）找不到：标题之后应紧接着它")
    while i < len(cells):
        c = cells[i]
        if not (c.get("cell_type") == "markdown" and text_of(c).lstrip().startswith("## ")):
            raise Stop("验算 notebook 第 %d 格不在任何 `## ` 代码段里" % i)
        only_heading(text_of(c), "代码段标题 cell「%s」" % text_of(c).strip().split("\n")[0])
        group = [c]
        i += 1
        while i < len(cells) and not (cells[i].get("cell_type") == "markdown" and text_of(cells[i]).lstrip().startswith("## ")):
            group.append(cells[i])
            i += 1
        if not any(x.get("cell_type") == "code" for x in group[1:]):
            raise Stop("代码段「%s」没有 code cell" % text_of(c).strip())
        pairs.append(group)
    return setup, pairs


def load_mapping(m, n_ex, n_pairs):
    if not isinstance(m, dict):
        raise Stop("mapping.json 要是物件")
    extra = set(m) - {"title", "ex_to_code", "intro", "outro"}
    if extra:
        raise Stop("mapping.json 有不认识的字段 %s（子节标题请写在习题 md 里，用 `### `）" % sorted(extra))
    if not isinstance(m.get("title"), str) or not m["title"].strip():
        raise Stop("mapping.json 要有 title")
    raw = m.get("ex_to_code")
    if not isinstance(raw, dict):
        raise Stop("mapping.json 要有 ex_to_code 物件")
    out = {}
    for k, v in raw.items():
        if not (isinstance(k, str) and k.isdigit() and str(int(k)) == k):
            raise Stop("ex_to_code 的键要是不带前导零的习题编号（0-based 数字字符串）：%r" % k)
        if v is not None and (isinstance(v, bool) or not isinstance(v, int) or not 0 <= v < n_pairs):
            raise Stop("习题 %s 指向的代码段 %r 不存在（共有 %d 段）" % (k, v, n_pairs))
        out[int(k)] = v
    if sorted(out) != list(range(n_ex)):
        raise Stop("ex_to_code 要正好给出习题 0..%d（习题 md 里有 %d 道题），现在是 %s" % (n_ex - 1, n_ex, sorted(out)))
    unused = sorted(set(range(n_pairs)) - {v for v in out.values() if v is not None})
    if unused:
        raise Stop("代码段 %s 没有任何习题用到" % unused)
    for x in ("intro", "outro"):
        if x in m and not isinstance(m[x], str):
            raise Stop("mapping.json 的 %s 要是字符串" % x)
    return out


def no_duplicates(pairs):
    keys = [k for k, _ in pairs]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        raise Stop("mapping.json 里有重复的键 %s" % dup)
    return dict(pairs)


def assemble(md_path, nb_path, map_path, out_path):
    if os.path.exists(out_path):
        raise Stop("输出 %s 已存在，不覆盖" % out_path)
    try:
        with open(md_path, encoding="utf-8") as f:
            items = parse_exercises(f.read())
        with open(nb_path, encoding="utf-8") as f:
            vnb = json.load(f)
        with open(map_path, encoding="utf-8") as f:
            mapping = json.load(f, object_pairs_hook=no_duplicates)
    except (OSError, ValueError) as e:
        raise Stop("读不了输入：%s" % e)
    exercises = [x for x in items if x[0] == "exercise"]
    if not exercises:
        raise Stop("习题 md 里没有 {exercise} 块")
    setup, pairs = parse_verify(vnb)
    ex_to_code = load_mapping(mapping, len(exercises), len(pairs))

    cells = []

    def md(text):
        cells.append({"cell_type": "markdown", "metadata": {}, "source": lines_of(text)})

    head = "# %s\n" % mapping["title"].strip()
    if mapping.get("intro"):
        head += "\n" + mapping["intro"].rstrip("\n") + "\n"
    md(head)
    cells.append(dict(setup))
    emitted, k = set(), 0
    for item in items:
        if item[0] == "md":
            md(item[1])
            continue
        md(item[1])
        cp = ex_to_code[k]
        if cp is not None and cp not in emitted:
            for c in pairs[cp][1:]:  # 代码段的 `## ` 标题只是对应用的，不放进成品；其余 cell 原样（含输出）
                cells.append(dict(c))
            emitted.add(cp)
        k += 1
    if mapping.get("outro"):
        md(mapping["outro"])
    for i, c in enumerate(cells):
        c["id"] = "c%03d" % i
        if c["cell_type"] == "code":
            c.setdefault("outputs", [])
            c.setdefault("execution_count", None)
    meta = {"kernelspec": vnb.get("metadata", {}).get("kernelspec") or
            {"display_name": "Python 3", "language": "python", "name": "python3"}}
    if vnb.get("metadata", {}).get("language_info"):
        meta["language_info"] = vnb["metadata"]["language_info"]
    nb = {"cells": cells, "metadata": meta, "nbformat": 4, "nbformat_minor": 5}

    d = os.path.dirname(os.path.abspath(out_path))
    try:
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".assemble-", suffix=".ipynb", dir=d)
    except OSError as e:
        raise Stop("建不了输出目录或临时文件：%s" % e)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
            f.write("\n")
        if os.path.exists(out_path):
            raise Stop("输出 %s 在写入期间出现了，不覆盖" % out_path)
        os.replace(tmp, out_path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    n_md = sum(c["cell_type"] == "markdown" for c in cells)
    print("组合完成：%d 道习题、%d 段代码 → %d 个 cell（markdown %d、code %d）：%s"
          % (len(exercises), len(pairs), len(cells), n_md, len(cells) - n_md, out_path))


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows 的管道或非 UTF-8 控制台下也能打印中文
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    if len(sys.argv) != 5:
        sys.stderr.write(__doc__)
        sys.exit(2)
    try:
        assemble(*sys.argv[1:5])
    except Stop as e:
        sys.stderr.write("停下：%s。没有写出任何东西\n" % e)
        sys.exit(1)


if __name__ == "__main__":
    main()
