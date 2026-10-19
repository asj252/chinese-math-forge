# 繁中 → 英文 語域與格式規範

本檔管「**怎麼寫**」（英文的語氣、用詞、格式）；流程見 `SKILL.md`。
術語的逐詞對應以專案的術語表（由本 skill 的 `references/glossary_seed.yaml` 複製而來）為準，本檔不重複列舉術語。

---

## 1. 語域（register）

目標讀者是美國大學部修數學課的學生；語域對標美式大學教科書：**正式但不生硬，解釋性強，會直接對讀者說話**。

### 1.1 必須遵守

- **不使用縮寫式**：寫 `do not` / `it is` / `we have` / `cannot`，不寫 `don't` / `it's` / `we've` / `can't`。
- **第二人稱 you 可用**，但僅限引導直覺、下指令、給學習提示的句子：
  「Once you have read this chapter, you will have a working vocabulary.」
  正式的定義、定理、證明內文不使用 you。
- **第一人稱複數 we 可用**，這是數學寫作的標準敘事人稱：
  「We begin with the most basic notions.」「Here we prove both inclusions.」
- **時態**：數學事實一律現在式（"the empty set is a subset of every set"）；
  歷史敘事用過去式（"Weierstrass constructed a function that…"）。
- **不使用縮略語 iff**：一律寫 `if and only if`。
- **不使用 s.t.、w.r.t.、resp.** 這類簡寫，全部寫成英文。

### 1.2 必須避免的中文直譯腔

| 中文結構 | 不要這樣寫 | 應該這樣寫 |
|---|---|---|
| 我們將從基礎概念出發 | We will start out from basic concepts | We begin with the basic notions |
| 值得一提的是 | It is worth mentioning that | Note that / 直接刪去，讓句子自己說 |
| 進行了系統整理 | has carried out a systematic organization of | organizes / collects |
| 看似簡單，卻是… | Seems simple, but is… | Simple as they look, these three conditions are… |
| 這正是…的地方 | This is exactly the place where… | This is precisely where… |
| 所謂的 X | the so-called X | X（直接用，除非原文真的在標示術語首次出現） |

- 中文一句常包含三、四個分句以逗號串接。英文譯文**允許斷句**，一個中文長句可拆成兩到三個英文句子，
  只要語意與論證順序不變。反過來不允許：不可把兩段合併、不可省略原文的論證步驟。
- 中文的「——」（破折號）插入語，英文用 em dash（—）或括號，依節奏擇一，不要每處都照搬。

### 1.3 敘事段落（章首的歷史／動機文字）

教材章首常有大段敘事散文。這些段落要譯得**像英文散文，不像翻譯**：節奏、停頓、修辭效果優先於逐字對應，
但**事實、人名、年份、書名、論證鏈條一字不可改**。

- 人名首次出現時，中文原文常寫「魏爾斯特拉斯（Weierstrass）」；英文版只留英文名 `Weierstrass`，
  刪去括號（括號裡本來就是給中文讀者的注音）。若原文括號中是外語原名（如 *Éléments de mathématique*），保留。
- 書名、期刊名維持斜體。

### 1.4 只和中文讀者有關的內容

只對中文讀者有意義的內容（例如台灣中學課本的用語說明「叉積常稱為外積」、台灣教育制度脈絡、簡體與繁體中文的行／列用法差異），先列出來問使用者是否在英文版**整句（或整個 directive）省略**，不擅自改寫成泛稱。
省略的內容若帶有 `:label:` 或被 `{ref}` 引用，不要自行刪除 label（各語言版本共用同一組 label）；經使用者同意刪除的 label 記在進度表的「英文版刻意省略的內容」，驗證時用 `--allow-missing-label` 列出，視為預期差異。若整個不含 `{ref}`／`{prf:ref}`／`{numref}`／`{eq}`／`{solution}` 的 Markdown cell 都只對中文讀者有意義且經使用者同意整格省略，不可從譯本刪除該 cell（譯本的 cell 數與類型序列必須與原稿一致）：保留原類型的空 cell，在 patch JSON 中將該格的值寫成空字串 `""`（例如省略 cell index 7（0-based）寫 `{"7": ""}`；原有 `:label:` 若經同意一併省略則加 `--allow-missing-label`），並同樣記進進度表的「英文版刻意省略的內容」。若該 Markdown cell 含有上述引用或 `{solution}`，或為 code cell，不可整格清空為 `""`（否則步驟 7 會因引用不一致或語法樹不同而失敗）：Markdown cell 僅刪去只對中文讀者有意義的語句並保留引用；code cell 保留程式語法結構，僅刪去註解或將顯示字串改為空字串 `""`。

---

## 2. `prf:` 環境與 directive

### 2.1 關鍵字一律不譯

`prf:definition`、`prf:theorem`、`prf:proposition`、`prf:lemma`、`prf:property`、
`prf:example`、`prf:remark`、`prf:proof`、`exercise`、`solution`、`admonition`、
`note`、`tip`、`warning`、`caution`、`hint`、`important`、`attention`、
`figure`、`math`、`mermaid`、`table` — 全部保持原樣。

### 2.2 標題引數譯成英文名詞短語

directive 後面那個標題引數要譯，且**只譯成名詞短語，不加贅字**：

```
:::{prf:definition} 集合          →   :::{prf:definition} Set
:::{prf:definition} 冪集合        →   :::{prf:definition} Power Set
:::{prf:example} 文氏圖           →   :::{prf:example} Venn Diagrams
:::{prf:property} 複合映射的基本性質 →  :::{prf:property} Basic Properties of Composition
::::{exercise} 互相包含的集合      →   ::::{exercise} Mutually Contained Sets
```

- **不要**寫成 `Definition of a Set`、`The Definition of Set`、`Example: Venn Diagram`
  — 環境本身已經印出 "Definition"／"Example"，再加一次是贅字。
- 標題採 **Title Case**（實詞首字母大寫，介系詞／冠詞／連接詞小寫）：
  `Basic Properties of Composition`、`The Preimage Characterization`。
- 原標題若帶 `◆` / `◇` / `*` 等提示記號（如 `` ```{tip} ◇*複合映射與矩陣* ``），
  記號位置與星號逐字保留，只譯中間文字：`` ```{tip} ◇*Composition and Matrices* ``。

### 2.3 label 一字不改

`:label: def-set-detailed` 這類值在各語言版本共用，**逐字保留，絕不翻譯、絕不重編**。
`{prf:ref}` / `{ref}` 的引數同理。
`:::{solution} exer-subset-equal` 的引數必須與對應 exercise 的 label 完全一致，翻譯時不得更動。

### 2.4 遇到 `:name:` 一律改成 `:label:`

MyST 的錨點寫 `:label:`；`:name:` 在部分匯出流程（例如 Typst）不參與交叉引用解析。
原文若還有 `:name:`，**英文版一律寫成 `:label:`，值不變**。這是唯一允許在翻譯時修正的原文問題，
其他任何原文瑕疵（錯字、格式不一致）都照原樣譯出，另行回報，不擅自修改。

---

## 3. 步驟與強調格式

### 3.1 步驟編號

| 情形 | 繁中格式 | 英文格式 |
|---|---|---|
| 定理敘述、證明、性質列表 | 標準 Markdown 有序列表（`1.` `2.` …） | 同樣的有序列表，只譯列表文字 |
| 例子（`prf:example`）與程式碼解說 | `**步驟1：**`（全形冒號） | `**Step 1.**`（**半形句點**，非冒號） |

`**Step 1.**` 後面接一個半形空格再接內容。編號從 1 開始，與程式中的 0-based 索引互不衝突。

### 3.2 粗體導語

中文行文常用「**導語**：」開頭的短標籤。英文版一律改成 **粗體＋半形句點**：

| 繁中 | 英文 |
|---|---|
| `**直觀理解：**` | `**Intuition.**` |
| `**分析**：` | `**Analysis.**` |
| `**等價表述**：` | `**Equivalent formulation.**` |
| `**推廣到 $n$ 重直積：**` | `**Generalization to the $n$-fold product.**` |
| `**重要區別**：` | `**An important distinction.**` |
| `**關鍵特性：**` | `**Key properties.**` |
| `**注意**` | `**Note.**` |
| `*提示*：` | `*Hint.*` |

只有第一個字大寫（句子式大小寫），不用 Title Case——這些是句首標籤，不是標題。

### 3.3 證明結尾

證明結尾的 `$\square$` 逐字保留，不改成 `∎`、`QED`、`$\blacksquare$`。

---

## 4. 章節結構標題

同一個標題全書只有一種英文譯法，避免每章各翻一次不同版本。第一次遇到某種結構標題時，把譯法補進專案的術語表，之後照表。常見的寫法：

| 繁中 | 英文 |
|---|---|
| `# 第一章 集合論與映射` | `# Chapter 1 Sets and Mappings` |
| `## 1.1 集合論基礎` | `## 1.1 Foundations of Set Theory` |
| `:::{admonition} §X.Y 小結` | `:::{admonition} §X.Y Summary` |
| `## X.Y 本章小結` | `## X.Y Chapter Summary` |

章名（`# 第 N 章 …`）的英文一律採 `# Chapter N <Title>` 格式，Title Case，不加冒號。

---

## 5. 逐字保留、絕不翻譯的東西

翻譯時以下內容**一個字元都不能動**：

1. **LaTeX 數學式**：`$…$`、`$$…$$` 內的全部內容，包含 `\mathbf`、`\top`、`\square`、
   `\operatorname{Im}`、Unicode `⟨` `⟩` 等。
   - 唯一例外：數學式**內部**若嵌有中文文字（如 `$B = \{x | x \text{ 是小於 10 的正偶數}\}$`
     或 `$\underbrace{\mathbb{R} \times \cdots}_{n \text{ 個}}$`），只譯 `\text{}` 內的中文，
     其餘符號結構完全不動：`$B = \{x | x \text{ is a positive even number less than 10}\}$`、
     `` `_{n \text{ copies}}` ``。
   - 英文文字放進數學式時一律包在 `\text{}` 裡；直接寫在數學模式中，字與字之間的空白會消失、字母變成斜體。
2. **label / ref 值**：`:label:`、`{prf:ref}`、`{ref}`、`{solution}` 的引數。
3. **所有十六進位色值**：程式碼與 Mermaid 裡的色碼逐字保留；註解裡的色名照術語表譯。
4. **`§X.Y` 格式**：章節交叉引用寫法不變。
5. **程式碼邏輯**：變數名、函數名、非顯示用途的字串（作為資料鍵的字典 key、檔案路徑、欄位名等；作為顯示標籤的字典 key 照第 6 節第 3 點翻譯）、數值、API 呼叫。
6. 原文刻意避開的寫法（例如為了 Typst 匯出相容而不用 `\color{}`、`\intercal`、`\substack`），英文版同樣不用。
7. **`◆` / `◇` 等提示記號**與其位置。
8. Mermaid 的 `%%{init: …}%%` 區塊、`classDef` / `class` 語句、節點 ID、箭頭語法。

---

## 6. 程式碼 cell 的翻譯範圍

`.ipynb` 的 code cell **要翻譯**下列三類中文，其餘一律不動：

1. **註解**（`#` 之後的中文，含 `# --- 步驟 1：… ---` 這類分隔註解與 docstring）。
2. **會被印出或畫出的字串字面值**：`print()` 的內容、`ax.set_title()`、
   `plt.xlabel()`、`fig.update_layout(title=…)`、圖例 `name=`、標註 `text=`、
   hover 模板中的說明文字。f-string 只譯文字部分，`{…}` 裡的運算式一字不動。
3. **作為顯示標籤的字典 key**（例如 `"單射 (Injective)"` → `"Injective"`）。
   - **注意**：這種 key 若在後面的程式碼中被引用，改名時必須同步改所有引用處，
     否則 notebook 會壞掉。驗證腳本會檢查：同一個中文字串在程式裡被當成 key 或下標使用時，各處譯法必須相同。

**不翻譯**：變數名、函數名、非顯示用途的字串、docstring 中的數學符號、
`plt.rcParams['font.family']` 的字型清單（中文字型名保留，確保英文版即使混排中文字元也不會出現豆腐方塊；驗證時用 `--allow` 列出這些字型名）。

### 6.1 code cell 中固定出現的樣板

若教材的 code cell 共用同一組樣板函數（例如 `print_step`、`compare_print` 印出的「步驟」「代碼計算值」「公式預期值」），樣板輸出的譯法必須全書一致：第一次遇到時定下譯法、補進術語表，之後照表。例如：

```python
print_step(1, "建立矩陣")                 →   print_step(1, "Build the matrix")
f"\n▶ 步驟 {step}: {desc}"               →   f"\n▶ Step {step}: {desc}"
print_header("例 1.1｜集合運算文氏圖")      →   print_header("Example 1.1 | Venn Diagrams for Set Operations")
```

全形直立線 `｜` 改成半形 ` | `，兩側各一空格。

---

## 7. Mermaid 圖

- `%%{init: …}%%` 主題區塊、`classDef` / `class` 語句、節點 ID（`A`、`S1`、`P1`）**不動**。
- 節點顯示文字（`A("集合的定義<br/>確定性・互異性・無序性")`）**要譯**，
  `<br/>` 位置保留，中文間隔號 `・` 改成半形 ` · ` 或 `, `，擇一後全書一致。
- subgraph 標題內的 HTML（`<span style='color:…;font-weight:bold'>§1.1 集合論基礎</span>`）
  只譯文字，`style` 屬性與色碼不動。
- 箭頭標籤（`-->|有序對結構|`）要譯：`-->|ordered-pair structure|`。
- subgraph 標題維持引號包覆，節點 ID 仍僅用英數字。

---

## 8. 表格

Markdown 表格的**表頭與內容要譯**，欄位對齊列（`|---|---|`）不動。
數學式欄位（如 `$\|f^{-1}[\{y\}]\| \leq 1$`）逐字保留。

符號表若有「符號｜含義｜英文用語」這類對照欄，英文版譯表頭（`Symbol | Meaning | English term`），
「含義」欄譯成英文，**本來就是英文的欄位原封不動**；譯完後兩欄內容重複也保留原結構，不合併。

---

## 9. 拼寫與標點

- **美式拼寫**：`analyze`、`behavior`、`center`、`generalization`、`modeling`（不用英式 `analyse`、`centre`）。
- **Oxford comma 使用**：`unions, intersections, and complements`。
- 全形標點（`，` `。` `、` `：` `；` `「」` `（）` `｜`）在英文譯文中**全部換成半形對應標點**，
  唯一例外是逐字保留區（第 5 節）內的內容。
- 數學式與前後英文之間留一個半形空格：`the set $A$ is finite`。

---

## 10. 行／列與序數

- 英文直接寫 row / column，以公式與程式錨點決定意思：row $i$ 是 $\text{row}_i(\mathbf{A})$、`A[i, :]`；column $j$ 是 $\text{col}_j(\mathbf{A})$、`A[:, j]`；row vector 是 $1\times n$，column vector 是 $n\times 1$；$m\times n$ matrix 有 $m$ rows、$n$ columns。
- **不可順著中文字面對應**：繁體中文「行 = column、列 = row」（見 `references/tc-conventions.md`），先把原文歸一到 row / column 或公式錨點，再寫英文。
- 指涉索引時保持 0-based 與數字：「row 0」「column 2」「the 0-th row」「the $i$-th column」，不改成 1-based；與索引無關的行文序數寫成英文（the first, the second）。
