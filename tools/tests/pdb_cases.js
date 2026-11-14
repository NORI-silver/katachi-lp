// 製品仕様DBの当て方の回帰テスト（日本標準商品分類を含む約2.4万品目から、入力に近い製品を当てる）
// 使い方: リポジトリのルートで `python3 -m http.server 8765` を動かしてから node tools/tests/pdb_cases.js [http://localhost:8765/]
const {chromium}=require('playwright');
const base=process.argv[2]||'http://localhost:8765/';
// [入力, 当たってほしい名前に含まれる語（null = 当たらないこと）]
const cases=[
  ['うすくちしょうゆを自社ブランドで作りたい','うすくちしょうゆ'],['犬の首輪','首輪'],['化粧水','化粧水'],['空気清浄機','空気清浄機'],
  ['ギター','ギター'],['ネジ','ねじ'],['スーツケース','スーツケース'],['ハーモニカ','ハーモニカ'],['電子レンジ','電子レンジ'],
  ['大型犬用・完全非抱き上げ式電動車載リフト','リフト'],['ふとんカバー','ふとんカバー'],['ベアリング','軸受'],
  ['ラグ',null],  // 「ラグビー」に当てない
  // 言い換え語・品目表（HS）・新しい製品
  ['ボールベアリング','軸受'],['リチウムイオン電池','リチウム'],['スマホ','スマートフォン'],['エアコン','空気調和'],
  ['アクリルブロック','アクリル'],['キャットタワー','キャットタワー'],['ポータブル電源','ポータブル電源'],['ラバスト','ラバー'],
  ['ハンディファン','ハンディファン'],['ペットカメラ','ペットカメラ'],['抱き枕カバー','抱き枕'],['フライトケース',null],
];
(async()=>{const b=await chromium.launch();const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto(base);
  const r=await p.evaluate(async cs=>{const P=window.KATACHI_PDB;await P.load();return cs.map(([q])=>{const d=P.match(q);return d?d.name:null})},cases);
  let ng=0;cases.forEach(([q,want],i)=>{const ok=want===null?r[i]===null:!!r[i]&&r[i].includes(want);if(!ok)ng++;console.log(ok?'OK':'NG',q,'→',r[i])});
  const n=await p.evaluate(()=>fetch('/data/products.json').then(r=>r.json()).then(d=>d.products.length+(d.jscc?d.jscc.items.filter(i=>i[2]).length:0)));
  console.log('当てられる品目',n);if(n<20000){ng++;console.log('NG 品目が少なすぎます')}
  if(errs.length){ng++;console.log('NG',errs)}
  await b.close();console.log(ng?ng+'件 NG':'すべてOK');process.exit(ng?1:0)})();
