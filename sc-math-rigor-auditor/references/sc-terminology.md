# SC 术语与地区用语参考

本表是审查时的**候选线索**，不是自动替换规则，也不是数学真值来源。命中后须按语境判断：大陆教材中若两种译名皆通行，只要全书一致即可，不列为错误。已由 converter 后处理的项目（见 `tc-sc-ipynb-converter` 的「数学术语后处理」）若仍出现旧写法，属 `conversion_error`；其余属 `terminology` 或风格。

## 行/列相关（最高优先）

本节遵守 SKILL.md 的防污染规则：**以英文概念为主键**，只列 SC 应有写法。表中不出现 TC 的行/列字面，避免同一张表里同一个字承载两种语义。需要比对 TC 时，先把 TC 原文归一到英文概念，再查本表。

| 英文概念（锚点） | 公式／代码锚点 | SC 应为 |
|---|---|---|
| row vector | $1\times n$ | 行向量 |
| column vector | $n\times 1$ | 列向量 |
| row $i$ | $\text{row}_i(\mathbf{A})$、`A[i, :]` | 第 $i$ 行 |
| column $j$ | $\text{col}_j(\mathbf{A})$、`A[:, j]` | 第 $j$ 列 |
| row space | $\text{span}\{\text{row}_i\}$ | 行空间 |
| column space | $\text{span}\{\text{col}_j\}$ | 列空间 |
| (elementary) row operation | 左乘初等矩阵 | （初等）行变换／行运算 |
| (elementary) column operation | 右乘初等矩阵 | （初等）列变换 |
| row echelon form | | 行阶梯形 |
| reduced row echelon form | | 简化行阶梯形（亦称行最简形） |
| full row rank | $\operatorname{rank}\mathbf{A}=m$ | 行满秩 |
| full column rank | $\operatorname{rank}\mathbf{A}=n$ | 列满秩 |
| $m\times n$ matrix | $m$ rows, $n$ columns | $m$ 行 $n$ 列 |

判断以公式／代码锚点为准，文字只是结果。

## 数学术语（台湾 → 大陆常用）

| 台湾用语 | 大陆常用 | 备注 |
|---|---|---|
| 純量 | 标量 | converter 已处理 |
| 純量積 | 数量积／点积 | converter 已处理 |
| 對射／嵌射／映成函數 | 双射／单射／满射 | converter 已处理 |
| 線性獨立／線性相依 | 线性无关／线性相关 | |
| 基底 | 基 | |
| 維度 | 维数 | 指空间维数时 |
| 反矩陣 | 逆矩阵 | |
| 么正矩陣／單式矩陣 | 酉矩阵 | |
| 厄米特矩陣／埃爾米特 | 埃尔米特矩阵（Hermite 矩阵） | 全书统一 |
| 伴隨矩陣 | 伴随矩阵 | 区分 adjugate 与 adjoint，按原意核对 |
| 餘因子 | 代数余子式 | cofactor；minor 为余子式 |
| 高斯消去法 | 高斯消元法 | |
| 樞軸／軸元 | 主元 | pivot |
| 自由變數／變數 | 自由变量／变量 | |
| 最小平方法 | 最小二乘法 | |
| 疊代 | 迭代 | |
| 演算法 | 算法 | |
| 向量積／外積 | 叉积／向量积 | 注意教材里的「外积」也可能指 $\mathbf{u}\mathbf{v}^*$，按原意核对 |
| 座標 | 坐标 | |
| 矩陣的跡 | 迹 | |
| 本徵值 | 特征值 | 量子物理语境可用本征值，全章一致即可 |
| 正規矩陣 | 正规矩阵 | |
| 正定 | 正定 | 相同 |

## 一般用语与程序相关

| 台湾用语 | 大陆常用 |
|---|---|
| 程式／程式碼／程式設計 | 程序／代码／程序设计 |
| 函式 | 函数 |
| 變數 | 变量 |
| 預設 | 默认（「预设」在「预设前提」等语义下可保留） |
| 資料 | 数据 |
| 物件 | 对象 |
| 陣列 | 数组 |
| 迴圈 | 循环 |
| 遞迴 | 递归 |
| 支援 | 支持 |
| 訊息 | 信息 |
| 品質 | 质量 |
| 透過 | 通过 |
| 圖形介面 | 图形界面 |
| 模組 | 模块 |

## 转换伤害特征

- 「列行式」「列为」：固定术语被误调。
- 全大写代号残留（`DETTERM`、`BEHAVR`、`PARALLELOGRAM`、`PERMUTATION`、`PARALLEL`、`TWOROWNOTATION`、`SEQUENCE`、`PROCEED`、`EXECUTE` 等）：占位符未还原。
- 数学式、代码、label、`{ref}` 目标、Mermaid 节点 ID 中出现被转换的字符。
- `\text{}` 内中文的行/列是否与外部公式语义一致。
