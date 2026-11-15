// マッチング精度の回帰テスト（Nori 2026-11-15「マッチング精度が命」）
// 依頼文ごとに、サイトの③で実際に出る会社（★の会社・完成品メーカー・工程ごとの候補）を取り出し、
// 依頼ごとの「正解の基準」（tools/tests/match_cases.json の ok / ng / gold / code）で採点する。採点は match_judge.js。
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから
//   node tools/tests/match_eval.js [http://localhost:8765/] [出力JSON] [--check]
//   --check: tools/tests/match_baseline.json より悪くなったら失敗（PRのチェックで使う）
//   CASES=別のファイル.json / ONLY=id1,id2 で依頼を絞れる。BASELINE=1 で基準（match_baseline.json）を今の結果で書き直す
//   TEXT="依頼文" で1件だけ流し、サイトに出る会社を見る
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const judge=require('./match_judge.js');
const argv=process.argv.slice(2);const check=argv.includes('--check');const [base='http://localhost:8765/',out='']=argv.filter(a=>!a.startsWith('--'));
let cases=JSON.parse(fs.readFileSync(process.env.CASES||path.join(__dirname,'match_cases.json'),'utf8'));
// TEXT="依頼文" で1件だけ流し、サイトに出る会社をそのまま見る（会社名を人に答える前の確認用。Nori 2026-11-15「サイトの候補を確かめてから」）
if(process.env.TEXT)cases=[{id:'text',text:process.env.TEXT}];
if(process.env.ONLY){const s=new Set(process.env.ONLY.split(','));cases=cases.filter(c=>s.has(c.id))}
async function one(b,cs){const c=await b.newContext({viewport:{width:1280,height:900}});
  try{
  await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
  await c.route(/script\.google\.com|googletagmanager|google-analytics/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
  // 画面の中の変数（S・GDB）と関数を読むため、テストのときだけ index.html に出口を1つ足す
  await c.route(u=>/\/(index\.html)?(#.*)?$/.test(new URL(u).pathname+new URL(u).hash)&&!/\.(js|json|css|png|svg)$/.test(new URL(u).pathname),async r=>{const resp=await r.fetch();let body=await resp.text();
    body=body.replace('window.KATACHI_RL=()=>S.lastRL;','window.KATACHI_RL=()=>S.lastRL;window.__KM=()=>({S,GDB,makersFor,CAPN});');r.fulfill({response:resp,body})});
  const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
  const text=cs.file?fs.readFileSync(path.join(__dirname,'specs',cs.file),'utf8'):cs.text;
  await p.fill('#idea',text);await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
  await p.waitForSelector('#mFspec,#mNext,[data-gonext],#mPlans,.mstep,.stepnow',{timeout:30000}).catch(()=>{});await p.waitForTimeout(300);
  await p.evaluate(()=>{location.hash='co'});await p.waitForSelector('#mPlans,.mstep',{timeout:30000,state:'attached'}).catch(()=>{});await p.waitForTimeout(600);
  const r=await p.evaluate(gold=>{const {S,GDB,makersFor,CAPN}=window.__KM();const row=x=>x&&{n:x[0],pref:x[1]==='JP'?x[2]:x[1],lv:x[10],sum:x[11]||'',caps:(x[5]||[]).map(i=>GDB.caps[i])};
    const byN=new Map(GDB.c.map(x=>[x[0],x]));
    const A=S.anal||{};const mkOn=!!document.querySelector('.mkr');const MK=mkOn&&A.codes&&A.codes.length?makersFor(A):null;
    const secs=(S.secs||[]).map(s=>({c:s.c,name:CAPN[s.c]||s.c,n:s.list.length,top:s.list.slice(0,10).map(row),all:s.list}));
    // 正解の会社（gold の言葉が社名・概要にある、注文できる会社）が、候補のどこに出るか
    let G=null;if(gold){const re=new RegExp(gold);const gs=GDB.c.filter(x=>re.test((x[0]||'')+' '+(x[11]||'')));
      const rank=new Map();const put=(n,k)=>{if(!rank.has(n)||rank.get(n)>k)rank.set(n,k)};
      secs.forEach(s=>s.all.forEach((x,i)=>put(x[0],i)));(MK?MK.rows:[]).forEach((x,i)=>put(x[0],i));
      G={n:gs.length,inList:gs.filter(x=>rank.has(x[0])).length,top20:gs.filter(x=>rank.has(x[0])&&rank.get(x[0])<20).length,
        missed:gs.filter(x=>!rank.has(x[0])).slice(0,8).map(x=>x[0]+'｜'+(x[11]||'').slice(0,40)+'｜'+(x[5]||[]).map(i=>GDB.caps[i]).join(','))}}
    return {concept:A.concept?(A.concept.id||'')+'/'+(A.concept.name||''):'',codes:A.codes||[],plan:S.planPick||'',rule:(S.lastRL||{}).id||'',
      maker:MK?{k:MK.k,rows:MK.rows.map(row)}:null,
      picked:(S.recSel||S.gsel||[]).map(n=>({step:(S.gstep||{})[n]||'',...(row(byN.get(n))||{n})})),
      secs:secs.map(({all,...s})=>s),gold:G}},cs.gold||'');
  r.id=cs.id;r.errs=errs;return r}finally{await c.close()}}
(async()=>{const b=await chromium.launch();const res=new Array(cases.length);let next=0;
  const N=+(process.env.PAR||4);
  await Promise.all(Array.from({length:N},async()=>{while(next<cases.length){const i=next++;
    try{res[i]=await one(b,cases[i])}catch(e){res[i]={id:cases[i].id,error:String(e).slice(0,200),picked:[],secs:[],codes:[]}}}}));
  await b.close();
  const J=judge.run(cases,res);
  for(const x of J.cases)console.log(`${x.v} ${x.id.padEnd(18)} ${x.plan.padEnd(5)} ${x.picks.map(p=>(p.ok?'○':p.ng?'×':'△')+p.n).join(' / ')}${x.codeMiss?'  ［工程の読み違い］':''}${x.gold?`  正解社 ${x.gold.top20}/${x.gold.n}`:''}`);
  if(process.env.TEXT){const r=res[0];console.log(`工程: ${(r.codes||[]).join(', ')}\n案: ${r.plan}`);for(const p of r.picked)console.log(`★ ${p.step} | ${p.n}（${p.pref||''}）${p.sum||''}`);
    if(r.maker)console.log('完成品メーカー: '+r.maker.rows.slice(0,8).map(x=>x.n).join('、'));for(const s of r.secs)console.log(`${s.name}（${s.n}社）: `+s.top.slice(0,5).map(x=>x.n).join('、'));return}
  console.log('\n'+judge.summaryText(J.sum));
  // AI経由（API・MCP の search_companies）の上位が、サイトの③の★と同じ会社か（Nori 2026-11-15「MCPの候補がサイトの★と一致しない」）。
  // 先に `node api/build.mjs` でサイトの JS を API 用に取り出しておく。API=0 で省く
  let apiBad=[],apiN=0;
  if(process.env.API!=='0'&&fs.existsSync(path.join(__dirname,'../../api/src/gen/site.js'))){const core=await import(path.join(__dirname,'../../api/src/core.js'));
    cases.forEach((cs,i)=>{const r=res[i];const text=cs.file?fs.readFileSync(path.join(__dirname,'specs',cs.file),'utf8'):cs.text;if(!text||text.length>200||!r||r.error)return;
      const site=r.plan==='maker'&&r.maker?[r.maker.rows[0]&&r.maker.rows[0].n]:(r.picked||[]).filter(p=>(p.step||'')!=='設計（図面・3Dデータ）').map(p=>p.n);if(!site.length||!site[0])return;
      let top;try{top=core.searchCompanies({product:text}).companies.slice(0,3).map(c=>c.name)}catch(e){return}
      apiN++;const ok=site.includes(top[0])&&(site.length>=3?top.every(n=>site.includes(n)):site.every(n=>top.includes(n)));
      if(!ok)apiBad.push(`${cs.id}：サイト★ ${site.slice(0,3).join('・')} ／ API ${top.join('・')}`)});
    console.log(`AI経由（API・MCP）の上位3社がサイトの★と同じ ${apiN-apiBad.length}/${apiN}件`+(apiBad.length?'\n  '+apiBad.join('\n  '):''))}
  if(out)fs.writeFileSync(out,JSON.stringify({sum:J.sum,cases:J.cases,raw:res},null,1));
  if(process.env.BASELINE){const s=J.sum;fs.writeFileSync(path.join(__dirname,'match_baseline.json'),JSON.stringify({date:new Date().toISOString().slice(0,10),note:'node tools/tests/match_eval.js --check の基準。精度が上がったら BASELINE=1 を付けて流し、書き直す',ok:s.ok,mid:s.mid,ng:s.ng,codeMiss:s.codeMiss,top5:s.top5,recall:s.recall,recall20:s.recall20,verdicts:s.verdicts},null,1)+'\n');console.log('基準を書き直しました')}
  if(check){const bl=JSON.parse(fs.readFileSync(path.join(__dirname,'match_baseline.json'),'utf8'));const bad=judge.compare(J.sum,bl);
    for(const x of apiBad)bad.push('AI経由の候補がサイトと違う '+x);
    if(bad.length){console.log('\n✗ マッチング精度が基準より下がりました:\n- '+bad.join('\n- '));process.exit(1)}
    console.log('\n✓ 基準（match_baseline.json）以上です')}
})();
