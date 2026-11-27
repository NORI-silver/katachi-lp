/* Browser-independent renderer checks only. Real company responses are not fabricated. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),page=fs.readFileSync(path.join(root,'index.html'),'utf8');
const range=(a,b)=>{const i=page.indexOf(a),j=page.indexOf(b,i);assert.ok(i>=0&&j>i,a);return page.slice(i,j)};
const escape=page.split('\n').find(x=>x.startsWith('const esc='));
const ctx=vm.createContext({});
vm.runInContext(escape+'\n'+range('function rfqCheckLines(text)','function coCard(r,chipCodes)'),ctx);
// Synthetic requests only; keep private requester input out of the repository.
const cases=[
 {id:'wet-work-platform',text:'洗浄工程で使う作業台を設計から製作まで。濡れても耐荷重90kgが必要。濡れた床でずれない固定、滑りにくさが条件。設置スペースは1.5〜2m。最終は2台だけ。',keepers:['耐荷重90kg','濡れた床','ずれない固定','1.5〜2m','2台']},
 {id:'machine-trolley-two-fitments',text:'40kgの計測器を作業者1人で段階移乗させたい。完全に吊り上げないことが必須。移動台も人が持ち上げずに積み込む。使用時だけ取り付け、脱着式固定具は可。\n【3. 対応機種】\n・架空モデル T-7\n・架空モデル C-12',keepers:['40kg','1人','段階移乗','完全に吊り上げない','移動台も人が持ち上げず','脱着式固定具','架空モデル T-7','架空モデル C-12']},
 {id:'optical-on-two-surfaces',text:'つや消し面と光沢面の両方で、傷・傾き・厚みを測れる検査装置を作りたい。光沢面での測定と、つや消し面との精度差を検証したい。基板・ファーム・筐体の試作3台。',keepers:['つや消し面と光沢面','傷・傾き・厚み','光沢面での測定','精度差','基板・ファーム・筐体','試作3台']},
];
for(const c of cases){
 const snippets=ctx.rfqCheckLines(c.text),flat=snippets.join('\n'),box=ctx.rfqCheckBox(c.text);
 for(const w of c.keepers)assert.ok(flat.includes(w),c.id+': '+w);
 assert.ok(snippets.every(x=>c.text.includes(x)),c.id+' fabricated snippet');
 assert.match(box,/会社の回答で確かめます/);
 assert.match(box,/translate="no"/);
 assert.doesNotMatch(box,/対応済み|受注確定|全社未確認|全条件適合|mailto:|https?:\/\//);
}
const oneBox=ctx.rfqCheckBox('1台で <img src=x onerror=alert(1)> を固定。連絡先：秘密 05012345678。\n【将来の機能】\n顔認識を設置。\n【現在の仕様】\n高さ 1.2m 必須。');
assert.match(oneBox,/&lt;img/);
assert.doesNotMatch(oneBox,/<img|秘密|顔認識/);
assert.match(oneBox,/1\.2m/);
assert.ok(ctx.rfqCheckLines('Must carry a 50 kg load without manual lifting.').length);
assert.ok(ctx.rfqCheckLines('必须测量长毛犬的心率。').length);
for(const [kind,label,reason] of [['process','板金','工程の分類'],['design','製品設計','設計相談の分類'],['maker','完成品メーカー','製品分野の分類'],['text','','社名・掲載説明の言葉']]){
 const h=ctx.rfqCandidateBasis(kind,label);assert.ok(h.includes(label)&&h.includes(reason)); assert.doesNotMatch(h,/会社の回答|受注可/);
}
assert.ok(page.includes('${toBar}${rfqCheckBox(S.idea)}'));
for(const call of ["rfqCandidateBasis('process',a.name)","rfqCandidateBasis('design',T.name)","rfqCandidateBasis('maker',MK.name)"])assert.ok(page.includes(call));
const x=page.split('\n').find(x=>x.startsWith('window.KATACHI_I18N='));
const dict=JSON.parse(x.slice('window.KATACHI_I18N='.length).replace(/;\s*$/, ''));
for(const k of ['案件ごとの確認','依頼文から抜粋した確認条件','ほかの条件を見る','候補にした理由：','工程の分類','製品分野の分類','設計相談の分類','社名・掲載説明の言葉']){
 assert.ok(dict[k]?.length===2&&dict[k].every(x=>x&&x!==k),k+' missing en/zh');
}
console.log('PASS: 3 synthetic RFQs keep case-specific conditions separate from candidate reasons; JP/EN/ZH copy, escaping, no transport claims.');
// Distinct lines must not disappear merely because the requirement has no engineering unit.
for(const items of [
 ['個人からの依頼です','図面はありません','予算は3万円までです','2027年3月末までに納品希望です','屋外で使います','試作は1点です'],
 ['食器に直接触れます','食品に触れる部分に使います','食洗機にかけます','幅160mmです'],
]){
 const text=items.map(x=>x+'。').join('\n'),picked=ctx.rfqCheckLines(text);
 assert.deepEqual(Array.from(picked),items);
 assert.match(ctx.rfqCheckBox(text),items.length>4?/<details>/:/<ul>/);
}
const excluded='図面なし：<svg onload=alert(1)>。\n連絡先：条件は 09000000000。\nhttps://example.test/roof\n予算3万円。sample@example.test に連絡してください。\n【将来のオプション】\n屋外で使います。\n【現在の仕様】\n食洗機に対応。\n【参考品のページから読み取った内容】\n予算は50万円。';
const protectedBox=ctx.rfqCheckBox(excluded);
assert.match(protectedBox,/&lt;svg/);
assert.match(protectedBox,/食洗機に対応/);
assert.doesNotMatch(protectedBox,/<svg|09000000000|https:|sample@example|屋外で使います|50万円/);
// Exercise the actual multi-company renderer with synthetic companies only.
Object.assign(ctx,{S:{folds:{}},COCOL:['#000','#111'],MPHASE:[['工程',/./]],mphaseOf:()=>0,phIcon:()=>'',fmt:String,CTRY:{},gmapA:()=>''});
vm.runInContext(range('function recWhy(r,qmax,multi)','function recBox(R3,secs,qmax)'),ctx);
const fake=(name)=>[name,'JP','千葉県','千葉市','',[],null,null,null,null,'gov'];
const asm=fake('架空の組立会社 <img>'),parts=fake('架空の部品会社');
const mkStep=(c,name,r,integ)=>({c,name,r,integ,cmp:r?[r]:[],def:r,n:r?1:0});
const opts=[mkStep('parts','加工',parts,false),mkStep('assembly','組立',asm,true)];
const team=ctx.whoBox(opts,1);
assert.equal(ctx.S.whoN,2);
assert.match(team,/取りまとめ役の候補/);
assert.match(team,/組立・検査・品質管理をどこまで任せられるかは、会社の回答で確認します/);
assert.match(team,/架空の組立会社 &lt;img&gt;/);
assert.match(team,/架空の部品会社/);
assert.doesNotMatch(team,/<img|責任を持つ会社です|会社が責任を持ち/);
const missing=ctx.whoBox([mkStep('parts','加工',parts,false),mkStep('finish','仕上げ',asm,false),mkStep('assembly','組立',null,true)],1);
assert.match(missing,/取りまとめ役は未選定/);
assert.doesNotMatch(missing,/取りまとめ役の候補<\/b>/);
for(const k of ['取りまとめ役の候補','取りまとめ役は未選定','組立・検査・品質管理をどこまで任せられるかは、会社の回答で確認します。']){
 assert.ok(dict[k]?.length===2&&dict[k].every(x=>x&&x!==k),k+' missing en/zh');
}
console.log('PASS: standalone quote/use constraints, sensitive-text exclusions, and both assigned and missing integration roles.');
