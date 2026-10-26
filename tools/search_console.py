"""Search Console の検索成績を取ってきて、表にして見せる。

    python tools/search_console.py                      # 工房サイト・直近28日・検索語ごと
    python tools/search_console.py --site cafe          # カフェサイト
    python tools/search_console.py --by page            # ページごと
    python tools/search_console.py --days 90 --limit 50

鍵のファイル（サービスアカウントの JSON）は既定で

    .secrets/search-console-key.json

を見る。--key で別の場所も指せる。このファイルは絶対に git に入れないこと
（.gitignore に入れてある）。鍵の中身を画面に出すこともしない。

取れる数字の意味:
  表示回数  検索結果にこのサイトが出た回数
  クリック  実際に押された回数
  CTR       クリック ÷ 表示回数
  掲載順位  検索結果の平均の順位（小さいほど上）
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# Windows のコンソールは既定が cp932 で、日本語を出すと落ちることがある
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEY = ROOT / ".secrets" / "search-console-key.json"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
API = "https://searchconsole.googleapis.com/webmasters/v3"

# 4つのドメイン。ドメインプロパティ（sc-domain:）で登録している前提
SITES = {
    "factory": "sc-domain:lunacaldofactory.com",
    "cafe":    "sc-domain:cafelunacaldo.com",
    "academy": "sc-domain:lunacaldoacademy.com",
    "hub":     "sc-domain:lunacaldo.com",
}


def token(key_path: Path) -> str:
    if not key_path.exists():
        sys.exit(
            f"鍵のファイルが見つかりません: {key_path}\n"
            "Google Cloud で作ったサービスアカウントの JSON を、この場所に置いてください。"
        )
    creds = service_account.Credentials.from_service_account_file(
        str(key_path), scopes=[SCOPE]
    )
    creds.refresh(Request())
    return creds.token


def query(site: str, bearer: str, start: date, end: date,
          dims: list[str], limit: int) -> list[dict]:
    res = requests.post(
        f"{API}/sites/{requests.utils.quote(site, safe='')}/searchAnalytics/query",
        headers={"Authorization": f"Bearer {bearer}"},
        json={
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": dims,
            "rowLimit": limit,
        },
        timeout=60,
    )
    if res.status_code == 403:
        sys.exit(
            f"このプロパティを読む権限がありません: {site}\n"
            "Search Console の「設定 → ユーザーと権限」で、サービスアカウントの\n"
            "メールアドレスを『制限付き』で追加してください。"
        )
    if res.status_code != 200:
        sys.exit(f"API がエラーを返しました（{res.status_code}）:\n{res.text[:500]}")
    return res.json().get("rows", [])


def show(rows: list[dict], label: str) -> None:
    if not rows:
        print("  データがありません。期間を延ばすか、登録直後なら数日待ってください。")
        return
    w = max(len(label), *(width(r["keys"][0]) for r in rows))
    print(f"  {label.ljust(w)}  表示   クリック   CTR    掲載順位")
    print("  " + "-" * (w + 34))
    for r in rows:
        k = r["keys"][0]
        pad = " " * (w - width(k))
        print(f"  {k}{pad}  {r['impressions']:>5.0f}  {r['clicks']:>7.0f}  "
              f"{r['ctr']*100:>5.1f}%  {r['position']:>7.1f}")


def width(s: str) -> int:
    """全角を2、半角を1として数える（表の桁をそろえるため）。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in "FWA" else 1 for c in s)


def main() -> None:
    p = argparse.ArgumentParser(description="Search Console の検索成績を表示する")
    p.add_argument("--site", default="factory",
                   help=f"{' / '.join(SITES)} のいずれか、または sc-domain:... を直接")
    p.add_argument("--by", default="query",
                   choices=["query", "page", "country", "device", "date"],
                   help="何ごとに集計するか（既定: query＝検索語）")
    p.add_argument("--days", type=int, default=28, help="さかのぼる日数（既定: 28）")
    p.add_argument("--limit", type=int, default=25, help="表示する行数（既定: 25）")
    p.add_argument("--key", type=Path, default=DEFAULT_KEY, help="鍵ファイルの場所")
    p.add_argument("--json", action="store_true", help="生のJSONで出す")
    a = p.parse_args()

    site = SITES.get(a.site, a.site)
    # Search Console のデータは2〜3日遅れて入るため、終わりを3日前にする
    end = date.today() - timedelta(days=3)
    start = end - timedelta(days=a.days)

    rows = query(site, token(a.key), start, end, [a.by], a.limit)

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return

    label = {"query": "検索語", "page": "ページ", "country": "国",
             "device": "端末", "date": "日付"}[a.by]
    print(f"\n{site}　{start} 〜 {end}（{a.days}日間）\n")
    show(rows, label)
    tot_i = sum(r["impressions"] for r in rows)
    tot_c = sum(r["clicks"] for r in rows)
    print(f"\n  上位{len(rows)}件の合計: 表示 {tot_i:.0f} 回 / クリック {tot_c:.0f} 回\n")


if __name__ == "__main__":
    main()
