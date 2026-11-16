// 工場に依頼するときの必要情報（定義表 tools/fspec.py の NEED）の回帰テスト（Nori 2026-11-16「必要情報への翻訳、追加取得」）
// 文章 → 品目・読み取った項目・②の前の質問・工場に届く依頼の要点（fsText）を確かめる。どの製品でも同じ仕組みで動くかを、品目の違う製品で見る。
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから
//   node tools/tests/need_cases.js [http://localhost:8765/]
const {chromium}=require('playwright');
const [base='http://localhost:8765/']=process.argv.slice(2);
// v: 文章から読めるはずの値（項目キー → 含む文字）、cats/nocats: 品目、ask/noask: ②の前に聞く／聞かない項目、nogot: 依頼の要点の「決まっていること」に出ない言葉
const cases=[
  {id:'collar',text:'犬の首輪に付けるGPSと心拍センサーの見守りタグを作りたい。充電式で防水。まず試作3個。',cats:['elec','pet'],v:{power:'充電式',comm:'GPS',qs:'3個'},noask:['power','comm'],ask:['target']},
  {id:'tshirt',text:'オリジナルのTシャツを作りたい。お店で売る。',cats:['apparel'],v:{weave:'ニット',purpose:'売る'},ask:['fabric','sizes','deco']},
  {id:'tshirt2',text:'綿のTシャツにロゴを刺繍で入れたい。S・M・Lで300枚。',cats:['apparel'],v:{fabric:'綿',deco:'刺繍',sizes:'3サイズ'},noask:['fabric','deco','sizes']},
  {id:'bracket',text:'ステンレスの棚受け金具を100個',cats:['metal'],nocats:['wood'],v:{grade:'ステンレス'}},
  {id:'serum',text:'美容液をOEMで作りたい。30ml、500本',cats:['cosme'],nocats:['goods'],v:{vol:'30ml',ctype:'スキンケア'},noask:['vol','ctype'],nogot:['素材：','大きさ：']},
  {id:'granola',text:'自社ブランドのグラノーラをOEMで作りたい',cats:['food'],nocats:['goods'],v:{form:'乾燥'},ask:['recipe'],nogot:['アルミ']},
  {id:'keyholder',text:'イベントで配るアクリルキーホルダーを300個',cats:['goods'],nocats:['cosme'],ask:['colors','art']},
  {id:'slope',text:'犬用のプールのスロープ。INTEXのプール450×220×84cmに付けたい。50kgの犬が乗る',cats:['pet','struct'],v:{load:'50kg',where:'水',target:'大型犬'},noask:['load','where','target']},
  {id:'putter',text:'ゴルフのパターのカバーを革で作りたい',cats:['apparel'],nocats:['metal'],v:{fabric:'革'}},
  {id:'thermo',text:'部屋の温度を表示する小さな置き時計。通信は使わない。電池は単3電池で動かしたい',cats:['elec'],v:{comm:'使わない',power:'乾電池'}},
  {id:'nobat',text:'ステンレスで植木鉢を置くスタンドを作りたい。電池やセンサーは使わない',cats:['metal'],nocats:['elec','goods']},
  {id:'plant',text:'観葉植物の土が乾いたらスマホに知らせるセンサーを作りたい。電池で動かしたい。自社の商品として100個売りたい。',cats:['elec'],v:{power:'乾電池',comm:'スマホに知らせる',qf:'100個'},noask:['power','comm','qf']},
  {id:'shelf',text:'カフェに置く木の陳列棚を2台作りたい',cats:['wood'],v:{place:'店舗'},ask:['inst']},
  // 電子部品の無い長い設計書・依頼書で、電源・通信を聞かない（Nori 2026-11-16「これもうなんかいもやってるからいい加減やめて」。見出し・否定・将来の節の言葉は証拠にしない）
  {id:'slope_spec',file:'pool_slope_spec.md',nocats:['elec'],noask:['power','comm']},
  {id:'bench_spec',file:'wood_bench_spec.md',nocats:['elec'],noask:['power','comm']},
  {id:'wheelchair_spec',file:'dog_wheelchair_spec.md',nocats:['elec'],noask:['power','comm']},
  {id:'tote_spec',file:'tote_spec.md',nocats:['elec'],noask:['power','comm']},
  {id:'sign_spec',file:'metal_sign_spec.md',nocats:['elec'],noask:['power','comm']},
  // 中身の品（食品・化粧品）は作る物そのものでないと聞かない
  {id:'salon_shelf',text:'美容室に置く、シャンプーのボトルを並べる木の棚を1台。',cats:['wood'],nocats:['cosme','food','elec']},
  {id:'tumbler',text:'ステンレスの保冷タンブラーにロゴを入れて300個。コーヒーやお茶を入れて使う。',nocats:['food','cosme','elec']},
  {id:'cake_box',text:'ケーキ屋さんで使う、ロゴ入りの紙の箱を500個作りたい。',nocats:['food','elec']},
  {id:'guide_noel',text:'犬用のプールのスロープ\n数量：まず試作で1個\n材料：金属\n電子部品：使わない',nocats:['elec'],noask:['power','comm']},
];
const MAXQ=6;
(async()=>{const b=await chromium.launch();let ng=0;
  for(const cs of cases){const c=await b.newContext({viewport:{width:1280,height:900}});
    await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com|googletagmanager|google-analytics/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    await c.route(u=>/\/(index\.html)?$/.test(new URL(u).pathname),async r=>{const resp=await r.fetch();let body=await resp.text();
      body=body.replace('window.KATACHI_RL=()=>S.lastRL;','window.KATACHI_RL=()=>S.lastRL;window.__FS=()=>({S,fsBuild,fsText});');r.fulfill({response:resp,body})});
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    if(cs.file)cs.text=require('fs').readFileSync(require('path').join(__dirname,'specs',cs.file),'utf8');
    await p.fill('#idea',cs.text);await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
    await p.waitForSelector('#mCq,#mPlans,.mstep',{timeout:30000}).catch(()=>{});await p.waitForTimeout(300);
    const r0=await p.evaluate(()=>{const {S,fsBuild}=window.__FS();const F=fsBuild(S.anal);const V={};for(const k in F.V)V[k]=F.V[k].v;return {cats:F.cats.map(k=>k.id),V}});
    // 質問は全部「わからない」で答え、聞いた項目を集める
    const asked=[];for(let i=0;i<12;i++){const k=await p.$eval('#mCq',e=>e.dataset.fk).catch(()=>null);if(!k)break;asked.push(k);await p.click('#mCq [data-cqu]');await p.waitForTimeout(350)}
    const txt=await p.evaluate(()=>{const {S,fsBuild,fsText}=window.__FS();return fsText(fsBuild(S.anal))});
    const bad=[];
    for(const k of cs.cats||[])if(!r0.cats.includes(k))bad.push('品目に'+k+'が無い');
    for(const k of cs.nocats||[])if(r0.cats.includes(k))bad.push('品目に'+k+'が入った');
    for(const [k,v] of Object.entries(cs.v||{}))if(!String(r0.V[k]||'').includes(v))bad.push(k+'が「'+v+'」と読めていない（'+(r0.V[k]||'なし')+'）');
    for(const k of cs.ask||[])if(!asked.includes(k))bad.push(k+'を聞いていない');
    for(const k of cs.noask||[])if(asked.includes(k))bad.push(k+'は文章にあるのに聞いた');
    if(asked.length>MAXQ)bad.push('質問が'+asked.length+'問（'+MAXQ+'問まで）');
    const got=(txt.split('■ 決まっていること')[1]||'').split('■')[0];
    for(const w of cs.nogot||[])if(got.includes(w))bad.push('決まっていることに「'+w+'」');
    if(/要確認/.test(txt))bad.push('依頼の要点に「要確認」の行が残っている');
    if(!/■ 作りたいもの：/.test(txt)||!/■ お聞きしたいこと/.test(txt))bad.push('依頼の要点の形が違う');
    if(txt.length>1500)bad.push('依頼の要点が'+txt.length+'字（工場へのメールは1,500字で切れる）');
    if(errs.length)bad.push('エラー '+errs.join(';'));
    if(bad.length)ng++;
    console.log((bad.length?'NG ':'OK ')+cs.id.padEnd(10)+' 品目 '+r0.cats.join(',')+' ／ 質問 '+asked.join(',')+' ／ '+txt.length+'字'+(bad.length?'\n   - '+bad.join('\n   - '):''));
    await c.close()}
  await b.close();console.log(ng?`\n✗ ${ng}件 NG`:'\n✓ すべてOK');process.exit(ng?1:0)})();
