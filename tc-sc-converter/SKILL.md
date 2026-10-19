---
name: tc-sc-converter
description: 將繁體中文 Markdown（.md）轉成簡體，處理數學教材行／列方向及術語，保護公式、程式與 MyST 識別字。使用者要求繁簡轉換且輸入為 .md 時使用。
metadata:
  version: "0.2.0"
---

# 繁體 → 簡體 Markdown

先讀 [行列慣例](references/conventions.md)：繁體行 = column、列 = row；簡體相反。
行列式等非方向詞不對調。詞表與逐字對調無法判斷句意，每一行含行／列的正文都要人工核對。

## 操作

1. 確認輸入、輸出路徑與 Python 3.12 以上環境。需要的依賴列在 `requirements.txt`。
   缺少依賴時沿用使用者已授權的安裝範圍；未授權時先問，腳本不自動安裝。
2. 執行 `python <本 skill 目錄>/scripts/tc_sc_convert.py INPUT OUTPUT`。
   產出轉換檔與 `OUTPUT.review.md`；兩個目標任一已存在就停止，不覆蓋。
3. 逐條對照原稿、英文 row／column、公式與程式索引，核對清單中的行列、術語及保留區域。
   需要修訂時只改登記行範圍的文字；不改公式骨架、程式邏輯與引用目標。
   在清單「結果」原文後補注位置與修法；保留位置、類型、原文，把狀態精確改為「已核對」。
4. 回報兩個產物路徑、核對與修訂結果、保留繁體的範圍、未驗證項目。
   有無法判斷的項目就明說並請使用者確認，不把未核對產物稱為完成。

## 解析與保護範圍

以 markdown-it-py 的 CommonMark 區塊、連結、表格單元格與行內規則切分，
另啟用 MyST target、role、冒號圍欄與 dollarmath。按原文範圍改字，不重新渲染。
段落、標題、清單、引用、表格文字、directive 標題／內文及 caption/title/alt/subtitle 選項照轉。
YAML 文字選項由 PyYAML scalar 的原文位置決定範圍，保留鍵名、引號與折行。
數學式只轉 `\text{…}` 等文字命令，其他部分保留；`$…$` 的空白、數字與配對條件沿用 MyST dollarmath 預設。
程式碼（含縮排式與無標籤圍欄）、Mermaid、front matter、HTML、label、引用識別字、連結目標、路徑參數原樣。
參考連結的識別文字也保留；顯示文字可能仍是繁體，須按清單核對。
裸 http/https 網址從 scheme 起保護到空白或中文標點，含巢狀括號；不推測網址外的文字。

未閉合圍欄、容器提前結束、跨行或未閉合的數學文字命令，以及無法逐字映射的解析結果會停止，不寫出產物。
未被解析器認作連結的跨行目標會停止；含跳脫管線的表格、tab 縮排等寫法可能無法映射。
請依錯誤訊息調整輸入副本再重跑。
未知 directive 內文按 Markdown；帶程式、路徑或設定的 directive 依腳本列出的名稱保留。
嵌套在 directive 裡、認不出的引用寫法原樣保留，列進人工確認。
自檢比較保護片段與數學骨架，檢查轉後正文的 OpenCC 殘留及 code cell 語法樹；不能代替句意核對。
兩個輸出排他建立；寫入失敗會回滾本次新檔，回滾失敗時列出殘留路徑。

另一種輸入格式請使用 `tc-sc-ipynb-converter`。
