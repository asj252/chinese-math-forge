#!/usr/bin/env python
"""繁體 MyST Markdown / notebook 轉簡體。Python >=3.12。
用法：python scripts/tc_sc_convert.py INPUT OUTPUT [--review FILE] [--code-strings]
輸出已存在時停止；每次轉換後必須逐條核對清單。依賴見 requirements.txt。
"""
import ast
import io
import json
import os
import re
import sys
import tempfile
import tokenize
try:
    from md_spans import Stop, parse, scan_inline, text_commands, skeleton
except ImportError as exc:
    sys.stderr.write('缺少解析依賴：請先安裝 requirements.txt（腳本不自動安裝）：' + str(exc) + '\n')
    raise SystemExit(2)

NON_DIRECTIONAL = [
    "行列式", "行為", "進行", "執行", "運行", "平行", "並行", "銀行", "可行", "行動", "行星", "行政", "流行", "旅行",
    "舉行", "實行", "履行", "自行", "另行", "例行", "發行", "行李", "行業", "同行", "步行", "盛行", "先行", "行使",
    "行號", "行程", "雙行記法", "行經", "行之有效", "現行", "通行", "推行", "施行", "奉行", "行得通", "發行量",
    "排列", "序列", "數列", "陣列", "列表", "列出", "下列", "並列", "列舉", "系列", "列印", "列車", "隊列", "羅列",
    "陳列", "列入", "上列", "前列", "分列", "列席", "列強", "數列極限",
]
# 可能有方向歧義的組合（例：「第 0 行為零向量」是「第 0 行」加「為」，不是「行為」）：在清單裡另外註明。
AMBIGUOUS = ["行為", "列為", "行與", "列與", "行和", "列和", "列出", "列入"]
# OpenCC 之後的大陸數學用語替換（簡體字形，長的在前）。第三欄是不要替換的前文（避免「單純量」之類的誤傷）。
TERMS = [
    ("坐标变换矩阵", "过渡矩阵", ""), ("座标变换矩阵", "过渡矩阵", ""), ("映成函数", "满射", ""), ("程式设计", "程序设计", ""),
    ("纯量积", "数量积", ""), ("程式码", "代码", ""), ("纯量", "标量", "单"), ("对射", "双射", ""), ("嵌射", "单射", ""),
    ("座标", "坐标", ""), ("阵列", "数组", ""), ("程式", "程序", ""),
]
CJK = re.compile(r"[\u3400-\u9fff]")

def span(a, b):
    """核對清單的位置：一行寫「第 a 行」，一段寫「第 a–b 行」。"""
    return f"第 {a} 行" if a == b else f"第 {a}–{b} 行"


class Converter:
    def __init__(self, cc, code_strings=False):
        self.cc = cc
        self.code_strings = code_strings
        self.review = []  # (排序鍵, 位置, 類型, 原文, 結果)
        self.words = sorted(NON_DIRECTIONAL, key=len, reverse=True)
        self.hits = None

    def fresh(self):
        self.hits = {"rowcol": False, "skipped": [], "ambiguous": False, "terms": []}

    def swap(self, s):
        out, i = [], 0
        while i < len(s):
            w = next((w for w in self.words if s.startswith(w, i)), None)
            if w:
                out.append(w)
                self.hits["skipped"].append(w)
                i += len(w)
                continue
            ch = s[i]
            if ch in "行列":
                self.hits["rowcol"] = True
            out.append("列" if ch == "行" else "行" if ch == "列" else ch)
            i += 1
        return "".join(out)

    def prose(self, s):
        """一段正文：對調行／列、轉簡體、替換術語（命中的事記在 self.hits）。"""
        if not CJK.search(s):
            return s
        if any(a in s for a in AMBIGUOUS):
            self.hits["ambiguous"] = True
        t = self.cc.convert(self.swap(s))
        for old, new, avoid in TERMS:
            pat = (f"(?<!{re.escape(avoid)})" if avoid else "") + re.escape(old)
            if re.search(pat, t):
                t = re.sub(pat, new, t)
                self.hits["terms"].append(f"{old} → {new}")
        return t

    def math(self, s):
        out, i = [], 0
        for a, b in text_commands(s):
            out.append(s[i:a] + "".join(self.prose(x) if k == "prose" else x for k, x in scan_inline(s[a:b])))
            i = b
        return "".join(out) + s[i:]

    def piece(self, kind, s):
        return self.prose(s) if kind == "prose" else self.math(s) if kind == "math" else s

    def register(self, key, loc, before, after):
        """一行（或一段註解）轉完：只要正文裡有「行」「列」就登記，不論有沒有對調。"""
        h = self.hits
        if h["rowcol"] or h["skipped"]:
            extra = (["有歧義的組合"] if h["ambiguous"] else []) + \
                (["含非方向詞，未對調：" + "、".join(dict.fromkeys(h["skipped"]))] if h["skipped"] else [])
            kind = "行列" + ("（%s）" % "；".join(extra) if extra else "")
            self.review.append((key, loc, kind, before.strip(), after.strip()))
        if h["terms"]:
            self.review.append((key, loc, "術語替換", "、".join(dict.fromkeys(h["terms"])), after.strip()))

    def markdown(self, text, where, base_key=0):
        rows, notes = parse(text, front_matter=not where)  # notebook 的 markdown cell 沒有 front matter
        lines = text.split("\n")
        out = []
        for ln, row in enumerate(rows, 1):
            self.fresh()
            new = "".join(self.piece(k, s) for k, s in row)
            out.append(new)
            self.register((base_key, ln, 0), f"{where}第 {ln} 行", lines[ln - 1], new)
        for a, b, kind, msg in notes:
            self.review.append(((base_key, a, 1), f"{where}{span(a, b)}", kind, msg, "原樣保留"))
        return "\n".join(out)

    # ---------- 程式碼 ----------
    def code(self, src, where, base_key=0):
        """code cell：轉註解；加 --code-strings 時也轉字串常量（f-string 只轉文字部分）。逐 token 換回原位，其餘一字不動。"""
        def note(ln, kind, a, b, last=None):
            self.review.append(((base_key, ln, 1), f"{where}{span(ln, last or ln)}", kind, a, b))

        lines = src.split("\n")
        whole = max(1, len(src.rstrip("\n").split("\n")))  # 整格原樣保留時登記整格的行號範圍
        first = next((x for x in lines if x.strip()), "")
        if first.lstrip().startswith("%%"):
            if CJK.search(src):
                note(1, "程式碼未轉換", "cell magic（%%）整格原樣保留", "需要時手動改", whole)
            return src
        magic = set()
        masked = []
        for k, ln in enumerate(lines, 1):
            s = ln.lstrip()
            if s.startswith(("%", "!")):  # 魔術命令行換成同樣長度的註解，再交給 tokenize（字串裡的同樣一行不受影響，見下）
                magic.add(k)
                p = len(ln) - len(s)
                ln = ln[:p] + "#" + ln[p + 1:]
            masked.append(ln)
        try:
            toks = list(tokenize.generate_tokens(io.StringIO("\n".join(masked)).readline))
        except (tokenize.TokenError, SyntaxError, IndentationError):
            if CJK.search(src):
                note(1, "程式碼未轉換", "無法切分成 token", "整格原樣保留，需要時手動改註解", whole)
            return src

        def orig(t):  # token 在原文裡的文字（按位置取，魔術命令遮蔽不影響字串內容）
            (r1, c1), (r2, c2) = t.start, t.end
            if r1 == r2:
                return lines[r1 - 1][c1:c2]
            return "\n".join([lines[r1 - 1][c1:]] + lines[r1:r2 - 1] + [lines[r2 - 1][:c2]])

        T = {name: getattr(tokenize, name, None) for name in
             ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END", "TSTRING_START", "TSTRING_MIDDLE", "TSTRING_END")}
        starts, ends = {T["FSTRING_START"], T["TSTRING_START"]} - {None}, {T["FSTRING_END"], T["TSTRING_END"]} - {None}
        mids = {T["FSTRING_MIDDLE"], T["TSTRING_MIDDLE"]} - {None}
        brace = []  # 每一層 f-string 裡 `{…}` 的深度（由外到內）
        edits = []
        for t in toks:
            if t.type in starts:
                brace.append(0)
                continue
            if t.type in ends:
                brace.pop()
                continue
            if brace and t.type == tokenize.OP and t.string in "{}":
                brace[-1] += 1 if t.string == "{" else -1
                continue
            if t.type not in (tokenize.COMMENT, tokenize.STRING) and t.type not in mids:
                continue
            text = orig(t)
            if not CJK.search(text):
                continue
            ln, last = t.start[0], t.end[0]  # 多行字串登記整段行號
            loc = f"{where}第 {ln} 行"
            in_expr = any(b > 0 for b in brace)  # 在某一層 f-string 的 `{…}` 裡：運算式、格式規格與巢狀 f-string 都是程式邏輯
            if t.type == tokenize.COMMENT:
                if ln in magic and t.start[1] == len(lines[ln - 1]) - len(lines[ln - 1].lstrip()):
                    note(ln, "程式碼未轉換", text[:80], "魔術命令原樣保留")
                    continue
                self.fresh()
                new = "#" + self.prose(text[1:])
                self.register((base_key, ln, 0), loc + "（註解）", text, new)
                edits.append((t.start, t.end, new))
            elif t.type == tokenize.STRING or t.type in mids:
                if in_expr:
                    note(ln, "程式字串未轉換", text[:80], "f-string 運算式裡的字串，原樣保留", last)
                elif t.type == tokenize.STRING and re.match(r"[rRbBuU]*[fFtT]", text):
                    note(ln, "程式字串未轉換", text[:80], "f-string 原樣保留（Python 3.12 以上執行本腳本才會只轉文字部分）", last)
                elif self.code_strings:
                    self.fresh()
                    new = self.prose(text)
                    edits.append((t.start, t.end, new))
                    note(ln, "程式字串已轉換", text[:80], new[:80], last)
                else:
                    note(ln, "程式字串未轉換", text[:80], "預設不轉；確認只是顯示文字後加 --code-strings 重轉，或手動改", last)
        for (r1, c1), (r2, c2), new in sorted(edits, reverse=True):
            head, tail = lines[r1 - 1][:c1], lines[r2 - 1][c2:]
            lines[r1 - 1:r2] = (head + new + tail).split("\n")
        return "\n".join(lines)


# ---------- 自我檢查 ----------
def check_md(src, out, where, cc, problems):
    front = where == "全文"
    rs, _ = parse(src, front)
    try:
        ro, _ = parse(out, front)
    except Stop as e:
        problems.append(f"{where}：轉換後的切分出錯（{e}）")
        return
    if len(rs) != len(ro):
        problems.append(f"{where}：行數改變（{len(rs)} → {len(ro)}）")
        return
    for ln, (a, b) in enumerate(zip(rs, ro), 1):
        if [k for k, _ in a] != [k for k, _ in b]:
            problems.append(f"{where}第 {ln} 行：切分結構改變")
            continue
        for (k, x), (_, y) in zip(a, b):
            if k == "keep" and x != y:
                problems.append(f"{where}第 {ln} 行：原樣保留的部分被改動（{x[:30]} → {y[:30]}）")
            if k == "math" and skeleton(x) != skeleton(y):
                problems.append(f"{where}第 {ln} 行：數學式（文字命令以外）被改動（{x[:30]} → {y[:30]}）")
            texts = [y] if k == "prose" else [y[p:q] for p, q in text_commands(y)] if k == "math" else []
            for s in texts:
                for kk, z in scan_inline(s) if k == "math" else [("prose", s)]:
                    if kk == "prose" and cc.convert(z) != z:
                        left = sorted({c1 for c1, c2 in zip(z, cc.convert(z)) if c1 != c2})
                        problems.append(f"{where}第 {ln} 行：轉換後的正文還有繁體字 {''.join(left)[:20]}")


def masked_ast(src):
    lines = []
    for ln in src.split("\n"):
        s = ln.lstrip()
        lines.append(ln[:len(ln) - len(s)] + "#" + s[1:] if s.startswith(("%", "!")) else ln)
    try:
        return ast.parse("\n".join(lines))
    except (SyntaxError, ValueError):
        return None


class _Blank(ast.NodeTransformer):
    def visit_Constant(self, node):
        return ast.copy_location(ast.Constant(value=""), node) if isinstance(node.value, str) else node


def check_code(src, out, where, code_strings, problems):
    a = masked_ast(src)
    if a is None:
        return
    b = masked_ast(out)
    if b is None:
        problems.append(f"{where}：轉換後的程式不能解析")
        return
    if code_strings:
        a, b = _Blank().visit(a), _Blank().visit(b)
    if ast.dump(a) != ast.dump(b):
        problems.append(f"{where}：程式的語法樹改變（{'字串常量以外' if code_strings else '只該改註解'}）")


# ---------- 寫出 ----------
def write_all(items):
    """全部寫成臨時檔，再逐個放到目標（不覆蓋已存在的檔案）；任一失敗就移除本次已放好的檔案。"""
    paths = [os.path.abspath(p) for p, _ in items]
    if len(set(os.path.normcase(p) for p in paths)) != len(paths):
        raise Stop("輸出與核對清單是同一個路徑")
    for p in paths:
        if os.path.lexists(p):
            raise Stop(f"{p} 已存在，不覆蓋")
    temps, placed = [], []
    try:
        for p, (_, text) in zip(paths, items):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix=".tc_sc-", dir=os.path.dirname(p))
            temps.append(tmp)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        for p, tmp, (_, text) in zip(paths, temps, items):
            try:
                os.link(tmp, p)  # 目標已存在時失敗，不會覆蓋
                placed.append(p)
                continue
            except FileExistsError:
                raise Stop(f"{p} 已存在，不覆蓋")
            except OSError:
                pass
            # 檔案系統不支援硬連結：改用排他建立（目標已存在時失敗，同樣不覆蓋）直接寫入
            try:
                fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o666)
            except FileExistsError:
                raise Stop(f"{p} 已存在，不覆蓋")
            placed.append(p)
            with os.fdopen(fd, "wb") as f:
                f.write(text.encode("utf-8"))
    except (OSError, Stop) as e:
        left = []
        for p in placed:
            try:
                os.unlink(p)
            except OSError:
                left.append(p)
        msg = str(e) if isinstance(e, Stop) else f"寫不出檔案：{e}"
        err = Stop(msg + ("；以下檔案已寫出、但移除失敗，請手動刪除：" + "、".join(left) if left else "；沒有留下任何輸出"))
        err.final = True
        raise err
    finally:
        for tmp in temps:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def cellsafe(s):
    """放進 Markdown 表格的一格：跳脫直線、換行寫成 ⏎。"""
    return s.replace("|", "\\|").replace("\n", " ⏎ ")


def cell_text(c):
    s = c.get("source", "")
    return ("".join(s) if isinstance(s, list) else s).replace("\r\n", "\n")


def run(inp, outp, review_path, code_strings):
    try:
        import opencc
    except ImportError:
        sys.stderr.write("需要 OpenCC：pip install opencc-python-reimplemented（本腳本不自動安裝）\n")
        sys.exit(2)
    cc = opencc.OpenCC("t2s")
    conv = Converter(cc, code_strings)
    try:
        with open(inp, encoding="utf-8") as f:
            raw = f.read()
    except (OSError, UnicodeDecodeError) as e:
        raise Stop(f"讀不到 {inp}：{e}")
    problems = []
    if inp.lower().endswith(".ipynb"):
        try:
            nb = json.loads(raw)
            cells = nb["cells"]
            if not isinstance(cells, list) or not all(isinstance(c, dict) for c in cells):
                raise TypeError("cells 不是 cell 的陣列")
        except (ValueError, KeyError, TypeError) as e:
            raise Stop(f"{inp} 不是合法的 notebook：{e}")
        for k, c in enumerate(cells):
            src = cell_text(c)
            where = f"第 {k} 格"
            if c.get("cell_type") == "markdown":
                new = conv.markdown(src, where, k)
                check_md(src, new, where, cc, problems)
            elif c.get("cell_type") == "code":
                new = conv.code(src, where, k)
                check_code(src, new, where, code_strings, problems)
                if c.get("outputs"):
                    conv.review.append(((k, 10 ** 9, 1), where, "輸出未轉換", "存檔的輸出原樣保留", "需要時重新執行"))
            else:
                new = src
            c["source"] = new.splitlines(keepends=True) if isinstance(c.get("source"), list) else new
        result = json.dumps(nb, ensure_ascii=False, indent=1) + "\n"
    else:
        result = conv.markdown(raw, "")
        check_md(raw, result, "全文", cc, problems)
    if problems:
        raise Stop("自我檢查不過：\n  " + "\n  ".join(problems))
    rows = ["# 繁→簡轉換核對清單", "", f"來源：`{os.path.basename(inp)}` → `{os.path.basename(outp)}`", "",
            "每一行含「行」「列」的正文都列在這裡（不論有沒有對調）：對照公式或程式錨點（row／column）確認，"
            "核對過把狀態改成「已核對」；改了輸出就在「結果」後面注明。", "",
            "| 位置 | 類型 | 原文 | 結果 | 狀態 |", "|---|---|---|---|---|"]
    for _, where, kind, a, b in sorted(conv.review, key=lambda r: r[0]):
        rows.append("| %s | %s | %s | %s | 未核對 |" % (where or "全文", kind, cellsafe(a), cellsafe(b)))
    write_all([(outp, result), (review_path, "\n".join(rows) + "\n")])
    kinds = {}
    for _, _, kind, _, _ in conv.review:
        kinds[kind.split("（")[0]] = kinds.get(kind.split("（")[0], 0) + 1
    print("寫出 %s；核對清單 %s（%s）" % (outp, review_path, "、".join(f"{k} {v} 條" for k, v in kinds.items()) or "沒有要核對的項目"))


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows 的管道或非 UTF-8 主控台下也能印中文
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    if sys.version_info < (3, 12):
        sys.stderr.write("需要 Python 3.12 以上\n")
        sys.exit(2)
    args, review, code_strings = [], None, False
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--review" and i + 1 < len(argv):
            review = argv[i + 1]
            i += 2
        elif argv[i] == "--code-strings":
            code_strings = True
            i += 1
        elif argv[i].startswith("--"):
            sys.stderr.write(__doc__)
            sys.exit(2)
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 2:
        sys.stderr.write(__doc__)
        sys.exit(2)
    review = review or args[1] + ".review.md"
    if os.path.abspath(args[0]) in (os.path.abspath(args[1]), os.path.abspath(review)):
        sys.stderr.write("停下：輸入與輸出（或核對清單）是同一個檔案\n")
        sys.exit(2)
    try:
        run(args[0], args[1], review, code_strings)
    except Stop as e:
        sys.stderr.write("停下：%s。%s\n" % (e, "" if getattr(e, "final", False) else "沒有寫出任何東西。"))
        sys.exit(1)


if __name__ == "__main__":
    main()
