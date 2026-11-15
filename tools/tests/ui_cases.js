// 全面リニューアル（2026-11）の画面の流れを確かめる：トップ→整理した条件→会社→確認して送る→受付。
// スマホ（375・320）とPC、日英中で、横スクロールが出ないこと・ページのエラーがないことも確かめる。
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから node tools/tests/ui_cases.js [http://localhost:8765/] [スクショのフォルダ]
const {chromium}=require('playwright');const path=require('path');
const [base='http://localhost:8765/',shots]=process.argv.slice(2);
(async()=>{const b=await chromium.launch();let ng=0;const ok=(n,c,x)=>{console.log((c?'OK ':'NG ')+n+(c?'':' '+JSON.stringify(x)));if(!c)ng++};
  const ctx=async(w,h,lang)=>{const c=await b.newContext({viewport:{width:w,height:h}});await c.addInitScript(l=>localStorage.setItem('katachi-lang',JSON.stringify({lang:l})),lang);return c};
  const hs=p=>p.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
  /* 1. トップは入力欄が主役：見出し・入力欄・添付・「相談を始める」が最初の画面に収まり、数量や会社の種類を選ばせない */
  {const c=await ctx(375,667,'ja');await c.route(/script\.google\.com|googletagmanager/,r=>r.fulfill({status:200,body:'{}'}));const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    const r=await p.evaluate(()=>{const v=s=>{const e=document.querySelector(s);if(!e)return false;const z=e.getBoundingClientRect();return z.bottom<=innerHeight&&z.width>0};
      return {h1:document.querySelector('.hero h1').textContent,ta:v('#idea'),go:v('#cmp button.pri'),clip:v('#pick'),qty:document.querySelectorAll('#cmp [data-qty]').length,goTxt:document.querySelector('#cmp button.pri').textContent.trim()}});
    ok('トップの見出しは「作りたいものを、カタチに。」',r.h1==='作りたいものを、カタチに。',r.h1);
    ok('入力欄・添付・「相談を始める」が最初の画面に入る（375×667）',r.ta&&r.go&&r.clip,r);
    ok('トップで数量を選ばせない',r.qty===0,r);ok('ボタンの文言は「相談を始める」',r.goTxt==='相談を始める',r.goTxt);
    ok('横スクロールなし（トップ 375）',await hs(p)<=0,await hs(p));
    // 空のまま押すと進まない
    await p.click('#cmp button.pri');ok('空のまま押しても進まない',await p.evaluate(()=>location.hash===''));
    // 添付：名前の省略・外す・元に戻す
    await p.setInputFiles('#fileIn',{name:'とても長いファイルの名前のサンプル_図面_最終版_v12.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4 test')});
    let f=await p.evaluate(()=>({n:document.querySelectorAll('#files .fchip').length,t:document.querySelector('#files .fchip .n')?.textContent||''}));
    ok('添付するとチップが出て、名前は拡張子を残して省略',f.n===1&&/…/.test(f.t)&&/\.pdf$/.test(f.t),f);
    await p.click('#files .fx');f=await p.evaluate(()=>({n:document.querySelectorAll('#files .fchip').length,u:!!document.querySelector('[data-fundo]')}));
    ok('外すと「元に戻す」が出る',f.n===0&&f.u,f);await p.click('[data-fundo]');
    ok('「元に戻す」で戻る',await p.evaluate(()=>document.querySelectorAll('#files .fchip').length)===1);
    // ほかの始め方
    ok('入力欄の上で図面の「ある／ない」を選べる',await p.$$eval('.hasdw [data-start]',x=>x.length)===2);
    // 図面がない人のガイド：押すと入力欄に1行足し、書いた点に ✓ が付く。押し直すと同じ行を置き換える
    await p.fill('#idea','');await p.click('[data-gadd="qty"]:nth-child(3)');await p.click('[data-gadd="qty"]:nth-child(2)');await p.click('[data-gadd="mat"]:nth-child(3)');
    let g=await p.evaluate(()=>({v:document.querySelector('#idea').value,ok:[...document.querySelectorAll('#gde li.gdok')].map(l=>l.dataset.gk),n:document.querySelectorAll('#gde [data-gk]').length}));
    ok('ガイドは7項目（何を・数量・大きさ・材料・用途・電子部品・時期）',g.n===7,g);
    ok('押すと入力欄に足し、同じ項目は置き換える',g.v==='数量：10個くらい\n材料：布',g.v);
    ok('書いた点に ✓ が付く',g.ok.includes('qty')&&g.ok.includes('mat')&&!g.ok.includes('size'),g.ok);
    ok('ガイドに写真・似た製品のURL・例文',await p.$$eval('#gde [data-gpick],#gde [data-gref],#gde [data-gex]',x=>x.length)===3);
    await p.fill('#idea','アルミの部品');await p.click('.hasdw [data-start="draw"]');
    ok('「ある」に切り替えても書いた文は残り、図面の添付が出る',await p.inputValue('#idea')==='アルミの部品'&&await p.$$eval('#dPick',x=>x.length)===1);
    await p.click('.hasdw [data-start="idea"]');await p.fill('#idea','');
    if(shots)await p.screenshot({path:path.join(shots,'ui_top.png')});
    // 2. 書いて進む → 整理した条件と会社
    await p.fill('#idea','店のロゴを入れたトートバッグを綿で100個作りたい');await p.click('#cmp button.pri');
    await p.waitForSelector('.stepnow',{timeout:30000});await p.waitForTimeout(300);
    const m=await p.evaluate(()=>{const rows=[...document.querySelectorAll('#mCond .cdr')].map(r=>[r.querySelector('dt').textContent,r.querySelector('.cdt').textContent]);
      return {hash:location.hash,rows,step:document.querySelector('.stepbar li.on')?.textContent,sel:(window.KATACHI_SEL?window.KATACHI_SEL():null),q:!!document.querySelector('#mCond .cdq'),files:document.querySelectorAll('.rqf .fchip').length,dock:!!document.querySelector('#gRfq')}});
    ok('②は #co、進み具合は「会社を選ぶ」',m.hash==='#co'&&/会社を選ぶ/.test(m.step),m);
    ok('整理した条件：数量・材料は「あなたの入力」',m.rows.some(([t,l])=>t==='数量'&&l==='あなたの入力')&&m.rows.some(([t,l])=>t==='材料'&&l==='あなたの入力'),m.rows);
    ok('整理した条件：未定の項目は「未定」',m.rows.some(([,l])=>l==='未定'),m.rows);
    ok('未定の点は畳んだ任意の質問（開かなくても送れる）',m.q&&await p.$eval('#mCond .cdq',d=>!d.open),m);
    ok('②に添付が引き継がれる',m.files===1,m);ok('下のバーに送るボタン',m.dock,m);
    ok('横スクロールなし（② 375）',await hs(p)<=0,await hs(p));
    // 任意の質問に答えても、選んだ会社は変わらない
    const before=await p.$eval('#dock .gdl small',x=>x.textContent);
    await p.evaluate(()=>{const d=document.querySelector('#mCond .cdq');d.open=true});await p.click('#mCond [data-cdu]');await p.waitForTimeout(400);
    const after=await p.$eval('#dock .gdl small',x=>x.textContent);
    ok('「相談したい」を選ぶと、その項目は「相談したい」になる',await p.$$eval('#mCond .cdv',a=>a.some(x=>x.textContent==='相談したい')));
    ok('任意の質問に答えても、選んだ会社は変わらない',before===after,{before,after});
    if(shots)await p.screenshot({path:path.join(shots,'ui_list.png'),fullPage:true});
    // 3. 確認して送る
    await p.click('#gRfq');await p.waitForSelector('#rf',{timeout:10000});
    ok('送る画面の進み具合は「確認して送る」',/確認して送る/.test(await p.$eval('#ov .stepbar li.on',x=>x.textContent)));
    await p.evaluate(()=>document.querySelector('#rf').requestSubmit());await p.waitForTimeout(200);
    ok('必須が空なら止まって知らせる',/入力してください/.test(await p.$eval('#rfErr',x=>x.textContent)));
    ok('横スクロールなし（送る画面 375）',await hs(p)<=0,await hs(p));
    ok('ページのエラーなし（ja 375）',!errs.length,errs);await c.close()}
  /* 4. 二重送信しない・通信の失敗で入力が消えない（受付をまねる） */
  {const c=await ctx(1280,900,'ja');let n=0,fail=true;
    await c.route(/script\.google\.com/,async r=>{let j={};try{j=JSON.parse(r.request().postData()||'{}')}catch(e){}if(j.type==='rfq'){n++;if(fail)return r.abort();await new Promise(z=>setTimeout(z,600))}return r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'})});
    await c.route(/googletagmanager/,r=>r.fulfill({status:200,body:''}));
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    // FORM_URL がある本番の形で試す（localhost でも送る）
    await p.fill('#idea','アルミの部品を10個つくりたい。図面があります');await p.click('#cmp button.pri');await p.waitForSelector('.stepnow,#mPlans',{timeout:30000});await p.waitForTimeout(300);
    await p.evaluate(()=>window.KATACHI_RFQ(Object.keys(window.KATACHI_DATA.companies).filter(k=>(window.KATACHI_DATA.companies[k].country||'JP')==='JP').slice(0,1)));await p.waitForSelector('#rf');
    await p.evaluate(()=>{const f=document.querySelector('#rf');document.querySelector('#qkWho .qkopt')?.click();document.getElementById('f-mail').value='a@example.com';document.getElementById('f-agree').checked=true;const ms=document.getElementById('f-mailsend');if(ms)ms.checked=false});
    const hasForm=await p.evaluate(()=>!!document.querySelector('#rf'));
    await p.evaluate(()=>{const f=document.querySelector('#rf');f.requestSubmit();f.requestSubmit()});await p.waitForTimeout(1500);
    const e1=await p.$eval('#rfErr',x=>x.textContent).catch(()=>'');const still=await p.evaluate(()=>!!document.querySelector('#rf')&&document.getElementById('f-mail').value);
    ok('2回押しても1回だけ送る',n===1,{n});
    ok('通信に失敗したら、入力を残して知らせる',hasForm&&/送れませんでした/.test(e1)&&still==='a@example.com',{e1,still});
    fail=false;n=0;await p.evaluate(()=>document.querySelector('#rf').requestSubmit());await p.waitForTimeout(2500);
    ok('もう一度押すと送れて、送ったあとの流れが出る',n===1&&/担当者/.test(await p.$eval('#ov',x=>x.textContent)),{n});
    if(shots)await p.screenshot({path:path.join(shots,'ui_done.png')});
    ok('ページのエラーなし（送信）',!errs.length,errs);await c.close()}
  /* 5. 日英中 × 幅：横スクロールなし・エラーなし */
  for(const lang of ['ja','en','zh'])for(const [w,h] of [[320,640],[375,812],[1280,860]]){const c=await ctx(w,h,lang);await c.route(/script\.google\.com|googletagmanager/,r=>r.fulfill({status:200,body:'{}'}));
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);await p.waitForTimeout(300);const h1=await hs(p);
    await p.fill('#idea',{ja:'ステンレスの折りたたみ焚き火台を200個つくりたい',en:'I want to make 200 folding stainless fire pits',zh:'想做200个不锈钢折叠篝火台'}[lang]);await p.click('#cmp button.pri');await p.waitForSelector('.stepnow,.empty',{timeout:30000}).catch(()=>{});await p.waitForTimeout(300);const h2=await hs(p);
    await p.click('#gRfq').catch(()=>{});await p.waitForTimeout(500);const h3=await hs(p);
    ok(`横スクロールなし・エラーなし（${lang} ${w}px：トップ/②/送る）`,h1<=0&&h2<=0&&h3<=0&&!errs.length,{h1,h2,h3,errs});await c.close()}
  await b.close();console.log(ng?ng+'件 NG':'すべてOK');process.exit(ng?1:0)})();
