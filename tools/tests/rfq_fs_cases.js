// 見積依頼フォームの「見積に要ること」（どこまで頼むか・手元の資料・数量3段階・品目別の項目）の確認
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから
//   node tools/tests/rfq_fs_cases.js [http://localhost:8765/] [スクショを保存するフォルダ]
const {chromium}=require('playwright');const path=require('path');
const [base='http://localhost:8765/',shots]=process.argv.slice(2);
const cases=[
  {text:'散歩中の犬の心拍を測れる首輪を作りたい。Bluetoothでスマホに送る。図面はない。',must:['fs-scope','fs-docs','fs-qs','fs-qf','fs-qc','fs-escope'],chips:['電子の部分でどこまで頼むか','電源'],noPow:true,scope:'設計から（図面がない）',alt:'#fs-power'},
  {text:'店のロゴを入れたトートバッグを綿で100個作りたい。ロゴのデータはあります。',must:['fs-scope','fs-docs','fs-fabric','fs-sizes'],chips:['生地','サイズ展開と色数']},
  {text:'自社ブランドのドライフルーツミックスを袋詰めで500袋つくりたい',must:['fs-recipe','fs-form'],chips:['配合・レシピ']},
];
(async()=>{const b=await chromium.launch();let ng=0;
  for(const[i,cs]of cases.entries()){const c=await b.newContext({viewport:{width:1280,height:900}});
    await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    await p.fill('#idea',cs.text);await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
    await p.waitForSelector('#mFspec',{timeout:20000});await p.waitForTimeout(400);
    await p.evaluate(()=>window.KATACHI_RFQ([]));await p.waitForSelector('#rf',{timeout:10000});await p.waitForTimeout(300);
    const ids=await p.$$eval('#rf [id^="fs-"]',a=>a.map(x=>x.id));
    const chips=await p.$$eval('.ready .rc span',a=>a.map(x=>x.textContent.replace('✓ ','')));
    const pow=await p.$('#f-pow');
    // 1つ答える → 仕様書の答えに保存され、見積に必要な点の数が増えるか
    // 文章に書いてあれば最初から選ばれている（例：「図面はない」→設計から）。そのときは品目別の項目（電源）で確かめる
    const pre=await p.$eval('#fs-scope',x=>x.value);const fk=pre?cs.alt:'#fs-scope';
    const before=await p.$$eval('.ready .rc span.on',a=>a.length);
    await p.selectOption(fk,{index:1});await p.waitForTimeout(200);
    const after=await p.$$eval('.ready .rc span.on',a=>a.length);
    const saved=await p.evaluate(()=>Object.keys(localStorage).some(k=>k.startsWith('katachi-fa-')&&(o=>o.scope||o.power)(JSON.parse(localStorage.getItem(k)))));
    const sent=await p.$eval(fk,x=>x.value);
    const ok=cs.must.every(x=>ids.includes(x))&&cs.chips.every(x=>chips.includes(x))&&(!cs.noPow||!pow)&&after===before+1&&saved&&!!sent&&(!cs.scope||pre===cs.scope)&&!errs.length;if(!ok)ng++;
    console.log(ok?'OK':'NG',cs.text.slice(0,24),JSON.stringify({ids,chips,pre,before,after,saved,pow:!!pow}),errs.join(';'));
    if(shots){await p.evaluate(()=>{const g=[...document.querySelectorAll('#rf details.grp')].find(d=>d.querySelector('[id^="fs-"]'));g&&g.scrollIntoView()});await p.waitForTimeout(300);await p.screenshot({path:path.join(shots,'rfq_fs'+i+'.png')})}
    await c.close()}
  await b.close();console.log(ng?ng+'件 NG':'すべてOK');process.exit(ng?1:0)})();
