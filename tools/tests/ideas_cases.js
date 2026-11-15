// 作例から選ぶ（#ideas）はトップとは別の画面（Nori 2026-11-15）。使い方: node tools/tests/ideas_cases.js [http://localhost:8765/]
const {chromium}=require('playwright');const base=process.argv[2]||'http://localhost:8765/';(async()=>{const b=await chromium.launch();let ng=0;const ok=(n,c,x)=>{console.log((c?'OK ':'NG ')+n+(c?'':' '+JSON.stringify(x)));if(!c)ng++};
for(const [w,h] of [[375,812],[1280,860]]){const c=await b.newContext({viewport:{width:w,height:h}});await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));await c.route(/script\.google\.com|googletagmanager/,r=>r.fulfill({status:200,body:'{}'}));
const p=await c.newPage();const er=[];p.on('pageerror',e=>er.push(e.message));await p.goto(base);await p.waitForTimeout(500);
ok('トップに作例ギャラリーがない '+w,await p.$$eval('#ideas',x=>x.length)===0);
await p.fill('#idea','メモ');await p.click('#toIdeas');await p.waitForSelector('#ideas .icard',{timeout:10000});
ok('作例から選ぶ → #ideas に一覧 '+w,await p.evaluate(()=>location.hash==='#ideas'&&document.querySelectorAll('#ideas .icard').length>3));

ok('横スクロールなし '+w,await p.evaluate(()=>document.documentElement.scrollWidth-innerWidth)<=0);
await p.click('[data-ind]:nth-child(3)');await p.waitForTimeout(300);
await p.click('[data-ihome]');await p.waitForTimeout(400);ok('← 入力に戻ると書いた文が残る '+w,await p.inputValue('#idea')==='メモ');
await p.goBack().catch(()=>{});await p.evaluate(()=>location.hash='ideas');await p.waitForSelector('#ideas .icard');
await p.click('#ideas [data-idea]');await p.waitForSelector('.stepnow,.empty',{timeout:30000});ok('この内容で探す → 会社を選ぶ（まず未定の点を聞く） '+w,await p.evaluate(()=>location.hash==='#co'&&!!document.querySelector('#mCq')&&!document.querySelector('#gRfq')));
for(let i=0;i<10&&await p.$('#mCq');i++){await p.click('#mCq [data-cqu]');await p.waitForTimeout(300)}ok('答えると送るボタン '+w,await p.evaluate(()=>!!document.querySelector('#gRfq')));
await p.evaluate(()=>location.hash='ideas');await p.waitForSelector('#ideas [data-iedit]');await p.click('#ideas [data-iedit]');await p.waitForTimeout(400);
ok('書き換えて使う → トップの入力欄に入る '+w,await p.evaluate(()=>location.hash===''&&document.querySelector('#idea').value.length>10));
ok('エラーなし '+w,!er.length,er);await c.close()}
await b.close();console.log(ng?ng+' NG':'すべてOK');process.exit(ng?1:0)})();
