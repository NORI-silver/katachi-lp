// 設計の相談先のおすすめ（③「まず設計」）が、内容に合う種類になるかを確かめる
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから
//   node tools/tests/design_cases.js [http://localhost:8765/]
// 期待: 3つ目＝★になる種類、4つ目＝候補に入っていてほしい種類（inst＝設置工事までの会社）。
// expect＝★になる種類（fab/prod/elec/id/pattern/free/pub）、null＝「まず設計」を出さない（図面あり・食品・化粧品・完成品メーカー）
const {chromium}=require('playwright');
const [base='http://localhost:8765/']=process.argv.slice(2);
const cases=[
  ['犬用プールのスロープ（大型犬2頭）','家庭用プールに犬が入れるスロープを1台作りたい。大型犬2頭が乗る','fab'],
  ['軽バンの車載リフト','軽バンの後ろに付ける、犬（30kg）を乗せる電動リフトを1台作りたい','fab','inst'],
  ['店舗の什器','カフェで使う木製の商品陳列棚を3台つくりたい','fab'],
  ['ステンレスの焚き火台','ステンレスの折りたたみ焚き火台を自社商品として200個つくって販売したい','fab'],
  ['アクリルのスマホスタンド300個','自社ブランドのアクリルのスマホスタンドを300個つくりたい','prod'],
  ['樹脂の小物1個','趣味で使う、樹脂のケーブル整理クリップを2個だけ作りたい','free'],
  ['IoTの見守りセンサー（電子機器のODMが設計も受ける）','介護施設向けに、ベッドの離床を検知するセンサーを100台つくりたい',null],
  ['温度を記録するタグ','冷蔵庫の温度を記録してスマホで見られる小さなタグを試作で5個つくりたい','elec'],
  ['木のおもちゃ','木製の積み木のおもちゃを自社商品として100セットつくりたい','fab'],
  ['陶器のマグカップ','オリジナルの陶器のマグカップを個人で3個つくりたい','free'],
  ['自転車ライト','防水のスマート自転車ライトを自社商品として500個つくりたい','elec'],
  ['トートバッグ','オリジナルのトートバッグを100個つくりたい','pattern'],
  ['Tシャツ','自社ブランドのTシャツを50枚つくりたい','pattern'],
  ['図面あり','アルミの部品を10個つくりたい。図面があります（STEPデータ）',null],
  ['化粧品','オリジナルの化粧水を500本つくりたい',null],
  ['食品','オリジナルのクッキーを1000個つくりたい',null],
  ['犬の車椅子（完成品メーカー）','老犬の車椅子を1台作りたい',null],
];
(async()=>{const b=await chromium.launch();let ok=0;const rows=[];
  for(const [name,text,exp,has] of cases){const c=await b.newContext({viewport:{width:390,height:844}});
    await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com|googletagmanager|google-analytics/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    await p.fill('#idea',text);await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
    await p.waitForSelector('#mFspec,#mNext,[data-gonext],.stepnow',{timeout:30000}).catch(()=>{});await p.waitForTimeout(300);
    await p.evaluate(()=>{location.hash='co'});await p.waitForSelector('#mPlans,.mstep,.empty',{timeout:30000,state:'attached'}).catch(()=>{});await p.waitForTimeout(500);
    const r=await p.evaluate(()=>{const on=document.querySelector('#mDesign [data-dst][aria-pressed=true]');const all=[...document.querySelectorAll('#mDesign [data-dst]')].map(x=>x.dataset.dst);
      const co=document.querySelector('#mDesign input[data-dsn]:checked');const dbg=window.KATACHI_DS&&window.KATACHI_DS();return {dbg:dbg&&{...dbg.f,codes:dbg.codes},got:on?on.dataset.dst:null,all,co:co?co.dataset.dsn:'',steps:[...document.querySelectorAll('#mPlans .stp .sth b')].map(x=>x.textContent)}});
    const pass=r.got===exp&&(!has||r.all.includes(has));if(pass)ok++;rows.push([pass?'○':'×',name,exp,r.got,r.all.join(' '),r.co,errs.join(' | ')]);
    console.log(`${pass?'○':'×'} ${name}: 期待=${exp} 結果=${r.got} [${r.all.join(' ')}] ${r.co}${errs.length?' ERR '+errs.join(' | '):''}`);if(!pass||process.env.V)console.log('   ',JSON.stringify(r.dbg));
    await c.close()}
  /* トップの「アイデアから」で書いて「はじめる」を押すと、②に設計の相談先か、見積を頼む工場の一覧が出る（Nori 2026-11-15「相談会社一覧 もしくは 見積もり依頼工場一覧が出てくる」） */
  const top=[['ボタン：スロープ','家庭用プールに犬が入れるスロープを1台作りたい。大型犬2頭が乗る','fab'],['ボタン：クッキー（設計の箱は出さず、ひとこと）','オリジナルのクッキーを1000個つくりたい','none'],['ボタン：犬の車椅子（メーカーが設計から）','老犬の車椅子を1台作りたい','none']];
  for(const [name,text,exp] of top){const c=await b.newContext({viewport:{width:390,height:844}});
    await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com|googletagmanager|google-analytics/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    await p.fill('#idea',text);await p.click('#cmp button.pri');
    await p.waitForSelector('.stepnow',{timeout:30000}).catch(()=>{});await p.waitForTimeout(400);
    const r=await p.evaluate(()=>{const on=document.querySelector('#mDesign [data-dst][aria-pressed=true]');const h=document.querySelector('.stepnow');return {hash:location.hash,got:on?on.dataset.dst:h&&!/設計/.test(h.textContent)?'none':null}});
    const pass=r.hash==='#co'&&r.got===exp&&!errs.length;if(pass)ok++;
    console.log(`${pass?'○':'×'} ${name}: 期待=${exp} 結果=${r.got} ${r.hash}${errs.length?' ERR '+errs.join(' | '):''}`);await c.close()}
  {const c=await b.newContext({viewport:{width:390,height:844}});await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com|googletagmanager|google-analytics/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    const p=await c.newPage();await p.goto(base);const n=await p.$$eval('.start2 [data-start]',x=>x.length);await p.fill('#idea','家庭用プールに犬が入れるスロープを1台作りたい');await p.click('#cmp button.pri');await p.waitForTimeout(800);
    const h=await p.evaluate(()=>location.hash);const pass=n===2&&h==='#co';if(pass)ok++;console.log(`${pass?'○':'×'} 入口は2つ・「はじめる」は②（一覧）へ: 入口=${n} ${h}`);await c.close()}
  await b.close();const all=cases.length+top.length+1;console.log(`\n${ok}/${all}`);process.exit(ok===all?0:1)})();
