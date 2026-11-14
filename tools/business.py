"""品目の記事に「法人・お店として頼むとき」の章を足す（Nori 2026-11-14「SEOはおすすめでいいよ」：集客は個人から、売上の柱は中小企業）。

individual.py が個人向けに書き換えた品目の記事（INTRO）に、会社・店舗として頼む読者向けの章とFAQを足す。
数字は書かない（出典のある数字は各記事の本文にある）。
"""

L = lambda s, t: f'<a href="/guide/{s}/">{t}</a>'

NAME = {
    "cosmetics": "<li><strong>自社の名前で売れる</strong>：製造販売業の許可はOEM先が持ち、自社は「発売元」として名前を出せる場合が多い。役割の分け方は" + L("cosmetics-oem-license", "化粧品OEMに必要な許可") + "へ。</li>",
    "food": "<li><strong>自社の名前で売れる</strong>：表示の「販売者」を自社名にし、製造所はOEM先のまま。製造所固有記号の決まりは" + L("food-oem-license", "食品OEMの営業許可と表示") + "へ。</li>",
    "supplement": "<li><strong>自社の名前で売れる</strong>：表示の「販売者」を自社名にできる。効能は書けないので、言える表現を最初にOEM先と決める。表示の決まりは" + L("food-oem-license", "食品OEMの営業許可と表示") + "へ。</li>",
    "apparel": "<li><strong>自社の名前で売れる</strong>：品質表示（家庭用品品質表示法）の表示者を自社名にする。社員用の制服なら" + L("uniform-custom", "ユニフォームのオリジナル製作") + "へ。</li>",
    "goods": "<li><strong>販促・来店特典にするなら</strong>：配る品は景品表示法の上限額にかかることがある。名入れの選び方と合わせて" + L("novelty-small-lot", "ノベルティ制作を小ロットで") + "へ。店頭で売るなら" + L("store-original-goods", "店舗のオリジナルグッズ") + "へ。</li>",
    "parts": "<li><strong>図面がなくても会社として頼める</strong>：用途・大きさ・数・予算の4点で相談できる。進め方は" + L("prototype-outsourcing", "試作の外注の進め方") + "と" + L("no-drawing", "図面がなくても加工は頼める？") + "へ。</li>",
}

def section(cat):
    items = [
        "<li><strong>最初の1通に会社の情報を書く</strong>：会社名・用途（販売／配布／店舗で使う）・数・希望の時期・予算。法人だけ受ける会社にも頼める。</li>",
        NAME.get(cat, NAME["parts"]),
        "<li><strong>見積は同じ条件で並べる</strong>：数・仕様・納期をそろえて複数社に聞くと、差が単価なのか仕様なのかがわかる。</li>",
        "<li><strong>工程が分かれるなら取りまとめ役を1社決める</strong>：中身・容器・印刷・箱などを別の会社に頼むときは、窓口と責任の範囲を最初に書面で決める。</li>",
        "<li><strong>社内に設計担当がいなくても進められる</strong>：委託先の探し方は" + L("find-manufacturer", "製造の委託先の探し方") + "、全体の進め方は" + L("own-product-development", "自社製品の開発の進め方") + "、費用の一部は" + L("subsidy-prototype", "ものづくり補助金") + "が使える場合がある。</li>",
    ]
    tail = '<p>KATACHIでは、作りたいものを文章で書くと、頼める会社と、複数社の組み合わせ（取りまとめ役つき）を出せます。<a href="/">トップで試す</a></p>'
    return ("法人・お店として頼むとき", "<ul>" + "".join(items) + "</ul>" + tail)


FAQ = ("会社やお店として頼むときは何が違いますか？",
       "会社名・用途・数・予算を最初に伝えると、法人だけ受ける会社にも頼めます。販売者・発売元などの表示は自社名にでき、工程が分かれるときは取りまとめ役を1社決めます。")


def apply(articles, slugs, topic):
    by = {a["slug"]: a for a in articles}
    for slug in slugs:
        a = by[slug]
        secs = a["sections"]
        i = next((n for n, s in enumerate(secs) if s[0].startswith("個人で")), 1)
        secs.insert(i + 1, section(topic(slug)[0]))
        a["faq"] = list(a.get("faq", []))
        a["faq"].insert(min(1, len(a["faq"])), FAQ)
        rel = [s for s in ("own-product-development", "find-manufacturer") if s != slug]
        a["related"] = list(a.get("related", [])) + [s for s in rel if s not in a.get("related", [])]
