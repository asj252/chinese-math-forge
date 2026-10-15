#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_translation.py — 核對繁中原稿與英文譯本：結構沒壞、已譯部分沒有殘留中文、還沒譯的部分保持原文。

只依賴標準庫（json、ast、re）。不執行 notebook。

用法:
    python <本 skill 的目錄>/scripts/verify_translation.py <原稿.ipynb> <譯本.ipynb> [選項]

選項:
    --cells A:B                 本批是第 A..B-1 格：第 0..B-1 格視為已譯（結構全部檢查，殘留中文只查本批），
                                第 B 格起視為待譯，必須與原稿逐字相同。不給就是全部已譯（交付前做一次全量檢查）。
    --allow 文字                 允許留在已譯部分的中文（例如程式裡刻意保留的中文字型名「微軟正黑體」），可重複。
    --allow-missing-label 值     經使用者同意在英文版省略的 label，可重複。
    --accept 原文字串             程式碼裡用途不明、但確認只是顯示文字的中文字串（寫原稿的字串），允許譯本改掉，可重複。
    --skip-code K               第 K 格程式碼不做結構比對（原稿本身不能解析時才用，並在回報裡說明），可重複。

已譯部分的檢查（任一不過，結束碼 1）:
    1. 兩份都是合法的 notebook JSON，cell 數與類型序列相同。
    2. 每格的 label：原稿的 `:label:` 與 `:name:` 的值，依序等於譯本的 `:label:` 的值（扣掉允許省略的）；譯本不再有 `:name:`。
    3. 每格的引用：`{ref}`、`{prf:ref}`、`{numref}`、`{eq}` 的目標（`文字 <label>` 只比 label），以及 `{solution}` 的引數，依序相同。
    4. 每格程式碼：除了字串，語法樹相同；**不含中文的字串一律與原稿相同**（色值、模板名、路徑、欄位名等）。
       含中文的字串按位置分四類：
       - 顯示文字：docstring 與單獨成句的字串；`print`、`set_title`、`xlabel`、`text`、`annotate` 等顯示函數的**位置引數**；
         繪圖呼叫（plot、scatter、bar、Scatter…）與顯示函數的 `label=`、`title=`、`name=`、`text=` 等文字關鍵字引數
         （含其中用 `+` 串接、條件運算式選出、清單或元組裡的字串）。可以自由翻譯；f-string 的文字部分可以改寫（原稿文字部分不含中文的 f-string 除外，要逐字相同），
         `{…}` 裡的運算式要相同、順序不變。
       - 引用位置：字典的 key、下標、清單／元組／集合的元素、比較運算的兩邊。原稿在某個字典裡當 key 的中文字串，
         在引用位置可以改名，但它在所有引用位置的譯法（含保持原文）必須相同，同一個字典裡改名後的 key 不能撞在一起；
         不是任何字典 key 的中文字串，在引用位置要保持原文（或用 --accept 列出）。
       - 其他位置（指派、一般函數的引數、f-string 運算式裡的常量等）：必須與原稿相同；確認只是顯示文字的，用 --accept 列出。
         字典 key 改了名、同字面的字串卻在其他位置保持原文時（例如同名的路徑），腳本照常通過，但列出提醒：
         若程式用變數間接取 key（如 `d[path]`），請人工核對。
       以 `%`、`!` 開頭的 IPython 魔術命令行逐字比對；以 `%%` 開頭的 cell 整格逐字比對。
    5. 本批（不給 --cells 時是全部）沒有殘留中文字與全形標點（--allow 列出的除外）。
待譯部分（第 B 格起）：source 與原稿逐字相同。

已知限制：顯示函數的清單是常見的 print 與 matplotlib／plotly 寫法，自訂的輸出函數裡的中文字串歸「其他位置」，
要用 --accept 列出；f-string 的 `{…}` 譯後換了順序會判為結構不同。「引用位置」是語法上的近似：字典 key 經由
清單下標（如 `['甲'][0]`）、集合或推導式間接使用時，腳本看不出它與 key 的關係；--accept 只放行字串改動，
不保證 key 各處同步。腳本列出的提醒與這些情形都要人工核對。

結束碼：0 全部通過；1 有檢查不過；2 用法錯誤或讀不到檔案。
"""
import ast
import json
import re
import sys

CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
FULLWIDTH = re.compile(r"[　-〿！-／：-＠［-｀｛-･・]")
LABEL = re.compile(r"^\s*:(label|name):\s*(\S+)", re.M)
REF = re.compile(r"\{(?:ref|prf:ref|numref|eq)\}`([^`]*)`")
SOLUTION = re.compile(r"^\s*(?::{3,}|`{3,})\{solution\}\s*(\S+)", re.M)
DISPLAY_FUNCS = {  # 位置引數是顯示文字
    "print", "title", "xlabel", "ylabel", "zlabel", "suptitle", "figtext", "text", "annotate",
    "set_title", "set_xlabel", "set_ylabel", "set_zlabel", "set_label", "set_text", "set_suptitle", "Markdown",
}
PLOT_FUNCS = {  # 只有文字關鍵字引數是顯示文字
    "plot", "scatter", "bar", "barh", "hist", "fill", "fill_between", "quiver", "axhline", "axvline", "errorbar",
    "step", "stem", "pie", "imshow", "contour", "contourf", "plot_surface", "plot_wireframe", "arrow", "legend",
    "update_layout", "update_xaxes", "update_yaxes", "add_annotation", "add_trace",
    "Scatter", "Scatter3d", "Bar", "Heatmap", "Surface", "Cone", "Mesh3d", "Histogram", "Figure",
}
DISPLAY_KWARGS = {"label", "title", "name", "text", "xlabel", "ylabel", "zlabel", "hovertemplate", "hovertext",
                  "texttemplate", "xaxis_title", "yaxis_title", "zaxis_title", "title_text", "legend_title_text", "s"}
PASS_POS = (ast.BinOp, ast.IfExp, ast.Tuple, ast.List, ast.Set, ast.Starred)  # 這些節點把「顯示」位置傳給子節點


def usage():
    sys.stderr.write(__doc__)
    sys.exit(2)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            nb = json.load(f)
    except (OSError, ValueError) as e:
        sys.stderr.write("讀不到 %s：%s\n" % (path, e))
        sys.exit(2)
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        sys.stderr.write("%s 不是合法的 notebook（沒有 cells 清單）\n" % path)
        sys.exit(2)
    return nb


def text(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else str(src)


def ref_targets(s):
    out = []
    for m in REF.finditer(s):
        t = m.group(1)
        k = t.rfind("<")
        out.append(t[k + 1:-1] if k >= 0 and t.endswith(">") else t)  # `顯示文字 <label>` 只比 label
    return out + ["solution:" + m.group(1) for m in SOLUTION.finditer(s)]


def split_magics(src):
    """把 IPython 魔術命令行換成 pass，回傳（可解析的程式碼, 魔術命令行清單）。"""
    code, magics = [], []
    for line in src.split("\n"):
        st = line.lstrip()
        if st.startswith(("%", "!")):
            magics.append(line)
            code.append(line[: len(line) - len(st)] + "pass")
        else:
            code.append(line)
    return "\n".join(code), magics


def func_name(call):
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None


class Extract:
    """前序走訪語法樹：把字串換成佔位，回傳結構描述；字串依出現順序收進 items：(值, 位置)。
    位置：'display'、'doc'（docstring／單獨成句）、'key'（字典的 key）、'other'。dicts 記每個字典的 key 在 items 裡的索引。"""

    def __init__(self):
        self.items, self.dicts = [], []

    def node(self, n, pos):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            self.items.append((n.value, pos))
            return "S"
        if isinstance(n, ast.JoinedStr):
            exprs = [self.node(v.value, "other") + "!" + str(v.conversion) + ":" +
                     (self.node(v.format_spec, "other") if v.format_spec else "")
                     for v in n.values if isinstance(v, ast.FormattedValue)]
            if pos in ("display", "doc"):  # 顯示位置：文字部分合起來當一個字串比（原稿不含中文就要相同）
                self.items.append(("".join(v.value for v in n.values if isinstance(v, ast.Constant)), "ftext"))
                # 文字逐段與 `{…}` 交錯的完整序列另記一項：原稿文字含中文時可以重排，不含中文時每段文字和位置都不能變
                self.items.append(("|".join(repr(v.value) if isinstance(v, ast.Constant) else "{}" for v in n.values), "fseq"))
                return "F(%s)" % ",".join(exprs)
            # 非顯示位置的 f-string：文字部分也要逐段相同，文字與 `{…}` 的交錯順序也不能變
            seq, ei = [], iter(exprs)
            for v in n.values:
                if isinstance(v, ast.Constant):
                    self.items.append((v.value, pos))
                    seq.append("S")
                else:
                    seq.append(next(ei))
            return "F*(%s)" % ",".join(seq)
        if isinstance(n, ast.Expr) and isinstance(n.value, (ast.Constant, ast.JoinedStr)):
            return "Expr(%s)" % self.node(n.value, "doc")
        if isinstance(n, ast.Call):
            fname = func_name(n)
            disp = fname in DISPLAY_FUNCS
            parts = ["Call", self.node(n.func, "other")]
            parts += [self.node(a, "display" if disp else "other") for a in n.args]
            for kw in n.keywords:
                kpos = "display" if ((disp or fname in PLOT_FUNCS) and kw.arg in DISPLAY_KWARGS) else "other"
                parts.append("kw:%s=%s" % (kw.arg, self.node(kw.value, kpos)))
            return "(" + " ".join(parts) + ")"
        if isinstance(n, ast.Subscript):
            return "(Subscript %s %s)" % (self.node(n.value, "other"), self.node(n.slice, "ref"))
        if isinstance(n, ast.Compare):
            return "(Compare %s %s %s)" % (self.node(n.left, "ref"), [type(o).__name__ for o in n.ops],
                                           ",".join(self.node(c, "ref") for c in n.comparators))
        if isinstance(n, (ast.List, ast.Tuple, ast.Set)) and pos != "display":
            return "(%s [%s])" % (type(n).__name__, ",".join(self.node(e, "ref") for e in n.elts))
        if isinstance(n, ast.Dict):
            keys, parts = [], ["Dict"]
            for k, v in zip(n.keys, n.values):
                if k is None:
                    parts.append("**")
                else:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        keys.append(len(self.items))
                    parts.append(self.node(k, "key"))
                parts.append(self.node(v, "other"))
            self.dicts.append(keys)
            return "(" + " ".join(parts) + ")"
        if isinstance(n, ast.AST):
            child = pos if isinstance(n, PASS_POS) and pos == "display" else "other"
            if isinstance(n, ast.IfExp):  # 條件本身不是顯示文字
                return "(IfExp %s %s %s)" % (self.node(n.test, "other"), self.node(n.body, child), self.node(n.orelse, child))
            parts = [type(n).__name__]
            for field in n._fields:
                if field in ("ctx", "type_comment", "kind"):
                    continue
                v = getattr(n, field, None)
                if isinstance(v, list):
                    parts.append("[%s]" % ",".join(self.node(x, child) if isinstance(x, ast.AST) else repr(x) for x in v))
                elif isinstance(v, ast.AST):
                    parts.append(self.node(v, child))
                else:
                    parts.append(repr(v))
            return "(" + " ".join(parts) + ")"
        return repr(n)


def parse_range(s, n):
    a, sep, b = s.partition(":")
    if not sep or (a and not a.isdigit()) or (b and not b.isdigit()):
        usage()
    lo = int(a) if a else 0
    hi = int(b) if b else n
    if lo > hi or lo > n:
        usage()
    return lo, min(hi, n)


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows 的管道或非 UTF-8 主控台下也能印中文
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    argv, pos = sys.argv[1:], []
    opts = {"--cells": [], "--allow": [], "--allow-missing-label": [], "--accept": [], "--skip-code": []}
    i = 0
    while i < len(argv):
        if argv[i] in opts:
            if i + 1 >= len(argv):
                usage()
            opts[argv[i]].append(argv[i + 1])
            i += 2
        elif argv[i].startswith("--"):
            usage()
        else:
            pos.append(argv[i])
            i += 1
    if len(pos) != 2 or len(opts["--cells"]) > 1 or not all(k.isdigit() for k in opts["--skip-code"]):
        usage()
    tc, en = load(pos[0]), load(pos[1])
    tcells, ecells = tc["cells"], en["cells"]
    batch = bool(opts["--cells"])
    lo, hi = parse_range(opts["--cells"][0], len(ecells)) if batch else (0, len(ecells))
    allow, missing, accept = opts["--allow"], set(opts["--allow-missing-label"]), set(opts["--accept"])
    skip = {int(k) for k in opts["--skip-code"]}
    problems = []

    tt, et = [c.get("cell_type") for c in tcells], [c.get("cell_type") for c in ecells]
    if tt != et:
        problems.append("cell 數或類型序列不同（原稿 %d 格、譯本 %d 格）" % (len(tt), len(et)))
        report(problems)
    code_pairs = []
    for k, (tcell, ecell) in enumerate(zip(tcells, ecells)):
        ts, es = text(tcell), text(ecell)
        if k >= hi:  # 待譯部分：保持原文
            if ts != es:
                problems.append("第 %d 格在本批之後（待譯），應與原稿逐字相同" % k)
            continue
        tl = [v for _, v in LABEL.findall(ts) if v not in missing]
        el = [v for kind, v in LABEL.findall(es) if kind == "label"]
        if any(kind == "name" for kind, _ in LABEL.findall(es)):
            problems.append("第 %d 格：譯本還有 :name:（應改成 :label:）" % k)
        if tl != el:
            problems.append("第 %d 格：label 不同（原稿 %s，譯本 %s）" % (k, tl, el))
        if ref_targets(ts) != ref_targets(es):
            problems.append("第 %d 格：引用不同（原稿 %s，譯本 %s）" % (k, ref_targets(ts), ref_targets(es)))
        if tcell.get("cell_type") == "code" and k not in skip:
            if ts.lstrip().startswith("%%"):
                if ts != es:
                    problems.append("第 %d 格：以 %%%% 開頭的 cell 要整格逐字相同" % k)
            else:
                (tcode, tm), (ecode, em) = split_magics(ts), split_magics(es)
                if tm != em:
                    problems.append("第 %d 格：魔術命令行不同" % k)
                try:
                    ta = ast.parse(tcode)
                except SyntaxError as e:
                    problems.append("第 %d 格：原稿不能解析（%s）；請人工核對，確認後用 --skip-code %d 略過" % (k, e.msg, k))
                    ta = None
                if ta is not None:
                    try:
                        ea = ast.parse(ecode)
                    except SyntaxError as e:
                        problems.append("第 %d 格：譯本不能解析（第 %s 行：%s）" % (k, e.lineno, e.msg))
                        ea = None
                    if ea is not None:
                        xa, xb = Extract(), Extract()
                        if xa.node(ta, "other") != xb.node(ea, "other") or len(xa.items) != len(xb.items):
                            problems.append("第 %d 格：程式結構不同（字串以外的部分被改動，或 f-string 的運算式被改）" % k)
                        else:
                            code_pairs.append((k, xa, xb))
        if (lo <= k < hi) or not batch:
            rest = es
            for a in allow:
                rest = rest.replace(a, "")
            for ln, line in enumerate(rest.split("\n"), 1):
                hit = sorted(set(CJK.findall(line) + FULLWIDTH.findall(line)))
                if hit:
                    problems.append("第 %d 格第 %d 行：殘留中文或全形標點 %s：%s" % (k, ln, "".join(hit), line.strip()[:60]))
    # 第 4 項的字串比對：先找出已譯部分所有當字典 key 的中文字串
    key_strings = {xa.items[i][0] for _, xa, _ in code_pairs for d in xa.dicts for i in d if CJK.search(xa.items[i][0])}
    key_uses, kept_elsewhere = {}, {}
    for k, xa, xb in code_pairs:
        ftext_cjk = False  # 最近一個顯示位置 f-string 的原稿文字是否含中文
        for (a, p), (b, _) in zip(xa.items, xb.items):
            if p == "ftext":
                ftext_cjk = bool(CJK.search(a))
            if p == "fseq":
                if not ftext_cjk and a != b:
                    problems.append("第 %d 格：原稿文字不含中文的 f-string，文字的分段或與 {…} 的相對位置被改了（%s → %s）" % (k, a, b))
                continue
            if not CJK.search(a):
                if a != b:
                    problems.append("第 %d 格：不含中文的字串 %r 被改成 %r（不含中文的字串一律不變）" % (k, a, b))
                continue
            if p in ("display", "doc", "ftext"):
                continue
            if p in ("key", "ref") and a in key_strings:
                key_uses.setdefault(a, set()).add(b)
                continue
            if a != b and a not in accept:
                problems.append("第 %d 格：%s的中文字串 %r 被改成 %r；保留原文，或確認只是顯示文字後用 --accept 列出"
                                % (k, "引用位置（不是字典 key）" if p == "ref" else "用途不明", a, b))
            elif a == b and a in key_strings:
                kept_elsewhere.setdefault(a, set()).add(k)
        for d in xa.dicts:
            tk, ek = [xa.items[i][0] for i in d], [xb.items[i][0] for i in d]
            if len(set(tk)) == len(tk) and len(set(ek)) != len(ek):
                problems.append("第 %d 格：字典的 key 改名後撞在一起：%s → %s" % (k, tk, ek))
    for a, bs in sorted(key_uses.items()):
        if len(bs) > 1:
            problems.append("字典 key「%s」在各引用位置（字典、下標、清單、比較）的譯法不同：%s（引用處要同步改）" % (a, sorted(bs)))
    notes = ["提醒：字典 key「%s」改成了 %s，同字面的字串在第 %s 格的其他位置保持原文；若程式用變數間接取 key，請人工核對"
             % (a, sorted(key_uses[a] - {a}), sorted(ks)) for a, ks in sorted(kept_elsewhere.items()) if key_uses.get(a, {a}) != {a}]
    for line in notes:
        print("  ! " + line)
    report(problems, len(tcells), (lo, hi), batch)


def report(problems, n=None, rng=None, batch=False):
    if n is not None:
        print(("cell 數 %d；本批 %d:%d，第 %d 格起待譯" % (n, rng[0], rng[1], rng[1])) if batch else ("cell 數 %d；全量檢查" % n))
    for p in problems:
        print("  ✗ " + p)
    print("全部通過" if not problems else "未通過：%d 項" % len(problems))
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
