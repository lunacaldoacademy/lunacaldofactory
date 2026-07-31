# ルナカルド工房 公式サイト

https://lunacaldofactory.com/

1ページ完結の静的サイト。ビルドツールも npm も使いません。ファイルを直接編集して push すると、そのまま公開されます。

姉妹サイト [ルナカルドアカデミー](https://lunacaldoacademy.com/) と同じ作りです。設計・公開手順はそちらを踏襲しています。

---

## ファイルの役割

| ファイル | 役割 |
|---|---|
| `index.html` | ページの全内容。文章はすべてここにあります |
| `css/style.css` | 見た目のすべて |
| `js/main.js` | スライドショー・スクロール演出など。**触らないでください** |
| `img/` | 公開用の画像。**スクリプトが作り直すので手で置かないでください** |
| `img-src/hero/` | トップのスライドに使う写真（ここに入れる） |
| `img-src/lib/` | 決まった場所で使う写真（ここに入れる） |
| `tools/optimize_images.py` | 写真を軽くして `img/` に書き出す |
| `tools/bump_assets.py` | CSS/JS の更新をブラウザに確実に伝える |
| `robots.txt` / `sitemap.xml` | 検索エンジン向け |

---

## どこを直せばいいか

`index.html` は `<!-- ===== 4. 作品のかたち ===== -->` のような見出しコメントで区切ってあります。直したい場所のコメントを探してください。

| 直したいもの | 見出しコメント |
|---|---|
| トップの写真・キャッチコピー | `1. ヒーロー` |
| 「ひとつずつ、手で仕上げています」の文章と3つの心がけ | `2. 大切にしていること` |
| 流れる写真（6枚） | `3. ギャラリー` |
| 作品3種の紹介 | `4. 作品のかたち` |
| オーダーの5ステップ | `5. オーダーの流れ` |
| 作り手の自己紹介 | `6. 作り手について` |
| 素材の話とお手入れの三箇条 | `7. 素材とお手入れ` |
| Creema / minne のリンク | `8. ショップ` |
| よくあるご質問 | `9. よくあるご質問` |
| 連絡先・地図 | `10. ご相談・アクセス` |
| 電話番号・住所・姉妹サイト | `フッター` |
| スマホ下部のボタン | `スマホ固定CTA` |

### 触らないところ

- `img/` の中身（`tools/optimize_images.py` が作り直します）
- `<!-- HERO-SLIDES:START -->` 〜 `<!-- HERO-SLIDES:END -->` の間（自動生成）
- `js/main.js`

### 元に戻したいとき

```bash
git restore .
```

---

## 表現のルール

正本は `sns-bot/src/factory/brand.py` の `SHOP_INFO` です。Instagram の投稿文と同じルールで書きます。

- **一人称は「わたし」または無し。**「わたしたち」「私たち」「弊店」「当店」は使いません（個人でやっているため）
- **ウォルナット／メープル／マホガニーは色の名前であって、素材の名前ではありません**
  - ✕ ウォルナット材のネームプレート
  - ○ 木のプレート／深い色合いの木のプレート
  - 木は「木」「木材」、革は「革」。ナラ・ヒノキなど具体的な樹種が分かっているときだけ樹種名を書いてよい
- **素材を選べるとは書きません**（「素材をお選びいただけます」✕）。相談できるのは**書体・サイズ・レイアウト**まで
- **価格はどこにも載せません**（構造化データの `priceRange` も入れない）。価格は Creema / minne で見てもらう
- 使わない言葉
  - 大げさな称賛：最高／最強／神／すごい
  - 保証めいた表現：絶対／必ず／間違いない
  - 煽り：お得／激安／限定◯個
  - 「月替わり」（アカデミーと共通の方針）
  - 競合店の名前、お客さまの本名・住所
- です・ます調。短い文で余韻を残す。説明し尽くさない

### 事実（勝手に変えない）

| 項目 | 値 |
|---|---|
| 屋号 | ルナカルド工房（英字 Lunacaldo Factory） |
| 工房 | 〒587-0002 大阪府堺市美原区黒山422-1 **カフェルナカルド 1階** |
| 電話 | 080-4249-3221 |
| Instagram | https://www.instagram.com/lunacaldo_factory/ （@lunacaldo_factory） |
| 販売 | Creema（メイン）／ minne |
| 姉妹サイト | [カフェルナカルド](https://cafelunacaldo.com/) ／ [ルナカルドアカデミー](https://lunacaldoacademy.com/) |

> 住所は 2階 から **1階** に移りました。アカデミーの教室は 2階 のままなので混同しないこと。
> `index.html` では フッター・アクセス・構造化データ の3か所に住所があります。直すときは全部そろえてください。

### FAQ を直すとき

`<details>` の文章と、`<head>` の `FAQPage` 構造化データは**同じ内容**にしておく必要があります。片方だけ直さないでください。

---

## 写真を入れ替える

### トップのスライド

1. `img-src/hero/` に `01_木のキーホルダー.jpeg` のように **連番＋アンダーバー＋説明** の名前で置く
   - **`_` より後ろの文字がそのまま alt（画像の説明）になります**
   - 並び順はファイル名順。枚数は自由
2. 下のコマンドを実行すると `img/hero-01.jpg` などが作られ、`index.html` のスライド部分も自動で書き換わります

### 決まった場所の写真

`img-src/lib/` に、下の名前で置いてください（拡張子は何でも可）。

| ファイル名 | 使う場所 | 切り抜かれる比率 |
|---|---|---|
| `atelier` | 「大切にしていること」の写真 | 正方形 |
| `gallery-01` 〜 `gallery-06` | 流れるギャラリー | 正方形 |
| `work-gift` / `work-memorial` / `work-daily` | 作品カード3枚 | 正方形 |
| `maker` | 作り手の写真 | 縦4:5 |
| `material` | 「素材とお手入れ」の写真 | 正方形 |
| `texture` | 「ご相談」の背景 | 横3:2 |
| `_logo-source.png` | ロゴ（先頭の `_` は「一括処理から外す」印） | そのまま |

比率は `tools/optimize_images.py` の `LIB_SIZES` で決めています。`index.html` の `width` / `height` と揃えてあるので、変えるときは両方直してください。

### 実行

```bash
python tools/optimize_images.py
```

ロゴから favicon と OGP画像（SNSで共有したときのカード）も一緒に作られます。

iPhone の `.heic` を読ませたいときは、一度だけ:

```bash
pip install pillow-heif
```

---

## 更新して公開する

CSS か JS を変えたときだけ実行（ブラウザが古い見た目を使い回すのを防ぎます）:

```bash
python tools/bump_assets.py
```

そのあと:

```bash
git add . && git commit -m "変更内容" && git push
```

1〜2分で反映されます。

### 手元で確認する

```bash
python -m http.server 8000
```

http://localhost:8000 を開いてください。地図が `file://` では表示されないため、確認はこの方法で行います。

---

## 公開の仕組み

| 項目 | 値 |
|---|---|
| URL | https://lunacaldofactory.com/ |
| ホスティング | Cloudflare Pages（プロジェクト `lunacaldofactory-site`） |
| ビルド設定 | Framework preset `None` ／ Build command **空** ／ Output directory `/` |
| ドメイン | Cloudflare Registrar（アカデミー・カフェと同じアカウント） |
| SSL | Cloudflare 自動 |

### DNS（どちらも Proxied ／ オレンジ雲）

```
lunacaldofactory.com   CNAME   lunacaldofactory-site.pages.dev   Proxied   Auto
www                    CNAME   lunacaldofactory-site.pages.dev   Proxied   Auto
```

`www` から本体への転送は Cloudflare の **Rules → Redirect Rules** で作ります（301・クエリ文字列は保持）。アカデミーの "Redirect from WWW to root" と同じ設定です。

### Cloudflare の設定

- **Web Analytics: ON**（Cookie を使わないので同意バナーは不要）
- **Email Address Obfuscation: OFF**（このサイトはメールアドレスを載せていないため影響はないが、アカデミーと揃えておく）

### 検索エンジン

Google Search Console には **ドメインプロパティ**で登録します（http/https/www をまとめて扱えるため）。Cloudflare に `TXT google-site-verification=...` のレコードを追加します。**このレコードは消さないでください。**

サイトマップは省略形ではなく完全な URL で送信します:

```
https://lunacaldofactory.com/sitemap.xml
```

---

## ドメインを変えるとき

次の場所をすべて直します。

- `index.html` … `canonical` / `og:url` / `og:image` / 構造化データの `@id`・`url`・`logo`・`image`
- `sitemap.xml` … `<loc>`
- `robots.txt` … `Sitemap:`
- Cloudflare Pages のカスタムドメイン、DNS、リダイレクトルール
- このREADME
