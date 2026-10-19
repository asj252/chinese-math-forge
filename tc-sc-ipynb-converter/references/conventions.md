# 繁體／簡體中文的行列慣例

本 skill 是少數必須同時持有兩套慣例的情境：輸入是繁體中文（行 = column、列 = row），輸出是簡體中文（行 = row、列 = column）。
判斷時一律回到英文概念或公式／程式錨點，不要逐字比對兩邊的「行」「列」。

| 英文概念 | 公式／程式錨點 | 繁體寫法 | 簡體寫法 |
|---|---|---|---|
| row $i$ | $\text{row}_i(\mathbf{A})$、`A[i, :]` | 第 $i$ 列 | 第 $i$ 行 |
| column $j$ | $\text{col}_j(\mathbf{A})$、`A[:, j]` | 第 $j$ 行 | 第 $j$ 列 |
| row vector | $1\times n$ | 列向量 | 行向量 |
| column vector | $n\times 1$ | 行向量 | 列向量 |
| row space | $\text{Row}(\mathbf{A})$ | 列空間 | 行空间 |
| column space | $\text{Col}(\mathbf{A})$ | 行空間 | 列空间 |
| (elementary) row operation | 左乘初等矩陣 | （基本）列運算 | （初等）行变换／行运算 |
| (elementary) column operation | 右乘初等矩陣 | （基本）行運算 | （初等）列变换 |
| $m\times n$ matrix | $m$ rows, $n$ columns | $m$ 列 $n$ 行 | $m$ 行 $n$ 列 |

序數兩邊都用阿拉伯數字，與 0-based 索引一致：繁體「第 0 列」（row 0）＝ 簡體「第 0 行」（row 0）。

不帶方向義的詞（行列式、行為、進行、執行、平行、排列、序列、數列、陣列、下列、列出…）不對調。
但要按句意判斷，不能只看字串：繁體「第 0 行為零向量」是「第 0 行」（column 0）加「為」，簡體要寫成「第 0 列为零向量」；
「這一點列為重點」的「列」是「列入」的意思，不是 row。這類情形腳本無法判斷，會列進核對清單。
