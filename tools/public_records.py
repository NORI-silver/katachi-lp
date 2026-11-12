"""国の公開データ（gBizINFO）の「認定・表彰・補助金・特許・官公庁の受注」と設立・資本金を、
会社詳細に出すための小さなJSONに分けて書き出す。

使い方: python3 public_records.py <katachi-matching/data/gbiz> <リポジトリ>
入力:  companies.jsonl と 種類ごとの jsonl（katachi-matching/katachi/importers/gbiz_records.py の説明を参照）
出力:  <リポジトリ>/data/rec/00.json 〜 31.json（会社を開いたときに、その会社の入ったファイルだけを読む）

- 法人番号で結合する。サイトは社名で会社を引くので、社名を正規化した鍵（template.html の recKey と同じ）で引く。
  同じ鍵に別の会社が複数あるときは都道府県で見分け、見分けられなければ出さない（画面側）。
- これは国の公開データの事実。点数にはせず、品質の保証ではないと画面に書く。
"""
import json, os, sys, unicodedata, re, collections

SHARDS = 32
KINDS = ('certification', 'commendation', 'subsidy', 'patent', 'procurement')
SHOW = 3  # 種類ごとに画面に出す件数（新しい順）。件数は全件で数える
CORP = re.compile(r'株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人|\(株\)|\(有\)|㈱|㈲')


def rec_key(name):
    s = unicodedata.normalize('NFKC', name or '')
    s = CORP.sub('', s)
    return re.sub(r'[\s・･.,，。「」"\'’]', '', s).lower()


def shard(key):
    h = 0
    for ch in key:
        h = (h * 31 + ord(ch)) & 0xffffffff
    return h % SHARDS


def rows(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]


def main(src, repo):
    cos = {str(r['corporate_number']): r for r in rows(os.path.join(src, 'companies.jsonl')) if r.get('corporate_number')}
    recs = collections.defaultdict(lambda: collections.defaultdict(list))
    for k in KINDS:
        for r in rows(os.path.join(src, k + '.jsonl')):
            n = str(r.get('corporate_number') or '')
            if n in cos and r.get('title'):
                recs[n][k].append(r)
    out = [collections.defaultdict(list) for _ in range(SHARDS)]
    n_with = 0
    for n, c in cos.items():
        est = str(c.get('date_of_establishment') or '')
        item = {'cn': n, 'pref': c.get('prefecture'), 'at': c.get('retrieved_at'),
                'est': est[:4] if est[:4].isdigit() else None,
                'cap': c.get('capital_yen'), 'emp': c.get('employees'), 'r': {}}
        for k, lst in recs[n].items():
            lst.sort(key=lambda r: str(r.get('date') or ''), reverse=True)
            item['r'][k] = {'n': len(lst), 'top': [{'t': r['title'], 'by': r.get('issuer'), 'd': r.get('date'),
                                                    'amt': r.get('amount')} for r in lst[:SHOW]]}
        if not (item['r'] or item['est'] or item['cap'] or item['emp']):
            continue
        n_with += bool(item['r'])
        key = rec_key(c.get('name'))
        if key:
            out[shard(key)][key].append(item)
    d = os.path.join(repo, 'data', 'rec')
    os.makedirs(d, exist_ok=True)
    for i, o in enumerate(out):
        json.dump(o, open(os.path.join(d, '%02d.json' % i), 'w'), ensure_ascii=False, separators=(',', ':'))
    print('companies', len(cos), 'with records', n_with)


if __name__ == '__main__':
    main(*sys.argv[1:3])
