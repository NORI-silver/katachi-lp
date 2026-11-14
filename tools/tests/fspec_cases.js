// 工場向け仕様書の確認（文章→仕様書・質問・工場に出せる度）
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから
//   node tools/tests/fspec_cases.js [http://localhost:8765/] [スクショを保存するフォルダ]
const {chromium}=require('playwright');const fs=require('fs'),path=require('path');
const [base='http://localhost:8765/',shots]=process.argv.slice(2);
const cases=[
  {file:'smart_collar_nori.txt',cats:['elec','pet'],mode:'design'},
  {text:'店のロゴを入れたトートバッグを綿で100個作りたい。ロゴのデータはあります。',cats:['apparel'],mode:'more'},
  {text:'アルミの削り出しでカメラ用のブラケットを10個。図面があります。3か月以内にほしい。',cats:['metal'],mode:'more'},
  // 既製品をもとに作る：参考品の値は「参考品」、変えるところ・採寸／スキャン・権利の質問が付くか
  {text:'【参考にした既製品】K-9カート（wancare.jp）\nURL：https://wancare.jp\n参考品の大きさ：幅30×長さ50cm\n参考品の素材：アルミパイプ、EVAタイヤ\n【変えたいところ】素材、サイズ\n【どう変えたいか】もっと軽く、超小型犬向けに\n※参考品をそのまま複製せず、特許・意匠・商標を確かめたうえでオリジナルとして作りたい',cats:['pet'],mode:'design',ref:true},
];
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});let ng=0;
  for(const[i,cs]of cases.entries()){const c=await b.newContext({viewport:{width:1280,height:900}});
    await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    const text=cs.text||fs.readFileSync(path.join(__dirname,'specs',cs.file),'utf8');
    await p.fill('#idea',text);await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
    await p.waitForSelector('#mFspec',{timeout:20000});await p.waitForTimeout(500);
    const r=await p.evaluate(()=>{const S={fs:window.KATACHI_FS()};const V=S.fs.V;return {cats:S.fs.cats.map(k=>k.id),mode:S.fs.mode,score:S.fs.score,ask:S.fs.ask.length,fq:S.fs.fq.length,name:(V.name||{}).v,ref:!!S.fs.ref&&!!(V.diff||{}).v&&(V.mat||{}).lv==='参考品'&&S.fs.fq.some(q=>/3Dスキャン/.test(q))&&!!document.querySelector('#fsJpp')}});
    // 質問に「わからない」と1つ答えて反映 → 仮が入るか
    const q=await p.$('.fsqi');let after=null;if(q){await q.$eval('.fsb:last-child',x=>x.click());await p.click('#fsApply');await p.waitForTimeout(300);after=await p.evaluate(()=>window.KATACHI_FS().score)}
    const ok=cs.cats.every(x=>r.cats.includes(x))&&(!cs.mode||r.mode===cs.mode)&&(!cs.ref||r.ref)&&!errs.length;if(!ok)ng++;
    console.log(ok?'OK':'NG',(cs.file||cs.text).slice(0,30),JSON.stringify(r),'after',after,errs.join(';'));
    if(shots){await p.evaluate(()=>document.querySelector('#mFspec').scrollIntoView());await p.waitForTimeout(400);await p.screenshot({path:path.join(shots,'fspec'+i+'.png'),fullPage:false})}
    await c.close()}
  // 貼り戻しJSON：新しい項目（scope・due・budget・docs・category_items）が入り、根拠の原文がない値は落ちるか
  {const c=await b.newContext();const p=await c.newPage();await p.goto(base);
    const r=await p.evaluate(()=>{const t='犬用の首輪型デバイス。図面はありません。予算は1台2万円以内。電池は充電式で1週間もつこと。';
      const j='```json\n'+JSON.stringify({scope:{value:'設計から',quote:'図面はありません'},budget:{value:'1台2万円以内',quote:'予算は1台2万円以内'},docs:[{value:'なし',quote:'図面はありません'}],category_items:[{item:'電源',value:'充電式・1週間',quote:'電池は充電式で1週間もつこと'},{item:'電源',value:'3年',quote:'書いていない文'}]})+'\n```';return window.KATACHI_SX(j,t)});
    const ok=r&&r.scope.value==='設計から'&&r.budget.value==='1台2万円以内'&&r.docs.length===1&&r.category_items.length===1;if(!ok)ng++;console.log(ok?'OK':'NG','貼り戻しJSON（新しい項目）');await c.close()}
  await b.close();console.log(ng?ng+'件 NG':'すべてOK');process.exit(ng?1:0)})();
