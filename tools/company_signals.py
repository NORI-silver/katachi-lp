"""会社ごとの「比べる目安」の材料（料金・品質・納期）を companies.json の列14に入れる。
点数は持たない。掲載情報（集約・公式サイト）と国の公開データ（gBizINFO）に書いてある事実だけを持ち、画面が出典つきで表示する。
  lt: 納期の記載（掲載情報の文言そのまま）   sp: 説明文に「短納期」「最短◯日」などの記載がある
  cs: 試作・改良時の技術相談（free/paid/yes） ja: 日本語対応  sh: 日本へ発送
  iso: 説明文に書かれた認証（ISO9001 など。認証機関での照合はまだ）
  em: 従業員数（gBizINFO）  sub: 製造系の補助金の採択（gBizINFO）
gBizINFO との照合は「社名＋都道府県」の完全一致だけ（同名の別会社を避けるため、県が違えば結び付けない）。

使い方（今ある data/companies.json に足す）:
  python3 company_signals.py <katachi-matching> <リポジトリ>/data/companies.json
guided_data.py で作り直すときも、この関数で同じ列を付ける。
"""
import csv, json, os, re, sys

ISO = re.compile(r'ISO\s*-?\s*(9001|14001|13485|22000|22716|45001)|IATF\s*16949|FSSC\s*22000|HACCP|GMP|AS\s*9100|JIS\s*Q\s*9100', re.I)
FAST = re.compile(r'短納期|最短\s*\d+\s*(日|営業日|時間)|即日|翌日出荷|スピード対応')


def load_gbiz(root):
    d = os.path.join(root, 'data', 'gbiz')
    gb, sub = {}, set()
    p = os.path.join(d, 'companies.jsonl')
    if os.path.exists(p):
        for l in open(p, encoding='utf-8'):
            o = json.loads(l)
            gb[(o['name'], o.get('prefecture') or '')] = o
    p = os.path.join(d, 'subsidy.jsonl')
    if os.path.exists(p):
        for l in open(p, encoding='utf-8'):
            sub.add(json.loads(l)['corporate_number'])
    return gb, sub


def signals(x, gb, sub):
    """x: companies.csv の1行（dict）。返り値: dict か None"""
    o = {}
    txt = (x.get('概要') or '') + ' ' + (x.get('相談の根拠') or '')
    if x.get('納期'):
        o['lt'] = x['納期'][:40]
    elif FAST.search(txt):
        o['sp'] = 1
    cs = x.get('試作・改良時の技術相談') or ''
    if cs.startswith('可'):
        o['cs'] = 'free' if '無償' in cs else 'paid' if '有償' in cs else 'yes'
    if x.get('日本語対応') == '可':
        o['ja'] = 1
    if x.get('日本へ発送') == '可':
        o['sh'] = 1
    iso = []
    for m in ISO.finditer(txt):
        k = re.sub(r'\s|-', '', m.group(0)).upper()
        if k not in iso:
            iso.append(k)
    if iso:
        o['iso'] = iso
    g = gb.get((x.get('社名'), x.get('都道府県') or ''))
    if g and (x.get('国') or 'JP') == 'JP':
        if g.get('employees'):
            o['em'] = g['employees']
        if g['corporate_number'] in sub:
            o['sub'] = 1
    return o or None


if __name__ == '__main__':
    root, path = sys.argv[1:3]
    gb, sub = load_gbiz(root)
    by = {}
    for x in csv.DictReader(open(os.path.join(root, 'data', 'real', 'companies.csv'), encoding='utf-8-sig')):
        by.setdefault((x['社名'], x['都道府県'], x['国'] or 'JP'), x)
    d = json.load(open(path, encoding='utf-8'))
    n = 0
    for r in d['c']:
        x = by.get((r[0], r[2], r[1]))
        s = signals(x, gb, sub) if x else None
        r[14:] = [s]
        n += bool(s)
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(n, 'companies with signals')
