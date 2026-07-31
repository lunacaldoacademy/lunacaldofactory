"""ルナカルド工房 公式サイト用 画像最適化スクリプト

img-src/ に置いた元画像を読み取り、Web配信用に軽量化して img/ に書き出す。

  img-src/hero/ … トップのスライドショー（ファイル名順に表示。枚数自由）
  img-src/lib/  … 作品カード・作り手写真・背景など、決まった場所で使う画像

トップのスライドは img-src/hero/ の中身に合わせて index.html も自動で書き換える。

使い方:
    python tools/optimize_images.py

出力:
    img/hero-01.webp / .jpg …  トップのスライド（ファイル名順）
    img/<lib名>.webp / .jpg  …  その他の画像
    img/logo.png / favicon.png / ogp.jpg
"""
from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

# iPhoneのHEICも読めるようにする（入っていなければ黙って諦める）
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF_OK = True
except ImportError:
    HEIF_OK = False

HERE = Path(__file__).resolve().parent
HP = HERE.parent
HERO_SRC = HP / "img-src" / "hero"
LIB_SRC = HP / "img-src" / "lib"
LOGO_SRC = HP / "img-src" / "lib" / "_logo-source.png"
OUT = HP / "img"
INDEX = HP / "index.html"

WEBP_QUALITY = 82
JPEG_QUALITY = 85
LIB_MAX_EDGE = 1000       # ライブラリ画像の長辺上限

# トップのスライド。4:3 に切り抜いて統一する
HERO_W, HERO_H = 1400, 1050
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

# 変換せずそのままコピーするもの
COPY_AS_IS: set[str] = set()
# 透明背景を保持すべきファイル（WebP のみ出力、JPEG フォールバックなし）
TRANSPARENT_BG: set[str] = set()
# アンダーバー始まりのファイルは lib の一括処理から除外する（ロゴなど個別に扱うもの）

# 置き場所が決まっている画像は、index.html の width/height と一致させるため
# 縦横比を指定して切り抜く（object-fit: cover 相当）。
# ここに無い画像は長辺 LIB_MAX_EDGE に収めるだけで、比率はそのまま。
LIB_SIZES: dict[str, tuple[int, int]] = {
    "atelier":       (1000, 1000),   # 「大切にしていること」の写真
    "gallery-01":    (1000, 1000),   # 流れるギャラリー（9枚）
    "gallery-02":    (1000, 1000),
    "gallery-03":    (1000, 1000),
    "gallery-04":    (1000, 1000),
    "gallery-05":    (1000, 1000),
    "gallery-06":    (1000, 1000),
    "gallery-07":    (1000, 1000),
    "gallery-08":    (1000, 1000),
    "gallery-09":    (1000, 1000),
    "work-gift":     (1000, 1000),   # 作品カード（3枚）
    "work-memorial": (1000, 1000),
    "work-daily":    (1000, 1000),
    "maker":         (800, 1000),    # 作り手の写真（縦4:5）
    "material":      (1000, 1000),   # 素材とお手入れの写真
    "texture":       (1000, 667),    # ご相談セクションの背景
}

# ブランドカラー（sns-bot/src/factory/brand.py が正本）
C_INK = (14, 11, 8)        # BLACK  #0E0B08
C_PAPER = (247, 244, 238)  # WHITE  #F7F4EE
C_MAHOGANY = (116, 44, 15)  # MAHOGANY #742C0F
C_MAPLE = (212, 165, 116)  # MAPLE  #D4A574
C_MUTED = (142, 131, 119)

# 見出しは明朝（サイトのタイポグラフィに合わせる）。無ければゴシックに落ちる
FONT_MINCHO = [
    r"C:\Windows\Fonts\yumindb.ttf",
    r"C:\Windows\Fonts\yumin.ttf",
    r"C:\Windows\Fonts\msmincho.ttc",
]
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\YuGothR.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
]


def load_font(size: int, mincho: bool = False) -> ImageFont.FreeTypeFont:
    paths = (FONT_MINCHO + FONT_CANDIDATES) if mincho else FONT_CANDIDATES
    for path in paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------- 共通処理

def open_image(path: Path) -> Image.Image:
    """画像を開き、写真の「向き」の情報を実際の画素に反映させる。

    スマホやパソコンの写真アプリで画像を回転させると、多くの場合
    画素はそのままで Exif の Orientation という札だけが書き換わる。
    写真アプリはその札を見て回して表示するが、そのまま読み込むと
    札は無視され、回す前の向きで書き出されてしまう。
    exif_transpose で札のとおりに回してから扱う。
    """
    return ImageOps.exif_transpose(Image.open(path))


def flatten(img: Image.Image) -> Image.Image:
    """アルファを白背景に合成して RGB 化（JPEG 出力用）。"""
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def fit(img: Image.Image, max_edge: int) -> Image.Image:
    """長辺を max_edge に収める（拡大はしない）。"""
    w, h = img.size
    scale = min(1.0, max_edge / max(w, h))
    if scale >= 1.0:
        return img
    return img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)


def crop_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """中央基準で w:h の比率に切り抜き、w×h にそろえる（object-fit: cover 相当）。"""
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_w = round(img.height * dst_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    elif src_ratio < dst_ratio:
        new_h = round(img.width / dst_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    return img.resize((w, h), Image.LANCZOS)


def save_pair(img: Image.Image, stem: str, jpg_fallback: bool = True) -> tuple[int, int]:
    webp = OUT / f"{stem}.webp"
    img.save(webp, "WEBP", quality=WEBP_QUALITY, method=6)
    kb_webp = webp.stat().st_size // 1024
    if jpg_fallback:
        jpg = OUT / f"{stem}.jpg"
        img_rgb = img.convert("RGB") if img.mode == "RGBA" else img
        img_rgb.save(jpg, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        kb_jpg = (OUT / f"{stem}.jpg").stat().st_size // 1024
    else:
        kb_jpg = 0
    return kb_webp, kb_jpg


def sorted_photos(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    files, skipped = [], []
    for f in sorted(folder.iterdir(), key=lambda p: unicodedata.normalize("NFC", p.name)):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext not in PHOTO_EXTS:
            continue
        if ext in (".heic", ".heif") and not HEIF_OK:
            skipped.append(f.name)
            continue
        files.append(f)
    if skipped:
        print("  [注意] HEIC形式のため読み込めませんでした:", ", ".join(skipped))
        print("         `pip install pillow-heif` を一度実行すると読めるようになります")
    return files


# ---------------------------------------------------------------- トップのスライド

def alt_from_filename(path: Path) -> str:
    """`01_木のネームプレート.jpg` -> `木のネームプレート`"""
    stem = path.stem
    if "_" in stem:
        stem = stem.split("_", 1)[1]
    return stem.strip() or "ルナカルド工房の作品"


def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def export_hero() -> list[dict]:
    sources = sorted_photos(HERO_SRC)
    if not sources:
        print("  [skip] img-src/hero/ に画像がありません。トップ画像は変更しません")
        return []

    for pattern in ("hero-*.webp", "hero-*.jpg"):
        for old in OUT.glob(pattern):
            old.unlink()

    slides = []
    for i, src in enumerate(sources, start=1):
        img = crop_cover(flatten(open_image(src)), HERO_W, HERO_H)
        stem = f"hero-{i:02d}"
        kb_webp, kb_jpg = save_pair(img, stem)
        slides.append({"stem": stem, "alt": alt_from_filename(src)})
        print(f"  {stem}: {src.name} -> webp {kb_webp}KB / jpg {kb_jpg}KB")
    return slides


def update_hero_slides(slides: list[dict]) -> None:
    """index.html のスライド部分（マーカーの間）を書き換える。"""
    if not slides or not INDEX.exists():
        return

    start = "<!-- HERO-SLIDES:START"
    end = "<!-- HERO-SLIDES:END -->"
    html = INDEX.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(html):
        print("  [skip] index.html にスライドのマーカーが見つかりません")
        return

    lines = [start + " ここから img-src/hero/ をもとに tools/optimize_images.py が"
                     "自動生成します。手で書き換えないでください -->"]
    for i, s in enumerate(slides):
        current = " is-current" if i == 0 else ""
        loading = ' fetchpriority="high"' if i == 0 else ' loading="lazy"'
        alt = escape_html(s["alt"])
        lines += [
            f'      <figure class="hero__slide{current}">',
            '        <picture>',
            f'          <source srcset="img/{s["stem"]}.webp" type="image/webp">',
            f'          <img src="img/{s["stem"]}.jpg" width="{HERO_W}" height="{HERO_H}"'
            f' alt="{alt}"{loading}>',
            '        </picture>',
            '      </figure>',
        ]
    lines.append("      " + end)

    INDEX.write_text(pattern.sub("\n".join(lines), html), encoding="utf-8")
    print(f"  index.html のスライドを {len(slides)} 枚に更新しました")


# ---------------------------------------------------------------- ライブラリ画像

def export_lib() -> None:
    if not LIB_SRC.exists():
        print("  [skip] img-src/lib/ がありません")
        return
    for src in sorted(LIB_SRC.iterdir(), key=lambda p: p.name):
        if not src.is_file() or src.name.startswith("_"):
            continue
        if src.name in COPY_AS_IS:
            shutil.copyfile(src, OUT / src.name)
            print(f"  {src.name}（無変換コピー）")
            continue
        if src.suffix.lower() not in PHOTO_EXTS:
            continue
        src_img = open_image(src)
        # 透明背景を保持すべき画像か判定
        keep_transparent = src.stem in TRANSPARENT_BG
        if keep_transparent:
            img = fit(src_img, LIB_MAX_EDGE)
            kb_webp, kb_jpg = save_pair(img, src.stem, jpg_fallback=False)
            print(f"  {src.stem}: {img.size[0]}x{img.size[1]} -> webp {kb_webp}KB")
            continue

        size = LIB_SIZES.get(src.stem)
        if size:
            # index.html の width/height と一致させるため決め打ちで切り抜く
            img = crop_cover(flatten(src_img), *size)
        else:
            img = fit(flatten(src_img), LIB_MAX_EDGE)
        kb_webp, kb_jpg = save_pair(img, src.stem)
        print(f"  {src.stem}: {img.size[0]}x{img.size[1]} "
              f"-> webp {kb_webp}KB / jpg {kb_jpg}KB")

    missing = [k for k in LIB_SIZES if not (OUT / f"{k}.jpg").exists()]
    if missing:
        print("  [注意] index.html が参照しているのに未作成の画像:",
              ", ".join(sorted(missing)))


# ---------------------------------------------------------------- ロゴ・アイコン

def cut_out_background(img: Image.Image) -> Image.Image:
    """四隅から連結した白地だけを透過にする（文字の白フチは残る）。"""
    rgb = img.convert("RGB")
    marker = (255, 0, 255)
    w, h = rgb.size
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if rgb.getpixel(corner) == marker:
            continue
        ImageDraw.floodfill(rgb, corner, marker, thresh=24)
    alpha = Image.new("L", rgb.size, 255)
    px_rgb, px_a = rgb.load(), alpha.load()
    for y in range(h):
        for x in range(w):
            if px_rgb[x, y] == marker:
                px_a[x, y] = 0
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def export_logo() -> Image.Image | None:
    """ロゴを透過のまま書き出す（余白を詰める）。

    工房のロゴは生成り色の円に黒の文字で、四隅は透明。
    RGB に落とすと四隅が黒くなり、ヘッダーで四角い影として見えてしまうため
    アルファを保ったまま PNG で保存する。
    """
    if not LOGO_SRC.exists():
        print("  [skip] ロゴが見つかりません:", LOGO_SRC)
        return None
    img = open_image(LOGO_SRC).convert("RGBA")
    img = fit(img, 600)
    img.save(OUT / "logo.png", "PNG", optimize=True)
    print(f"  logo.png: {img.size[0]}x{img.size[1]} "
          f"{(OUT / 'logo.png').stat().st_size // 1024}KB")
    return img


def export_favicon(logo: Image.Image) -> None:
    """ロゴを正方形の黒地に置いてファビコンにする。"""
    pad = round(max(logo.size) * 0.08)
    side = max(logo.size) + pad * 2
    canvas = Image.new("RGB", (side, side), C_INK)
    pos = ((side - logo.width) // 2, (side - logo.height) // 2)
    canvas.paste(logo, pos, logo if logo.mode == "RGBA" else None)
    canvas.resize((180, 180), Image.LANCZOS).save(OUT / "favicon.png", "PNG", optimize=True)
    print("  favicon.png: 180x180")


def export_ogp() -> None:
    """SNS共有用 OGP 画像（1200x630）。黒基調でサイトの世界観に合わせる。"""
    W, H = 1200, 630
    canvas = Image.new("RGB", (W, H), C_INK)

    # 背景に1枚目のトップ画像を薄く敷く
    hero = OUT / "hero-01.jpg"
    if hero.exists():
        bg = crop_cover(Image.open(hero).convert("RGB"), W, H)
        overlay = Image.new("RGB", (W, H), C_INK)
        # 作品写真は明るいものが多いので、アカデミー（0.74）より強めに沈める。
        # 下段の --muted 色の文字が読める濃さがこのあたり
        canvas = Image.blend(bg, overlay, 0.84)

    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, 5], fill=C_MAHOGANY)

    f_kicker = load_font(26)
    f_main = load_font(62, mincho=True)
    f_sub = load_font(28, mincho=True)
    f_foot = load_font(24)

    d.text((80, 128), "レーザー彫刻の工房", font=f_kicker, fill=C_MAPLE)
    d.text((80, 196), "贈るひとを想って、", font=f_main, fill=C_PAPER)
    d.text((80, 284), "ひとつだけを刻む", font=f_main, fill=C_PAPER)

    d.line([(80, 404), (176, 404)], fill=C_MAHOGANY, width=3)
    d.text((80, 428), "ルナカルド工房 ／ 大阪・堺市美原区", font=f_sub, fill=C_PAPER)
    d.text((80, 522), "木と革の名入れ・記念品・1点もの　オーダー承ります",
           font=f_foot, fill=C_MUTED)

    canvas.save(OUT / "ogp.jpg", "JPEG", quality=88, optimize=True, progressive=True)
    print(f"  ogp.jpg: 1200x630 {(OUT / 'ogp.jpg').stat().st_size // 1024}KB")


# ---------------------------------------------------------------- 実行

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    print("トップのスライド:")
    update_hero_slides(export_hero())
    print("ライブラリ画像:")
    export_lib()
    print("ロゴ・アイコン:")
    logo = export_logo()
    if logo is not None:
        export_favicon(logo)
    export_ogp()
    print(f"\n完了 -> {OUT}")


if __name__ == "__main__":
    main()
