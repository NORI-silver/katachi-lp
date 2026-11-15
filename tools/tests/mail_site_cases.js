// 見積の依頼で「メールですぐ届ける」が出るか、送る内容に入るか、確認メールのボタン（?send=）で送った結果が出るか。
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから node tools/tests/mail_site_cases.js [http://localhost:8765/] [スクショのフォルダ]
const {chromium}=require('playwright');const path=require('path');
const [base='http://localhost:8765/',shots]=process.argv.slice(2);
(async()=>{const b=await chromium.launch();let ng=0;const ok=(n,c,x)=>{console.log((c?'OK ':'NG ')+n+(c?'':' '+JSON.stringify(x)));if(!c)ng++};
  const c=await b.newContext({viewport:{width:1280,height:900}});
  await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
  const posts=[];let mailName='';
  await c.route(/script\.google\.com/,r=>{let j={};try{j=JSON.parse(r.request().postData()||'{}')}catch(e){}posts.push(j);
    if(j.type==='mailable')return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,on:true,names:j.names.slice(0,1),max:10})});
    if(j.type==='rfqsend')return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,id:'K1',sent:['株式会社テスト'],skipped:['B工業']})});
    return r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'})});
  const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
  await p.fill('#idea','店のロゴを入れたトートバッグを綿で100個作りたい。');await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
  await p.waitForSelector('#mFspec,.stepnow',{timeout:20000});await p.waitForTimeout(400);
  // 国内の会社2社と海外1社を送り先にする
  const names=await p.evaluate(()=>{const D=window.KATACHI_DATA;const all=Object.entries(D.companies);const jp=all.filter(([,v])=>(v.country||'JP')==='JP').slice(0,2).map(x=>x[0]);const ab=all.filter(([,v])=>v.country&&v.country!=='JP').slice(0,1).map(x=>x[0]);return jp.concat(ab)});
  await p.evaluate(n=>window.KATACHI_RFQ(n),names);await p.waitForSelector('#rf',{timeout:10000});
  await p.waitForSelector('#f-mailsend',{timeout:8000}).catch(()=>{});
  const q=posts.find(x=>x.type==='mailable');
  ok('受付には国内の会社だけ聞く（海外は聞かない）',q&&q.names.length===2&&!q.names.includes(names[2]),q);
  ok('「メールですぐ届ける」とチェック（最初から入）',await p.$eval('#f-mailsend',x=>x.checked).catch(()=>false));
  ok('送り先の会社に「メールで届く」',await p.$$eval('#rf li[data-co] .chip.hi',a=>a.map(x=>x.textContent)).then(a=>a.includes('メールで届く')));
  ok('担当者の箱の文言が変わる',/確認メールのボタンを押すとすぐ届きます/.test(await p.$eval('#rfStaff',x=>x.textContent)));
  await p.evaluate(()=>{const r=document.querySelector('#wzRest');if(r)r.hidden=false;document.querySelectorAll('#rf details').forEach(d=>d.open=true)});
  // 必須を埋める
  await p.evaluate(()=>{const f=document.querySelector('#rf');f.dataset.who=1;f.querySelectorAll('.cks').forEach(x=>{const i=x.querySelector('input');if(i&&!x.querySelector('input:checked'))i.checked=true});
    f.querySelectorAll('select').forEach(s=>{if(!s.value&&s.options.length>1)s.selectedIndex=1});
    ['f-sum','f-qty','f-size','f-due'].forEach(id=>{const e=document.getElementById(id);if(e&&!e.value)e.value='テスト 100個'});
    document.getElementById('f-mail').value='a@example.com';document.getElementById('f-name')&&(document.getElementById('f-name').value='山田');document.getElementById('f-agree').checked=true});
  // 住所が無いと送れない
  await p.evaluate(()=>document.querySelector('#rf').requestSubmit());await p.waitForTimeout(400);
  ok('送る人の住所が無いと止まる',!posts.some(x=>x.type==='rfq')&&/住所/.test(await p.$eval('#rfErr',x=>x.textContent)));
  await p.fill('#f-sname','テスト商店');await p.fill('#f-saddr','東京都千代田区');
  await p.evaluate(()=>{const d=document.querySelector('#mlPrev');d.open=true;d.dispatchEvent(new Event('toggle'))});await p.waitForTimeout(200);
  const prev=await p.$eval('#mlPrev .trbox',x=>x.textContent);
  ok('見本の末尾に送る人の名前と住所',/送信者（依頼者）: テスト商店\n住所: 東京都千代田区/.test(prev),prev.slice(-120));
  ok('会社に届くメールの見本：要点あり、名前・メールなし',/ご担当者さま/.test(prev)&&/依頼の要点/.test(prev)&&!/a@example\.com|山田/.test(prev),prev.slice(0,200));
  if(shots){await p.$eval('#mlBox',x=>x.scrollIntoView());await p.waitForTimeout(200);await p.screenshot({path:path.join(shots,'mail_rfq.png')})}
  await p.evaluate(()=>document.querySelector('#rf').requestSubmit());await p.waitForTimeout(2500);
  const rq=posts.find(x=>x.type==='rfq');
  ok('依頼に mail（国内の会社名）と送る人が入る',rq&&JSON.stringify(rq.mail)===JSON.stringify([q.names[0]])&&rq.mail_sender&&rq.mail_sender.addr==='東京都千代田区',rq&&{mail:rq.mail,err:await p.$eval('#rfErr',x=>x.textContent).catch(()=>'')});
  ok('受付の画面に「確認メールの…を押す」',/メールで送る」を押す/.test(await p.$eval('#ov',x=>x.textContent).catch(()=>'')));
  // チェックを外すと送らない
  // 確認メールのボタンから開く
  const p2=await c.newPage();p2.on('pageerror',e=>errs.push(e.message));await p2.goto(base+'?send='+'A'.repeat(24));await p2.waitForTimeout(2500);
  const t2=await p2.$eval('#ov',x=>x.textContent).catch(()=>'');
  ok('?send= で送った結果（送った会社・担当者から打診する会社）',/送りました（1社）/.test(t2)&&/株式会社テスト/.test(t2)&&/担当者から打診する会社/.test(t2)&&!/send=/.test(p2.url()),t2.slice(0,200));
  if(shots)await p2.screenshot({path:path.join(shots,'mail_send.png')});
  ok('ページのエラーなし',!errs.length,errs);
  await b.close();console.log(ng?ng+'件 NG':'すべてOK');process.exit(ng?1:0)})();
