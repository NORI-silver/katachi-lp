// 工場の返事ページ（/reply/?k=鍵）の確認。受付（GAS）はまねた応答に差し替える。
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから node tools/tests/reply_cases.js [base] [スクショのフォルダ]
const {chromium}=require('playwright');const path=require('path');
const [base='http://localhost:8765/',shots]=process.argv.slice(2);
const KEY='abcdEFGH2345jkmnPQRS6789';
const VIEW={ok:true,company:'株式会社サンプル精工',state:null,when:'',price:'',msg:'',answered:'',req:{id:'K261114-AB12',kind:'見積の依頼',summary:'店のロゴを入れたトートバッグを綿で100個作りたい',qty:'100個',due:'2027年3月まで',files:1,
 steps:['縫製・布・革製品'],mat:'綿',flex:'急がない（空き時期でよい）',from:'2027-01',to:'2027-03',bundle:true,items:[['用途・使う人','店頭での販売'],['工場向け仕様書（KATACHIが整理）','寸法: 380×420mm\n持ち手: 60cm']]}};
(async()=>{const b=await chromium.launch();let ng=0;const ok=(n,c,x)=>{console.log((c?'OK ':'NG ')+n+(c?'':' '+JSON.stringify(x||'')));if(!c)ng++};
 for(const [ans,w] of [['accept',1280],['question',390],['decline',1280]]){
  const c=await b.newContext({viewport:{width:w,height:900}});await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
  const sent=[];await c.route(/script\.google\.com/,r=>{const j=JSON.parse(r.request().postData()||'{}');sent.push(j);r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(j.type==='offer'?VIEW:{ok:true,state:j.answer})})});
  const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base+'reply/?k='+KEY);
  await p.waitForSelector('.choice');const txt=await p.textContent('#app');
  ok(ans+' 要点を表示',txt.includes('トートバッグ')&&txt.includes('2027-01 〜 2027-03')&&txt.includes('まとめて作ってよい'));
  ok(ans+' 依頼者の情報は出さない',!/@|電話/.test(txt));
  if(shots&&ans==='accept')await p.screenshot({path:path.join(shots,'reply_view.png'),fullPage:true});
  await p.click(`.choice[data-a="${ans}"]`);
  if(ans==='question'){await p.click('#rf .btn');ok('質問は空だと送らない',(await p.textContent('#rf')).includes('質問を書いてください')&&sent.filter(x=>x.type==='offerreply').length===0);await p.fill('#r-msg','材料の指定はありますか');}
  if(ans==='accept'){await p.fill('#r-when','2027年1月から');await p.fill('#r-price','1枚 800円前後');}
  if(ans==='decline'){await p.check('.rs input[value="時期が合わない"]');}
  if(shots)await p.screenshot({path:path.join(shots,'reply_'+ans+'.png'),fullPage:true});
  await p.click('#rf .btn');await p.waitForSelector('.done');
  const r=sent.find(x=>x.type==='offerreply');
  ok(ans+' 送った内容',r&&r.k===KEY&&r.answer===ans&&(ans!=='accept'||r.when==='2027年1月から')&&(ans!=='decline'||r.reasons[0]==='時期が合わない'),r);
  await p.click('#chg');ok(ans+' 答えを直せる',await p.$('.choice[aria-pressed="true"]')!==null);
  ok(ans+' エラーなし',!errs.length,errs);await c.close()}
 // 英語・鍵が不正
 const c=await b.newContext();await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'en'})));
 await c.route(/script\.google\.com/,r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(VIEW)}));
 const p=await c.newPage();await p.goto(base+'reply/?k='+KEY);await p.waitForSelector('.choice');ok('英語',(await p.textContent('#app')).includes('Accept'));
 await p.goto(base+'reply/?k=short');await p.waitForSelector('.err');ok('不正な鍵',(await p.textContent('.err')).includes("isn't valid"));
 await b.close();console.log(ng?ng+'件 NG':'すべてOK');process.exit(ng?1:0)})();
