<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="chinese-math-forge：中文数学教材的写作与审查用的 agent skill——数学严谨性审查、繁简转换、繁体译英文、LaTeX 习题流水线">
</p>

# chinese-math-forge

中文数学教材的写作与审查用的 agent skill：审查繁体原稿与简体版的数学严谨性、把繁体 Markdown／notebook 转成简体、把繁体 notebook 翻译成英文、把 LaTeX 习题做成带验算的习题 notebook。每个 skill 是一个目录，核心是一份 `SKILL.md`，放进能读取 skill 目录的 agent 宿主即可使用。

> **English.** chinese-math-forge is a small set of agent skills for Chinese-language math textbooks written in MyST Markdown and Jupyter Notebooks: auditing the mathematical rigor of a Traditional Chinese manuscript and of its Simplified Chinese conversion (including errors introduced by the conversion, such as the row/column terms whose meanings are swapped between the two scripts), translating Traditional Chinese notebooks into English with a locked glossary and a verification script, and turning a LaTeX exercise file into an exercise notebook with NumPy check code. Each skill is a folder with a `SKILL.md`; copy it into the skills directory your agent host reads. The collection also includes Traditional-to-Simplified Chinese Markdown and notebook converters based on markdown-it-py, with a mandatory review checklist for row/column terminology. The skills that work on Traditional Chinese sources are written in Traditional Chinese; the others in Simplified Chinese.

> 状态：试用版（0.2.0）。原有四个 skill 各在小样例上验证过一次，0.2.0 发布前又各在另一个 agent 宿主上照公开稿跑过一次样例；新增的两个繁简转换 skill 附带解析器依赖，验证范围见「已知限制」。较大的真实教材仍需逐条核对。

## 相关仓库

同一作者的其他 skill 仓库：

- [persona-masks-cn](https://github.com/asj252/persona-masks-cn)：让 AI 助手把「想、做、查」分开的一套轻量角色约定，做成文件型 skill。
- [myst-textbook-forge](https://github.com/asj252/myst-textbook-forge)：用 MyST 写教科书的工具：章节编辑、视觉风格与 Python 代码整理。
- [writing-forge](https://github.com/asj252/writing-forge)：写作用的 skill：讲解文章的认知审查、忠于原文的简报、README 头图设计。


## 包含的 skill

| skill | 做什么 | 正文语言 |
|---|---|---|
| [`tc-math-rigor-auditor`](tc-math-rigor-auditor/SKILL.md) | 审查繁体中文数学教材（MyST Markdown、Jupyter Notebook）的数学正确性与用语严谨性：定义、量词、假设、证明、退化情形与跨章一致性，输出可定位、附证据的问题报告 | 繁体中文 |
| [`sc-math-rigor-auditor`](sc-math-rigor-auditor/SKILL.md) | 审查由繁体原稿转换来的简体版：除了数学问题，还对照繁体原稿找出转换引入的错误（行／列对调、术语被破坏、占位符残留、公式或 label 损坏）、繁体字与台湾用语残留，并判明根因在原稿还是在转换 | 简体中文 |
| [`tc-en-ipynb-translator`](tc-en-ipynb-translator/SKILL.md) | 把繁体中文的数学 notebook 翻译成英文：先查、补项目的术语表再逐格翻译，按美式大学教科书的语域；附抽取、写回与验证脚本（cell 结构、label 与引用、代码逻辑不变，残留中文报出） | 繁体中文 |
| [`tex-exercise-pipeline`](tex-exercise-pipeline/SKILL.md) | 把 LaTeX 习题文件（`.tex`）做成习题 notebook：解析成 MyST 习题（解答放在 dropdown 里）、为每道题写 NumPy 验算代码、用附带的脚本把习题与验算交错组合成 `.ipynb` | 简体中文 |
| [`tc-sc-converter`](tc-sc-converter/SKILL.md) | 繁体 MyST Markdown 转简体，按解析器边界保护数学、代码与链接，附行列和保留区域的核对清单 | 繁体中文 |
| [`tc-sc-ipynb-converter`](tc-sc-ipynb-converter/SKILL.md) | 繁体 notebook 转简体，保留非 source 字段，代码字符串默认不转，注释与保留区域列入核对清单 | 繁体中文 |

两个审查 skill 是一对：先用 `tc-math-rigor-auditor` 审繁体原稿，转换成简体后再用 `sc-math-rigor-auditor` 对照原稿审简体版。

## 安装

把需要的 skill 目录整个复制到宿主读取 skill 的位置（各宿主一般有用户级与项目级两种 skills 目录，见宿主自己的文档），目录名保持与 `SKILL.md` 里的 `name` 一致：

```bash
git clone https://github.com/asj252/chinese-math-forge.git
SKILLS_DIR="$HOME/path/to/skills"   # 先换成宿主实际读取的 skills 目录
mkdir -p "$SKILLS_DIR"
cp -r chinese-math-forge/tc-math-rigor-auditor "$SKILLS_DIR/"
```

整个目录一起复制：各 skill 的 `references/`、`scripts/`、`templates/` 都会被 `SKILL.md` 引用。

执行时用到的是宿主本身的能力：

- 六个 skill 都要能读写文件。
- 原有四个 skill 附带的脚本（抽取 notebook 内容、写回译文、验证译本、组合习题 notebook）要宿主能执行 Python 3 脚本，只用标准库。
- 两个繁简转换 skill 需要 Python 3.12 以上及各自 `requirements.txt` 中的 markdown-it-py、mdit-py-plugins、PyYAML、OpenCC。依赖未安装且尚未获授权时先问使用者；脚本不自动安装。
- `tc-en-ipynb-translator` 每翻完一批就在你的 Git 仓库提交一次（只加本批写到的文件，不推送），宿主要能执行 Git。
- `tex-exercise-pipeline` 要实际执行验算 notebook 时，需要你的环境装有 Jupyter（nbconvert、ipykernel）与 NumPy；没有时 skill 会先问你怎么执行，不会自行安装。这些不是安装 skill 的前提。

## 已知限制

- 两个繁简转换 skill：按 markdown-it-py 与 MyST 插件切分，回归覆盖表格、链接、YAML 多行选项等旧问题；行／列对调和术语替换仍须按句意核对。代码、HTML、front matter、引用识别字、notebook 存档输出等区域可能保留繁体。跨行数学文字命令、未闭合围栏及无法逐字映射的语法会明确停止；支持范围见各自 SKILL。脚本检查保护区域与结构，不能证明整份教材的转换语义正确。
- 两个审查 skill：审查质量依赖宿主模型的阅读与判断，报告是给作者的修改建议；样例 notebook 里的代码没有执行。
- `tc-en-ipynb-translator`：验证脚本只查确定的事（cell 结构、label 与引用、代码的语法结构与部分字符串的一致性、残留中文），不查数学式，也不能保证代码语义完全不变（例如间接取用的字典 key，脚本会列出提醒）；译文是否准确、术语是否恰当、数学式有没有被改要靠人读。带存档输出的 notebook 翻完 source 后，输出仍是中文，要在你的环境重跑才会一致，进度表在这之前标为 `done*`。
- `tex-exercise-pipeline`：样例的验算 notebook 与成品在一个 NumPy 2.4 的环境实际执行过一次（所有验算都通过）；其他版本与更大的习题册没有验证。

## 许可

本仓库以 [Apache-2.0](LICENSE) 发布。六个 skill 都是作者自己的教材工具，公开时去掉了书稿专用的路径、命名与项目约定，需要的约定收成随 skill 附带的参考文件。

变更记录见 [CHANGELOG.md](CHANGELOG.md)。
