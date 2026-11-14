// ③「一社か組み合わせか」のおすすめルールの確認（体に合わせる・中身と容器・試作で図面なし・図面あり/100個以上）
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから
//   node tools/tests/plan_rule_cases.js [http://localhost:8765/] [スクショを保存するフォルダ]
const {chromium}=require('playwright');const path=require('path');
const [base='http://localhost:8765/',shots]=process.argv.slice(2);
// want: 期待するルール（fit/fill/proto/full/docs/other）。maker:true は完成品メーカーの箱が出る
const cases=[
  {text:'老犬の後ろ足が弱ってきたので、体に合わせた犬の車椅子を作りたい',want:'fit'},
  {text:'猫用の服を、体型に合わせて採寸して10着作りたい',want:null,maker:true},
  {text:'オリジナルの化粧水を作って、ボトルに詰めて300本売りたい',want:'fill'},
  {text:'散歩中の犬の心拍を測れる首輪を、まず5個だけ試作したい',want:'proto',maker:true},
  {text:'ステンレスの板金とアクリルの板を組み合わせたスマホスタンドを3個だけ試作したい',want:'proto',ask:['fit','docs']},
  {text:'アルミの削り出しの台座とアクリルのカバーを組み合わせた展示用スタンドを500個。図面があります',want:'full'},
  {text:'ステンレスの板金とアクリルの板を組み合わせたスマホスタンドを300個。図面があります',want:'docs'},
];
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});let ng=0;
  for(const[i,cs]of cases.entries()){const c=await b.newContext({viewport:{width:1280,height:900}});
    await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    await p.fill('#idea',cs.text);await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
    await p.waitForSelector('#mFspec,#mNext',{timeout:20000});await p.waitForTimeout(300);
    await p.evaluate(()=>{location.hash='co'});await p.waitForSelector('#mPlans',{timeout:20000});await p.waitForTimeout(500);
    const r=await p.evaluate(()=>{const R=window.KATACHI_RL&&window.KATACHI_RL();const box=document.querySelector('#mPlans');
      return {rl:R&&R.id,ask:R?R.ask:[],maker:!!document.querySelector('.mkr'),win:!!box.querySelector('.rwin'),cmp:!!document.querySelector('#mCmp'),title:(box.querySelector('h3')||{}).textContent}});
    const ok=(r.rl||null)===cs.want&&r.win&&(!cs.maker||r.maker)&&(!cs.ask||cs.ask.every(k=>r.ask.includes(k)))&&!errs.length;if(!ok)ng++;
    console.log(ok?'OK':'NG',cs.text.slice(0,24),JSON.stringify(r),errs.join(';'));
    if(shots){await p.evaluate(()=>{const d=document.querySelector('#mPlans');d.scrollIntoView();window.scrollBy(0,-90)});await p.waitForTimeout(300);await p.screenshot({path:path.join(shots,'plan'+i+'.png'),fullPage:false})}
    // 試作の例：「図面・3Dデータがある」と答えると、試作の一社案から外れる
    if(cs.want==='proto'&&!cs.maker){await p.click('[data-rl="docs"][data-rlv="0"]');await p.waitForTimeout(600);const r2=await p.evaluate(()=>window.KATACHI_RL().id);
      const ok2=r2!=='proto';if(!ok2)ng++;console.log(ok2?'OK':'NG','  図面ありと答えたあと',r2)}
    await c.close()}
  await b.close();console.log(ng?`NG ${ng}件`:'すべてOK');process.exit(ng?1:0)})();
