// 製品イメージ案の回帰テスト（長い仕様文で違う種類の製品にならないか）
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから
//   node tools/tests/concept_cases.js [http://localhost:8765/] [スクショを保存するフォルダ]
const {chromium}=require('playwright');const fs=require('fs'),path=require('path');
const [base='http://localhost:8765/',shots]=process.argv.slice(2);const dir=path.join(__dirname,'specs');
const cases=JSON.parse(fs.readFileSync(path.join(dir,'cases.json'),'utf8'));
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});let ng=0;
  for(const[i,cs]of cases.entries()){const c=await b.newContext({viewport:{width:1280,height:900}});
    await c.addInitScript(()=>localStorage.setItem('katachi-lang',JSON.stringify({lang:'ja'})));
    await c.route(/script\.google\.com/,r=>r.fulfill({status:200,contentType:'application/json',body:'{"ok":false}'}));
    const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
    const text=cs.text||fs.readFileSync(path.join(dir,cs.file),'utf8');
    await p.fill('#idea',text);await p.evaluate(()=>document.querySelector('#idea').form.requestSubmit());
    await p.waitForSelector('#mConcept',{timeout:20000});await p.waitForTimeout(600);
    const r=await p.evaluate(()=>({name:document.querySelector('#mConcept .cname').textContent,k:JSON.parse(document.querySelector('#mConcept .cview').dataset.v3f).k}));
    const ok=r.k===cs.k&&(!cs.name||r.name===cs.name)&&!errs.length;if(!ok)ng++;
    console.log(ok?'OK':'NG',cs.file||cs.text,'→',r.k,r.name,errs.join(';'));
    if(shots){await p.evaluate(()=>document.querySelector('#mConcept').scrollIntoView());await p.waitForTimeout(1500);await p.screenshot({path:path.join(shots,'case'+i+'.png')})}
    await c.close()}
  await b.close();console.log(ng?ng+'件 NG':'すべてOK');process.exit(ng?1:0)})();
