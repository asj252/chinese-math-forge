---
name: tc-en-ipynb-translator
description: >
  將繁體中文的 MyST / Jupyter Notebook 數學教材（.ipynb）翻譯成英文。
  當使用者說「翻譯這章成英文」、「翻下一章的英文版」、「tc 轉 en」、
  「繼續 tc-en 翻譯」、「接續英文翻譯」、「translate the next chapter to English」、
  「continue translating to English」、「把這個 notebook 翻成英文」、
  「英文版翻到哪了」、「更新翻譯進度」，或指定某個繁體中文 notebook 要出英文版時，
  必須觸發此 skill。流程強制「先鎖術語再翻譯」：翻譯前一定先查 / 補專案的術語表，
  再依 references/style.md 的美式大學教科書語域逐格翻譯。適用於含 LaTeX 數學式、
  prf: 定理環境、exercise/solution、Mermaid 圖與 matplotlib / plotly 程式碼的學術教材 notebook。
---

# 繁體中文 → 英文 Jupyter Notebook 翻譯 Skill

## 這不是全自動轉換

| | `tc-sc-ipynb-converter` | **本 skill（`tc-en`）** |
|---|---|---|
| 本質 | 機械式 OpenCC 字符轉換 | 需要真正生成英文語言的翻譯 |
| 腳本能做的 | **全自動跑完整份 notebook** | **只負責安全讀寫 cell JSON** |
| 翻譯決策 | 規則表決定 | **由執行本 skill 的 agent 依術語表 + 風格規範逐格完成** |
| 詞彙一致性 | OpenCC 詞典保證 | **靠專案術語表（術語鎖）強制** |

不存在「跑一個腳本就翻完一章」的路徑。`nb_extract.py` / `nb_apply.py` 只做
「把 cell 文字讀出來」與「把譯好的文字寫回去」，`verify_translation.py` 只做檢查，中間的翻譯由 agent 逐格完成。

## 隨 skill 附帶的資源與專案裡的檔案

| 檔案 | 作用 |
|---|---|
| `references/glossary_seed.yaml` | 術語鎖的種子表。第一次使用時**複製到專案**（例如 `glossary.yaml`），之後只改專案裡那一份；下文的「術語表」都指專案裡的這一份 |
| `references/tc-conventions.md` | 繁體中文的行／列、序數慣例。原文的「行」「列」先依它解讀成 row / column 再翻譯，不可順著字面 |
| `references/style.md` | 「怎麼寫」：語域、`prf:` 標題、步驟格式、逐字保留清單、行／列與序數的英文寫法 |
| `templates/translation_progress.md` | 進度表範本。第一次使用時**複製到專案**；下文的「進度表」都指專案裡的這一份 |
| `scripts/nb_extract.py` | 把 notebook 逐格 dump 成純文字（純標準庫 `json`） |
| `scripts/nb_apply.py` | 把譯好的 cell 寫回譯本，只換 `source`，並記下原稿指紋 |
| `scripts/verify_translation.py` | 步驟 7 的檢查，任一項不過以非零結束碼結束 |

原稿與譯本的路徑由使用者決定（常見的做法是放在 `tc/`、`en/` 兩個目錄，檔名主體相同）。腳本只需要 Python 3 標準庫。

---

## 執行步驟

### 步驟 1：確認這次要翻哪一個檔案

讀進度表，取第一個狀態不是 `done` 的項目。使用者若指定了檔案，以使用者指定的為準；
專案還沒有進度表時，問使用者要翻哪個檔、譯本放哪裡，再從範本建一份進度表。

- 狀態是 `in-progress` → 從「完成到 cell」欄記的索引 **+1** 接續，不要從頭重翻。
- 譯本的路徑照進度表；進度表「原稿」「譯本」兩欄一律填相對於進度表所在目錄（專案根目錄）的相對路徑，使用 `/`（例如原稿 `tc/ch02.ipynb` → 譯本 `en/ch02.ipynb`）。

不必問使用者「上次翻到哪」——進度全部落在檔案裡。

### 步驟 2：抽出原文

```bash
python <本 skill 的目錄>/scripts/nb_extract.py tc/ch02.ipynb <臨時目錄>/ch02.txt
```

切塊時加 `--range`（半開區間，`0:20` 表示第 0..19 格）：

```bash
python <本 skill 的目錄>/scripts/nb_extract.py tc/ch11.ipynb <臨時目錄>/ch11_a.txt --range 0:20
```

暫存檔一律放在系統的臨時目錄，**不進版本控制**。

### 步驟 3：術語掃描（不得跳過）

通讀本批原文，列出術語表尚未收錄的術語：

- **常見、無歧義的詞** → 直接補進術語表，`src` 欄註明來源（檔案或章節），繼續翻譯。
- **有歧義或高風險的詞** → **先列出來問使用者**，確認後才寫進術語表與譯文。

判定「高風險」的操作準則：同一個中文詞若能想出兩個以上都說得通的英文譯法，
而且選錯會讓讀者理解成不同的數學對象——那就要問。種子表第 0 節列的易誤譯詞
（嵌射、映成函數、對射、純量、坐標變換矩陣）就是這一類。

補完術語表後把 `meta.version` 加一、更新 `meta.updated`；`meta.covers` 記已完成翻譯的原稿檔名（只寫檔名，如 `ch02.ipynb`，不含目錄；分批翻譯時於該檔案最後一批完成時才加入，若最後一批無新增術語也在此時更新 `meta.covers`；單批完成則於本批加入）。

> **術語表沒鎖定的詞，不准出現在譯文裡。**

### 步驟 4：逐格翻譯

依 `references/style.md`。最常用到的幾條：

- **語域**：美式大學教科書。不用縮寫式（寫 `do not` 不寫 `don't`），不用 `iff`，
  we / you 各有其位（定義與證明內文不用 you）。
- **`prf:` 標題**：關鍵字不譯，標題引數譯成 Title Case 名詞短語
  （`:::{prf:definition} 集合` → `Set`，**不寫** `Definition of a Set`）。
- **步驟格式**：例子與程式碼解說的 `**步驟1：**` → `**Step 1.**`（半形句點）；
  定理／證明中的有序列表格式不變。
- **粗體導語**：`**分析**：` → `**Analysis.**`，其餘見 style 第 3.2 節對照表。
- **`:name:` → `:label:`**：值不變。這是唯一允許在翻譯時修正的原文問題。
- **逐字保留**：`:label:` 值、`{prf:ref}` 引數、LaTeX 數學式、色碼、`§X.Y`、
  `◆`/`◇` 記號、程式邏輯、Mermaid 的 `%%{init}%%` 與 `classDef`。
  數學式內若嵌有 `\text{中文}`，只譯 `\text{}` 內的中文。
- **code cell**：只譯註解、docstring、會被印出／畫出的字串、顯示用的 dict key。
  改 dict key 時務必同步所有引用處（步驟 7 會檢查）。f-string 只譯文字部分，`{…}` 裡的運算式不動。

把譯好的 cell 寫成 patch JSON（`{"0": "...", "3": "..."}`；不含引用與 `{solution}` 的純文字 Markdown cell 若經使用者同意整格省略，保留原類型的空 cell、patch 值寫 `""`，見 `references/style.md` §1.4），同樣放臨時目錄。

> **code cell 的推薦作法**：不要重打整格程式碼。讀出 TC 原始 source，
> 寫一支定點替換腳本（每條替換 `assert` 命中次數），只換註解與字串。
> 這樣程式邏輯不可能被改壞。

### 步驟 5：切塊規則

超過約 20 個 cells 的檔案要切塊：

- 每批 **15–20 個 cells**，一批跑完步驟 6～8（含 commit）才進下一批。
- 單一 cell 極長時（上千行），批次縮到 5–10 個 cells，以能完整讀完並翻好為準。
- 第二批起，`nb_apply.py` 加 `--continue`：以既有譯本為基底套用 patch，
  所以前幾批的成果不會被中文原文蓋回去——這是切塊能安全進行的關鍵。

### 步驟 6：寫回 notebook

```bash
python <本 skill 的目錄>/scripts/nb_apply.py tc/ch02.ipynb <臨時目錄>/patch.json en/ch02.ipynb
```

第一批（譯本還不存在）不加旗標；第二批起加 `--continue`。譯本已存在卻沒加 `--continue`，腳本會停下，避免誤蓋。
`nb_apply.py` 會在譯本的 metadata 記下原稿指紋；續譯時原稿若在上一批之後改過，腳本停下。這時先比對原稿的差異、
重新翻譯並驗證受影響的批次，再加 `--accept-source-change` 續譯，並在進度表的備註寫明。

### 步驟 7：驗證（每一批都要做）

每一項都由 `verify_translation.py` 檢查，任一項不過就以結束碼 1 結束，**不得進入步驟 8**：

```bash
python <本 skill 的目錄>/scripts/verify_translation.py tc/ch02.ipynb en/ch02.ipynb --cells 0:20
```

`--cells A:B` 表示本批是第 A..B-1 格：第 B 格以前都當成已譯、全部檢查；第 B 格起當成待譯，必須與原稿逐字相同。
最後一批之後、交付之前，不加 `--cells` 再跑一次全量檢查。

1. **JSON 合法且 cell 數、類型序列相同**。
2. **`:label:` 值逐格一致**——原稿的 `:label:`（與殘留的 `:name:`）依序等於譯本的 `:label:`；
   經使用者同意省略的用 `--allow-missing-label` 列出。
3. **`{prf:ref}` / `{ref}` / `{solution}` 引數逐格一致**。
4. **code cell 程式結構未變**——比對語法樹；不含中文的字串（色值、模板名、路徑、欄位名）一字不變。含中文的字串：
   顯示文字（docstring、`print` 等顯示函數的位置引數、繪圖呼叫的 `label=`／`title=` 等文字關鍵字）可以自由翻譯，
   f-string 只改文字、`{…}` 裡的運算式不動；中文的字典 key 可以改名，但它在字典、下標、清單、比較裡的譯法要相同、
   同一個字典裡不能撞名；其他位置（指派、一般函數的引數、運算式裡的常量）保持原文，確認只是顯示文字的用 `--accept` 列出。
   以 `%`、`!` 開頭的魔術命令逐字比對。腳本列出的「提醒」要人工看過；原稿本身不能解析的 cell，人工核對後用
   `--skip-code` 略過並在回報說明。
5. **本批殘留中文檢查**——只查本批；刻意保留的中文（例如字型清單裡的中文字型名）用 `--allow` 列出。

### 步驟 8：更新進度並 commit

編輯進度表：狀態、完成到第幾個 cell、原稿指紋、最後一批的 commit（與譯本同一次提交時填本批 commit 訊息如 `translate: en/ch02.ipynb cells 0-19`，或於下一批回填上一批的短雜湊，不在同一筆提交裡預填自身的雜湊）、備註。
若術語表有新增條目或更新了 `meta.covers`，一併說明並加入暫存。

```bash
git add -- en/ch02.ipynb <進度表> <術語表>
git commit -m "translate: en/ch02.ipynb cells 0-19"
```

只加本批寫到的檔案，不用 `git add -A`。**不自動 push。** push 前一律另外向使用者確認。

### 步驟 9：回報

回報摘要即可：**檔名、cell 範圍、新增術語、驗證結果、commit hash**。

- **不要把整份 notebook 貼進對話**——那會把 context 燒光。
- 需要使用者審核用詞時，只挑代表性的兩三段。

---

## 發現原文問題時

**不要順手修正。** 記錄到進度表的「原文問題」段落，
回報使用者，由使用者裁決。裁決通過後，原稿與譯本**一起改**。

唯一例外是 `:name:` → `:label:`（MyST 的錨點寫 `:label:`，值不變）。

若某個原文問題會讓英文版直接說錯話（例如術語與全書慣例相反），
可以先依全書實際慣例翻譯，但**必須在回報中明確標出這一處沒有照字面譯**，
讓使用者知道並確認。

## 需要執行環境時

本流程只改 `.ipynb` 的原始文字、不執行 notebook，所以不需要
numpy / matplotlib / plotly / nbformat。

例外是帶存檔 outputs 的 notebook：翻完 source 後那些輸出仍是中文，必須在使用者的環境重跑才會一致。
處理這些檔案前**先問使用者怎麼執行他的環境**，不要自行猜測 Python 的路徑。
環境確認前可先翻 source、outputs 原樣留著，進度標記為 `done*`。

## 不要做的事

- ❌ 跳過步驟 3 的術語掃描直接翻譯。
- ❌ 臨場翻譯術語表已收錄的詞（要改就改術語表，並告知使用者）。
- ❌ 更動 `:label:` 值、數學式、色碼、程式邏輯。
- ❌ 自動 `git push`。
- ❌ 擅自修正原文的錯字或內容問題（`:name:` → `:label:` 除外）。
- ❌ 把臨時目錄的暫存檔（extract 的 `.txt`、patch 的 `.json`）加進版本控制。
