---
name: tex-exercise-pipeline
description: >
  将 LaTeX 习题文件（.tex）转换为教材习题 Jupyter Notebook，
  涵盖三个阶段：(A) 解析 .tex 生成 MyST Markdown 习题（含解答 dropdown）、
  (B) 为每道题编写 NumPy Python 验算代码、(C) 将习题与验算交错组合成 .ipynb。
  当用户说「把这个 tex 转成习题 notebook」、「从 tex 生成习题」、
  「帮我把习题转成 MyST」、「生成练习题的 ipynb」，或上传 .tex 习题文件并
  要求输出 Jupyter Notebook 时，必须触发此 skill。
  特别适用于线性代数、微积分等大学数学课程的习题册，
  以及包含计算验算、几何直觉与数学证明的混合型题目。
---

# LaTeX 习题 → 验算 Notebook 流水线

本 skill 执行三个阶段，可单独或完整执行。
若用户未指定阶段，默认执行全部三个阶段。习题与解答的语言跟随 `.tex` 原文（繁体或简体中文都可以）。

```
.tex 习题文件
    │
    ▼  [阶段 A]
MyST Markdown（中间产物 → 临时目录）
  ::::{exercise} + :::{solution} dropdown
    │
    ▼  [阶段 B]
验算 Notebook（中间产物 → 临时目录）
  每道题一段代码，含执行输出
    │
    ▼  [阶段 C：使用 scripts/assemble_ipynb.py]
成品 Notebook（路径由用户指定）
  习题 markdown ↔ 验算代码 交错排列
```

---

## 阶段 A：LaTeX → MyST Markdown

### A1. 读取 .tex 文件

读取用户指定的 `.tex` 文件。中间产物一律放在系统的临时目录，不进版本控制。
先扫描整体结构（`\begin{enumerate}` → `\item`），统计题目数量与主题群。

**LaTeX 结构对照：**

| LaTeX | MyST |
|-------|------|
| `\begin{enumerate}` | 习题列表开始 |
| `\item` | `::::{exercise}` |
| `\begin{enumerate}` (子列表) | 题目内的 `1.` `2.` `3.` 有序列表 |
| `\mathbf{v}` | `\mathbf{v}`（保留，LaTeX 兼容） |
| `$$...$$` | `$$\n...\n$$`（MyST 块数学） |
| `$...$` | `$...$`（行内数学） |
| `\begin{cases}` | `\begin{cases}`（保留） |

### A2. 生成 MyST Markdown

**每道题的格式模板：**

```markdown
::::{exercise} [习题标题（2-5字，概括题目核心）]
:label: exer-ch[章号]-[slug]

[题目正文，保留所有 LaTeX 数学式]

**提示：** [一句话提示，指出关键方法或公式]

:::{solution} exer-ch[章号]-[slug]
:class: dropdown

[按步骤的完整解答]

**步骤1：** [...]

**步骤2：** [...]

（结论用 $\underline{...}$ 强调）
:::
::::
```

**格式规范：**

- 题目之间用 `---` 分隔
- 子节用 `### [子节标题]` 组织（如 `### 基础运算`、`### 投影与距离`）；阶段 C 会把它们原样变成单独的 markdown cell
- 习题块里若还要嵌套 directive（如 `{tip}`、`{solution}`），外层的冒号要比里层多：例如外层 `:::::{exercise}`、里层 `::::{tip}`、`:::{solution}`
- 向量用 `\mathbf{v}`（粗体小写），矩阵用 `\mathbf{A}`（粗体大写）
- 索引从 0 开始（$v_0, v_1, \ldots$）
- 解答中用 **步骤N：** 格式（中文冒号）
- 纯推导题（如正弦定理的向量证明）可无 Python 验算，在提示中标注

**标签命名（`:label:`）：**

```
exer-ch2-linear-comb-calc     ← ch + 章号 + slug（kebab-case，英文）
exer-ch2-centroid-discovery
exer-ch2-cross-product-basic
```

### A3. 输出

保存为 `<临时目录>/ch[N]_exercises.md`（中间产物）。

---

## 阶段 B：生成 Python 验算代码

### B1. 代码风格（完整教科书规范）

若装有 `python-textbook-code-optimizer`（`myst-textbook-forge` 仓库），遵循它的完整规范；没装就照本节。第一个 code cell 必须包含所有全局设置与辅助函数：

```python
import numpy as np
np.set_printoptions(precision=4, suppress=True, linewidth=100)

# ── 输出格式函数 ──────────────────────────────────────────
def print_header(title):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_step(step, desc):
    print(f"\n▶ 步骤 {step}: {desc}")
    print("-" * 40)

def compare_print(label, actual, expected_desc):
    print(f"\n[{label}]")
    print(f"  代码计算值：{actual}")
    print(f"  公式预期值：{expected_desc}")

# ── 数学辅助函数 ──────────────────────────────────────────
def proj(u, v):
    """v 在 u 方向的投影向量"""
    return np.dot(u, v) / np.dot(u, u) * u

def para_area(u, v):
    """u, v 张成的平行四边形面积"""
    return np.sqrt(np.dot(u,u)*np.dot(v,v) - np.dot(u,v)**2)

def triple(u, v, w):
    """有向体积 D(u,v,w) = u·(v×w)"""
    return np.dot(u, np.cross(v, w))
```

辅助函数按题目需要增减；`print_header`、`print_step`、`compare_print` 三个固定保留。

### B2. 每道题的代码结构

每段代码的第一个 code cell **必须严格遵循以下三行开头样板**（同一段里后续的 code cell 不必重复）：

```python
# ============================================================
print_header("习题 [章号]-[题号]｜[题目标题]")
# ============================================================
```

之后依步骤使用 `print_step()` 分段，并对关键数学结果使用 `compare_print()` 对比验算：

```python
# ============================================================
print_header("习题 2-3｜向量投影")
# ============================================================

# --- 步骤 1 ---
print_step(1, "定义向量")
u = np.array([1, 2, 3])
v = np.array([4, 5, 6])

# --- 步骤 2 ---
print_step(2, "计算投影 proj_u(v)")
result = proj(u, v)
compare_print("proj_u(v)", result, "(u·v / u·u) * u")

print("\n验算（allclose）:", np.allclose(result, np.dot(u,v)/np.dot(u,u)*u))
```

**命名与符号规范：**
- 注释与 `print` 中使用 LaTeX 风格符号：`A^T`、`λ_i`、`||x||`、`Σ` 等
- 向量用 `\mathbf{v}`（在 Markdown 标题中），代码中用小写 `u`, `v`, `w`
- 索引从 0 开始（`v[0], v[1], ...`）
- 样板里的「习题」「步骤」等字样跟随习题的语言（繁体原文就用对应的繁体字样）

### B3. 代码组织策略（何时省略完整规范）

- **一题一段代码**（默认）
- **多题合并**（当多题共用同一数值设置，如「正交基底 R²/R³/R⁴」）
- **无代码**（纯推导或存在性证明题）

验算 Notebook 的结构（阶段 C 的脚本按这个结构读）：可选的 `# ` 标题 cell，接着第一个 code cell（imports + helpers），
之后每段代码以一个 markdown cell `## 第 N 题：[题目标题]` 起头，后面跟一个或多个 code cell（需要时可以夹说明用的 markdown cell），
直到下一个 `## `。不要有不属于任何一段的 cell；`# ` 与 `## ` 标题 cell 里只写一行标题，说明另起一个 markdown cell。

### B4. 执行并嵌入输出

```bash
jupyter nbconvert --to notebook --execute \
    <临时目录>/ch[N]_verify.ipynb \
    --output <临时目录>/ch[N]_verify.ipynb \
    --ExecutePreprocessor.timeout=60
```

需要用户的环境装有 `jupyter`（nbconvert）、ipykernel 与 numpy；没有时先问用户怎么执行，不要自行安装。
若执行失败，检查并修正代码后重试。

### B5. 输出

保存为 `<临时目录>/ch[N]_verify.ipynb`（中间产物）。

---

## 阶段 C：组合 Notebook

### C1. 生成映射设定文件（`mapping.json`）

根据习题与代码的对应关系，生成 `mapping.json`：

```json
{
  "title": "§2.6 习题",
  "ex_to_code": {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": null,
    "4": null,
    "5": 3,
    "6": 3
  }
}
```

**映射规则说明：**
- `"title"`：成品第一个 cell 的标题（必填）；可选 `"intro"`、`"outro"`：标题下的说明与结尾的文字
- `"ex_to_code"`：习题索引（0-based，按习题 md 里 `{exercise}` 块的顺序）→ 验算 notebook 的代码段索引（0-based）；**每一道题都要列出**
- `null` 表示该题无对应 Python 验算（纯推导题）
- 多题共用同一段代码时，后续习题指向同一个代码段索引（脚本只在第一次出现时放入）
- 每一段代码都必须被至少一道题用到
- 子节标题不写在这里，写在习题 md 里（`### `）

### C2. 执行组合脚本

```bash
python <本 skill 的目录>/scripts/assemble_ipynb.py \
    <临时目录>/ch[N]_exercises.md \
    <临时目录>/ch[N]_verify.ipynb \
    <临时目录>/mapping.json \
    <输出路径>.ipynb
```

PowerShell 里写成一行（路径有空格时加引号）：

```powershell
python "<本 skill 的目录>\scripts\assemble_ipynb.py" "<临时目录>\ch2_exercises.md" "<临时目录>\ch2_verify.ipynb" "<临时目录>\mapping.json" "<输出路径>.ipynb"
```

脚本自动处理：
- 解析 `{exercise}` 块（按冒号数配对开头与结尾，块内嵌套的 directive 与代码围栏原样保留）。支持范围：冒号写法的 directive，
  开头与结尾缩进 0–3 格；缩进 4 格以上的行当普通内容。反引号写法的 directive、引用块或列表里的 directive 不支持——
  习题请用冒号写法，习题之外不要放 directive
- 读取验算 notebook 的代码段（每段的 code cell、说明 cell 与执行输出原样带过来）
- 依 mapping.json 交错排列，习题 md 里的 `### ` 子节标题与其他文字按原位置放入

任何对不上的地方（习题块没有结尾、冒号数不对、习题外有 directive 或孤立的结尾、映射缺题、越界或编号重复、代码段没被用到、验算 notebook 有无法归属的 cell 或标题 cell 里夹了别的文字）都会停下报错，不写出任何东西；输出文件已存在时也停下，不覆盖（不防同时有别的程序写同一个文件）。习题之间的 `---` 分隔线不放进成品（cell 本身已经分开）。

### C3. 输出

成品保存到用户指定的路径（常见做法：与对应章节放在同一个目录，文件名加 `_exercises`）。
若用户的项目有 MyST 配置（如 `myst.yml`），提示用户把新文件加进目录（`toc`）与导出设定。

---

## 完整执行示例

```
用户：「这是第二章的 tex 习题，帮我生成验算 notebook」
动作：
  1. 读取用户给的 ch02_exercises.tex
  2. [阶段 A] 生成 MyST md → <临时目录>/ch2_exercises.md
  3. [阶段 B] 生成验算 ipynb，执行并嵌入输出
  4. [阶段 C] 生成 mapping.json，执行 assemble_ipynb.py
  5. 写入用户指定的成品路径
```

---

## 注意事项

- 每次执行前先确认章号与节号（从 `.tex` 的标题或用户说明获取）
- 若 `.tex` 包含 `\input{...}` 宏，先询问用户是否有对应的定义文件
- 纯推导证明题（如反证法、不等式证明）不需要 Python 验算，在 mapping 中设为 `null`
- 若多道题数值设置相同（如向量 $\mathbf{u}$、$\mathbf{v}$ 在多道子题共用），可合并为一段代码
