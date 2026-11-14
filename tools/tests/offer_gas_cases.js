// 受付（backend/forms.gs）の打診：工場に見せる要点から依頼者の情報が抜けるか、鍵の形。 node tools/tests/offer_gas_cases.js
const fs=require('fs'),vm=require('vm'),path=require('path');
const ctx={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../backend/forms.gs'),'utf8'),ctx);
const sheet=rows=>({getLastRow:()=>rows.length,getLastColumn:()=>rows[0].length,getRange:(r,c,n,m)=>({getValues:()=>rows.slice(r-1,r-1+n).map(x=>x.slice(c-1,c-1+(m||1)))})});
const other=['用途・使う人: 店頭での販売','工場向け仕様書（KATACHIが整理）: 寸法: 380×420mm','持ち手 60cm','納品先: 大阪府大阪市北区1-2-3','写真・動画・図面: logo.png','時期の幅: 急がない（工場の空き時期でよい）'].join('\n');
const main=sheet([ctx.HEAD,['K1',new Date(),'見積の依頼','ja','a@example.com','山田商店 / 山田','個人','090-1111-2222','トートを作りたい','トートバッグ 綿 100個','100個','2027年3月まで','縫製: A社','',other,'logo.png','未対応','1件']]);
const req=sheet([ctx.SLOT_REQ_HEAD,['K1',new Date(),'manufacturing.textile','縫製・布・革製品','綿','100個','急がない（空き時期でよい）','2027-01','2027-03','2027年3月まで','まとめてよい','未対応']]);
ctx.sheet_=()=>Object.assign(main,{getParent:()=>({getSheetByName:n=>n==='依頼の時期'?req:null})});
const o=ctx.offerSummary_('K1');let ng=0;const ok=(n,c,x)=>{console.log((c?'OK ':'NG ')+n+(c?'':' '+JSON.stringify(x)));if(!c)ng++};
const all=JSON.stringify(o);
ok('概要・数量・時期',o.summary==='トートバッグ 綿 100個'&&o.qty==='100個'&&o.due==='2027年3月まで',o);
ok('メール・電話・名前・納品先は出さない',!/example\.com|090|山田|大阪府/.test(all),all);
ok('添付ありは件数だけ',o.files===1&&!all.includes('logo.png'),all);
ok('複数行の仕様書がまとまる',o.items.some(x=>x[0].startsWith('工場向け仕様書')&&x[1].includes('持ち手 60cm')),o.items);
ok('時期の幅・期間・まとめ可',o.flex==='急がない（空き時期でよい）'&&o.from==='2027-01'&&o.to==='2027-03'&&o.bundle===true&&o.steps[0]==='縫製・布・革製品',o);
ctx.Utilities={getUuid:()=>require('crypto').randomUUID()};
const ks=new Set([...Array(200)].map(()=>ctx.offerKey_()));ok('鍵は24文字・重ならない',[...ks].every(k=>/^[A-Za-z0-9]{24}$/.test(k))&&ks.size===200);
ok('鍵の形でない文字は探さない',ctx.offerFind_('../../x')===null&&ctx.offerFind_('')===null);
console.log(ng?ng+' NG':'all OK');process.exit(ng?1:0);
