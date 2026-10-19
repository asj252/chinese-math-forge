# 变更记录

## 0.2.0（2026-10-19）

### 仓库

- README 开头加头图 `assets/readme/hero.svg`：仓库的标志（行列对调）、一句话说明与四项能力的标签。

### `tc-sc-converter`

- 新增繁体 MyST Markdown 转简体：用 markdown-it-py 与 MyST 插件切分，按原文位置转换正文、数学文字与 YAML 文字选项，保留代码、链接目标和识别字，附逐条核对清单。

### `tc-sc-ipynb-converter`

- 新增繁体 notebook 转简体：与 Markdown 版共用相同脚本；代码字符串默认保留，注释转换，保留 metadata、outputs 与其他非 source 字段。

### `tc-math-rigor-auditor`

- 报告格式统一发现 id 示例为 `rigor-tc-<来源档名主体>-NNN`（如 `rigor-tc-ch02-001`），与简体审查报告对应。
- `SKILL.md` 与报告格式写明：源文件 SHA-256 按实际读取的文件字节计算（Windows 检出为 CRLF 时按实际读取的字节算）。
- `SKILL.md` 说明 `missing_condition` 涵盖命题漏写前提条件，以及证明或例题套用定理时未验证假设条件的论证缺口。

### `sc-math-rigor-auditor`

- 报告格式统一发现 id 示例为 `rigor-sc-<来源档名主体>-NNN`（如 `rigor-sc-ch02-001`），并补引用繁体报告 id 的示例。
- `SKILL.md` 与报告格式写明：SC 与 TC 的 SHA-256 均按实际读取的文件字节计算（与繁体审查一致）。
- `SKILL.md` 补充「类型」与「根因来源」的组合示例（如 label 被转换改坏为类型 `structural_issue`、根因 `conversion_error`）、`missing_condition` 对未验证定理假设的归类，以及判定「规则性 `conversion_error`」所需的证据要求。
- 行/列防污染规则写明同样适用于读取既有繁体审查报告（`rigor_TC_*.md`）。
- code cell 行/列问题的根因记为 `conversion_error`，是否「规则性」照根因一节的机制证据门槛判，不再直接记为规则性。

### `tc-en-ipynb-translator`

- 进度表范本与 `SKILL.md` 规定：「最后一批的 commit」栏在随译本同批提交时填本批 commit 讯息或于下一批回填短哈希，避免提交引用自身；「原稿」「译本」两栏统一填相对于进度表所在项目根目录的相对路径（使用 `/`）。
- `SKILL.md` 明确术语表 `meta.covers` 在整份原稿翻译完成（最后一批）时更新。
- `references/style.md` §1.4 与 `SKILL.md` 补充整格省略时的 patch 写法（不含引用与 `{solution}` 的纯文字 Markdown cell 保留原类型的空 cell、patch 值写 `""`，含引用或为 code cell 时保留受保护结构）。
- `references/style.md` 第 5 节写明不翻译的是作为数据键的字典 key，作为显示标签的字典 key 照第 6 节翻译（原先两节说法冲突）；`meta.covers` 只写文件名、不含目录。

### `tex-exercise-pipeline`

- 阶段 B4 写明：用户选择不执行（或环境无法执行）时，经语法编译检查后可照样进入阶段 C 组合，并在成品与回报中注明「验算代码未执行」。
- 明确验算代码的标题、注释、docstring 与输出文字（含 B1 的「步骤」「代码计算值」「公式预期值」等）一律跟随习题语言。
- 明确用 `{tip}` 块写提示时取代模板中的 `**提示：**` 行；B2 的 `[题号]` 与 B3 的 `## 第 N 题` 均从 1 起算。
- 流程概述与完整执行示例改为「用户同意执行时含执行输出」，与 B4 一致；验算 notebook 的段落标题字样跟随习题语言（繁体原文用繁体字形）；B 阶段补繁体行/列提醒：「列」是 row、「行」是 column，组矩阵的代码要与原文一致。

## 0.1.0（2026-10-15）

首次发布，四个 skill：

- `tc-math-rigor-auditor`：繁体中文数学教材的严谨性审查。公开时去掉书稿专用的路径与约定，需要的约定收成随 skill 附带的参考文件（`references/tc-conventions.md`）与报告格式。
- `sc-math-rigor-auditor`：由繁体原稿转换来的简体版的严谨性审查，对照原稿判明根因在原稿还是在转换。公开时同样去掉书稿专用内容，附简体的约定、术语与报告格式。
- `tc-en-ipynb-translator`：繁体中文数学 notebook 的英文翻译。公开时把术语表改为「随 skill 附一份种子表、复制到项目里维护」，去掉书稿专用内容；写回脚本在译本已存在时要明确续译，并用原稿指纹发现原稿在上一批之后改过；验证脚本核对结构、label 与引用、代码逻辑（含字典 key 与 f-string 的处理）与残留中文。
- `tex-exercise-pipeline`：LaTeX 习题转习题 notebook。公开时转为简体，重写组合脚本：五个以上冒号的习题、同一题的多个 code cell、习题外的小节文字都不再被丢；映射对不上、越界或有代码没被用到时停下报错，不覆盖已有输出。

繁简转换的两个 skill 留到下一版。
