#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""nb_apply.py — 把翻譯後的 cell 文字寫回譯本 notebook。

只依賴標準庫（json、hashlib），不需要 nbformat。
除了 `source` 欄位之外，其餘欄位（cell_type、metadata、outputs、execution_count、
notebook 層級的 nbformat）全部原樣保留；notebook 層級的 metadata 另記一筆原稿指紋（見下）。

用法:
    python <本 skill 的目錄>/scripts/nb_apply.py <原稿.ipynb> <patch.json> <譯本.ipynb> [--continue] [--accept-source-change]

patch.json 格式（二選一）:
    {"0": "新的 cell 0 文字", "3": "新的 cell 3 文字"}
    [{"index": 0, "source": "..."}, {"index": 3, "source": "..."}]

新建與續譯:
    譯本不存在時：以原稿為基底複製一份，再套用這批 patch，並在譯本的
    metadata.translation_source 記下原稿的檔名與指紋（只算各 cell 的類型與 source）。
    譯本已存在時：必須加 --continue（明確表示續譯），以既有譯本為基底套用這批 patch，
    前幾批的譯文不會被原文蓋回去。續譯前檢查：
      - 譯本與原稿的 cell 數、cell 類型序列相同；
      - 原稿的指紋與譯本記下的相同。不同表示原稿在上一批之後改過，先比對原稿的差異、
        重新驗證受影響的批次，再加 --accept-source-change 更新指紋後續譯。

結束碼：0 成功；1 檢查不過或讀寫失敗（不寫出任何東西）；2 用法錯誤。
"""
import hashlib
import json
import os
import sys
import tempfile

META_KEY = "translation_source"


def fail(msg, code=1):
    sys.stderr.write("停下：%s\n" % msg)
    sys.exit(code)


class DuplicateKey(ValueError):
    pass


def no_duplicates(pairs):
    keys = [k for k, _ in pairs]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        raise DuplicateKey("物件裡有重複的鍵 %s" % dup)
    return dict(pairs)


def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=no_duplicates)
    except (OSError, ValueError) as e:
        fail("讀不到%s %s：%s" % (what, path, e))


def cell_text(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def fingerprint(nb):
    """原稿指紋：只看各 cell 的類型與 source，outputs 與 metadata 的變動不影響。"""
    data = [[c.get("cell_type"), cell_text(c)] for c in nb.get("cells", [])]
    return hashlib.sha256(json.dumps(data, ensure_ascii=False).encode("utf-8")).hexdigest()


def load_patch(path, n):
    data = load_json(path, " patch")
    out = {}
    if isinstance(data, dict):
        items = list(data.items())
    elif isinstance(data, list):
        items = []
        for item in data:
            if not isinstance(item, dict) or set(item) != {"index", "source"}:
                fail("patch 的清單形式每一項都要正好是 {\"index\": …, \"source\": …}")
            items.append((item["index"], item["source"]))
    else:
        fail("patch 要是物件或清單")
    for k, v in items:
        if isinstance(k, bool) or not ((isinstance(k, int) and k >= 0) or (isinstance(k, str) and k.isdigit())):
            fail("patch 的 index 要是非負整數：%r" % (k,))
        i = int(k)
        if i in out:
            fail("patch 的 index %d 重複" % i)
        if not isinstance(v, str):
            fail("patch 第 %d 格的內容要是字串（不是 %s）" % (i, type(v).__name__))
        if i >= n:
            fail("patch 的 index %d 超出範圍（notebook 有 %d 格）" % (i, n))
        out[i] = v
    return out


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows 的管道或非 UTF-8 主控台下也能印中文
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if len(args) != 3 or any(f not in ("--continue", "--accept-source-change") for f in flags):
        sys.stderr.write(__doc__)
        sys.exit(2)
    cont, accept = "--continue" in flags, "--accept-source-change" in flags
    src_path, patch_path, out_path = args
    if os.path.abspath(src_path) == os.path.abspath(out_path):
        fail("原稿與譯本是同一個檔案")

    src_nb = load_json(src_path, "原稿")
    cells = src_nb.get("cells")
    if not isinstance(cells, list):
        fail("原稿沒有 cells 清單")
    n = len(cells)
    fp = fingerprint(src_nb)

    if os.path.exists(out_path):
        if not cont:
            fail("譯本 %s 已存在；續譯請加 --continue" % out_path)
        nb = load_json(out_path, "譯本")
        if [c.get("cell_type") for c in nb.get("cells", [])] != [c.get("cell_type") for c in cells]:
            fail("譯本與原稿的 cell 數或類型序列不同（譯本 %d 格、原稿 %d 格），不是同一份原稿的譯本"
                 % (len(nb.get("cells", [])), n))
        recorded = (nb.get("metadata", {}).get(META_KEY) or {}).get("fingerprint")
        if recorded != fp and not accept:
            fail("原稿的指紋與譯本記下的不同（%s → %s）：原稿在上一批之後改過，或譯本不是用本工具建立的。"
                 "先比對原稿的差異、重新驗證受影響的批次，再加 --accept-source-change" % (recorded, fp))
        base = out_path
    else:
        if cont:
            fail("譯本 %s 不存在，不能續譯；新建請去掉 --continue" % out_path)
        nb = json.loads(json.dumps(src_nb))
        base = src_path

    patch = load_patch(patch_path, n)
    for i, text in patch.items():
        nb["cells"][i]["source"] = text.splitlines(keepends=True)
    nb.setdefault("metadata", {})[META_KEY] = {"file": os.path.basename(src_path), "fingerprint": fp}

    d = os.path.dirname(os.path.abspath(out_path))
    try:
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".nb_apply-", suffix=".ipynb", dir=d)
    except OSError as e:
        fail("建不了輸出目錄或臨時檔：%s（譯本沒有改動）" % e)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, out_path)
    except Exception as e:  # noqa: BLE001
        try:
            os.unlink(tmp)
        except OSError:
            pass
        fail("寫出失敗：%s（譯本沒有改動）" % e)
    print("基底=%s → 寫出 %s（%d 格，本批套用 %d 格：%s）" % (base, out_path, n, len(patch), sorted(patch)))


if __name__ == "__main__":
    main()
