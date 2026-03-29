"""
商品データからHugo用のMarkdown記事を自動生成するモジュール
テンプレートのバリエーションを用意し、重複コンテンツを回避する
"""

import os
import re
import random
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from config import Config

# 自サイトのURL（姉妹サイト相互リンク用）
CURRENT_SITE_URL = "https://musclelove-777.github.io/shiroto-squad/"


# ============================================================
# 記事テンプレート群（バリエーションで重複コンテンツを回避）
# ============================================================

# CSSは使わず全てインラインスタイルで対応（テーマのCSS干渉を防止）
RESPONSIVE_CSS = ""

ARTICLE_TEMPLATES = [
    # テンプレートA: ストレート紹介型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["素人", "おすすめ"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


## {{ hook_title }}

{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### 素人作品の注目ポイント・商品情報

| 項目 | 内容 |
|------|------|
{% if price %}| 価格 | {{ price }} |
{% endif %}{% if maker %}| メーカー | {{ maker }} |
{% endif %}{% if series %}| シリーズ | {{ series }} |
{% endif %}{% if actresses %}| 出演 | {{ actresses }} |
{% endif %}

{{ body_text }}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートB: レビュー風型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["レビュー", "素人"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


{{ intro_text }}

<!--more-->

## リアルすぎるエロス！素人作品の見どころ

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

{{ body_text }}

{% if actresses %}
### 出演者について

{{ actresses }}さんが出演するこの作品。素人好きなら見逃せない一本です。
{% endif %}

{% if maker %}
> **{{ maker }}**からリリースされたこの作品は、素人・ハメ撮りジャンルで定評があります。
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートC: ランキング・おすすめ型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["ピックアップ", "注目作品"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


## 本日の素人作品ピックアップ

{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### この素人作品をおすすめする理由

{{ body_text }}

{% if price %}
**価格: {{ price }}** --- コスパも申し分なし！
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ related_section }}
"""),

    # テンプレートD: Q&A型
    Template("""---
title: "{{ title }}"
date: {{ date }}
tags: [{{ tags }}]
categories: ["素人", "よくある質問"]
draft: false
description: "{{ meta_description }}"
cover:
  image: "{{ image_url }}"
  alt: "{{ alt_text }}"
  hidden: false
---


{{ intro_text }}

<!--more-->

![{{ alt_text }}]({{ image_url }})

{{ sample_gallery }}

{{ sample_movie }}

### Q. どんな素人作品？

{{ body_text }}

### Q. 価格は？

{% if price %}{{ price }}で視聴できます。{% else %}詳細はリンク先でご確認ください。{% endif %}

{% if actresses %}
### Q. 誰が出演している？

{{ actresses }}さんが出演しています。
{% endif %}

{{ cta_section }}

---

{{ footer_brand }}

{{ sns_section }}

{{ related_section }}
"""),
]


# ============================================================
# 導入文のバリエーション
# ============================================================

INTRO_VARIATIONS = [
    "リアルすぎてヤバい...！**「{title}」**は{genre_text}好きにはたまらない一本です。",
    "素人好きにはたまらない...！**「{title}」**、{genre_text}好きなら絶対ハマる作品が来ました。",
    "{genre_text}で興奮したいならコレ！**「{title}」**がマジでおすすめ。",
    "話題沸騰中の**「{title}」**をピックアップ。{genre_text}のド直球素人作品です。",
    "**「{title}」**が気になってる人、正解です。{genre_text}ジャンルの中でもガチで抜ける素人作品。",
    "本日の厳選素人作品は**「{title}」**。{genre_text}好きの間で「神作品」と話題に。",
    "新着から見つけた掘り出し物！**「{title}」**、{genre_text}がたっぷり詰まったリアルな一本です。",
    "サンプル動画だけでも興奮必至！**「{title}」**は{genre_text}の最高傑作かも。",
    "今週一番シコれる素人作品はコレ。**「{title}」**、{genre_text}好きは見逃すな！",
    "MuscleLoveが厳選！**「{title}」**は{genre_text}好きなら見逃せない素人作品です。",
    "MuscleLove編集部おすすめの**「{title}」**。{genre_text}ジャンルで今一番アツい素人作品。",
    "MuscleLoveイチオシ！**「{title}」**、{genre_text}好きを唸らせる最高の素人作品が来ました。",
]

BODY_VARIATIONS = [
    "カメラワークが絶妙で、素人ならではのリアルなリアクションを余すところなく映し出しています。特に生々しさとエロさの両立が素晴らしい。抜きどころ満載の一本。",
    "序盤からテンション高めの展開で、一気に引き込まれます。素人ならではの初々しさと大胆さが入り混じる濃厚な絡みシーンは、何度もリピートしたくなるクオリティ。",
    "とにかくシチュエーションが最高。ハメ撮りのリアル感が際立つ演出で、見応え抜群です。サンプル動画でその片鱗を確認してみてください。",
    "完成度が高く、素人ジャンルの魅力が全開。展開のバリエーションも豊富で飽きることなく最後まで楽しめる作品です。リピート確定レベル。",
    "映像のクオリティが高く、素人の自然な表情や空気感がしっかり映えています。オカズとしてもコレクションとしても満足度の高い一本。",
    "素人好きなら間違いなく刺さる作品。リアルな臨場感・カメラアングル・ドキドキ感、すべてが高水準でまとまっています。",
    "抜けるかどうかで言えば、間違いなく抜ける。素人ならではのリアル感と、ここぞという場面のねっとり感のバランスが絶妙です。",
]

HOOK_TITLES = [
    "今夜のリアルタイムはコレで決まり",
    "素人好き必見の抜けるおすすめ作品",
    "見逃し厳禁！リアル感MAXの素人作品",
    "素人AVの本日のシコネタ",
    "ガチで抜ける素人厳選ピックアップ",
    "素人サンプルを今すぐチェック",
    "リアル感がたまらない素人作品",
    "話題の素人系セクシー作品を紹介",
    "MuscleLoveのイチオシ素人作品",
    "MuscleLove厳選！今日の素人",
    "MuscleLoveが選ぶ注目のハメ撮り作品",
]


def generate_articles(
    products: list[dict],
    output_dir: str = "",
) -> list[str]:
    """
    商品データからHugo用Markdown記事を生成する

    Args:
        products: fetch_productsで取得した商品データリスト
        output_dir: 出力先ディレクトリ（空の場合はConfig.CONTENT_DIR）

    Returns:
        生成されたファイルパスのリスト
    """
    if not output_dir:
        output_dir = Config.CONTENT_DIR

    # 出力ディレクトリを作成
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    generated_files = []

    for i, product in enumerate(products):
        try:
            filepath = _generate_single_article(product, output_dir, i)
            if filepath:
                generated_files.append(filepath)
                print(f"[生成] {Path(filepath).name}")
        except Exception as e:
            print(f"[エラー] 記事生成に失敗: {product.get('title', '不明')} - {e}")

    print(f"\n[完了] {len(generated_files)}件の記事を生成しました → {output_dir}")
    return generated_files


def _generate_single_article(
    product: dict,
    output_dir: str,
    index: int,
) -> str:
    """
    1商品分の記事を生成する

    Args:
        product: 商品データ辞書
        output_dir: 出力先ディレクトリ
        index: 商品のインデックス（ファイル名衝突回避用）

    Returns:
        生成されたファイルパス
    """
    title = product.get("title", "タイトル不明")
    image_url = product.get("image_url", "")
    affiliate_url = product.get("affiliate_url", "")
    price = product.get("price", "")
    genres = product.get("genres", [])
    actresses = ", ".join(product.get("actresses", []))
    maker = product.get("maker", "")
    series = product.get("series", "")
    sample_images = product.get("sample_images", [])
    sample_movie_url = product.get("sample_movie_url", "")

    # 日付の整形（APIの日付 or 今日の日付）
    raw_date = product.get("date", "")
    article_date = _format_date(raw_date)

    # スラッグの生成
    slug = _make_slug(product.get("content_id", ""), index)

    # ファイル名
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_prefix}-{slug}.md"
    filepath = os.path.join(output_dir, filename)

    # 既存ファイルがあればスキップ
    if os.path.exists(filepath):
        print(f"[スキップ] 既に存在: {filename}")
        return ""

    # タグの生成
    tag_list = genres[:5] if genres else ["素人", "ハメ撮り"]
    tags = ", ".join(f'"{t}"' for t in tag_list)

    # ジャンルテキスト（導入文用）
    genre_text = "・".join(genres[:3]) if genres else "素人"

    # テンプレート変数の準備
    intro_text = random.choice(INTRO_VARIATIONS).format(
        title=_truncate(title, 40),
        genre_text=genre_text,
    )
    body_text = random.choice(BODY_VARIATIONS)
    hook_title = random.choice(HOOK_TITLES)
    meta_description = _build_meta_description(title, genre_text, actresses)

    # CTAセクションの生成
    cta_section = _build_cta(affiliate_url, title)

    # サンプル画像ギャラリー
    sample_gallery = _build_sample_gallery(sample_images)

    # サンプル動画セクション
    sample_movie = _build_sample_movie(sample_movie_url)

    # SNSリンクセクション
    sns_section = _build_sns_section()

    # フッターブランド表示
    footer_brand = _build_footer_brand()

    # 関連商品セクション
    related_section = _build_related_section()

    # alt属性テキストの生成（SEO向け具体的説明）
    alt_text = _build_alt_text(title, actresses, genre_text)

    # ランダムにテンプレートを選択
    template = random.choice(ARTICLE_TEMPLATES)

    # レンダリング
    content = template.render(
        title=_truncate(title, 60),
        date=article_date,
        tags=tags,
        meta_description=meta_description,
        hook_title=hook_title,
        intro_text=intro_text,
        image_url=image_url,
        body_text=body_text,
        price=price,
        maker=maker,
        series=series,
        actresses=actresses,
        alt_text=alt_text,
        cta_section=cta_section,
        sample_gallery=sample_gallery,
        sample_movie=sample_movie,
        sns_section=sns_section,
        footer_brand=footer_brand,
        related_section=related_section,
        responsive_css=RESPONSIVE_CSS,
    )

    # ファイル書き出し
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

    return filepath


def _format_date(raw_date: str) -> str:
    """常に生成時の今日の日付をHugo用のISO形式で返す（未来日付を防止）"""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")


def _make_slug(content_id: str, index: int) -> str:
    """URLスラッグを生成する"""
    if content_id:
        # 英数字とハイフンのみ残す
        slug = re.sub(r"[^a-zA-Z0-9]", "-", content_id).strip("-").lower()
        if slug:
            return slug
    return f"product-{index:03d}"


def _build_meta_description(title: str, genre_text: str, actresses: str) -> str:
    """SEOキーワードを自然に含んだmeta descriptionを生成する"""
    desc_variations = [
        f"{title}のサンプル動画・レビュー。素人・ハメ撮りの{genre_text}系作品を紹介。",
        f"素人好き必見の「{title}」を徹底レビュー。{genre_text}好きにおすすめのハメ撮りAV。",
        f"リアル感MAXの{genre_text}作品「{title}」。素人シチュエーションに興奮必至。",
        f"素人作品の注目作「{title}」。{genre_text}のハメ撮りシーンをサンプル動画付きで紹介。",
    ]
    if actresses:
        desc_variations.append(
            f"{actresses}出演「{title}」。{genre_text}系素人・ハメ撮り動画をチェック。"
        )
    desc = random.choice(desc_variations)
    return _truncate(desc, 155)


def _truncate(text: str, max_len: int) -> str:
    """テキストを指定文字数で切り詰める"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _build_alt_text(title: str, actresses: str, genre_text: str) -> str:
    """SEO向けの具体的なalt属性テキストを生成する"""
    alt_variations = [
        f"素人・ハメ撮り作品「{title}」のパッケージ画像",
        f"「{title}」{genre_text}系素人作品のサムネイル",
        f"リアル感がたまらない「{title}」の作品画像",
    ]
    if actresses:
        alt_variations.append(f"{actresses}出演「{title}」素人・ハメ撮り作品の画像")
    return _truncate(random.choice(alt_variations), 120)


def _build_cta(affiliate_url: str, title: str) -> str:
    """CTAボタンセクションを生成する"""
    if not affiliate_url:
        return ""

    cta_texts = [
        "サンプル動画を見る",
        "今すぐ抜きに行く",
        "この作品をチェック",
        "フル動画はこちら",
        "作品ページへGO",
    ]
    cta_text = random.choice(cta_texts)

    return f"""
<div style="text-align: center; margin: 2em 0;">
  <a href="{affiliate_url}" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 15px 40px; background: #e63946; color: #fff; text-decoration: none; border-radius: 8px; font-size: 1.1em; font-weight: bold;">
    {cta_text}
  </a>
  <p style="margin-top: 0.5em; font-size: 0.85em; color: #888;">※外部サイトに移動します</p>
</div>
"""


def _build_sample_gallery(sample_images: list[str]) -> str:
    """サンプル画像ギャラリーを生成する（最大6枚、インラインスタイル）"""
    if not sample_images:
        return ""

    images = sample_images[:6]

    gallery_html = """
### サンプル画像

<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 1em 0;">
"""
    for idx, img_url in enumerate(images, 1):
        gallery_html += f'  <a href="{img_url}" target="_blank" rel="nofollow"><img src="{img_url}" alt="素人・ハメ撮り作品のサンプル画像{idx}" style="width: 100%; border-radius: 4px;" loading="lazy" /></a>\n'

    gallery_html += "</div>\n"
    return gallery_html


def _build_sample_movie(sample_movie_url: str) -> str:
    """サンプル動画の埋め込みセクションを生成する"""
    if not sample_movie_url:
        return ""

    return f"""
### サンプル動画を見る

<div style="width: 100%; max-width: 560px; margin: 1.5em auto;">
  <iframe src="{sample_movie_url}" width="560" height="360" frameborder="0" allowfullscreen
          style="width: 100%; height: auto; aspect-ratio: 560/360; border-radius: 8px;"></iframe>
</div>
"""


def _build_sns_section() -> str:
    """SNSリンクセクションを生成する"""
    return """
### MuscleLove

<div style="display: flex; gap: 16px; flex-wrap: wrap; margin: 1.5em 0;">
  <a href="https://www.patreon.com/c/MuscleLove" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #FF424D; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove on Patreon
  </a>
  <a href="https://x.com/MuscleGirlLove7" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #000; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove on X
  </a>
  <a href="https://linktr.ee/ILoveMyCats" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #43e660; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove Links
  </a>
  <a href="https://musclelove.booth.pm/" rel="nofollow" target="_blank"
     style="display: inline-block; padding: 10px 24px; background: #fc4d50; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold;">
    MuscleLove on BOOTH
  </a>
</div>
"""


def _build_footer_brand() -> str:
    """フッターのブランド表示を生成する"""
    return """
<p style="text-align: center; margin: 2em 0 0.5em; font-size: 0.9em; color: #888;">Presented by <strong>MuscleLove</strong></p>
"""


def _build_related_section() -> str:
    """関連コンテンツセクションを生成する"""
    suggestions = [
        "MuscleLoveでもっと素人・ハメ撮り系の作品を探す。",
        "このジャンルの他の抜ける素人作品もMuscleLoveでチェック！",
        "関連する素人作品は、カテゴリーページからご覧いただけます。",
    ]
    sister = _build_sister_sites()

    return f"""
### MuscleLoveでもっと見る

{random.choice(suggestions)}

[カテゴリー一覧を見る](/shiroto-squad/categories/) | [タグ一覧を見る](/shiroto-squad/tags/)

[もっと多くのジャンルを見る → エロナビ](https://musclelove-777.github.io/eronavi/)

{sister}
"""


def _build_sister_sites():
    """姉妹サイトへの相互リンク（SEOリンクジュース循環）"""
    sites = {
        "エロナビ（総合）": "https://musclelove-777.github.io/eronavi/",
        "アニメエロナビ": "https://musclelove-777.github.io/anime-navi/",
        "筋肉美女ナビ": "https://musclelove-777.github.io/fitness-affiliate-blog/",
        "NTRナビ": "https://musclelove-777.github.io/ntr-navi/",
        "没入エロスVR": "https://musclelove-777.github.io/vr-eros/",
        "艶妻コレクション": "https://musclelove-777.github.io/entsuma/",
        "シロウト発掘隊": "https://musclelove-777.github.io/shiroto-squad/",
        "おっぱいパラダイス": "https://musclelove-777.github.io/oppai-paradise/",
        "二次元嫁実写化計画": "https://musclelove-777.github.io/nijigen-realize/",
        "フェチの殿堂": "https://musclelove-777.github.io/fetish-dendo/",
    }
    others = [(k, v) for k, v in sites.items() if v != CURRENT_SITE_URL]
    picks = random.sample(others, min(3, len(others)))
    links = "\n".join([f'- [{name}]({url})' for name, url in picks])
    return f"""### 姉妹サイト

{links}"""


if __name__ == "__main__":
    # テスト用のダミーデータで動作確認
    test_products = [
        {
            "title": "テスト商品 素人ハメ撮り",
            "image_url": "https://example.com/image.jpg",
            "affiliate_url": "https://example.com/affiliate",
            "price": "1,980円",
            "date": "2026-03-29 10:00:00",
            "content_id": "test001",
            "product_id": "test001",
            "genres": ["素人", "ハメ撮り"],
            "actresses": ["テスト出演者"],
            "maker": "テストメーカー",
            "series": "",
            "sample_images": [
                "https://example.com/sample1.jpg",
                "https://example.com/sample2.jpg",
                "https://example.com/sample3.jpg",
            ],
            "sample_movie_url": "https://example.com/sample_movie.mp4",
        }
    ]
    files = generate_articles(test_products)
    for f in files:
        print(f"  生成: {f}")
