import json,sys,os
S=sys.argv[1]
sys.path.insert(0,S)
from i18n import T
from concepts import js as concepts_js, gen_js as concepts_gen_js
o=json.loads(open(S+'/data.js').read()[len('window.KATACHI_DATA='):-1])
for i,(k,v) in enumerate(o['companies'].items()):
    if v['level']=='demo':
        v['terms'].setdefault('material_procurement', ['factory','both','customer','factory'][i%4])
        v['terms'].setdefault('design_consultation', 1 if i%3 else 0)
        v['terms'].setdefault('consultation_fee', 'free' if i%2 else 'paid')
h=open(S+'/v2.html').read().replace('__DATA__','window.KATACHI_DATA='+json.dumps(o,ensure_ascii=False)+';').replace('__CONCEPTS__',concepts_js()).replace('__CGEN__',concepts_gen_js()).replace('__I18N__',json.dumps({k:list(v) for k,v in T.items()},ensure_ascii=False))
open(S+'/katachi.html','w').write(h)
