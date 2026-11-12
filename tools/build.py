import json,sys
S=sys.argv[1]; sys.path.insert(0,S+'/km')
from katachi.taxonomy import CAPABILITIES
cap={c[0]:c[2] for c in CAPABILITIES}
real=json.load(open(S+'/km/data/real/companies_2026-11-11.json'))
fx=json.load(open(S+'/km/data/fixtures/demo_companies.json'))
def lvl(c):
    s=c.get('source') or {}; k=s.get('kind'); u=s.get('url') or ''
    if c.get('evidence_type')=='fixture': return 'demo'
    if k=='official_site': return 'official'
    if k=='news': return 'news'
    if k=='public_list' and 'ipros' in u and c.get('solved_problems'): return 'listing'
    return 'aggregator'
def comp(c):
    return dict(name=c['name'],country=c.get('country'),pref=c.get('prefecture'),city=c.get('city'),web=c.get('website'),summary=c.get('summary'),
      level=lvl(c),src=(c.get('source') or {}).get('url'),checked=(c.get('source') or {}).get('retrieved_at'),
      terms=c.get('terms') or {},caps=[dict(n=cap.get(x['code'],x['code']),sp=x.get('level')=='specialty',ev=x.get('evidence'),et=x.get('evidence_type')) for x in c.get('capabilities',[])],
      solved=[dict(p=p['problem'],a=p.get('approach'),ex=p.get('example_product'),et=p.get('evidence_type')) for p in c.get('solved_problems',[])],
      certs=c.get('certifications',[]))
def slim(res,pool,used):
    assigned=set(m['company']+'|'+r.split(' ')[0] for t in res['teams'] for m in t['members'] for r in m['requirements'])
    for pr in res['per_requirement']:
        pr['requirement']['cap']=cap.get(pr['requirement']['capability_code'],'')
        rid=pr['requirement']['id']
        pr['candidates']=[c for i,c in enumerate(pr['candidates']) if i<6 or (c['company']+'|'+rid) in assigned]
        for cd in pr['candidates']: used.add(cd['company'])
    for t in res['teams']:
        for m in t['members']: used.add(m['company'])
    return res
out={'cap':cap,'scen':{},'companies':{}}
for key,f,pool,label,idea,qty in [('collar','collar_real.json',real,'実データ','セントバーナードのような長毛の大型犬用に、心拍・体温・活動量を測ってスマホで見られる首輪を作りたい',5),
  ('mimamori','mimamori.json',real,'実データ','高齢の親の見守り用に、玄関ドアの開閉と室温をスマホに知らせる小型センサーを100個作りたい',100),
  ('bike','bike.json',real,'実データ','自転車のハンドルに付ける、防水でBLE接続できるスマートライトを試作したい',10),
  ('demo','collar_fx.json',fx,'記入例','セントバーナードのような長毛の大型犬用に、心拍・体温・活動量を測ってスマホで見られる首輪を作りたい',5)]:
    used=set(); r=slim(json.load(open(S+'/'+f)),pool,used); r['idea']=idea; r['qty']=qty; r['dataset']=label
    out['scen'][key]=r
    for c in pool:
        if c['name'] in used: out['companies'][c['name']]=comp(c)
import estimates
out['est']=estimates.build(real,[p['requirement']['capability_code'] for r in out['scen'].values() for p in r['per_requirement']])
out['realCount']=len(real); out['realAbroad']=sum(1 for c in real if c.get('country') not in (None,'JP','日本')); out['realVerified']=sum(1 for c in real if lvl(c) in('official','news','listing'))
open(S+'/data.js','w').write('window.KATACHI_DATA='+json.dumps(out,ensure_ascii=False)+';')
print(len(out['companies']),out['realVerified'], len(open(S+'/data.js').read()))
