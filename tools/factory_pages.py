"""工場をさがす（/factory/）：工程ごと・都道府県ごとの会社一覧のページを data/companies.json から作る。
seo_pages.py から呼ぶ（手で直さない）。

- 国の登録情報（gBizINFO）だけの会社は、社名か事業内容に工程の言葉（companies.json の kw）がある会社だけ載せる。
- 出すのは国内（JP）の会社だけ。国内の会社は利用者が注文できる（AGENTS.md の canOrder と同じ考え）。
- ページは「工程（PROC）× 都道府県」で、会社が MIN_PAGE 社以上あるときだけ作る（薄いページを作らない）。
  足りない都道府県は工程のページ（/factory/<工程>/）の表にだけ出す。
- 会社の情報は掲載どおり（試作対応・図面なし相談・最小ロットは掲載があるものだけ）。点数・口コミ・評価は出さない。
- 情報の確かさ（公開情報で確認／集約サイトに掲載・未確認／国の登録情報）を会社ごとに出す。
- 国の登録情報は「出典：Gビズインフォ（経済産業省）をもとにKATACHI作成」と書く。
- 費用の目安は estimates.py の出典つきの行だけ。
"""
import html, json, os, collections, re
import estimates as EST_MOD
import ideas as IDEAS_MOD
import visuals as V

SITE = "https://katachi.shiokonbu.com"
MIN_PAGE = 10   # 都道府県×工程のページを作る最少の社数
SHOW = 50       # 1ページに並べる会社の数

# 工程：コード → (URL, 短い名前, 分野(visuals.CAT), 絵, 関連ガイド, 頼むときに確かめること)
PROC = [
    ('manufacturing.sheet_metal', 'sheet-metal', '板金加工', 'parts', 'sheet', ['sheet-metal-quote', 'sheet-metal-prototype', 'no-drawing'],
     ['材質・板厚・数量・表面処理・欲しい時期をそろえて伝える', '金額は切断・曲げの回数・溶接・表面処理・段取りの積み上げ', '図面がなければ、寸法を書いた絵や現物で図面化から相談する']),
    ('manufacturing.cnc', 'cnc-machining', '切削加工', 'parts', 'part', ['cnc-machining-small-lot', 'prototype-cost', 'no-drawing'],
     ['材質・数量・公差（精度）・表面処理を伝える', '精度を指示するのは、はめ合いなど大事な所だけにすると安くなりやすい', '数が増えたら射出成形・鋳造などほかの工法と比べる']),
    ('manufacturing.injection_molding', 'injection-molding', '射出成形', 'parts', 'case', ['injection-molding-small-lot', 'resin-prototype', 'prototype-cost'],
     ['金型代と成形の単価を分けて見積を取る', '数量（最初と、その後の見込み）で金型の種類（アルミ型・鉄の型）が変わる', '金型の持ち主と保管場所を契約で決める']),
    ('manufacturing.silicone_molding', 'silicone-rubber', 'シリコーン・ゴム成形', 'parts', 'case', ['resin-prototype', 'injection-molding-small-lot'],
     ['硬さ（ショア硬度）・色・数量を伝える', '少ない数は真空注型（シリコン型）で受ける会社がある', '型代・単価は公開されていないことが多く、見積で確かめる']),
    ('manufacturing.rapid_proto', 'rapid-prototype', '試作（3Dプリント・簡易型）', 'parts', 'printer', ['3d-print-request', '3d-print-cost', 'resin-prototype'],
     ['3Dデータの有無と形式（STLなど）を伝える', '方式と素材で単価が大きく変わる', '形の確認と強度の確認では選ぶ素材が違う']),
    ('manufacturing.assembly', 'assembly', '組立・検査（EMS）', 'parts', 'device', ['iot-development', 'pcb-prototype', 'prototype-outsourcing'],
     ['部品の支給か、組立の会社が手配するかを決める', '検査の項目と合格の基準を書いて渡す', '台数（試作・量産）と梱包・出荷まで頼むかを伝える']),
    ('electronics.pcba', 'pcb-assembly', '基板実装', 'parts', 'pcb', ['pcb-prototype', 'iot-development'],
     ['ガーバーデータ・部品表（BOM）・部品の位置のデータをそろえる', '部品の調達まで頼むかを決める', '無線を使うなら技適済みモジュールを使うのが近道']),
    ('electronics.pcb_design', 'pcb-design', '回路・基板設計', 'parts', 'pcb', ['pcb-prototype', 'design-outsourcing-cost', 'iot-development'],
     ['何をする基板か（目的・電源・大きさ・使う場所）を文章で伝える', '成果物（回路図・ガーバーデータ・部品表）と権利を決める', '試作の基板の製造・実装まで頼めるかを確かめる']),
    ('food.processed_oem', 'food-oem', '食品OEM', 'food', 'pouch', ['food-oem-small-lot', 'food-oem-license', 'sweets-oem-small-lot'],
     ['作る品目に合った営業許可を持つ工場かを最初に確かめる', '最小ロットは品目・包装・殺菌の方法で変わる', '原材料・アレルゲンなどの表示を誰が作るかを決める']),
    ('food.beverage_oem', 'beverage-oem', '飲料・健康食品OEM', 'supplement', 'jar', ['supplement-oem-small-lot', 'food-oem-small-lot', 'food-oem-license'],
     ['容器（びん・缶・パウチ）と内容量で最小ロットが変わる', 'サプリ・健康食品は医薬品のような効能を書けない', '表示を誰が作るかを決める']),
    ('food.pet_food', 'pet-food-oem', 'ペットフードOEM', 'food', 'pouch', ['pet-goods-oem', 'food-oem-small-lot'],
     ['犬・猫のフードは5つの表示（名称・原材料名・賞味期限・事業者・原産国）が義務', '製造業者・輸入業者は事業を始める前に届出が要る', '病気の予防などをうたうと動物用医薬品等に当たる']),
    ('cosmetics.oem', 'cosmetics-oem', '化粧品OEM', 'cosmetics', 'bottle', ['cosmetics-oem-small-lot', 'cosmetics-oem-license', 'salon-original-cosmetics'],
     ['製造販売元をOEM先に頼むか、自社で許可を取るかを決める', '最小ロットは種類（化粧水・リップなど）と容器で変わる', '言える効能は決められた範囲だけ']),
    ('cosmetics.household', 'household-goods-oem', '日用品・雑貨OEM', 'goods', 'box', ['small-lot-oem', 'goods-small-lot', 'store-original-goods'],
     ['化粧品・雑貨・動物用のどれに当たるかで守る決まりが変わる', '中身・容器・ラベルをまとめて頼めるかを確かめる', '店名やロゴを使うなら商標を確かめる']),
    ('packaging.container', 'container', 'ボトル・容器', 'goods', 'box', ['cosmetics-oem-small-lot', 'lotion-oem', 'food-oem-small-lot'],
     ['既製の容器か特注かで最小ロットと期間が大きく変わる', '中身との相性（成分・温度）を確かめる', '印刷・ラベルを誰がするかを決める']),
    ('packaging.box', 'package-box', '化粧箱・紙器', 'goods', 'box', ['sweets-oem-small-lot', 'store-original-goods', 'goods-small-lot'],
     ['箱の形式・サイズ・印刷の色数を伝える', '食品を直接入れるなら、食品に触れて使える材料かを確かめる', '校正（色・レイアウトの確認）の回数と費用を確かめる']),
    ('packaging.label_print', 'label-print', 'ラベル・シール・印刷', 'goods', 'doc', ['store-original-goods', 'goods-small-lot', 'food-oem-license'],
     ['大きさ・紙やフィルムの種類・色数・枚数を伝える', '貼る物（瓶・袋・箱）と、水や冷蔵に強い材料が要るかを伝える', '表示の中身は品目の決まり（食品表示など）に合わせる']),
    ('apparel.garment_oem', 'apparel-oem', '衣料品OEM', 'apparel', 'shirt', ['apparel-oem-small-lot', 'uniform-custom', 'sportswear-oem'],
     ['生地・サイズ展開・色数・枚数を伝える', '生地は反単位で買うことが多く、少ない枚数では割高になりやすい', '組成・洗濯表示などの品質表示を付ける']),
    ('apparel.knit', 'knit', 'ニット・編み立て', 'apparel', 'cloth', ['apparel-oem-small-lot', 'goods-small-lot'],
     ['糸の種類・ゲージ（編み目の細かさ）・サイズを伝える', '色数と枚数で最小ロットが変わる', '品質表示を付ける']),
    ('apparel.print_embroidery', 'print-embroidery', 'プリント・刺繍', 'apparel', 'shirt', ['uniform-custom', 'novelty-small-lot', 'sportswear-oem'],
     ['シルク・転写・昇華・刺繍で、向く枚数と色数が違う', 'ロゴのデータ形式と色数・位置・大きさを伝える', '版代がかかるかを確かめる']),
    ('manufacturing.textile', 'sewing', '縫製・布製品', 'apparel', 'bag', ['bag-oem', 'goods-small-lot', 'apparel-oem-small-lot'],
     ['生地・大きさ・付属品（ファスナー・金具）・数量を伝える', 'サンプルを1点作ってもらい確かめる', '傷みやすい所の補強方法を相談する']),
    ('apparel.leather', 'leather', '革製品・バッグ・靴', 'apparel', 'bag', ['bag-oem', 'store-original-goods'],
     ['革の種類・色・金具・数量を伝える', 'ロゴの入れ方（刻印・箔押し）で版代がかかることがある', 'サンプルで縫製と仕上げを確かめる']),
    ('crafts.metal_goods', 'metal-goods', '金属製品・鋳造・アクセサリー', 'goods', 'badge', ['goods-small-lot', 'novelty-small-lot', 'outdoor-goods-oem'],
     ['素材（ステンレス・真鍮など）・大きさ・仕上げ・数量を伝える', '既製品への刻印か、形から作るかで期間と費用が大きく変わる', '食品に触れる物は食品衛生法の規格に合うかを確かめる']),
    ('crafts.wood_furniture', 'woodwork', '木工・家具', 'goods', 'board', ['goods-small-lot', 'outdoor-goods-oem', 'store-original-goods'],
     ['形・大きさ・樹種・仕上げ（オイルなど）を伝える', '焼印・レーザー刻印のロゴデータを用意する', '食品に触れる物は仕上げ材が食品に使えるかを確かめる']),
    ('crafts.ceramics_glass', 'ceramics-glass', '陶磁器・ガラス', 'goods', 'mug', ['goods-small-lot', 'novelty-small-lot', 'store-original-goods'],
     ['既製の形への名入れか、形から作るかを決める', 'ロゴの色数と位置、焼き付けの方法を確かめる', '食器は食品衛生法の規格に合うかを確かめる']),
]
PROC_BY = {p[0]: p for p in PROC}

PREFS = [('北海道', 'hokkaido'), ('青森県', 'aomori'), ('岩手県', 'iwate'), ('宮城県', 'miyagi'), ('秋田県', 'akita'), ('山形県', 'yamagata'),
         ('福島県', 'fukushima'), ('茨城県', 'ibaraki'), ('栃木県', 'tochigi'), ('群馬県', 'gunma'), ('埼玉県', 'saitama'), ('千葉県', 'chiba'),
         ('東京都', 'tokyo'), ('神奈川県', 'kanagawa'), ('新潟県', 'niigata'), ('富山県', 'toyama'), ('石川県', 'ishikawa'), ('福井県', 'fukui'),
         ('山梨県', 'yamanashi'), ('長野県', 'nagano'), ('岐阜県', 'gifu'), ('静岡県', 'shizuoka'), ('愛知県', 'aichi'), ('三重県', 'mie'),
         ('滋賀県', 'shiga'), ('京都府', 'kyoto'), ('大阪府', 'osaka'), ('兵庫県', 'hyogo'), ('奈良県', 'nara'), ('和歌山県', 'wakayama'),
         ('鳥取県', 'tottori'), ('島根県', 'shimane'), ('岡山県', 'okayama'), ('広島県', 'hiroshima'), ('山口県', 'yamaguchi'), ('徳島県', 'tokushima'),
         ('香川県', 'kagawa'), ('愛媛県', 'ehime'), ('高知県', 'kochi'), ('福岡県', 'fukuoka'), ('佐賀県', 'saga'), ('長崎県', 'nagasaki'),
         ('熊本県', 'kumamoto'), ('大分県', 'oita'), ('宮崎県', 'miyazaki'), ('鹿児島県', 'kagoshima'), ('沖縄県', 'okinawa')]
PREF_SLUG = dict(PREFS)
REGIONS = [('北海道・東北', PREFS[0:7]), ('関東', PREFS[7:14]), ('中部', PREFS[14:23]), ('近畿', PREFS[23:30]),
           ('中国', PREFS[30:35]), ('四国', PREFS[35:39]), ('九州・沖縄', PREFS[39:47])]
REGION_OF = {p: r for r, ps in REGIONS for p, _ in ps}
GROUPS = [('金属・樹脂の加工と試作', 'parts', ['manufacturing.sheet_metal', 'manufacturing.cnc', 'manufacturing.injection_molding', 'manufacturing.silicone_molding', 'manufacturing.rapid_proto', 'manufacturing.assembly']),
          ('電子機器・基板', 'parts', ['electronics.pcba', 'electronics.pcb_design']),
          ('食品・飲料', 'food', ['food.processed_oem', 'food.beverage_oem', 'food.pet_food']),
          ('化粧品・日用品', 'cosmetics', ['cosmetics.oem', 'cosmetics.household']),
          ('衣料・布・革', 'apparel', ['apparel.garment_oem', 'apparel.knit', 'apparel.print_embroidery', 'manufacturing.textile', 'apparel.leather']),
          ('雑貨・工芸', 'goods', ['crafts.metal_goods', 'crafts.wood_furniture', 'crafts.ceramics_glass']),
          ('包装・印刷', 'goods', ['packaging.container', 'packaging.box', 'packaging.label_print'])]
LV = {'pub': '公開情報で確認', 'unk': '集約サイトに掲載（未確認）', 'gov': '国の登録情報'}
GBIZ = '国の登録情報は「出典：Gビズインフォ（経済産業省）をもとにKATACHI作成」。'
e = html.escape


class DB:
    def __init__(self, root):
        d = json.load(open(os.path.join(root, 'data', 'companies.json'), encoding='utf-8'))
        self.caps = d['caps']
        self.kw = dict(zip(d['caps'], d['kw']))
        self.rows = [r for r in d['c'] if r[1] == 'JP']
        self.date = max(r[13] for r in self.rows if r[13])
        self.by = collections.defaultdict(list)          # (code, pref) -> rows
        self.nat = collections.defaultdict(list)         # code -> rows
        for r in self.rows:
            for i in set(r[5]):
                c = self.caps[i]
                if c in PROC_BY and self.fits(r, c):
                    self.nat[c].append(r)
                    if r[2] in PREF_SLUG:
                        self.by[(c, r[2])].append(r)

    def fits(self, r, code):
        # 国の登録情報だけの会社は、社名か事業内容に工程の言葉がある会社だけ載せる（業種の分類だけで工程が違う会社を出さない）
        if r[10] != 'gov':
            return True
        t = (r[0] or '') + (r[11] or '')
        return any(k in t for k in self.kw.get(code, []))

    def has_page(self, code, pref):
        return len(self.by.get((code, pref), [])) >= MIN_PAGE


def _key(r):
    return (r[10] != 'pub', not r[6], not r[7], r[8] is None, r[10] == 'gov', not r[4], not r[11], r[0])


def stats(rows):
    return dict(n=len(rows), proto=sum(1 for r in rows if r[6]), nodraw=sum(1 for r in rows if r[7]),
                lot=sum(1 for r in rows if r[8] is not None), lv=collections.Counter(r[10] for r in rows))


def company_li(r, show_pref=False):
    x = r[14] or {}
    name = e(r[0])
    name = f'<a href="{e(r[4])}" target="_blank" rel="nofollow noopener">{name}</a>' if r[4] else f'<b>{name}</b>'
    place = e((r[2] if show_pref else '') + (r[3] or ''))
    tags = []
    if r[6]: tags.append('試作対応')
    if r[7]: tags.append('図面なし相談')
    if r[8] is not None: tags.append(f'最小ロット{r[8]:,}個')
    if x.get('lt'): tags.append(e(x['lt']))
    if x.get('em'): tags.append(f'従業員{x["em"]:,}人')
    tag = ''.join(f'<span>{t}</span>' for t in tags)
    src = f'<a href="{e(r[12])}" target="_blank" rel="nofollow noopener">{LV.get(r[10], "")}</a>' if r[12] else LV.get(r[10], '')
    return (f'<li>{name}<small>{place}{"・" if place and r[11] else ""}{e(r[11] or "")}</small>'
            f'<span class="tg">{tag}<span class="lv">{src}</span></span></li>')


def est_block(code):
    rows = [r for r in EST_MOD.EST.get(code, {}).get('rows', [])]
    vals = [r for r in rows if r.get('lo') is not None]
    notes = [r for r in rows if r.get('lo') is None]
    if not vals:
        return '<p>公開されている相場は見つかっていません。数量と仕様をそろえて複数社に見積を取り、比べます。</p>'
    out = '<div class="tbl"><table><tr><th>項目</th><th>目安</th><th>中身</th><th>出典・確かさ</th></tr>'
    for r in vals:
        s = EST_MOD.SRC.get(r.get('s'), {})
        out += (f'<tr><td>{IDEAS_MOD.KIND.get(r["k"], "")}</td><td>{IDEAS_MOD.rng(r["lo"], r["hi"], r["u"])}</td><td>{e(r["t"])}</td>'
                f'<td><a href="{e(s.get("url", ""))}" target="_blank" rel="noopener">{e(s.get("t", ""))}</a>（{IDEAS_MOD.LEVEL.get(s.get("level"), "")}）</td></tr>')
    out += '</table></div>'
    out += ''.join(f'<p class="src">{e(r["t"])}</p>' for r in notes)
    out += '<p class="src">公開の料金表・記事の数字。形・材料・数量・納期で変わり、正式な金額は見積で決まります。ドルは1ドル＝150円で換算。</p>' if any(r['u'] == 'usd' for r in vals) else \
        '<p class="src">公開の料金表・記事の数字。形・材料・数量・納期で変わり、正式な金額は見積で決まります。</p>'
    return out


def rel_block(code, guides_by, limit_ideas=6):
    p = PROC_BY[code]
    gl = [g for g in p[5] if g in guides_by]
    ex = [x for x in IDEAS_MOD.IDEAS if x['code'] == code or any(c == code for c, _ in x['est'])][:limit_ideas]
    out = ''
    if gl:
        out += '<h2 class="sub">関連するガイド</h2><ul>' + ''.join(f'<li><a href="/guide/{g}/">{guides_by[g]["h1"]}</a></li>' for g in gl) + '</ul>'
    if ex:
        out += f'<h2 class="sub">{p[2]}の作例</h2><ul>' + ''.join(f'<li><a href="/idea/{x["k"]}/">{e(x["t"][0])}</a>（{e(x["lot"][0])}）</li>' for x in ex) + '</ul>'
    return out


CSS = """<style>.clist{list-style:none;padding:0;margin:12px 0}.clist li{border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:0 0 8px;background:#fff}
.clist li>a,.clist li>b{font-weight:700}.clist small{display:block;color:var(--mute);font-size:13px;line-height:1.6}
.clist .tg{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}.clist .tg span{font-size:12px;background:#eef3fd;color:#1b3a8f;border-radius:6px;padding:1px 8px}
.clist .tg .lv{background:#f3f4f6;color:var(--mute)}.clist .tg .lv a{color:var(--mute)}
.plist{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 14px;padding:0;list-style:none}.plist li a,.plist li span{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:14px;text-decoration:none}
.plist li span{color:var(--mute)}.num{text-align:right}.note{font-size:12.5px;color:var(--mute)}</style>"""


def faq_ld(items):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a)}} for q, a in items]}


def crumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}


def itemlist(rows):
    return {"@type": "ItemList", "numberOfItems": len(rows), "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "item": {"@type": "Organization", "name": r[0], **({"url": r[4]} if r[4] else {}),
                                                          "address": {"@type": "PostalAddress", "addressRegion": r[2], "addressLocality": r[3] or None, "addressCountry": "JP"}}}
        for i, r in enumerate(rows)]}


def pref_page(db, code, pref, guides_by):
    """都道府県×工程のページ。返り値: (path, title, desc, body, graph, og)"""
    p = PROC_BY[code]
    label, slug = p[2], p[1]
    rows = sorted(db.by[(code, pref)], key=_key)
    st = stats(rows)
    path = f'/factory/{slug}/{PREF_SLUG[pref]}/'
    title = f'{pref}の{label}の会社{st["n"]:,}社｜小ロット・試作の頼み先'
    desc = (f'{pref}で{label}を受ける会社{st["n"]:,}社の一覧（{db.date.replace("-", "/")}時点）。試作対応{st["proto"]}社・図面なし相談{st["nodraw"]}社の掲載、'
            f'市区町村別の数、費用の目安（出典つき）、小ロットで頼むときの確かめ方。')
    city = collections.Counter((r[3] or '').strip() for r in rows if (r[3] or '').strip())
    near = [(q, len(db.by.get((code, q), []))) for q, _ in dict(REGIONS)[REGION_OF[pref]] if q != pref]
    pts = [f'{pref}で{label}を受ける会社：{st["n"]:,}社（KATACHIの企業DB、公開情報から）',
           f'掲載で試作対応{st["proto"]}社・図面なし相談{st["nodraw"]}社・最小ロットの記載{st["lot"]}社。ほかの会社は見積で確かめる',
           ('多い市区町村：' + '、'.join(f'{e(c)}{n}社' for c, n in city.most_common(3))) if city else '市区町村の記載は一部の会社だけ',
           '点数・口コミは付けず、情報の確かさ（公開情報・集約サイト・国の登録情報）を会社ごとに表示']
    lead = (f'<p>{pref}で{label}を受ける会社は、KATACHIの企業DBに<strong>{st["n"]:,}社</strong>あります（{db.date.replace("-", "/")}時点）。'
            f'小ロット・試作の条件は会社ごとに違うため、数量・材料・欲しい時期をそろえて2〜3社に見積を取って比べます。</p>')
    shown = rows[:SHOW]
    lst = '<ul class="clist">' + ''.join(company_li(r) for r in shown) + '</ul>'
    if st['n'] > SHOW:
        lst += f'<p>ほか{st["n"] - SHOW:,}社は、<a href="/">トップ</a>でつくりたいものを書くと、工程ごとの候補として出ます。</p>'
    ctab = ''
    if city:
        ctab = '<ul class="plist">' + ''.join(f'<li><span>{e(c)} {n}社</span></li>' for c, n in city.most_common(12)) + '</ul>'
    lvtxt = '、'.join(f'{LV[k]} {st["lv"][k]:,}社' for k in ('pub', 'unk', 'gov') if st['lv'].get(k))
    nb = '<ul class="plist">' + ''.join(
        (f'<li><a href="/factory/{slug}/{PREF_SLUG[q]}/">{q} {n}社</a></li>' if n >= MIN_PAGE else f'<li><span>{q} {n}社</span></li>') for q, n in near) + '</ul>'
    tips = '<ul>' + ''.join(f'<li>{t}</li>' for t in p[6]) + '<li>同じ条件で2〜3社に見積を取り、初期費用（型代・版代・段取り）と単価を分けて比べる</li></ul>'
    faq = [(f'{pref}で{label}を小ロットで頼めますか？', f'掲載で試作対応がわかる会社は{st["proto"]}社、最小ロットの記載がある会社は{st["lot"]}社です。ほかの会社も、数量を伝えて見積の依頼で確かめられます。'),
           ('図面がなくても頼めますか？', f'掲載で図面なし相談ができる会社は{st["nodraw"]}社です。KATACHIに文章や写真で伝えると、工程に分けて図面なしで相談できる会社を探します。'),
           ('一覧の情報はどこから集めていますか？', f'会社の公式サイト・報道・企業の掲載ページ・国の登録情報（gBizINFO）などの公開情報です。内訳は{lvtxt}です。')]
    body_secs = (f'<h2>{pref}で{label}を受ける会社の一覧</h2><p>試作対応・図面なし相談の掲載がある会社から順に{len(shown)}社を表示しています。社名のリンクは各社の公式サイトです。</p>{lst}'
                 + (f'<h2>{pref}の{label}の会社（市区町村別）</h2>{ctab}' if ctab else '')
                 + f'<h2>{label}の費用・最低ロットの目安</h2>{est_block(code)}'
                 + f'<h2>{label}を小ロットで頼むときに確かめること</h2>{tips}'
                 + f'<h2>{REGION_OF[pref]}のほかの{label}の会社</h2>{nb}<p><a href="/factory/{slug}/">{label}の会社を都道府県から探す</a></p>'
                 + '<h2>よくある質問</h2><dl>' + ''.join(f'<dt>{q}</dt><dd>{a}</dd>' for q, a in faq) + '</dl>')
    cat = p[3]
    body = (f'<p class="crumb"><a href="/">KATACHI</a> › <a href="/factory/">工場をさがす</a> › <a href="/factory/{slug}/">{label}</a> › {pref}</p>'
            f'<h1>{pref}の{label}の会社</h1><p class="upd">更新日：{db.date.replace("-", "/")}</p>'
            f'{V.hero(cat, p[4], f"{pref}の{label}", label if len(label) <= 8 else None)}<div class="lead">{lead}</div>'
            + V.points('このページの要点', pts) + V.restructure(body_secs + CTA_F) + rel_block(code, guides_by)
            + f'<p class="note">KATACHIの企業DB（公開情報）から作った一覧です。掲載の順は推薦や評価ではありません。{GBIZ}</p>')
    url = SITE + path
    graph = [{"@type": "CollectionPage", "name": title, "url": url, "description": desc, "inLanguage": "ja", "dateModified": db.date,
              "about": f'{pref}の{label}', "mainEntity": itemlist(shown)},
             crumbs([('KATACHI', '/'), ('工場をさがす', '/factory/'), (label, f'/factory/{slug}/'), (pref, path)]), faq_ld(faq)]
    return path, title, desc, body, graph, f'/og/factory-{slug}.png'


def proc_page(db, code, guides_by):
    p = PROC_BY[code]
    label, slug = p[2], p[1]
    rows = db.nat[code]
    st = stats(rows)
    path = f'/factory/{slug}/'
    title = f'{label}の会社を都道府県から探す｜小ロット・試作の頼み先'
    desc = (f'国内で{label}を受ける会社{st["n"]:,}社を都道府県別に比較。試作対応・図面なし相談の掲載数、費用・最低ロットの目安（出典つき）、'
            f'小ロットで頼むときに確かめることをまとめました。')
    reg = ''
    for rg, ps in REGIONS:
        items = [(q, s, len(db.by.get((code, q), []))) for q, s in ps]
        items = [x for x in items if x[2]]
        if items:
            reg += f'<h3>{rg}</h3><ul class="plist">' + ''.join(
                (f'<li><a href="/factory/{slug}/{s}/">{q} {n}社</a></li>' if n >= MIN_PAGE else f'<li><span>{q} {n}社</span></li>') for q, s, n in items) + '</ul>'
    reg += f'<p class="src">リンクがある都道府県は、会社の一覧のページがあります（{MIN_PAGE}社以上）。</p>'
    big = sorted(((q, s, stats(db.by.get((code, q), []))) for q, s in PREFS), key=lambda x: -x[2]['n'])[:10]
    tbl = ('<div class="tbl"><table><tr><th>都道府県</th><th>会社数</th><th>試作対応の掲載</th><th>図面なし相談の掲載</th></tr>'
           + ''.join(f'<tr><td>{q}</td><td>{ss["n"]}社</td><td>{ss["proto"]}社</td><td>{ss["nodraw"]}社</td></tr>' for q, s, ss in big if ss['n'])
           + '</table></div>')
    top = sorted(rows, key=_key)[:20]
    top3 = sorted(((q, len(db.by.get((code, q), []))) for q, _ in PREFS), key=lambda x: -x[1])[:3]
    pts = [f'国内で{label}を受ける会社：{st["n"]:,}社（KATACHIの企業DB、{db.date.replace("-", "/")}時点）',
           '多い都道府県：' + '、'.join(f'{q}{n}社' for q, n in top3 if n),
           f'掲載で試作対応{st["proto"]}社・図面なし相談{st["nodraw"]}社・最小ロットの記載{st["lot"]}社',
           p[6][0]]
    lead = (f'<p>{label}を受ける会社は、国内に<strong>{st["n"]:,}社</strong>あります（KATACHIの企業DB）。'
            f'近くの会社は打ち合わせや納品がしやすく、遠くの会社も図面やデータのやり取りで頼めます。</p>')
    faq = [(f'{label}は小ロットや1個から頼めますか？', f'掲載で試作対応がわかる会社は{st["proto"]}社です。最小ロットは会社と作り方で変わるため、数量を伝えて見積で確かめます。'),
           ('近くの会社と遠くの会社、どちらに頼むべきですか？', '打ち合わせや現物の確認が多いなら近くの会社が便利です。図面やデータで伝えられるなら、得意な会社を地域にこだわらず選べます。'),
           ('どの会社が良いかはどう決めればいいですか？', 'KATACHIは点数や口コミを付けません。同じ条件で2〜3社に見積を取り、費用・納期・対応範囲で比べてください。')]
    secs = (f'<h2>都道府県別の{label}の会社の数</h2>{reg}<h2>{label}の会社が多い都道府県（比較表）</h2>{tbl}'
            f'<h2>{label}の会社の例（試作対応・図面なし相談の掲載がある順）</h2><ul class="clist">' + ''.join(company_li(r, True) for r in top) + '</ul>'
            f'<h2>{label}の費用・最低ロットの目安</h2>{est_block(code)}'
            f'<h2>{label}を小ロットで頼むときに確かめること</h2><ul>' + ''.join(f'<li>{t}</li>' for t in p[6]) + '</ul>'
            '<h2>よくある質問</h2><dl>' + ''.join(f'<dt>{q}</dt><dd>{a}</dd>' for q, a in faq) + '</dl>')
    body = (f'<p class="crumb"><a href="/">KATACHI</a> › <a href="/factory/">工場をさがす</a> › {label}</p>'
            f'<h1>{label}の会社を都道府県から探す</h1><p class="upd">更新日：{db.date.replace("-", "/")}</p>'
            f'{V.hero(p[3], p[4], label, label if len(label) <= 8 else None)}<div class="lead">{lead}</div>' + V.points('このページの要点', pts)
            + V.restructure(secs + CTA_F) + rel_block(code, guides_by)
            + f'<p class="note">KATACHIの企業DB（公開情報）から作った一覧です。掲載の順は推薦や評価ではありません。{GBIZ}</p>')
    graph = [{"@type": "CollectionPage", "name": title, "url": SITE + path, "description": desc, "inLanguage": "ja", "dateModified": db.date, "mainEntity": itemlist(top)},
             crumbs([('KATACHI', '/'), ('工場をさがす', '/factory/'), (label, path)]), faq_ld(faq)]
    return path, title, desc, body, graph, f'/og/factory-{slug}.png'


def index_page(db):
    path = '/factory/'
    title = '工場・製造の委託先を工程と地域から探す｜小ロット・試作'
    n = len(db.rows)
    desc = (f'板金・切削・射出成形・食品OEM・化粧品OEM・縫製など{len(PROC)}の工程ごとに、国内の製造会社を都道府県別に探せます。'
            '試作対応・図面なし相談の掲載と、出典つきの費用の目安つき。')
    out = ''
    for g, cat, codes in GROUPS:
        c, bg, _, _ = V.CAT[cat]
        out += f'<h2 class="sub">{g}</h2><div class="glist">'
        for code in codes:
            p = PROC_BY[code]
            k = len(db.nat[code])
            pages = sum(1 for q, _ in PREFS if db.has_page(code, q))
            out += (f'<a href="/factory/{p[1]}/"><span class="ic" style="background:{bg}">{V.icon(p[4], 28, c)}</span>'
                    f'<span><b>{p[2]}の会社 {k:,}社</b><small>{pages}都道府県の一覧あり。{p[6][0]}</small></span></a>')
        out += '</div>'
    # 比較表：工程ごとの会社数と掲載の内訳
    cmp = ('<h2 class="sub">工程ごとの会社数（比較表）</h2><div class="tbl"><table><tr><th>工程</th><th>会社数</th><th>試作対応</th>'
           '<th>図面なし相談</th><th>最小ロットの記載</th></tr>'
           + ''.join((lambda s, p: f'<tr><td><a href="/factory/{p[1]}/">{p[2]}</a></td><td>{s["n"]:,}社</td><td>{s["proto"]:,}社</td><td>{s["nodraw"]:,}社</td><td>{s["lot"]:,}社</td></tr>')(stats(db.nat[c]), PROC_BY[c])
                     for _, _, cs in GROUPS for c in cs)
           + '</table></div><p class="src">試作対応・図面なし相談・最小ロットは、掲載がある会社の数です（掲載がない会社も、見積で確かめられます）。</p>')
    cmp = V.enhance_block(cmp)
    body = (f'<p class="crumb"><a href="/">KATACHI</a></p><h1>工場・製造の委託先を工程と地域から探す</h1>'
            f'<p class="lead">KATACHIの企業DB（公開情報）にある国内の製造会社{n:,}社を、工程と都道府県で探せます（{db.date.replace("-", "/")}時点）。'
            '何をどこに頼むか決まっていないときは、トップでつくりたいものを書くと、工程に分けて候補の会社を組み合わせます。</p>'
            f'{out}{cmp}{CTA_F}<p class="note">掲載の順は推薦や評価ではありません。{GBIZ}</p>')
    graph = [{"@type": "CollectionPage", "name": title, "url": SITE + path, "description": desc, "inLanguage": "ja", "dateModified": db.date,
              "hasPart": [{"@type": "CollectionPage", "name": f'{p[2]}の会社を都道府県から探す', "url": f'{SITE}/factory/{p[1]}/'} for p in PROC]},
             crumbs([('KATACHI', '/'), ('工場をさがす', path)])]
    return path, title, desc, body, graph, '/og.png'


CTA_F = """<div class="cta"><b>つくりたいものを書くだけで、工程ごとに頼める会社をさがせます</b>
<p>KATACHIが作り方を工程に分け、図面なし・試作・小ロットで相談できる会社を組み合わせて提案します。工程の整理・会社の検索・見積の依頼は無料です。</p>
<a class="btn" href="/">つくりたいものを書いて探す</a></div>"""


def all_pages(root, guides_by):
    """[(path, title, desc, body, graph, og, lastmod)]"""
    db = DB(root)
    out = [index_page(db) + (db.date,)]
    for p in PROC:
        out.append(proc_page(db, p[0], guides_by) + (db.date,))
        for q, _ in PREFS:
            if db.has_page(p[0], q):
                out.append(pref_page(db, p[0], q, guides_by) + (db.date,))
    return out


def links_for_code(root_db, code):
    """作例・ガイドから工場ページへのリンク用（工程コード → (URL, 名前)）"""
    p = PROC_BY.get(code)
    return (f'/factory/{p[1]}/', f'{p[2]}の会社を都道府県から探す') if p else None


def guide_links(slug):
    """ガイドの slug → そのガイドを関連に持つ工程（工場ページへのリンク用）"""
    return [p for p in PROC if slug in p[5]]
