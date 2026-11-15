// マッチング精度の採点（match_eval.js から使う）。依頼ごとの「正解の基準」は match_cases.json:
//   ok   : その依頼を受けて作れる会社だと読める言葉（社名・概要に対する正規表現。専門家の目で「この品を作る・受ける会社」）
//   ng   : 明らかに分野違いの言葉（★に出たら×）
//   gold : 正解の会社を DB から拾う言葉（候補に入るか＝拾い漏れ、上位20社の枠がどれだけ正解の会社で埋まるか）
//   code : 読み取った工程に入っているべき工程（正規表現）
// 判定: ○＝★の会社（設計・試験などを除く作る会社）の半分以上が ok で、ng が1社もない
//       △＝ng はないが ok が半分未満　×＝ng の会社が★に出た、または★の会社がない
// 作る工程の言葉が入っていれば、設計と一緒でも採点する（「設計・縫製・革製品」の一社など）
const MAKE=/完成品|すべての工程|まとめて|縫製|成形|加工|製品|組立|実装|試作|印刷|刺繍|家具|木工|陶|ガラス|食品|飲料|化粧品|雑貨|OEM|箱|紙器|容器|ラベル|ニット|革|金属|鋳造|板金|切削|EMS|PCBA|アクセサリー/;
const SKIP=/設計|試験|認証|アプリ|クラウド|解析|ファームウェア|アルゴリズム|デザイン|評価|実証|信号処理|電源|無線通信|計測|測位/;
function txt(r){return ((r&&r.n)||'')+' '+((r&&r.sum)||'')}
function judgeCase(cs,r){const ok=cs.ok?new RegExp(cs.ok):null,ng=cs.ng?new RegExp(cs.ng):null;
  const picks=(r.picked||[]).filter(p=>!SKIP.test(p.step||'')||MAKE.test(p.step||'')).map(p=>({n:p.n,step:p.step,ok:!!(ok&&ok.test(txt(p))),ng:!!(ng&&ng.test(txt(p)))}));
  const nOk=picks.filter(p=>p.ok).length,nNg=picks.filter(p=>p.ng).length;
  const v=r.error||!picks.length||nNg?'×':nOk*2>=picks.length?'○':'△';
  // 上位5社の適合率：完成品メーカーの案ならその一覧、ほかは作る工程ごとの上位5社
  const lists=r.maker?[r.maker.rows]:(r.secs||[]).filter(s=>!SKIP.test(s.name||'')||MAKE.test(s.name||'')).map(s=>s.top);
  let t5=0,t5ok=0;for(const L of lists)for(const x of (L||[]).slice(0,5)){t5++;if(ok&&ok.test(txt(x))&&!(ng&&ng.test(txt(x))))t5ok++}
  const codeMiss=cs.code?!(r.codes||[]).some(c=>new RegExp(cs.code).test(c)):false;
  return {id:cs.id,v,plan:r.plan||'',picks,t5,t5ok,codeMiss,gold:r.gold||null,err:r.error||((r.errs||[]).length?r.errs[0]:'')}}
function run(cases,res){const C=cases.map((cs,i)=>judgeCase(cs,res[i]||{}));
  const s={n:C.length,ok:0,mid:0,ng:0,codeMiss:0,t5:0,t5ok:0,goldN:0,goldIn:0,gold20:0,goldCases:0,r20:0,errors:0,verdicts:{}};
  for(const x of C){s[{'○':'ok','△':'mid','×':'ng'}[x.v]]++;s.verdicts[x.id]=x.v;if(x.codeMiss)s.codeMiss++;s.t5+=x.t5;s.t5ok+=x.t5ok;if(x.err)s.errors++;
    if(x.gold&&x.gold.n){s.goldN+=x.gold.n;s.goldIn+=x.gold.inList;s.gold20+=x.gold.top20;s.goldCases++;s.r20+=x.gold.top20/Math.min(x.gold.n,20)}}
  s.top5=s.t5?+(s.t5ok/s.t5).toFixed(3):0;s.recall=s.goldN?+(s.goldIn/s.goldN).toFixed(3):0;s.recall20=s.goldCases?+(s.r20/s.goldCases).toFixed(3):0;delete s.r20;
  return {sum:s,cases:C}}
function summaryText(s){return `依頼 ${s.n}件：○ ${s.ok} / △ ${s.mid} / × ${s.ng}（工程の読み違い ${s.codeMiss}件、画面のエラー ${s.errors}件）
上位5社のうち基準に合う会社 ${(s.top5*100).toFixed(1)}%（${s.t5ok}/${s.t5}）
正解の会社の拾い率：候補に入る ${(s.recall*100).toFixed(1)}%（${s.goldIn}/${s.goldN}）／ 上位20社の枠が正解の会社で埋まる割合 ${(s.recall20*100).toFixed(1)}%（${s.goldCases}件の平均）`}
// 基準より悪くなったところを返す（PRのチェック）。少しの揺れは許す
function compare(s,bl){const bad=[];
  if(s.ok<bl.ok)bad.push(`○ ${s.ok}件（基準 ${bl.ok}件）`);
  if(s.ng>bl.ng)bad.push(`× ${s.ng}件（基準 ${bl.ng}件）`);
  if(s.codeMiss>bl.codeMiss)bad.push(`工程の読み違い ${s.codeMiss}件（基準 ${bl.codeMiss}件）`);
  if(s.top5<bl.top5-0.01)bad.push(`上位5社の適合率 ${s.top5}（基準 ${bl.top5}）`);
  if(s.recall20<bl.recall20-0.01)bad.push(`正解の会社の上位20社の拾い率 ${s.recall20}（基準 ${bl.recall20}）`);
  if(s.errors>0)bad.push(`画面のエラー ${s.errors}件`);
  for(const[id,v]of Object.entries(bl.verdicts||{}))if(v==='○'&&s.verdicts[id]==='×')bad.push(`${id}：○→×`);
  return bad}
module.exports={run,judgeCase,summaryText,compare};
