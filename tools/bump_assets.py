"""CSS / JS の読み込みURLに、中身から計算した符号を付け直す。

ブラウザは一度読んだ CSS や JS をしばらく使い回すため、ファイルを更新しても
古いままの見た目が表示されることがある（キャッシュ）。
読み込みURLの末尾を `style.css?v=a1b2c3d4` のように変えると、ブラウザは
別のファイルだと判断して必ず読み直す。

日付ではなく中身のハッシュを使っているので、

  - 中身を変えたときだけ符号が変わる（更新し忘れが起きない）
  - 中身が同じなら符号も同じ（不要な再ダウンロードが起きない）

使い方（HP フォルダで実行）:

    python tools/bump_assets.py

CSS や JS を編集したあと、コミットする前に一度実行してください。
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HP = Path(__file__).resolve().parent.parent

# 符号を書き換える HTML。ページを増やしたら、ここに足すこと。
# 足し忘れると、そのページだけ古い CSS のまま表示される。
PAGES = [
    HP / "index.html",
    HP / "novelty" / "index.html",
]

# 符号を付ける対象。(HTML内のパス, 実ファイル)
# 下層ページは "/css/style.css" と先頭に / を付けて書くので、
# 探すときは先頭の / の有無を問わず拾い、書き戻すときは元の形を保つ。
TARGETS = [
    ("css/style.css", HP / "css" / "style.css"),
    ("js/main.js", HP / "js" / "main.js"),
]


def short_hash(path: Path) -> str:
    """ファイルの中身から8桁の符号を作る。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def main() -> None:
    digests: dict[str, str] = {}
    for url, path in TARGETS:
        if path.exists():
            digests[url] = short_hash(path)
        else:
            print(f"  [skip] {url} が見つかりません")

    updated = 0
    for page in PAGES:
        if not page.exists():
            print(f"  [skip] 見つかりません: {page}")
            continue

        label = page.relative_to(HP).as_posix()
        html = page.read_text(encoding="utf-8")
        original = html

        for url, digest in digests.items():
            # "css/style.css" も "/css/style.css?v=旧い符号" も拾う
            pattern = re.compile(r"(/?)" + re.escape(url) + r"(\?v=[0-9a-f]+)?")

            found = pattern.search(html)
            if not found:
                print(f"  [skip] {label} に {url} の読み込みが見つかりません")
                continue

            before = found.group(2) or "（符号なし）"
            # 先頭の / は元の形のまま残す
            html = pattern.sub(lambda m: f"{m.group(1)}{url}?v={digest}", html)

            if before == f"?v={digest}":
                print(f"  {label} / {url}: 変更なし（?v={digest}）")
            else:
                print(f"  {label} / {url}: {before} -> ?v={digest}")

        if html != original:
            page.write_text(html, encoding="utf-8")
            updated += 1

    if updated:
        print(f"\n完了 -> {updated} ページを更新しました")
    else:
        print("\n更新の必要はありませんでした")


if __name__ == "__main__":
    main()
