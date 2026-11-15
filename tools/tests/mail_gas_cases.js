// 受付（backend/forms.gs）の工場へのメール：公開メールの拾い方・お断りの表示・工場に届く本文・送る流れ。 node tools/tests/mail_gas_cases.js
const fs=require('fs'),vm=require('vm'),path=require('path'),crypto=require('crypto');
const ctx={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../backend/forms.gs'),'utf8'),ctx);
let ng=0;const ok=(n,c,x)=>{console.log((c?'OK ':'NG ')+n+(c?'':' '+JSON.stringify(x)));if(!c)ng++};
const F=(h,host,c)=>ctx.mailFind_(h,host,c).map(x=>x.email);

// ---- アドレスを拾う ----
ok('mailtoと本文から、同じドメインを先に',F('<a href="mailto:info@kaneso.co.jp">お問い合わせ</a> 担当 tanaka@kaneso.co.jp','kaneso.co.jp')[0]==='info@kaneso.co.jp');
ok('全角＠・&#64; も読む',F('<p>info＠abc-seiko.co.jp</p><p>sales&#64;abc-seiko.co.jp</p>','abc-seiko.co.jp').length===2);
ok('採用・個人情報・noreply は使わない',F('recruit@a-kogyo.jp privacy@a-kogyo.jp noreply@a-kogyo.jp','a-kogyo.jp').length===0);
ok('別の会社のドメイン（サイトの制作会社など）は使わない',F('<footer>制作 web@design-office.com</footer>','a-kogyo.jp').length===0);
ok('フリーメール・プロバイダは使う',F('メール: a.kogyo@gmail.com / koujou@abc.ocn.ne.jp','a-kogyo.jp').length===2);
ok('画像の名前（logo@2x.png）は拾わない',F('<img src="logo@2x.png"><img src="icon@3x.webp">','a.jp').length===0);
ok('example・sample は拾わない',F('例：xxx@example.com','a.jp').length===0);
ok('サブドメイン・名前が同じ別の語尾も同じ会社',ctx.mailSameDomain_('mail.kaneso.co.jp','kaneso.co.jp')&&ctx.mailSameDomain_('kaneso.jp','kaneso.co.jp')&&!ctx.mailSameDomain_('abc.co.jp','abd.co.jp'));
ok('短い名前どうしは別の会社扱い（ab.jp と ab.co.jp）',!ctx.mailSameDomain_('ab.jp','ab.co.jp'));
ok('www は外して比べる',ctx.mailHost_('https://www.kaneso.co.jp/about/')==='kaneso.co.jp');

// ---- お断りの表示 ----
['営業目的のお問い合わせはご遠慮ください。','広告・宣伝メールの送信はお断りいたします','セールスのご連絡はお受けしておりません','特定電子メールの受信を拒否します','※営業・勧誘メールは固くお断りします'].forEach(t=>ok('お断り: '+t,ctx.mailRefuses_('<p>'+t+'</p>')));
['お問い合わせはお気軽にどうぞ','試作のご相談を受け付けています','営業時間 9:00〜17:00 ご連絡はメールで'].forEach(t=>ok('お断りではない: '+t,!ctx.mailRefuses_('<p>'+t+'</p>')));

// ---- お問い合わせのページを探す ----
const L=ctx.mailLinks_('<a href="/company/">会社概要</a><a href="contact.html">お問い合わせ</a><a href="https://other.com/contact">他社</a><a href="mailto:a@b.jp">メール</a><a href="/news/">お知らせ</a><a href="/files/a.pdf">お問い合わせ票</a>','https://www.a-kogyo.jp/index.html');
ok('お問い合わせ→会社概要の順、同じサイトだけ',JSON.stringify(L)===JSON.stringify(['https://www.a-kogyo.jp/contact.html','https://www.a-kogyo.jp/company/']),L);

// ---- 1社ぶんの判断 ----
const d1=ctx.mailDecide_('https://a-kogyo.jp/',[{url:'https://a-kogyo.jp/',html:'<p>tanaka@a-kogyo.jp</p>'},{url:'https://a-kogyo.jp/contact/',html:'<a href="mailto:info@a-kogyo.jp">mail</a>',contact:true}]);
ok('送れる・お問い合わせの info を選ぶ',d1.state==='送れる'&&d1.email==='info@a-kogyo.jp'&&d1.page==='https://a-kogyo.jp/contact/',d1);
const d2=ctx.mailDecide_('https://a-kogyo.jp/',[{url:'https://a-kogyo.jp/',html:'info@a-kogyo.jp'},{url:'https://a-kogyo.jp/contact/',html:'営業のメールはご遠慮ください',contact:true}]);
ok('どこかのページにお断りがあれば送らない',d2.state==='営業お断りの表示',d2);
ok('読めない',ctx.mailDecide_('https://x.jp/',[{url:'https://x.jp/',html:null}]).state==='読めない');
const d3=ctx.mailDecide_('https://x-kogyo.jp/',[{url:'https://x-kogyo.jp/',html:'web@hp-maker.com'}]);
ok('別ドメインだけ→見つからない（メモに残す）',d3.state==='見つからない'&&/hp-maker/.test(d3.memo),d3);

// ---- 工場に届く本文・依頼者への確認メール ----
const sheet=rows=>({rows,getLastRow:()=>rows.length,getLastColumn:()=>rows[0].length,getParent:()=>({getSheetByName:()=>null,getUrl:()=>'https://sheet'}),
  getRange:(r,c,n,m)=>({getValues:()=>rows.slice(r-1,r-1+(n||1)).map(x=>x.slice(c-1,c-1+(m||1))),setValue:v=>{rows[r-1][c-1]=v},setValues:vs=>{vs.forEach((v,i)=>{rows[r-1+i]=rows[r-1+i]||[];v.forEach((y,j)=>rows[r-1+i][c-1+j]=y)})}})});
const other=['用途・使う人: 店頭での販売','材質（記号）: おまかせ（工場の提案で）','納品先: 大阪府大阪市北区1-2-3','写真・動画・図面: logo.png'].join('\n');
const main=sheet([ctx.HEAD,['K1',new Date(),'見積の依頼','ja','a@example.com','山田商店 / 山田','個人','090-1111-2222','トートを作りたい','トートバッグ 綿 100個','100個','2027年3月まで','縫製: A社','',other,'logo.png','未対応','1件']]);
ctx.sheet_=()=>main;
const props={};const SND={name:'送信者テスト',addr:'東京都テスト区1-1'};
ctx.PropertiesService={getScriptProperties:()=>({getProperty:k=>props[k]||null,setProperty:(k,v)=>{props[k]=v}})};
const fm=ctx.factoryMail_('K1','株式会社テスト縫製','https://katachi.shiokonbu.com/reply/?k=AAA','https://katachi.shiokonbu.com/reply/?k=AAA&stop=1','https://t.jp/contact/',SND);
ok('本文に要点と打診リンク',/トートバッグ 綿 100個/.test(fm.body)&&/reply\/\?k=AAA\n/.test(fm.body)&&/用途・使う人: 店頭での販売/.test(fm.body),fm.body);
ok('依頼者のメール・電話・納品先・ファイル名は入らない',!/example\.com|090|山田|大阪府|logo\.png/.test(fm.body+fm.subject),fm.body);
ok('送信者の名前・住所・配信停止・掲載ページ（特定電子メール法の表示）',/送信者（依頼者）: 送信者テスト/.test(fm.body)&&/取り次ぎ: KATACHI/.test(fm.body)&&/住所: 東京都テスト区1-1/.test(fm.body)&&/stop=1/.test(fm.body)&&/t\.jp\/contact/.test(fm.body));
ok('おまかせの項目は「ご提案ください」に',/決まっていない点（ご提案ください）\n材質/.test(fm.body)&&!/材質（記号）: おまかせ/.test(fm.body),fm.body);
ok('件名に受付番号',/K1/.test(fm.subject)&&/^【KATACHI】見積のご相談/.test(fm.subject),fm.subject);
const ms={names:['株式会社テスト縫製','B工業'],url:'https://katachi.shiokonbu.com/?send=XYZ',preview:fm.body};
const rm=ctx.buildReplyMail_('K1',{type:'rfq',lang:'ja',team:[]},{'f-sum':'トート'},ms);
ok('確認メールに「2社にメールで送る」ボタンと見本',/2社にメールで送る/.test(rm.html)&&/send=XYZ/.test(rm.html)&&/send=XYZ/.test(rm.text)&&/1社目の見本/.test(rm.text));
ok('送る会社がなければボタンなし',!/send=/.test(ctx.buildReplyMail_('K1',{type:'rfq',lang:'en',team:[]},{},null).html));
ok('英語・中国語の確認メールも出る',/Email 2 companies/.test(ctx.buildReplyMail_('K1',{type:'rfq',lang:'en',team:[]},{},ms).html)&&/2家公司/.test(ctx.buildReplyMail_('K1',{type:'rfq',lang:'zh',team:[]},{},ms).html));

// ---- 送る流れ（確認待ち→送信済み、2回押しても1回だけ、お断り・停止の会社には送らない） ----
const tabs={'工場のメール':sheet([ctx.MAIL_HEAD,['株式会社テスト縫製','大阪府','https://t.jp/','info@t.jp','https://t.jp/contact/','送れる','2026-11-15',''],['B工業','東京都','https://b.jp/','info@b.jp','https://b.jp/','営業お断りの表示','2026-11-15',''],['C製作所','東京都','https://c.jp/','info@c.jp','https://c.jp/','送れる','2026-11-15','']]),
  'メール送信':sheet([ctx.SEND_HEAD]),'工場への打診':sheet([ctx.OFFER_HEAD])};
Object.values(tabs).forEach(t=>{t.appendRow=r=>t.rows.push(r)});
ctx.slotTab_=n=>tabs[n];
const cache={};ctx.CacheService={getScriptCache:()=>({get:k=>cache[k],put:(k,v)=>{cache[k]=v},remove:k=>{delete cache[k]}})};
ctx.Utilities={getUuid:()=>crypto.randomUUID(),formatDate:(d)=>d.toISOString().slice(0,16),base64EncodeWebSafe:b=>Buffer.from(b).toString('base64'),computeDigest:(a,s)=>[...crypto.createHash('md5').update(String(s)).digest()],DigestAlgorithm:{MD5:1}};
ctx.LockService={getScriptLock:()=>({tryLock:()=>true,releaseLock:()=>{}})};
ctx.Session={getEffectiveUser:()=>({getEmail:()=>'admin@x'})};
const sent=[];ctx.MailApp={getRemainingDailyQuota:()=>90,sendEmail:o=>sent.push(o)};
const av=ctx.mailable_({names:['株式会社テスト縫製','B工業','D社']});
ok('mailable: 送れる会社の名前だけ（アドレスは返さない）',av.on&&JSON.stringify(av.names)==='["株式会社テスト縫製"]'&&!JSON.stringify(av).includes('@'),av);
const prep=ctx.mailPrepare_('K1',{mail:['株式会社テスト縫製','B工業','C製作所'],team:[{company:'株式会社テスト縫製',country:'JP'},{company:'B工業',country:'JP'}],mail_sender:SND},'a@example.com');
ok('送信者の名前・住所が無ければ準備しない',ctx.mailPrepare_('K9',{mail:['株式会社テスト縫製'],team:[{company:'株式会社テスト縫製'}],mail_sender:{name:'山',addr:''}},'z@x.jp')===null);
ok('準備: 依頼の送り先に入っていて送れる会社だけ（C製作所は送り先でない、B工業はお断り）',JSON.stringify(prep.names)==='["株式会社テスト縫製"]'&&tabs['メール送信'].rows.length===2&&tabs['メール送信'].rows[1][3]==='依頼者の確認待ち',prep);
const k=prep.key;
const r1=ctx.rfqSend_({k});
ok('押すと送る',r1.ok&&JSON.stringify(r1.sent)==='["株式会社テスト縫製"]'&&sent.filter(m=>m.to==='info@t.jp').length===1,r1);
ok('記録: 送信済み・打診リンク・打診タブ',tabs['メール送信'].rows[1][3]==='送信済み'&&/reply\/\?k=/.test(tabs['メール送信'].rows[1][7])&&tabs['工場への打診'].rows.length===2);
ok('運営者に控え（本文つき）',sent.some(m=>m.to==='admin@x'&&/控え/.test(m.body)&&/1社目に送った本文/.test(m.body)));
ok('差出人が無いときも名前は「KATACHI 見積窓口」',sent.find(m=>m.to==='info@t.jp').name==='KATACHI 見積窓口');
{ // 差出人のアドレス（MAIL_FROM）: Gmail の別名にあれば GmailApp で from、無ければ返信先だけ
  const gs=[];ctx.GmailApp={getAliases:()=>['factory@x.jp'],sendEmail:(to,su,bo,o)=>gs.push({to,o})};
  props.MAIL_FROM='factory@x.jp';ctx.factorySend_('a@b.jp','s','b');
  ok('別名にあれば差出人・返信先ともそのアドレス',gs.length===1&&gs[0].o.from==='factory@x.jp'&&gs[0].o.replyTo==='factory@x.jp'&&gs[0].o.name==='KATACHI 見積窓口');
  ctx.GmailApp.getAliases=()=>[];const n0=sent.length;ctx.factorySend_('a@b.jp','s','b');
  ok('別名に無ければ MailApp で返信先だけ',gs.length===1&&sent.length===n0+1&&sent[n0].replyTo==='factory@x.jp');
  sent.pop();delete props.MAIL_FROM;delete ctx.GmailApp;
}
{ const g1=ctx.runGuard_('collectMail',330),g2=ctx.runGuard_('collectMail',330);g1.done();const g3=ctx.runGuard_('collectMail',330);
  ok('アドレス集めは同時に2つ動かない・終われば次が動く（スクリプトの鍵は持ち続けない）',g1&&g2===null&&g3);g3.done(); }
const r2=ctx.rfqSend_({k});
ok('2回押しても送り直さない',r2.ok&&r2.already&&sent.filter(m=>m.to==='info@t.jp').length===1,r2);
ok('知らない鍵',ctx.rfqSend_({k:'x'.repeat(24)}).error==='key'&&ctx.rfqSend_({k:'../'}).error==='key');
props.MAIL_SEND='off';
ok('MAIL_SEND=off で止まる',ctx.mailable_({names:['株式会社テスト縫製']}).on===false&&ctx.mailPrepare_('K2',{mail:['株式会社テスト縫製'],team:[{company:'株式会社テスト縫製'}],mail_sender:SND},'b@x.jp')===null);
delete props.MAIL_SEND;
ok('送ったメールの末尾に依頼者の名前・住所',sent.some(m=>m.to==='info@t.jp'&&/送信者（依頼者）: 送信者テスト\n住所: 東京都テスト区1-1/.test(m.body)));
// 配信停止
const kk=tabs['工場への打診'].rows[1][11];
const st=ctx.offerReply_({k:kk,answer:'stop'});
ok('配信停止を押すと、その会社には送らない',st.ok&&tabs['工場のメール'].rows[1][5]==='送らない（配信停止）'&&ctx.mailable_({names:['株式会社テスト縫製']}).names.length===0,st);
// 確認待ちの間に会社が止めた
const p2=ctx.mailPrepare_('K3',{mail:['C製作所'],team:[{company:'C製作所',country:'JP'}],mail_sender:SND},'c@x.jp');
tabs['工場のメール'].rows[3][5]='送らない（手で止める）';
const r3=ctx.rfqSend_({k:p2.key});
ok('確認待ちの間に止めた会社には送らない',r3.ok&&!r3.sent.length&&r3.skipped[0]==='C製作所'&&!sent.some(m=>m.to==='info@c.jp'),r3);
console.log(ng?ng+' NG':'all OK');process.exit(ng?1:0);
