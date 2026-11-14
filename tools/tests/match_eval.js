// マッチング精度の評価：依頼文ごとに③の「おすすめの頼み方」で選ばれる会社と、工程ごとの上位3社を取り出す
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから
//   node tools/tests/match_eval.js [http://localhost:8765/] [出力JSON]
// 依頼文は tools/tests/match_cases.json（Noriの実依頼3件＋よくある依頼）。判定は match_judge.py
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const [base='http://localhost:8765/',out='']=process.argv.slice(2);
const cases=JSON.parse(fs.readFileSync(process.env.CASES||path.join(__dirname,'match_cases.json'),'utf8'));
(async()=>{const b=await chromium.launch();const res=[];
  for(const cs of cases){const c=await b.newContext({viewport:{width:1280,height:900}});
    await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com|googletagmanager|google-analytics/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    // 画面の中の変数（S・GDB）を読むため、テストのときだけ index.html に出口を1つ足す
    await c.route(u=>/\/(index\.html)?(#.*)?$/.test(new URL(u).pathname+new URL(u).hash)&&!/\.(js|json|css|png|svg)$/.test(new URL(u).pathname),async r=>{const resp=await r.fetch();let body=await resp.text();
      body=body.replace('window.KATACHI_RL=()=>S.lastRL;','window.KATACHI_RL=()=>S.lastRL;window.__KM=()=>({S,GDB});');r.fulfill({response:resp,body})});
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    const text=cs.file?fs.readFileSync(path.join(__dirname,'specs',cs.file),'utf8'):cs.text;
    await p.fill('#idea',text);await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
    await p.waitForSelector('#mFspec,#mNext,[data-gonext]',{timeout:30000}).catch(()=>{});await p.waitForTimeout(300);
    await p.evaluate(()=>{location.hash='co'});await p.waitForSelector('#mPlans,.mstep',{timeout:30000}).catch(()=>{});await p.waitForTimeout(600);
    const r=await p.evaluate(()=>{const {S,GDB}=window.__KM();const row=x=>x&&{n:x[0],ct:x[1],pref:x[2],lv:x[10],sum:(x[11]||'').slice(0,90)};
      const find=n=>GDB.c.find(x=>x[0]===n)||(document.querySelector('.mkr')&&null);
      const mk=!!document.querySelector('.mkr');
      const A=S.anal||{};return {concept:A.concept?(A.concept.id||A.concept.k||'')+'/'+(A.concept.name||''):'',codes:A.codes||[],maker:mk,plan:S.planPick||'',rule:(S.lastRL||{}).id||'',
        picked:(S.gsel||[]).map(n=>({step:(S.gstep||{})[n]||'',...(row(find(n))||{n})})),
        secs:(S.secs||[]).map(s=>({c:s.c,n:s.list.length,top:s.list.slice(0,3).map(row)}))}});
    r.id=cs.id;r.errs=errs;res.push(r);
    console.log(`\n## ${cs.id} ${r.maker?'[完成品メーカー]':''} plan=${r.plan} rule=${r.rule} concept=${r.concept}\n  工程: ${r.codes.join(', ')}`);
    for(const x of r.picked)console.log(`  ★ ${x.step} | ${x.n} (${x.pref||x.ct||''}, ${x.lv||''}) ${x.sum||''}`);
    await c.close()}
  await b.close();if(out)fs.writeFileSync(out,JSON.stringify(res,null,1))})();
