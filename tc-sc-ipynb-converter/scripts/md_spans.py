"""MyST 原文範圍：依 markdown-it-py token 邊界標記，不重新渲染文件。"""
import copy
import re

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from mdit_py_plugins.colon_fence import colon_fence_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.myst_blocks import myst_block_plugin
from mdit_py_plugins.myst_role import myst_role_plugin
import yaml


class Stop(Exception):
    pass


TEXT_OPTIONS = {"caption", "title", "alt", "subtitle"}
CODE_DIRECTIVES = {"code-cell", "code", "code-block", "sourcecode", "literalinclude",
                   "mermaid", "raw", "csv-table", "toctree", "eval-rst", "jupyter-execute", "ipython"}
PATH_DIRECTIVES = {"figure", "image", "include", "bibliography", "iframe", "video", "embed", "glue:figure", "glue"}
REF_ROLES = {"ref", "numref", "doc", "download", "any", "eq", "term",
             "prf:ref", "std:ref", "std:numref", "std:doc", "std:term"}
CJK = re.compile(r"[\u3400-\u9fff]")
TEXT_COMMANDS = re.compile(r"\\(?:text|textrm|textbf|textit|textsf|textup|mbox|hbox)\s*\{")
URL = re.compile(r"https?://[^\s<>「」，。；、]+", re.I)


def text_commands(s, strict=False):
    spans, i = [], 0
    while m := TEXT_COMMANDS.search(s, i):
        b = m.start()
        while b and s[b - 1] == "\\":
            b -= 1
        if (m.start() - b) % 2:
            i = m.start() + 1
            continue
        j, depth = m.end(), 1
        while j < len(s) and depth:
            if s[j] == "\\":
                j += 2
                continue
            depth += {"{": 1, "}": -1}.get(s[j], 0)
            j += 1
        if depth or "\n" in s[m.end():j - 1]:
            raise Stop("文字命令未閉合或跨行；請把文字命令寫在同一行")
        spans.append((m.end(), j - 1))
        i = j
    return spans


def skeleton(s):
    for a, b in reversed(text_commands(s)):
        s = s[:a] + s[b:]
    return s


def merge(s, kinds):
    out = []
    for ch, kind in zip(s, kinds):
        if out and out[-1][0] == kind:
            out[-1] = (kind, out[-1][1] + ch)
        else:
            out.append((kind, ch))
    return out


def special(state, silent):
    p, s = state.pos, state.src
    url = URL.match(s, p)
    subst = re.match(r"\{\{[^\n]*?\}\}", s[p:])
    if url or subst:
        end = url.end() if url else p + subst.end()
        if not silent:
            state.push("cmf_keep", "", 0).content = s[p:end]
        state.pos = end
        return True
    m = re.match(r"\\(?:\(|\[|begin\{([A-Za-z*]+)\})", s[p:])
    if not m:
        return False
    close = "\\end{" + m.group(1) + "}" if m.group(1) else "\\)" if m.group(0) == "\\(" else "\\]"
    end = s.find(close, p + m.end(), state.posMax)
    if end < 0:
        if m.group(1):
            raise Stop("數學環境沒有結尾，或跨過 Markdown 區塊邊界")
        return False  # 沒有配對的 \[ 可是普通 Markdown 跳脫字元（C20）。
    end += len(close)
    if not silent:
        state.push("cmf_math", "", 0).content = s[p:end]
    state.pos = end
    return True


def parser(front=True):
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    md.use(colon_fence_plugin).use(myst_block_plugin).use(myst_role_plugin)
    # 和 MyST dollarmath 相同：allow_space/allow_digits 預設 True；不另加大括號規則。
    md.use(dollarmath_plugin, double_inline=True)
    if front:
        md.use(front_matter_plugin)
    md.inline.ruler.before("text", "cmf_special", special)
    for rule in list(md.inline.ruler.__rules__):
        original, name = rule.fn, rule.name

        def wrapped(state, silent, original=original, name=name):
            p, maximum = state.pos, state.posMax
            text_end = None
            if name == "text":
                m = URL.search(state.src, p + 1, maximum)
                if m:
                    terminator = state.md.inline.terminator_re.search(state.src, p)
                    if terminator is None or terminator.start() > m.start():
                        text_end = m.start()
            events = getattr(state, "cmf_events", None)
            if events is None:
                state.cmf_events = events = []
            before = len(events)
            try:
                if text_end is not None:
                    if not silent:
                        state.pending += state.src[p:text_end]
                    state.pos, ok = text_end, True
                else:
                    ok = original(state, silent)
            finally:
                state.posMax = maximum
            if not ok and name in {"link", "image"}:
                suspect = re.match(r"!?\[[^\]\n]+\]\([^)]*\n[^)]*\)", state.src[p:maximum])
                if suspect:
                    raise Stop("不支援未被解析器認作連結的跨行目標；請把目標寫在同一行")
            if not ok or silent:
                return ok
            q = state.pos
            del events[before:]
            kind = "prose" if name in {"text", "newline", "emphasis", "strikethrough"} else "keep"
            if name == "backticks" and not state.src[p:q].endswith("`"):
                kind = "prose"
            if name == "cmf_special" and state.src[p:q].startswith("\\") or name.startswith("math_inline"):
                kind = "math"
            spans = [(p, q, kind)]
            if name in {"link", "image"}:
                opening = p + (name == "image")
                end = md.helpers.parseLinkLabel(state, opening, True)
                # 完整、折疊與快捷參考連結的識別文字全保留，避免斷開定義。
                if end >= 0 and state.src[end + 1:end + 2] == "(":
                    spans += [(a + opening + 1, b + opening + 1, k)
                              for a, b, k in inline_spans(md, state.src[opening + 1:end], state.env)]
            if name == "myst_role":
                raw = state.src[p:q]
                m = re.match(r"\{([^}]+)\}(`+)", raw)
                if m:
                    role = m.group(1).strip()
                    a, b = p + m.end(), q - len(m.group(2))
                    content = state.src[a:b]
                    if role == "math":
                        spans.append((a, b, "math"))
                    elif role in REF_ROLES:
                        if title := re.fullmatch(r"(.*?)\s*<[^<>]+>", content, re.S):
                            spans.append((a, a + len(title.group(1)), "prose"))
                        elif role in {"term", "std:term"}:
                            spans.append((a, b, "prose"))
                    elif role == "abbr":
                        spans.append((a, b, "prose"))
            events.extend(spans)
            return ok

        md.inline.ruler.at(name, wrapped)

    # 在原規則仍持有容器狀態時，確認最後一行確實是閉欄。
    for name in ("fence", "colon_fence"):
        rule = next(r for r in md.block.ruler.__rules__ if r.name == name)
        original, alt = rule.fn, list(rule.alt)

        def fence(state, start, end, silent, original=original):
            count = len(state.tokens)
            ok = original(state, start, end, silent)
            if not ok or silent:
                return ok
            token = state.tokens[count]
            last = state.line - 1
            raw = state.src[state.bMarks[last] + state.tShift[last]:state.eMarks[last]]
            if last <= start or state.is_code_block(last) or not re.fullmatch(
                    re.escape(token.markup[0]) + "{" + str(len(token.markup)) + r",}\s*", raw):
                raise Stop("圍欄沒有結尾，或引用區塊／清單項目提前結束")
            return True

        md.block.ruler.at(name, fence, {"alt": alt})
    md.core.ruler.disable("inline")
    return md


def inline_spans(md, s, env=None):
    state = StateInline(s, md, env or {}, [])
    md.inline.tokenize(state)
    return getattr(state, "cmf_events", [])


def scan_inline(s):
    md = parser(False)
    kinds = ["prose"] * len(s)
    for a, b, k in inline_spans(md, s):
        kinds[a:b] = [k] * (b - a)
    return merge(s, kinds)


class Plan:
    def __init__(self, src, front=True, in_directive=False):
        self.src, self.kinds, self.notes = src, ["keep"] * len(src), []
        self.in_directive = in_directive
        self.uncertain = set()
        self.md = parser(front)
        self.lines = src.splitlines(keepends=True)
        self.starts, offset = [], 0
        for line in self.lines:
            self.starts.append(offset)
            offset += len(line)

    def set(self, mapping, a, b, kind):
        if kind == "math":
            text_commands("".join(self.src[mapping[i]] for i in range(a, b)), strict=True)
        for i in range(a, b):
            self.kinds[mapping[i]] = kind

    def locate(self, content, start, end, cursors=None):
        """逐行、單調映射；容器前綴不進 token。無法逐字映射時停止，不猜位置。"""
        mapping = []
        row = start
        for part in content.splitlines(keepends=True):
            text = part.rstrip("\n")
            if row >= end or row >= len(self.lines):
                raise Stop("解析器內容無法映射回原文行")
            pos = self.lines[row].find(text, (cursors or {}).get(row, 0))
            if pos < 0:
                raise Stop("解析器內容無法逐字映射；不支援此跳脫或縮排寫法")
            mapping += list(range(self.starts[row] + pos, self.starts[row] + pos + len(text)))
            if cursors is not None:
                cursors[row] = pos + len(text)
            if part.endswith("\n"):
                mapping.append(self.starts[row] + len(self.lines[row]) - 1)
            row += 1
        return mapping

    def inline(self, content, mapping, env, conservative=False):
        spans = inline_spans(self.md, content, env)
        if conservative or self.in_directive:
            # 未識別的方括號可能是引用識別字；整段保留，由 build() 登記人工確認。
            kinds = ["prose"] * len(content)
            for a, b, kind in spans:
                kinds[a:b] = [kind] * (b - a)
            if env is None or any(ch in "[]" and kind == "prose" for ch, kind in zip(content, kinds)):
                self.uncertain.update(mapping)
                return
        for a, b, kind in spans:
            self.set(mapping, a, b, kind)

    def directive(self, token, mapping, env):
        if env is None:
            self.uncertain.update(mapping)
            return  # 沒有外層資訊時不猜；預設 keep，交由人工確認。
        info = re.fullmatch(r"\{([\w:.-]+)\}(.*)", token.info.strip())
        if not info:
            return
        name, arg = info.groups()
        row = token.map[0]
        if name not in PATH_DIRECTIVES | CODE_DIRECTIVES | {"math"} and arg.strip():
            raw = self.lines[row]
            col = raw.find(token.info) + token.info.rfind(arg)
            self.inline(arg, list(range(self.starts[row] + col, self.starts[row] + col + len(arg))), env, True)
        body, pos = token.content, 0
        if body.startswith("---\n"):
            closing = re.search(r"(?m)^---\s*$", body[4:])
            if not closing:
                raise Stop("directive YAML 選項沒有結尾")
            stop = 4 + closing.start()
            raw = body[4:stop]
            try:
                node = yaml.compose(raw)
            except yaml.YAMLError as exc:
                raise Stop("directive YAML 無法解析：" + str(exc)) from exc
            if node and not isinstance(node, yaml.MappingNode):
                raise Stop("directive YAML 選項需要鍵值表")
            for key, value in node.value if node else []:
                if key.value not in TEXT_OPTIONS:
                    continue
                if not isinstance(value, yaml.ScalarNode) or value.tag != "tag:yaml.org,2002:str":
                    raise Stop("文字選項需要 YAML 字串")
                a, b = 4 + value.start_mark.index, 4 + value.end_mark.index
                if value.style in {"|", ">"}:
                    a = body.index("\n", a) + 1
                # 保留 YAML 原文、引號與折行；只轉 scalar 所佔的原文範圍。
                self.inline(body[a:b], mapping[a:b], env, True)
            pos = 4 + closing.end()
            if body[pos:pos + 1] == "\n":
                pos += 1
        else:
            for line in body.splitlines(keepends=True):
                option = re.match(r":([\w-]+):[ \t]*(.*?)(?:\n)?$", line)
                if not option:
                    break
                if option.group(1) in TEXT_OPTIONS:
                    a = pos + option.start(2)
                    self.inline(option.group(2), mapping[a:a + len(option.group(2))], env, True)
                pos += len(line)
        if name == "math":
            self.set(mapping, pos, len(body), "math")
        elif name not in CODE_DIRECTIVES | PATH_DIRECTIVES:
            nested = Plan(body[pos:], False, in_directive=True)
            nested.build(copy.deepcopy(env))
            for i, kind in enumerate(nested.kinds):
                self.kinds[mapping[pos + i]] = kind
            self.uncertain.update(mapping[pos + i] for i in nested.uncertain)

    def build(self, env=None):
        env = {} if env is None else env
        tokens = self.md.parse(self.src, env)
        cursors = {}
        for token in tokens:
            if token.type == "inline":
                mapping = self.locate(token.content, *token.map, cursors)
                self.inline(token.content, mapping, env)
            elif token.type in {"fence", "colon_fence"}:
                mapping = self.locate(token.content, token.map[0] + 1, token.map[1] - 1)
                self.directive(token, mapping, env)
            elif token.type.startswith("math_block"):
                mapping = self.locate(token.content, *token.map)
                self.set(mapping, 0, len(mapping), "math")
        # 未轉區域含中文時逐段登記完整行範圍，包括 metadata、程式、參考識別字。
        offset, start, uncertain = 0, None, False
        for row, line in enumerate(self.lines + [""], 1):
            needs_review = bool(self.uncertain.intersection(range(offset, offset + len(line))))
            has = any(k == "keep" and CJK.match(ch)
                      for ch, k in zip(line, self.kinds[offset:offset + len(line)])) or needs_review
            uncertain |= needs_review
            if has and start is None:
                start = row
            elif not has and start is not None:
                kind = "需要人工確認" if uncertain else "保護區域未轉換"
                msg = "無法確認的引用寫法；整段原樣保留，請對照原文確認" if uncertain else "含中文的保護區域；需要時對照原文手動核對"
                self.notes.append((start, row - 1, kind, msg))
                start = None
                uncertain = False
            offset += len(line)
        return self


def parse(src, front_matter=True):
    plan = Plan(src, front_matter).build()
    rows, offset = [], 0
    for line in src.split("\n"):
        rows.append(merge(line, plan.kinds[offset:offset + len(line)]))
        offset += len(line) + 1
    return rows, plan.notes
