# 简体中文版教材的语言惯例

适用范围：用本 skill 审查的简体中文版（SC）教材内容，以及以 SC 为对象的修订。审查繁体原稿（TC）时不用本文件；跨版本比对时，先把双方各自归一到英文 row / column 或公式锚点，再比较锚点。

本文件是 SC 惯例的依据。项目里由转换产生的 SC 记号表属于审查对象，不能作为 SC 惯例的依据。

## 内容语言

简体中文（大陆教材用语）。地区用语与术语参考见 [`sc-terminology.md`](sc-terminology.md)。

## 行／列

**行 = row，列 = column**，全书严格遵守。

以英文概念与公式／代码锚点为准：

| 英文概念 | 公式／代码锚点 | SC 写法 |
|---|---|---|
| row $i$ | $\text{row}_i(\mathbf{A})$、`A[i, :]` | 第 $i$ 行 |
| column $j$ | $\text{col}_j(\mathbf{A})$、`A[:, j]` | 第 $j$ 列 |
| row vector | $1\times n$ | 行向量 |
| column vector | $n\times 1$ | 列向量 |
| row space | $\text{Row}(\mathbf{A})$ | 行空间 |
| column space | $\text{Col}(\mathbf{A})$ | 列空间 |
| (elementary) row operation | 左乘初等矩阵 | （初等）行变换／行运算 |
| (elementary) column operation | 右乘初等矩阵 | （初等）列变换 |
| row echelon form | | 行阶梯形 |
| reduced row echelon form | | 简化行阶梯形（亦称行最简形） |
| $m\times n$ matrix | $m$ rows, $n$ columns | $m$ 行 $n$ 列 |

矩阵分量的指称：$\text{row}_i(\mathbf{A})$ 表示第 $i$ 行，$\text{col}_j(\mathbf{A})$ 表示第 $j$ 列。

Code cell 的注释、字符串与输出同样采用本惯例。注意：TC 的 code cell 采用 TC 惯例，转换工具未必对 code cell 做行/列对调（本仓库的 `tc-sc-ipynb-converter` 不做），因此 SC code cell 中的行/列是已知高风险区，须逐处按锚点核对。

不带方向义、不受上表影响的词：行列式、行为、进行、执行、平行、排列、序列、双行记法；「cell 内行号」的「行」指代码或文字的 line。但要按句意判断，不能只看字符串：TC 原文里「第 0 行」（column 0）后面紧跟「为」字时，转换工具可能把它当成「行为」保护起来，转出「第 0 行为零向量」，就读成了 row 0。

## 序数

统一使用阿拉伯数字，与 0-based 索引保持视觉一致：「第 0 行」（row 0）、「第 2 列」（column 2），不写「第零行」。
