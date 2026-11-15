/**
 * KATACHI（katachi.shiokonbu.com）の「見積の依頼」と「相談」の受付（Google Apps Script）
 *
 * 流れ（提携の申込み type:'partner' は「提携申込」タブへ。下の partner_ を参照）
 *   1. サイトのフォーム → doPost で、スプレッドシート「KATACHI 受付」の「受付」タブに1行追加
 *   2. 運営者に「新しい受付」のメール
 *   3. 依頼した人に「受け付けました」のメール（受付番号つき）
 *   会社への打診は、担当者が内容を確認してから手で行う。公開メールのわかる国内の会社には、依頼者が確認メールのボタンを押すとメールで届く（下の「見積の依頼を工場へメールで届ける」）。
 *
 * 置き方（はじめの1回だけ）
 *   script.google.com → 新しいプロジェクト（名前は「KATACHI 受付」）→ このファイルの中身を貼って保存
 *   → 関数 setup を選んで「実行」（権限の確認が出たら許可）→ スプレッドシートが作られる
 *   → デプロイ → 新しいデプロイ → 種類「ウェブアプリ」・実行ユーザー「自分」・アクセスできるユーザー「全員」
 *   → 出てきた URL（https://script.google.com/macros/s/〇〇/exec）をサイト担当に渡す
 *
 * 公開リポジトリに置くので、メールアドレスやシートIDはここに書かない（スクリプトのプロパティに入る）。
 */
var CONFIG = {
  SERVICE_NAME: 'KATACHI',
  SITE_URL: 'https://katachi.shiokonbu.com/',
  // 運営者のメール。空なら、このスクリプトを動かしている Google アカウント
  ADMIN_EMAIL: '',
  // 1日に受け付ける上限（いたずら対策）
  DAILY_LIMIT: 200,
  // 写真・動画などのアップロード（受付番号ごとに Google ドライブの非公開フォルダへ保存）
  UPLOAD_MAX_FILES: 20,             // 1件の依頼で送れるファイルの数
  UPLOAD_MAX_BYTES: 300 * 1048576,  // 1件の依頼で送れる合計（300MB）
  UPLOAD_FILE_MAX: 200 * 1048576,   // 1ファイルの上限（200MB、動画を想定）
  UPLOAD_FOLDER_NAME: 'KATACHI 受付ファイル',
  // 入力ログ（文章で書く・選んで探す）の1日の上限
  LOG_DAILY_LIMIT: 3000,
  // Googleの口コミ（Places API。ペットサイトと同じ方式）。スクリプトのプロパティ PLACES_API_KEY が無ければ動かず、サイトはGoogleマップへのリンクだけ出す
  REVIEW_MONTHLY_LIMIT: 900,        // 1か月に口コミを取り寄せる回数（無料の範囲 1,000回に収める。超えたら月末までリンクだけ）
  REVIEW_SEARCH_MONTHLY_LIMIT: 900, // 1か月に場所を探す回数（場所IDは覚えるので、同じ会社は2回目から探さない）
  PEEK_DAILY_LIMIT: 500,            // 参考品ページの読み取り：1日の上限
  GITEKI_DAILY_LIMIT: 500,
  PARTS_DAILY_LIMIT: 800,           // 部品の参考価格（DigiKey Product Information v4、無料枠は1日1,000回）：1日の上限          // 技適の検索（総務省 Web-API）：1日の上限
  SPEC_DAILY_LIMIT: 500,            // 仕様の整理結果の保存・読み出し：1日の上限（いたずら対策）
  SPEC_MAX_CHARS: 20000,            // 依頼文の文字数の上限
  REVIEW_DAILY_LIMIT: 150,          // 1日の上限（いたずら対策）
};

var HEAD = ['受付番号', '受付日時', '種類', '言語', 'メール', '会社名・お名前', '依頼者の区分', '電話', 'つくりたいもの（入力文）',
  '製品の概要', '段階と数量', '希望の時期', '送り先（工程: 会社）', '海外への提供に同意', 'その他の項目', '取り込んだ設計ファイル名', '状態', 'アップロードしたファイル'];

function setup() {
  sheet_();
  uploadRoot_();  // 写真・動画の保存先フォルダ（ここでGoogleドライブの権限の確認が出ます）
  UrlFetchApp.getRequest('https://www.googleapis.com/');  // 大きいファイルの小分け保存に使う権限の確認
  Logger.log('準備できました: ' + SpreadsheetApp.openById(prop_('SHEET_ID')).getUrl());
}

function doPost(e) {
  var out = {ok: false};
  try {
    var p = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (p.type === 'idea') return json_(logIdea_(p));
    if (p.type === 'file') return json_(saveChunk_(p));
    if (p.type === 'partner') return json_(partner_(p));
    if (p.type === 'reviews') return json_(reviews_(p));
    if (p.type === 'peek') return json_(peek_(p));
    if (p.type === 'giteki') return json_(giteki_(p));
    if (p.type === 'parts') return json_(parts_(p));
    if (p.type === 'spec') return json_(spec_(p));
    if (p.type === 'specsave') return json_(specSave_(p));
    if (p.type === 'offer') return json_(offerView_(p));
    if (p.type === 'offerreply') return json_(offerReply_(p));
    if (p.type === 'mailable') return json_(mailable_(p));
    if (p.type === 'rfqsend') return json_(rfqSend_(p));
    if (!limit_()) return json_({ok: false, error: 'busy'});
    if (p.type !== 'rfq' && p.type !== 'consult') return json_({ok: false, error: 'type'});
    var f = {};
    (p.fields || []).forEach(function (x) { if (x && x.id) f[x.id] = String(x.value || '').slice(0, 4000); });
    var email = String(p.type === 'rfq' ? (f['f-mail'] || '') : (p.email || '')).trim();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json_({ok: false, error: 'email'});
    var id = 'K' + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyMMdd') + '-' + Math.random().toString(36).slice(2, 6).toUpperCase();
    var team = (p.team || []).map(function (t) { return t.step + ': ' + t.company + (t.country && t.country !== 'JP' ? '（' + t.country + '）' : ''); }).join('\n');
    var known = ['f-mail', 'f-org', 'f-name', 'f-who', 'f-tel', 'f-sum', 'f-qty', 'f-due'];
    var other = (p.fields || []).filter(function (x) { return known.indexOf(x.id) < 0; }).map(function (x) { return x.label + ': ' + x.value; });
    if (p.type === 'consult') other = ['相談したいこと: ' + (p.topic || ''), 'いまの状況: ' + (p.body || ''), '相談先: ' + (p.to || []).join('、'), '会社: ' + (p.company || '')].concat((p.fields || []).map(function (x) { return x.label + ': ' + x.value; }));
    var row = [id, new Date(), p.type === 'rfq' ? '見積の依頼' : '相談', p.lang || 'ja', email,
      p.type === 'rfq' ? [f['f-org'], f['f-name']].filter(String).join(' / ') : (p.org || ''),
      f['f-who'] || '', f['f-tel'] || '', String(p.idea || '').slice(0, 4000), f['f-sum'] || '', f['f-qty'] || '', f['f-due'] || '',
      team, p.abroad_ok ? 'はい' : '', other.join('\n').slice(0, 45000), (p.files || []).join('、'), '未対応', openUpload_(id, p.upload)];
    var sh = sheet_();
    sh.appendRow(row.map(safe_));
    if (p.type === 'rfq') { try { slotRequest_(id, p.slot, f); } catch (err) { console.error(err); } }
    var ms = null;
    if (p.type === 'rfq' && (p.mail || []).length) { try { ms = mailPrepare_(id, p, email); } catch (err) { console.error(err); } }
    notifyAdmin_(id, row, sh, ms && ms.names.length ? 'メールで届ける予定（依頼者が確認メールのボタンを押すと送られます）: ' + ms.names.join('、') : '');
    replyUser_(id, email, p, f, ms && ms.names.length ? ms : null);
    out = {ok: true, id: id};
  } catch (err) {
    console.error(err);
    out = {ok: false, error: 'unavailable'};
  }
  return json_(out);
}

// 「文章で書く」「選んで探す」の入力を「入力ログ」タブに1行ずつ残す（傾向分析用。メールは送らない）
var LOG_HEAD = ['日時', '入口', '言語', '入力文', '数量', '読み取った工程', '工程の数', '候補の社数', '各工程の1位', '扱わない分野', '選択式の内容', '補足', 'ファイルの種類', 'ページ'];
function logIdea_(p) {
  if (!limit_('i', CONFIG.LOG_DAILY_LIMIT)) return {ok: false, error: 'busy'};
  var s = function (v, n) { return String(v == null ? '' : v).slice(0, n || 2000); };
  var list = function (v) { return (v || []).map(String).join('\n').slice(0, 4000); };
  var guided = p.mode === 'guided' ? [p.category, p.process, p.material, p.quantity, p.drawing, p.due, p.region].filter(String).join(' / ') : '';
  var row = [new Date(), p.mode === 'guided' ? '選んで探す' : '文章で書く', s(p.lang, 5), s(p.text), s(p.quantity, 40),
    list(p.steps), (p.steps || []).length, Number(p.companies) || '', list(p.top), list(p.notices), guided, s(p.note, 1000),
    (p.file_kinds || []).join('、').slice(0, 200), s(p.page, 200)];
  logSheet_().appendRow(row.map(safe_));
  return {ok: true};
}

function logSheet_() {
  var ss = sheet_().getParent();
  var sh = ss.getSheetByName('入力ログ');
  if (!sh) {
    sh = ss.insertSheet('入力ログ');
    sh.appendRow(LOG_HEAD);
    sh.setFrozenRows(1);
  }
  return sh;
}

function doGet() { return json_({ok: true, service: CONFIG.SERVICE_NAME}); }

function notifyAdmin_(id, row, sh, extra) {
  var to = CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail();
  var body = HEAD.map(function (h, i) { return '■ ' + h + '\n' + (row[i] instanceof Date ? Utilities.formatDate(row[i], 'Asia/Tokyo', 'yyyy-MM-dd HH:mm') : row[i]); }).join('\n\n');
  MailApp.sendEmail({to: to, subject: '[KATACHI] 新しい' + row[2] + ' ' + id, body: (extra ? '■ ' + extra + '\n\n' : '') + body + '\n\n一覧: ' + sh.getParent().getUrl()});
}

// ---------- 依頼した人への自動返信（HTMLメール＋テキスト版） ----------
var MAIL_TEXT = {
  ja: {
    subj_rfq: '【KATACHI】見積の依頼を受け付けました（{id}）', subj_consult: '【KATACHI】ご相談を受け付けました（{id}）',
    title_rfq: '見積の依頼を受け付けました', title_consult: 'ご相談を受け付けました',
    lead: 'KATACHI をご利用いただきありがとうございます。担当者が内容を確認してから、対応できそうな工場・専門家にお声がけします。',
    ref: '受付番号', ref_note: 'お問い合わせの際はこの番号をお知らせください',
    steps_rfq: [['受付', 'いま'], ['内容の確認', '1〜2営業日'], ['工場へ打診', '担当者が連絡'], ['見積が届く', 'ふつう1〜2週間']],
    steps_consult: [['受付', 'いま'], ['内容の確認', '1〜2営業日'], ['専門家・工場へ相談', '担当者が連絡'], ['返事が届く', 'ふつう1週間前後']],
    sum_h: 'お送りいただいた内容', k_sum: '製品の概要', k_idea: 'つくりたいもの', k_qty: '段階と数量', k_due: '希望の時期', k_team: '打診する予定の会社', k_topic: '相談したいこと', k_to: '相談先',
    att_h: '図面・写真・設計データはありますか？', att: 'このメールにそのまま返信して添付してください（合計20MBまで）。手描きのスケッチやスマホの写真でもかまいません。見積の精度が上がります。',
    att_up_h: '送っていただいたファイル', att_up: '{n}件のファイルをお預かりしました。担当者だけが見られる場所に保存し、見積を頼む会社にだけ渡します。あとから足したいファイルは、このメールへの返信で送れます。',
    note: 'まだ発注は決まっていません。見積や返事を見てから、依頼するかどうかをお決めください。工程の整理・会社の検索・見積の依頼は無料です。',
    send_h: 'メールのわかる{n}社には、すぐ届けられます', send_t: '下のボタンを押すと、{names} に依頼の要点を KATACHI からメールで送ります。あなたのお名前・メール・電話は送りません（会社が受けると決まってからお伝えします）。', send_btn: '{n}社にメールで送る', send_note: '{d}日以内に押してください。押さなければメールは送られず、これまでどおり担当者が確かめてから打診します。', send_prev: '会社に届くメール（1社目の見本）',
    btn: 'KATACHI を開く', foot: 'このメールは KATACHI のフォームから送信された方にお送りしています。お心当たりがない場合は、このメールに返信してお知らせください。'
  },
  en: {
    subj_rfq: '[KATACHI] We received your quote request ({id})', subj_consult: '[KATACHI] We received your consultation request ({id})',
    title_rfq: 'We received your quote request', title_consult: 'We received your consultation request',
    lead: 'Thank you for using KATACHI. Our staff will review what you sent and reach out to factories and experts who can help.',
    ref: 'Reference', ref_note: 'Please quote this number when contacting us',
    steps_rfq: [['Received', 'Now'], ['Review', '1–2 business days'], ['Contact factories', 'By our staff'], ['Quotes arrive', 'Usually 1–2 weeks']],
    steps_consult: [['Received', 'Now'], ['Review', '1–2 business days'], ['Ask experts', 'By our staff'], ['Replies arrive', 'Usually about 1 week']],
    sum_h: 'What you sent', k_sum: 'Product summary', k_idea: 'What you want to make', k_qty: 'Stage and quantity', k_due: 'Desired timing', k_team: 'Companies we plan to contact', k_topic: 'Topic', k_to: 'Ask',
    att_h: 'Do you have drawings, photos or design files?', att: 'Just reply to this email with them attached (up to 20 MB in total). Hand sketches and phone photos are fine, and they make quotes more accurate.',
    att_up_h: 'Files you sent', att_up: 'We received {n} file(s). They are stored where only our staff can see them, and are shared only with the companies we ask for quotes. To add more files later, just reply to this email.',
    note: 'Nothing has been ordered yet. You can decide whether to proceed after seeing the quotes. Organizing the process, searching companies and requesting quotes are free.',
    send_h: '{n} companies can get it by email right away', send_t: 'Press the button below and KATACHI will email the key points of your request to {names}. Your name, email and phone number are not sent (we share them once a company agrees to take it on).', send_btn: 'Email {n} companies', send_note: 'Please press it within {d} days. If you do not, nothing is emailed and our staff will review and contact companies as usual.', send_prev: 'The email companies receive (sample for the first one, in Japanese)',
    btn: 'Open KATACHI', foot: 'You received this email because this address was entered in a KATACHI form. If this was not you, please reply and let us know.'
  },
  zh: {
    subj_rfq: '[KATACHI] 已收到您的报价委托（{id}）', subj_consult: '[KATACHI] 已收到您的咨询（{id}）',
    title_rfq: '已收到您的报价委托', title_consult: '已收到您的咨询',
    lead: '感谢您使用 KATACHI。工作人员确认内容后，会联系合适的工厂和专家。',
    ref: '受理编号', ref_note: '咨询时请告知此编号',
    steps_rfq: [['受理', '现在'], ['确认内容', '1〜2个工作日'], ['联系工厂', '由工作人员联系'], ['收到报价', '通常1〜2周']],
    steps_consult: [['受理', '现在'], ['确认内容', '1〜2个工作日'], ['咨询专家・工厂', '由工作人员联系'], ['收到回复', '通常1周左右']],
    sum_h: '您提交的内容', k_sum: '产品概要', k_idea: '想做的东西', k_qty: '阶段与数量', k_due: '希望时间', k_team: '计划联系的公司', k_topic: '咨询内容', k_to: '咨询对象',
    att_h: '有图纸、照片或设计文件吗？', att: '请直接回复本邮件并附上（合计20MB以内）。手绘草图或手机照片也可以，能让报价更准确。',
    att_up_h: '您发送的文件', att_up: '已收到{n}个文件。文件保存在只有工作人员能查看的位置，只会提供给我们请求报价的公司。之后如需补充文件，请直接回复本邮件。',
    note: '目前尚未下单。看到报价或回复后，再决定是否委托即可。整理工序、搜索公司、委托报价均免费。',
    send_h: '可立即通过邮件发送给{n}家公司', send_t: '点击下方按钮，KATACHI 会将委托要点通过邮件发送给 {names}。不会发送您的姓名、邮箱和电话（公司确定接单后再告知）。', send_btn: '通过邮件发送给{n}家公司', send_note: '请在{d}天内点击。如未点击，则不会发送邮件，仍由工作人员确认后联系。', send_prev: '公司收到的邮件（第1家的示例，日文）',
    btn: '打开 KATACHI', foot: '您收到此邮件是因为有人在 KATACHI 的表单中填写了此邮箱。如非本人操作，请回复告知我们。'
  }
};

function esc_(v) { return String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/\n/g, '<br>'); }
function clip_(v, n) { v = String(v || '').trim(); return v.length > n ? v.slice(0, n) + '…' : v; }

function replyUser_(id, email, p, f, ms) {
  var mail = buildReplyMail_(id, p, f || {}, ms);
  MailApp.sendEmail({to: email, subject: mail.subject, body: mail.text, htmlBody: mail.html, name: CONFIG.SERVICE_NAME});
}

function buildReplyMail_(id, p, f, ms) {
  var L = MAIL_TEXT[p.lang] || MAIL_TEXT.ja, rfq = p.type !== 'consult';
  var C = {ink: '#0d1424', mute: '#566176', dim: '#8b94a7', line: '#e3e8f1', bg: '#f5f7fb', ice: '#2350c8', tint: '#eef3fd', mint: '#13845b'};
  var FONT = "-apple-system,BlinkMacSystemFont,'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP','Yu Gothic','PingFang SC','Microsoft YaHei',Meiryo,sans-serif";
  var subject = (rfq ? L.subj_rfq : L.subj_consult).replace('{id}', id);
  var title = rfq ? L.title_rfq : L.title_consult;
  var steps = rfq ? L.steps_rfq : L.steps_consult;
  var upN = p.upload && Number(p.upload.count) > 0 ? Math.min(Number(p.upload.count), CONFIG.UPLOAD_MAX_FILES) : 0;
  var attH = upN ? L.att_up_h : L.att_h, attT = upN ? L.att_up.replace('{n}', upN) : L.att;

  // 内容のまとめ
  var rows = [];
  if (rfq) {
    if (f['f-sum']) rows.push([L.k_sum, clip_(f['f-sum'], 400)]);
    else if (p.idea) rows.push([L.k_idea, clip_(p.idea, 400)]);
    if (f['f-qty']) rows.push([L.k_qty, clip_(f['f-qty'], 200)]);
    if (f['f-due']) rows.push([L.k_due, clip_(f['f-due'], 200)]);
  } else {
    if (p.topic) rows.push([L.k_topic, clip_(p.topic, 200)]);
    if (p.idea) rows.push([L.k_idea, clip_(p.idea, 400)]);
    if ((p.to || []).length) rows.push([L.k_to, clip_((p.to || []).join(', '), 200)]);
  }
  var team = rfq ? (p.team || []).slice(0, 12) : [];

  // ---- HTML ----
  // 工程の線の形（塗り→実線→破線→点線）はサイトの「確かさ」の表し方と同じ
  var marks = [
    'background:' + C.ice + ';border:2px solid ' + C.ice + ';color:#fff;',
    'background:#fff;border:2px solid ' + C.ice + ';color:' + C.ice + ';',
    'background:#fff;border:2px dashed ' + C.ice + ';color:' + C.ice + ';',
    'background:#fff;border:2px dotted ' + C.dim + ';color:' + C.dim + ';'
  ];
  var stepCells = steps.map(function (s, i) {
    return '<td width="25%" valign="top" style="padding:0 4px;text-align:center;">' +
      '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td width="30" height="30" style="' + marks[i] + 'border-radius:6px;font:700 13px/26px ' + FONT + ';text-align:center;">' + (i === 0 ? '&#10003;' : (i + 1)) + '</td></tr></table>' +
      '<div style="margin-top:8px;font:700 13px/1.4 ' + FONT + ';color:' + (i === 0 ? C.ice : C.ink) + ';">' + esc_(s[0]) + '</div>' +
      '<div style="margin-top:2px;font:12px/1.4 ' + FONT + ';color:' + C.mute + ';">' + esc_(s[1]) + '</div></td>';
  }).join('');

  var sumRows = rows.map(function (r) {
    return '<tr><td style="padding:10px 0;border-top:1px solid ' + C.line + ';">' +
      '<div style="font:12px/1.4 ' + FONT + ';color:' + C.mute + ';">' + esc_(r[0]) + '</div>' +
      '<div style="margin-top:3px;font:14px/1.7 ' + FONT + ';color:' + C.ink + ';">' + esc_(r[1]) + '</div></td></tr>';
  }).join('');
  if (team.length) {
    sumRows += '<tr><td style="padding:10px 0 2px;border-top:1px solid ' + C.line + ';"><div style="font:12px/1.4 ' + FONT + ';color:' + C.mute + ';">' + esc_(L.k_team) + '</div>' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:6px;">' +
      team.map(function (t) {
        var abroad = t.country && t.country !== 'JP';
        return '<tr><td style="padding:5px 0;font:13px/1.5 ' + FONT + ';color:' + C.ink + ';">' +
          '<span style="display:inline-block;padding:1px 8px;margin-right:8px;border:1px solid ' + C.ice + ';border-radius:4px;color:' + C.ice + ';font-size:12px;">' + esc_(t.step) + '</span>' +
          esc_(t.company) + (abroad ? ' <span style="color:' + C.dim + ';font-size:12px;">(' + esc_(t.country) + ')</span>' : '') + '</td></tr>';
      }).join('') + '</table></td></tr>';
  }
  var summary = sumRows ? '<tr><td style="padding:8px 32px 24px;">' +
    '<div style="font:700 15px/1.4 ' + FONT + ';color:' + C.ink + ';margin-bottom:6px;">' + esc_(L.sum_h) + '</div>' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">' + sumRows + '</table></td></tr>' : '';

  // メールで届ける会社がある：送るボタン（押すと送られる）と、会社に届くメールの見本
  var sendT = ms ? {h: L.send_h.replace('{n}', ms.names.length), t: L.send_t.replace('{names}', ms.names.join('、')), b: L.send_btn.replace('{n}', ms.names.length), note: L.send_note.replace('{d}', MAIL_CFG.KEY_DAYS)} : null;
  var sendBlk = sendT ? '<tr><td style="padding:0 32px 24px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:2px solid ' + C.ice + ';border-radius:10px;"><tr><td style="padding:18px 20px;">' +
    '<div style="font:700 15px/1.5 ' + FONT + ';color:' + C.ink + ';">&#9993; ' + esc_(sendT.h) + '</div>' +
    '<div style="margin-top:6px;font:13.5px/1.75 ' + FONT + ';color:' + C.ink + ';">' + esc_(sendT.t) + '</div>' +
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px;"><tr><td style="background:' + C.ice + ';border-radius:8px;">' +
    '<a href="' + esc_(ms.url) + '" style="display:inline-block;padding:13px 26px;font:700 15px/1 ' + FONT + ';color:#fff;text-decoration:none;">' + esc_(sendT.b) + ' &rarr;</a></td></tr></table>' +
    '<div style="margin-top:10px;font:12px/1.6 ' + FONT + ';color:' + C.mute + ';">' + esc_(sendT.note) + '</div>' +
    '<div style="margin-top:14px;font:700 12px/1.4 ' + FONT + ';color:' + C.mute + ';">' + esc_(L.send_prev) + '</div>' +
    '<div style="margin-top:6px;padding:12px 14px;background:' + C.bg + ';border-radius:8px;font:12px/1.7 ' + FONT + ';color:' + C.ink + ';">' + esc_(ms.preview) + '</div>' +
    '</td></tr></table></td></tr>' : '';

  var logo = '<table role="presentation" cellpadding="0" cellspacing="2" border="0" style="display:inline-table;vertical-align:middle;"><tr>' +
    '<td width="9" height="9" style="background:' + C.ice + ';font-size:0;line-height:0;">&nbsp;</td><td width="7" height="7" style="border:1px solid ' + C.ice + ';font-size:0;line-height:0;">&nbsp;</td></tr><tr>' +
    '<td width="7" height="7" style="border:1px dashed ' + C.ice + ';font-size:0;line-height:0;">&nbsp;</td><td width="9" height="9" style="background:#a7b9e9;font-size:0;line-height:0;">&nbsp;</td></tr></table>';

  var html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>' + esc_(subject) + '</title></head>' +
    '<body style="margin:0;padding:0;background:' + C.bg + ';">' +
    '<div style="display:none;max-height:0;overflow:hidden;">' + esc_(L.ref + ' ' + id + ' · ' + L.lead) + '</div>' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:' + C.bg + ';"><tr><td align="center" style="padding:28px 12px;">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;">' +
    // ヘッダー
    '<tr><td style="padding:0 8px 16px;">' + logo + '<span style="margin-left:10px;vertical-align:middle;font:800 16px/1 ' + FONT + ';letter-spacing:.18em;color:' + C.ink + ';">KATACHI</span></td></tr>' +
    // カード
    '<tr><td style="background:#fff;border:1px solid ' + C.line + ';border-radius:14px;overflow:hidden;">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">' +
    '<tr><td height="4" style="background:' + C.ice + ';font-size:0;line-height:0;">&nbsp;</td></tr>' +
    '<tr><td style="padding:30px 32px 8px;">' +
    '<div style="display:inline-block;padding:3px 10px;border-radius:999px;background:#e7f5ee;color:' + C.mint + ';font:700 12px/1.5 ' + FONT + ';">&#10003; ' + esc_(steps[0][0]) + '</div>' +
    '<h1 style="margin:12px 0 10px;font:800 24px/1.35 ' + FONT + ';color:' + C.ink + ';">' + esc_(title) + '</h1>' +
    '<p style="margin:0;font:14px/1.8 ' + FONT + ';color:' + C.mute + ';">' + esc_(L.lead) + '</p></td></tr>' +
    // 受付番号
    '<tr><td style="padding:18px 32px 6px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:' + C.tint + ';border-radius:10px;"><tr><td style="padding:16px 20px;">' +
    '<div style="font:12px/1.4 ' + FONT + ';color:' + C.mute + ';">' + esc_(L.ref) + '</div>' +
    '<div style="margin-top:4px;font:700 26px/1.2 Menlo,Consolas,\'Courier New\',monospace;letter-spacing:.06em;color:' + C.ice + ';">' + esc_(id) + '</div>' +
    '<div style="margin-top:4px;font:12px/1.4 ' + FONT + ';color:' + C.mute + ';">' + esc_(L.ref_note) + '</div></td></tr></table></td></tr>' +
    // ステップ
    '<tr><td style="padding:22px 28px 26px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' + stepCells + '</tr></table></td></tr>' +
    summary + sendBlk +
    // 添付のお願い
    '<tr><td style="padding:0 32px 24px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1.5px dashed ' + C.ice + ';border-radius:10px;"><tr><td style="padding:16px 20px;">' +
    '<div style="font:700 14px/1.5 ' + FONT + ';color:' + C.ink + ';">&#128206; ' + esc_(attH) + '</div>' +
    '<div style="margin-top:4px;font:13px/1.7 ' + FONT + ';color:' + C.mute + ';">' + esc_(attT) + '</div></td></tr></table></td></tr>' +
    // 注意とボタン
    '<tr><td style="padding:0 32px 30px;">' +
    '<p style="margin:0 0 20px;font:13px/1.8 ' + FONT + ';color:' + C.mute + ';">' + esc_(L.note) + '</p>' +
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td style="background:' + C.ice + ';border-radius:8px;">' +
    '<a href="' + CONFIG.SITE_URL + '" style="display:inline-block;padding:12px 26px;font:700 14px/1 ' + FONT + ';color:#fff;text-decoration:none;">' + esc_(L.btn) + ' &rarr;</a></td></tr></table></td></tr>' +
    '</table></td></tr>' +
    // フッター
    '<tr><td style="padding:18px 12px 0;font:11.5px/1.7 ' + FONT + ';color:' + C.dim + ';text-align:center;">' + esc_(L.foot) +
    '<br><a href="' + CONFIG.SITE_URL + '" style="color:' + C.dim + ';">katachi.shiokonbu.com</a> · &copy; KATACHI</td></tr>' +
    '</table></td></tr></table></body></html>';

  // ---- テキスト版（HTMLが表示できないメールソフト向け） ----
  var text = [L.lead, '', L.ref + ': ' + id, '',
    steps.map(function (s, i) { return (i === 0 ? '✓ ' : (i + 1) + '. ') + s[0] + '（' + s[1] + '）'; }).join('\n'), '',
    rows.length || team.length ? '■ ' + L.sum_h : '',
    rows.map(function (r) { return r[0] + ': ' + r[1]; }).join('\n'),
    team.length ? L.k_team + ':\n' + team.map(function (t) { return '  - ' + t.step + ': ' + t.company; }).join('\n') : '', '',
    sendT ? '■ ' + sendT.h + '\n' + sendT.t + '\n' + sendT.b + ': ' + ms.url + '\n' + sendT.note + '\n\n' + L.send_prev + ':\n' + ms.preview : '', '',
    '■ ' + attH, attT, '', L.note, '', CONFIG.SITE_URL].filter(function (x, i, a) { return !(x === '' && a[i - 1] === ''); }).join('\n');

  return {subject: subject, html: html, text: text};
}

// 見た目の確認用: エディタでこの関数を実行すると、自分宛てに見本（日本語）が届く
function previewReplyMail() {
  var p = {type: 'rfq', lang: 'ja', idea: '犬の首輪に小さなGPSを入れたい',
    team: [{step: '筐体の成形', company: '（見本）樹脂成形の会社', country: 'JP'}, {step: '回路基板', company: '（見本）基板実装の会社', country: 'CN'}]};
  var f = {'f-sum': '小型犬向けのGPS付き首輪。防水で、充電は1週間に1回程度。', 'f-qty': '試作 3個 → 小ロット 300個', 'f-due': '3か月以内に試作'};
  var to = Session.getEffectiveUser().getEmail();
  var mail = buildReplyMail_('K000000-TEST', p, f);
  MailApp.sendEmail({to: to, subject: '[見本] ' + mail.subject, body: mail.text, htmlBody: mail.html, name: CONFIG.SERVICE_NAME});
}

function sheet_() {
  var props = PropertiesService.getScriptProperties();
  var sid = props.getProperty('SHEET_ID');
  var ss = sid ? SpreadsheetApp.openById(sid) : null;
  if (!ss) {
    ss = SpreadsheetApp.create('KATACHI 受付');
    props.setProperty('SHEET_ID', ss.getId());
    var s0 = ss.getSheets()[0];
    s0.setName('受付');
    s0.appendRow(HEAD);
    s0.setFrozenRows(1);
  }
  var sh = ss.getSheetByName('受付');
  if (sh.getLastColumn() < HEAD.length) sh.getRange(1, 1, 1, HEAD.length).setValues([HEAD]);  // 列が増えたときの見出し
  return sh;
}

function prop_(k) { return PropertiesService.getScriptProperties().getProperty(k); }

function limit_(prefix, max) {
  var c = CacheService.getScriptCache();
  var k = (prefix || 'n') + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd');
  var n = Number(c.get(k) || 0);
  if (n >= (max || CONFIG.DAILY_LIMIT)) return false;
  c.put(k, String(n + 1), 21600);
  return true;
}

// 表計算の式として解釈されないようにする
function safe_(v) { return (typeof v === 'string' && /^[=+\-@]/.test(v)) ? "'" + v : v; }

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

// ---------- 写真・動画などのアップロード ----------
// サイトは見積の依頼・相談と一緒に upload = {key, count, bytes} を送り、続けてファイルを小分け（4MBずつ）で type:'file' として送る。
// key は送った本人のブラウザだけが知っている使い捨ての合言葉（6時間有効）。宣言した数と大きさを超えるものは受け付けない。
// ファイルは「KATACHI 受付ファイル / 受付番号」の非公開フォルダに入る（共有しない限り、このGoogleアカウントの人しか見られない）。
function openUpload_(id, up) {
  try {
    if (!up || !/^[A-Za-z0-9]{24,64}$/.test(String(up.key || ''))) return '';
    var n = Math.floor(Number(up.count) || 0), bytes = Math.floor(Number(up.bytes) || 0);
    if (n < 1 || n > CONFIG.UPLOAD_MAX_FILES || bytes < 1 || bytes > CONFIG.UPLOAD_MAX_BYTES) return '';
    var folder = uploadRoot_().createFolder(id);
    CacheService.getScriptCache().put('up_' + up.key, JSON.stringify({id: id, folder: folder.getId(), n: n, bytes: bytes, used: 0, done: []}), 21600);
    return folder.getUrl() + '\n（' + n + '件を送信中）';
  } catch (err) {
    console.error(err);
    return '';
  }
}

function uploadRoot_() {
  var props = PropertiesService.getScriptProperties();
  var fid = props.getProperty('UPLOAD_FOLDER_ID'), f = null;
  if (fid) { try { f = DriveApp.getFolderById(fid); } catch (e) { f = null; } }
  if (!f) {
    f = DriveApp.createFolder(CONFIG.UPLOAD_FOLDER_NAME);
    props.setProperty('UPLOAD_FOLDER_ID', f.getId());
  }
  return f;
}

function saveChunk_(p) {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(20000)) return {ok: false, error: 'busy'};
  try {
    var key = String(p.key || '');
    if (!/^[A-Za-z0-9]{24,64}$/.test(key)) return {ok: false, error: 'key'};
    var cache = CacheService.getScriptCache();
    var st = JSON.parse(cache.get('up_' + key) || 'null');
    if (!st) return {ok: false, error: 'expired'};
    var idx = Math.floor(Number(p.index)), size = Math.floor(Number(p.size)), off = Math.floor(Number(p.offset)) || 0;
    if (!(idx >= 0 && idx < st.n) || st.done.indexOf(idx) >= 0) return {ok: false, error: 'index'};
    if (!(size > 0 && size <= CONFIG.UPLOAD_FILE_MAX)) return {ok: false, error: 'size'};
    var bytes = Utilities.base64Decode(String(p.data || ''));
    var len = bytes.length;
    if (!len || off + len > size || st.used + len > st.bytes + 1048576) return {ok: false, error: 'size'};
    var name = (idx < 9 ? '0' : '') + (idx + 1) + '_' + String(p.name || 'file').replace(/[\\\/:*?"<>|\u0000-\u001f]/g, '_').slice(0, 120);
    var mime = /^[\w.+-]+\/[\w.+-]+$/.test(String(p.mime || '')) ? String(p.mime) : 'application/octet-stream';
    var finished = false;
    if (off === 0 && len === size) {
      DriveApp.getFolderById(st.folder).createFile(Utilities.newBlob(bytes, mime, name));
      finished = true;
    } else {
      // 大きいファイルは Google ドライブの「再開可能なアップロード」で小分けに書き足す
      var sk = 'us_' + key + '_' + idx, token = ScriptApp.getOAuthToken();
      var session = cache.get(sk);
      if (off === 0) {
        var start = UrlFetchApp.fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable', {
          method: 'post', contentType: 'application/json; charset=UTF-8',
          headers: {Authorization: 'Bearer ' + token, 'X-Upload-Content-Type': mime, 'X-Upload-Content-Length': String(size)},
          payload: JSON.stringify({name: name, parents: [st.folder]}), muteHttpExceptions: true
        });
        var hd = start.getAllHeaders();
        session = hd['Location'] || hd['location'];
        if (!session) { console.error(start.getResponseCode() + ' ' + start.getContentText()); return {ok: false, error: 'drive'}; }
        cache.put(sk, session, 21600);
      }
      if (!session) return {ok: false, error: 'expired'};
      var res = UrlFetchApp.fetch(session, {
        method: 'put', contentType: mime, payload: bytes, muteHttpExceptions: true,
        headers: {'Content-Range': 'bytes ' + off + '-' + (off + len - 1) + '/' + size}
      });
      var code = res.getResponseCode();
      if (code === 200 || code === 201) finished = true;
      else if (code !== 308) { console.error(code + ' ' + res.getContentText()); return {ok: false, error: 'drive'}; }
    }
    st.used += len;
    if (finished) {
      st.done.push(idx);
      noteUpload_(st, name);
    }
    cache.put('up_' + key, JSON.stringify(st), 21600);
    return {ok: true, done: finished};
  } catch (err) {
    console.error(err);
    return {ok: false, error: 'unavailable'};
  } finally {
    lock.releaseLock();
  }
}

// 受付の行の「アップロードしたファイル」に、届いたファイル名を書き足す
function noteUpload_(st, name) {
  var partner = String(st.id).charAt(0) === 'P';  // 提携申込み（P…）は「提携申込」タブ
  var sh = partner ? partnerSheet_() : sheet_();
  var hit = sh.getRange(1, 1, sh.getLastRow(), 1).createTextFinder(st.id).matchEntireCell(true).findNext();
  if (!hit) return;
  var cell = sh.getRange(hit.getRow(), partner ? PARTNER_HEAD.indexOf('アップロードしたファイル') + 1 : HEAD.length);
  var url = 'https://drive.google.com/drive/folders/' + st.folder;
  var names = String(cell.getValue() || '').split('\n').filter(function (x) { return x && x.indexOf('https://') !== 0 && !/^（.*）$/.test(x); });
  names.push(name);
  cell.setValue([url, '（' + st.done.length + '/' + st.n + '件 届いた）'].concat(names).join('\n'));
}

// ---------- 工場・開発企業の提携申込み（/partner/ のフォーム） ----------
// 「提携申込」タブに1行追加 → 運営者に通知 → 申し込んだ会社に受付メール。
// 最後の列「取り込み用JSON」は企業DB（katachi-matching）の company_record の形。
// 確認して承認の連絡（規約・料金表つき）→ 相手が同意したら「状態」を「提携成立」にし、
// katachi-matching の `python -m katachi.cli load-partners <このタブのCSV>` で企業DBに取り込んで「取り込み済み」にする。
var PARTNER_HEAD = ['受付番号', '受付日時', '言語', '会社名', '国', '都道府県・市区町村', '法人番号', '公式サイト', '事業の形', '従業員数',
  '担当者', '役職・部署', 'メール', '電話', '得意な工程', '対応できる工程', '受けられる数量', '会社の紹介', '解決してきた課題',
  '掲載の充実度', '口コミ掲載への同意', '状態', 'メモ', 'アップロードしたファイル', '取り込み用JSON'];

function partner_(p) {
  if (!limit_('p', 100)) return {ok: false, error: 'busy'};
  var r = p.record || {};
  var c = r.contact || {};
  var email = String(c.email || '').trim();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return {ok: false, error: 'email'};
  var name = String(r.name || '').trim();
  if (!name || !String(r.website || '').trim()) return {ok: false, error: 'fields'};
  var id = 'P' + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyMMdd') + '-' + Math.random().toString(36).slice(2, 6).toUpperCase();
  r.source = r.source || {};
  r.source.application_id = id;
  var s = function (v, n) { return String(v == null ? '' : v).slice(0, n || 500); };
  var caps = r.capabilities || [];
  var codes = function (lv) { return caps.filter(function (x) { return x && x.level === lv; }).map(function (x) { return s(x.code, 80); }).join('\n'); };
  var probs = (r.solved_problems || []).map(function (x) { return '・' + s(x.problem, 300) + (x.approach ? ' → ' + s(x.approach, 500) : ''); }).join('\n');
  var prof = r.profile || {};
  var json = JSON.stringify(r);
  if (json.length > 45000) return {ok: false, error: 'size'};
  var row = [id, new Date(), s(p.lang, 5), s(name, 200), s(r.country, 5), [r.prefecture, r.city].filter(String).join(' '),
    s(r.corporate_number, 20), s(r.website, 300), s(r.business_type, 40), r.employees || '',
    s(c.person, 100), s(c.role, 100), email, s(c.tel, 40), codes('specialty'), codes('capable'),
    s([].concat(prof.quantity_bands || []).join(', '), 200), s(r.summary, 2000), probs.slice(0, 4000),
    (prof.completeness != null ? prof.completeness + '%' : ''), (r.agreements || {}).reviews_publish ? 'はい' : 'いいえ', '未確認', '', openUpload_(id, p.upload), json];
  var sh = partnerSheet_();
  sh.appendRow(row.map(safe_));
  try { slotPartner_(id, name, prof); } catch (err) { console.error(err); }
  try { notifyPartnerAdmin_(id, row, sh); } catch (err) { console.error(err); }
  try { replyPartner_(id, email, p.lang, name, p.upload); } catch (err) { console.error(err); }
  return {ok: true, id: id};
}

function partnerSheet_() {
  var ss = sheet_().getParent();
  var sh = ss.getSheetByName('提携申込');
  if (!sh) {
    sh = ss.insertSheet('提携申込');
    sh.appendRow(PARTNER_HEAD);
    sh.setFrozenRows(1);
    // 状態は選んで入れる（未確認 → 確認中 → 提携成立 / 見送り、DBに入れたら取り込み済み）
    sh.getRange(2, PARTNER_HEAD.indexOf('状態') + 1, 999, 1).setDataValidation(
      SpreadsheetApp.newDataValidation().requireValueInList(['未確認', '確認中', '提携成立', '見送り', '取り込み済み'], true).build());
  }
  return sh;
}

function notifyPartnerAdmin_(id, row, sh) {
  var to = CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail();
  var body = PARTNER_HEAD.slice(0, -1).map(function (h, i) { return '■ ' + h + '\n' + (row[i] instanceof Date ? Utilities.formatDate(row[i], 'Asia/Tokyo', 'yyyy-MM-dd HH:mm') : row[i]); }).join('\n\n');
  MailApp.sendEmail({to: to, subject: '[KATACHI] 新しい提携申込み ' + id + ' ' + row[3],
    body: '確認すること: 法人番号・公式サイト・連絡先。目安は3営業日以内に返事。\n\n' + body + '\n\n一覧（「提携申込」タブ）: ' + sh.getParent().getUrl()});
}

var PARTNER_MAIL = {
  ja: {subj: '【KATACHI】提携のお申込みを受け付けました（{id}）',
    files: '写真・証明書を{n}件お預かりしました（運営者だけが見られる場所に保存します）。追加や差し替えは、このメールへの返信で送れます。',
    nofiles: '認証の証明書や、工場・設備・製品の写真は、あとからでも提出できます。このメールへの返信で送ってください。',
    body: '{name} ご担当者様\n\nKATACHI への提携のお申込み、ありがとうございます。\n\n受付番号: {id}\n\nこのあと次の順に進みます。\n1. KATACHI が法人番号・公式サイト・連絡先を確認します。\n2. 3営業日以内を目安に、提携の可否と、正式な規約・料金表をメールでお送りします。\n3. 規約と料金表にご同意いただいた時点で提携が成立し、掲載が始まります。確認が済むまで、工程は「自己申告」の印で表示されます。\n\n{files}\n\nお申込みの内容を直したいときも、このメールに返信してお知らせください。\n\nKATACHI\n{site}'},
  en: {subj: '[KATACHI] We received your partner application ({id})',
    files: 'We received {n} photo/certificate file(s). They are stored where only our staff can see them. To add or replace files, just reply to this email.',
    nofiles: 'You can send certificates and photos of your factory, equipment and products later by replying to this email.',
    body: 'Dear {name},\n\nThank you for applying to partner with KATACHI.\n\nReference: {id}\n\nWhat happens next:\n1. KATACHI checks your corporate number, website and contact details.\n2. Usually within 3 business days, we email you our decision together with the full terms and fee schedule.\n3. The partnership begins when you accept the terms and fee schedule, and your listing goes live. Until we verify them, your processes are shown as "self-reported".\n\n{files}\n\nTo correct anything in your application, just reply to this email.\n\nKATACHI\n{site}'},
  zh: {subj: '[KATACHI] 已收到贵公司的合作申请（{id}）',
    files: '已收到{n}个照片・证书文件（保存在只有工作人员能查看的位置）。如需补充或替换，请直接回复本邮件。',
    nofiles: '认证证书以及工厂・设备・产品照片可以之后提交，请回复本邮件发送。',
    body: '{name} 负责人您好：\n\n感谢贵公司申请与 KATACHI 合作。\n\n受理编号：{id}\n\n接下来的流程：\n1. KATACHI 确认法人编号、官方网站和联系方式。\n2. 一般在3个工作日内，通过邮件告知审核结果，并附上正式条款和收费表。\n3. 贵公司同意条款和收费表后合作成立，开始刊登。确认完成前，工序会标注为“自行申报”。\n\n{files}\n\n如需修改申请内容，也请直接回复本邮件。\n\nKATACHI\n{site}'}
};

function replyPartner_(id, email, lang, name, up) {
  var L = PARTNER_MAIL[lang] || PARTNER_MAIL.ja;
  var n = up && Number(up.count) > 0 ? Math.min(Number(up.count), CONFIG.UPLOAD_MAX_FILES) : 0;
  var f = function (t) { return t.replace(/\{files\}/g, n ? L.files.replace('{n}', n) : L.nofiles).replace(/\{id\}/g, id).replace(/\{name\}/g, name).replace(/\{site\}/g, CONFIG.SITE_URL); };
  MailApp.sendEmail({to: email, subject: f(L.subj), body: f(L.body), name: CONFIG.SERVICE_NAME});
}

// ---------- Googleの口コミ（ペットサイト pet.shiokonbu.com と同じ方式） ----------
// サイトの「Googleの口コミを見る」を押したときだけ、その会社の星・件数・口コミ（地図サービスが関連度の高い順に返す最大5件）を取り寄せて返す。
// 規約により、口コミ・星は保存しない（毎回取り寄せる）。保存するのは場所のIDだけ（見つからなければ '-'）。
// 書いた人（名前・アイコン・プロフィールへのリンク）と、口コミそれぞれの元のページへのリンクを一緒に返し、サイトは「Google Maps」の表示を付ける。
function reviews_(p) {
  var props = PropertiesService.getScriptProperties(), apiKey = props.getProperty('PLACES_API_KEY');
  if (!apiKey) return {ok: false, error: 'off'};
  var name = String(p.name || '').trim().slice(0, 80), pref = String(p.pref || '').trim().slice(0, 20), city = String(p.city || '').trim().slice(0, 40);
  var jp = !p.country || p.country === 'JP';
  var lang = {en: 'en', zh: 'zh-CN'}[p.lang] || 'ja';
  if (!name) return {ok: false, error: 'name'};
  if (!limit_('rv', CONFIG.REVIEW_DAILY_LIMIT)) return {ok: false, error: 'busy'};
  var ym = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMM');
  var key = 'PLACE_' + Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, [name, pref, city].join('|'), Utilities.Charset.UTF_8)).slice(0, 16);
  var placeId = props.getProperty(key);
  if (placeId === '-') return {ok: false, error: 'notfound'};
  try {
    if (!placeId) {
      var sk = 'REVIEW_SEARCH_' + ym, su = Number(props.getProperty(sk)) || 0;
      if (su >= CONFIG.REVIEW_SEARCH_MONTHLY_LIMIT) return {ok: false, error: 'limit'};
      props.setProperty(sk, String(su + 1));
      var body = {textQuery: [name, jp ? pref : '', city].filter(String).join(' ')};
      if (jp) body.regionCode = 'JP';
      body.languageCode = lang;
      var res = UrlFetchApp.fetch('https://places.googleapis.com/v1/places:searchText', {method: 'post', contentType: 'application/json', muteHttpExceptions: true,
        headers: {'X-Goog-Api-Key': apiKey, 'X-Goog-FieldMask': 'places.id,places.displayName'}, payload: JSON.stringify(body)});
      var found = {};
      try { found = JSON.parse(res.getContentText()) || {}; } catch (e) {}
      if (res.getResponseCode() !== 200) { Logger.log('口コミ：検索エラー ' + res.getResponseCode()); return {ok: false, error: 'unavailable'}; }
      // 所在地が分からない会社は、同じ名前の別の会社を拾わないよう、名前が同じときだけにする
      var core = placeNorm_(name), strict = !pref && !city;
      var hit = (found.places || []).filter(function (x) {
        var dn = placeNorm_((x.displayName || {}).text || '');
        return dn && core && (strict ? dn === core : (dn.indexOf(core) >= 0 || core.indexOf(dn) >= 0));
      })[0];
      placeId = hit && hit.id ? hit.id : '-';
      props.setProperty(key, placeId);
      if (placeId === '-') return {ok: false, error: 'notfound'};
    }
    var mk = 'REVIEW_COUNT_' + ym, used = Number(props.getProperty(mk)) || 0;
    if (used >= CONFIG.REVIEW_MONTHLY_LIMIT) return {ok: false, error: 'limit'};
    props.setProperty(mk, String(used + 1));
    var d = UrlFetchApp.fetch('https://places.googleapis.com/v1/places/' + encodeURIComponent(placeId) + '?languageCode=' + lang, {muteHttpExceptions: true,
      headers: {'X-Goog-Api-Key': apiKey, 'X-Goog-FieldMask': 'displayName,formattedAddress,rating,userRatingCount,reviews,googleMapsUri'}});
    if (d.getResponseCode() !== 200) { Logger.log('口コミ：取り寄せ失敗 ' + d.getResponseCode()); return {ok: false, error: 'unavailable'}; }
    var v = JSON.parse(d.getContentText());
    return {ok: true, rating: v.rating || 0, count: Number(v.userRatingCount) || 0, maps: v.googleMapsUri || '', place: (v.displayName || {}).text || '', address: v.formattedAddress || '', reviews: (v.reviews || []).slice(0, 5).map(function (x) {
      var a = x.authorAttribution || {};
      return {rating: x.rating || 0, when: x.relativePublishTimeDescription || '', text: ((x.text || x.originalText || {}).text || '').slice(0, 2000),
        author: a.displayName || '', authorUrl: a.uri || '', photo: a.photoUri || '', url: x.googleMapsUri || ''};
    })};
  } catch (e) {
    Logger.log('口コミ：エラー ' + e);
    return {ok: false, error: 'unavailable'};
  }
}

// 社名の照合用（全角・半角、空白、「株式会社」などの違いは気にしない）
function placeNorm_(x) {
  return String(x).normalize('NFKC').replace(/\s/g, '').toLowerCase()
    .replace(/株式会社|有限会社|合同会社|合資会社|合名会社|\(株\)|\(有\)|co\.,?ltd\.?|inc\.?|corp(oration)?\.?|limited|ltd\.?|,/g, '');
}


// ---------- 部品の参考価格・在庫（DigiKey Product Information API v4） ----------
// 利用者が入れた部品名・型番だけを DigiKey に送り、上位5件の型番・メーカー・説明・単価（1個）・在庫・製品ページを返す。
// キーはスクリプトのプロパティ DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET（無ければ error:'off'）。結果は保存しない（同じ語は6時間だけ覚えておく）。
function parts_(p) {
  var q = String(p.q || '').normalize('NFKC').replace(/[\s　]+/g, ' ').trim().slice(0, 80);
  if (q.length < 2) return {ok: false, error: 'short'};
  var id = prop_('DIGIKEY_CLIENT_ID'), secret = prop_('DIGIKEY_CLIENT_SECRET');
  if (!id || !secret) return {ok: false, error: 'off'};
  var cache = CacheService.getScriptCache(), ck = 'dk_' + Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, q, Utilities.Charset.UTF_8)).slice(0, 22);
  var hit = cache.get(ck);
  if (hit) return JSON.parse(hit);
  if (!limit_('dk', CONFIG.PARTS_DAILY_LIMIT)) return {ok: false, error: 'busy'};
  try {
    var tok = cache.get('dk_token');
    if (!tok) {
      var t = UrlFetchApp.fetch('https://api.digikey.com/v1/oauth2/token', {method: 'post', muteHttpExceptions: true,
        payload: {client_id: id, client_secret: secret, grant_type: 'client_credentials'}});
      if (t.getResponseCode() !== 200) { Logger.log('DigiKey token ' + t.getResponseCode() + ' ' + t.getContentText().slice(0, 300)); return {ok: false, error: 'auth'}; }
      var tj = JSON.parse(t.getContentText());
      tok = tj.access_token;
      cache.put('dk_token', tok, Math.max(60, Math.min(540, (Number(tj.expires_in) || 600) - 60)));
    }
    var r = UrlFetchApp.fetch('https://api.digikey.com/products/v4/search/keyword', {method: 'post', contentType: 'application/json', muteHttpExceptions: true,
      headers: {'X-DIGIKEY-Client-Id': id, 'Authorization': 'Bearer ' + tok, 'X-DIGIKEY-Locale-Site': 'JP', 'X-DIGIKEY-Locale-Language': 'ja', 'X-DIGIKEY-Locale-Currency': 'JPY'},
      payload: JSON.stringify({Keywords: q, Limit: 5, Offset: 0})});
    var code = r.getResponseCode();
    if (code === 401) cache.remove('dk_token');
    if (code !== 200) { Logger.log('DigiKey search ' + code + ' ' + r.getContentText().slice(0, 300)); return {ok: false, error: 'http' + code}; }
    var o = JSON.parse(r.getContentText()), list = (o.ExactMatches && o.ExactMatches.length ? o.ExactMatches : []).concat(o.Products || []);
    var seen = {}, rows = [];
    list.forEach(function (x) {
      var mpn = String(x.ManufacturerProductNumber || '');
      if (!mpn || seen[mpn] || rows.length >= 5) return;
      seen[mpn] = 1;
      rows.push({mpn: mpn.slice(0, 80), maker: String((x.Manufacturer || {}).Name || '').slice(0, 60),
        desc: String((x.Description || {}).ProductDescription || '').slice(0, 120), price: Number(x.UnitPrice) || 0,
        stock: Number(x.QuantityAvailable) || 0, status: String((x.ProductStatus || {}).Status || '').slice(0, 30), url: String(x.ProductUrl || '').slice(0, 300)});
    });
    var out = {ok: true, total: Number(o.ProductsCount) || rows.length, currency: 'JPY', at: Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd'), rows: rows};
    try { cache.put(ck, JSON.stringify(out), 21600); } catch (e) {}
    return out;
  } catch (err) { Logger.log('DigiKey error ' + err); return {ok: false, error: 'fetch'}; }
}


// ---------- 技適の検索（総務省「技術基準適合証明等を受けた機器の検索」Web-API、無料・登録不要） ----------
// 利用者が入れた無線モジュール・機器の型式（例：ESP32-WROOM-32E）だけを総務省に送り、件数と上位5件の
// 型式・名称・番号・日付・種類を返す。保存はしない（同じ型式は6時間だけ覚えておく）。
// ※2026-11-14 時点で総務省側が Google のサーバーからの接続を 403 で断るため、サイトからは使っていない（template.html の GITEKI=false）。
function giteki_(p) {
  var tn = String(p.tn || '').normalize('NFKC').replace(/[\s　]+/g, ' ').trim().slice(0, 80);
  if (tn.length < 3) return {ok: false, error: 'short'};
  var cache = CacheService.getScriptCache(), ck = 'gk_' + Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, tn, Utilities.Charset.UTF_8)).slice(0, 22);
  var hit = cache.get(ck);
  if (hit) return JSON.parse(hit);
  if (!limit_('gk', CONFIG.GITEKI_DAILY_LIMIT)) return {ok: false, error: 'busy'};
  var res;
  try {
    res = UrlFetchApp.fetch('https://www.tele.soumu.go.jp/giteki/list?SC=1&DC=1&OF=2&TN=' + encodeURIComponent(tn), {muteHttpExceptions: true});
  } catch (err) { return {ok: false, error: 'fetch'}; }
  if (res.getResponseCode() !== 200) return {ok: false, error: 'http' + res.getResponseCode()};
  var o;
  try { o = JSON.parse(res.getContentText('UTF-8')); } catch (e) { return {ok: false, error: 'parse'}; }
  var head = o.gitekiInformation || {}, list = o.giteki || [];
  if (!Array.isArray(list)) list = [list];
  var rows = list.map(function (x) { return x.gitekiInfo || x; }).slice(0, 5).map(function (g) {
    return {type: String(g.typeName || '').slice(0, 120), name: String(g.name || '').replace(/\s*法人番号\d{13}$/, '').slice(0, 80),
      number: String(g.number || '').slice(0, 40), date: String(g.date || '').slice(0, 10), tech: String(g.techCode || '').slice(0, 60),
      equip: String(g.radioEquipmentCode || '').slice(0, 80)};
  });
  var out = {ok: true, total: Number(head.totalCount) || rows.length, updated: String(head.lastUpdateDate || ''), rows: rows};
  try { cache.put(ck, JSON.stringify(out), 21600); } catch (e) {}
  return out;
}


// ---------- 参考品のページを読む（既製品をもとに作る） ----------
// 利用者が入れたURLのページを、この受付が1回だけ取りに行き、題名・説明・商品名・パンくずなど「何の製品か」がわかる短い文字だけを返す。
// 画像や本文は返さない・保存しない（同じURLは6時間だけ一時的に覚えておく）。会員ページ・社内のアドレスは読まない。
function peek_(p) {
  var url = String(p.url || '').trim().slice(0, 1000);
  if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
  var m = url.match(/^https?:\/\/([^\/?#:]+)/i);
  if (!m || !/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(m[1]) || /^(localhost|.*\.local|.*\.internal)$/i.test(m[1]) || /^\d+\.\d+\.\d+\.\d+$/.test(m[1])) return {ok: false, error: 'url'};
  var cache = CacheService.getScriptCache();
  var ck = 'pk_' + Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, url, Utilities.Charset.UTF_8)).slice(0, 22);
  var hit = cache.get(ck);
  if (hit) return JSON.parse(hit);
  if (!limit_('pk', CONFIG.PEEK_DAILY_LIMIT)) return {ok: false, error: 'busy'};
  var res;
  try {
    res = UrlFetchApp.fetch(url, {muteHttpExceptions: true, followRedirects: true, validateHttpsCertificates: true,
      headers: {'User-Agent': 'Mozilla/5.0 (compatible; KATACHI-preview/1.0; +https://katachi.shiokonbu.com/)', 'Accept-Language': 'ja,en;q=0.8'}});
  } catch (err) { return {ok: false, error: 'fetch'}; }
  var code = res.getResponseCode();
  if (code >= 400) return {ok: false, error: 'http' + code};
  var blob = res.getBlob(), html = blob.getDataAsString('UTF-8');
  var cs = (html.slice(0, 4000).match(/<meta[^>]+charset=["']?([\w-]+)/i) || [])[1] || '';
  if (cs && !/utf-?8/i.test(cs)) { try { html = blob.getDataAsString(cs); } catch (e) {} }
  html = html.slice(0, 800000);
  var dec = function (t) {
    return String(t || '').replace(/<[^>]*>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'")
      .replace(/&#(\d+);/g, function (a, n) { return String.fromCharCode(Number(n)); }).replace(/\s+/g, ' ').trim();
  };
  var meta = function (name) {
    var re = new RegExp('<meta[^>]+(?:name|property)=["\']' + name + '["\'][^>]*>', 'i'), t = (html.match(re) || [])[0] || '';
    return dec((t.match(/content=["']([^"']*)["']/i) || [])[1] || '').slice(0, 300);
  };
  var out = {ok: true, title: dec((html.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1]).slice(0, 200),
    desc: meta('description') || meta('og:description'), ogtitle: meta('og:title'), site: meta('og:site_name'), keywords: meta('keywords').slice(0, 200),
    h1: dec((html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i) || [])[1]).slice(0, 120), product: {}, crumbs: []};
  (html.match(/<script[^>]+application\/ld\+json[^>]*>[\s\S]*?<\/script>/gi) || []).slice(0, 8).forEach(function (blk) {
    try {
      var j = JSON.parse(blk.replace(/^<script[^>]*>|<\/script>$/gi, ''));
      var all = [].concat(j['@graph'] || j);
      all.forEach(function (o) {
        var ty = [].concat(o['@type'] || []).join(',');
        if (/Product/.test(ty) && !out.product.name) out.product = {name: dec(o.name).slice(0, 150), desc: dec(o.description).slice(0, 300), category: dec(o.category).slice(0, 100), material: dec(o.material).slice(0, 100)};
        if (/BreadcrumbList/.test(ty)) out.crumbs = (o.itemListElement || []).map(function (x) { return dec(x.name || (x.item && x.item.name)).slice(0, 40); }).filter(String).slice(0, 6);
      });
    } catch (e) {}
  });
  if (!out.title && !out.desc && !out.ogtitle && !out.product.name) out = {ok: false, error: 'empty'};
  cache.put(ck, JSON.stringify(out), 21600);
  return out;
}

/**
 * 依頼の文章（長い仕様文）を項目に整理した結果の保存と読み出し（AIのAPIは使わない＝費用ゼロ）
 * - 整理は利用者が自分の ChatGPT・Claude・Gemini で行い、決まった形の JSON を KATACHI に貼り戻す。
 * - type:'specsave' … 依頼文と JSON を受け取り、根拠の原文（quote）が依頼文に見つからない値を「要確認」にしてから、シート「仕様読み取り」に保存。
 * - type:'spec' … 同じ依頼文（ハッシュ）の保存済みの結果があれば返す。
 * - 「DBの一致」が空の行は、製品仕様DB（tools/product_db.py）にない新しい製品。見直してDBに足して育てる。
 */
var SPEC_HEAD = ['日時', 'ハッシュ', '保存した回数', 'DBの一致', '文字数', '製品名', '種類', '結果（JSON）'];

function specHash_(text) {
  var norm = String(text || '').replace(/\r\n?/g, '\n').trim().replace(/\s+/g, ' ');
  return Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, norm, Utilities.Charset.UTF_8)).replace(/=+$/, '');
}

function spec_(p) {
  var text = String(p.text || '').trim().slice(0, CONFIG.SPEC_MAX_CHARS);
  if (text.length < 20) return {ok: false, error: 'short'};
  var hash = specHash_(text), cache = CacheService.getScriptCache(), ck = 'sp_' + hash;
  var hit = cache.get(ck);
  if (hit) return {ok: true, spec: JSON.parse(hit)};
  if (!limit_('sp', CONFIG.SPEC_DAILY_LIMIT)) return {ok: false, error: 'busy'};
  var sh = specSheet_(), found = sh.getRange('B:B').createTextFinder(hash).matchEntireCell(true).findNext();
  if (!found) return {ok: false, error: 'none'};
  try { var js = sh.getRange(found.getRow(), 8).getValue(), o = JSON.parse(js); if (js.length < 90000) cache.put(ck, js, 21600); return {ok: true, spec: o}; } catch (e) { return {ok: false, error: 'parse'}; }
}

function specSave_(p) {
  var text = String(p.text || '').trim().slice(0, CONFIG.SPEC_MAX_CHARS);
  if (text.length < 20 || !p.spec || typeof p.spec !== 'object') return {ok: false, error: 'bad'};
  if (!limit_('ss', CONFIG.SPEC_DAILY_LIMIT)) return {ok: false, error: 'busy'};
  var ids = (p.kinds || []).filter(function (k) { return /^[a-z_]{1,30}$/.test(k); }).slice(0, 80).concat(['other']);
  var out = specCheck_(p.spec, text, ids), js = JSON.stringify(out);
  if (js.length > 45000) return {ok: false, error: 'big'};
  var hash = specHash_(text), sh = specSheet_(), lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var found = sh.getRange('B:B').createTextFinder(hash).matchEntireCell(true).findNext();
    var db = String(p.db || '').replace(/[^a-z0-9_]/g, '').slice(0, 60);
    var row = [new Date(), hash, 1, db, text.length, out.product_name.value, out.kind.value, js].map(safe_);
    if (found) { row[2] = (Number(sh.getRange(found.getRow(), 3).getValue()) || 1) + 1; sh.getRange(found.getRow(), 1, 1, row.length).setValues([row]); }
    else sh.appendRow(row);
  } finally { lock.releaseLock(); }
  CacheService.getScriptCache().put('sp_' + hash, js, 21600);
  return {ok: true, spec: out};
}

// 根拠の原文が依頼文に見つからない値は捨てる。数字の値は、その数字が根拠の原文に入っているものだけ残す
function specCheck_(o, text, ids) {
  var sq = function (s) { return String(s || '').replace(/[\s　]+/g, ''); };
  var T = sq(text), NA = '要確認';
  var ok1 = function (f) {
    var v = String((f && f.value) || '').trim().slice(0, 200), q = String((f && f.quote) || '').trim().slice(0, 120);
    if (!v || v === NA || !q || T.indexOf(sq(q)) < 0) return {value: NA, quote: ''};
    var nums = v.match(/\d+(?:\.\d+)?/g) || [];
    for (var i = 0; i < nums.length; i++) if (sq(q).indexOf(nums[i]) < 0) return {value: NA, quote: ''};
    return {value: v, quote: q};
  };
  var list = function (a) { return (a || []).map(ok1).filter(function (f) { return f.value !== NA; }).slice(0, 8); };
  var r = {};
  ['product_name', 'purpose', 'shape', 'width', 'length', 'height', 'weight', 'load', 'power', 'quantity_proto', 'quantity_mass'].forEach(function (k) { r[k] = ok1(o[k]); });
  ['components', 'processes', 'regulations', 'environment', 'open_items'].forEach(function (k) { r[k] = list(o[k]); });
  r.materials = (o.materials || []).map(function (m) { var f = ok1(m); return {part: f.value === NA ? '' : String(m.part || '').slice(0, 30), value: f.value, quote: f.quote}; })
    .filter(function (m) { return m.value !== NA; }).slice(0, 8);
  var kd = o.kind || {};
  r.kind = {value: ids.indexOf(kd.value) >= 0 ? kd.value : 'other', quote: ''};
  if (r.kind.value !== 'other') { var kq = ok1({value: 'x', quote: kd.quote}); r.kind.quote = kq.quote; if (!kq.quote) r.kind.value = 'other'; }
  return r;
}

function specSheet_() {
  var ss = sheet_().getParent();
  var sh = ss.getSheetByName('仕様読み取り');
  if (!sh) {
    sh = ss.insertSheet('仕様読み取り');
    sh.appendRow(SPEC_HEAD);
    sh.setFrozenRows(1);
  }
  return sh;
}

// ---------- 空き枠と時期の幅（小口の依頼を工場の空き時期に合わせる） ----------
// 依頼: 見積の依頼の slot = {flex, from, to, due, bundle, codes, mat, qty} を「依頼の時期」タブに1行。
//   flex は時期の幅（fixed=この日までに必要／m1=1か月ほど前後してよい／m3=2〜3か月のうちいつでも／any=急がない／''=選ばない）
// 工場: 提携申込みの profile.idle_slots = [{code, material, qty_min, qty_max, from, to, discount}] を「空き枠」タブに1行ずつ。
// 照らし合わせ: 関数 matchSlots（毎朝。setupSlots を1回実行すると時間の引き金が入る）が
//   工程が同じ・材料が合う（どちらかが空なら通す）・個数が幅に入る・期間が重なる組を「空き枠に合う」タブに、
//   まとめてよいと答えた同じ工程・材料の依頼で期間が重なるものを「まとめ候補」タブに書き、新しく見つかった組を運営者にメールする。
// 工場への連絡は担当者が内容を確認してから手で行う（自動では送らない）。値引きは工場が入れた場合だけ表示する。
var SLOT_REQ_HEAD = ['受付番号', '受付日時', '工程コード', '工程', '材料', '数量', '時期の幅', '作り始めてよい月', '遅くとも受け取りたい月', '希望の時期（入力）', 'まとめてよいか', '状態'];
var SLOT_HEAD = ['申込番号', '登録日時', '会社名', '工程コード', '材料', '個数の下限', '個数の上限', '空く月（から）', '空く月（まで）', '空き時期の値引き', '小口をまとめて受けられる', '状態'];
var SLOT_FLEX = {fixed: 'この日までに必要', m1: '1か月ほど前後してよい', m3: '2〜3か月のうちいつでも', any: '急がない（空き時期でよい）'};
var SLOT_DISC = {none: '値引きなし', ask: '値引きは相談可', '5': '目安 5%', '10': '目安 10%', '15': '目安 15%以上'};

function slotTab_(name, head) {
  var ss = sheet_().getParent(), sh = ss.getSheetByName(name);
  if (!sh) { sh = ss.insertSheet(name); sh.appendRow(head); sh.setFrozenRows(1); }
  return sh;
}

function slotRequest_(id, sl, f) {
  if (!sl || typeof sl !== 'object') return;
  var s = function (v, n) { return String(v == null ? '' : v).slice(0, n || 200); };
  var codes = [].concat(sl.codes || []).map(function (c) { return s(c, 80); }).filter(String).slice(0, 12);
  slotTab_('依頼の時期', SLOT_REQ_HEAD).appendRow([id, new Date(), codes.join('\n'), [].concat(sl.names || []).slice(0, 12).map(function (x) { return s(x, 60); }).join('\n'), s(sl.mat), s(sl.qty), SLOT_FLEX[sl.flex] || '',
    slotMonth_(sl.from), slotMonth_(sl.to), s(sl.due || f['f-due'], 100), sl.bundle === 1 ? 'まとめてよい' : sl.bundle === -1 ? 'まとめない' : '', '未対応'].map(safe_));
}

function slotPartner_(id, name, prof) {
  var list = [].concat((prof || {}).idle_slots || []).slice(0, 8);
  if (!list.length) return;
  var sh = slotTab_('空き枠', SLOT_HEAD), now = new Date();
  list.forEach(function (x) {
    if (!x || !x.code) return;
    var n = function (v) { v = Number(v); return v > 0 && v < 1e9 ? Math.round(v) : ''; };
    sh.appendRow([id, now, String(name).slice(0, 200), String(x.code).slice(0, 80), String(x.material || '').slice(0, 200), n(x.qty_min), n(x.qty_max),
      slotMonth_(x.from), slotMonth_(x.to), SLOT_DISC[x.discount] || '', prof.bundle_ok ? 'はい' : '', '未確認'].map(safe_));
  });
}

// 'YYYY-MM' だけ通す（それ以外は空）
function slotMonth_(v) {
  if (v instanceof Date) return Utilities.formatDate(v, 'Asia/Tokyo', 'yyyy-MM');
  var m = String(v || '').match(/^(\d{4})-(\d{1,2})/);
  return m && +m[2] >= 1 && +m[2] <= 12 ? m[1] + '-' + ('0' + +m[2]).slice(-2) : '';
}
// 月を数に（年*12+月-1）と、その逆
function slotN_(ym) { var m = String(ym || '').match(/^(\d{4})-(\d{2})/); return m ? +m[1] * 12 + +m[2] - 1 : null; }
function slotYm_(n) { return Math.floor(n / 12) + '-' + ('0' + (n % 12 + 1)).slice(-2); }

// 希望の時期の文から、受け取りたい月を読む（読めなければ null）。now は受付の月（数）
function slotDue_(t, now) {
  t = String(t || '').replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
  var m = t.match(/(\d{4})\s*[年\/.-]\s*(\d{1,2})\s*月?/);
  if (m && +m[2] >= 1 && +m[2] <= 12) return +m[1] * 12 + +m[2] - 1;
  m = t.match(/(\d{1,2})\s*月/);
  if (m && +m[1] >= 1 && +m[1] <= 12) { var y = Math.floor(now / 12), n = y * 12 + +m[1] - 1; return n < now ? n + 12 : n; }
  m = t.match(/(\d+)\s*(か月|ヶ月|カ月|ケ月|month)/i); if (m) return now + Math.min(+m[1], 36);
  m = t.match(/(\d+)\s*(週間|週|week)/i); if (m) return now + Math.ceil(+m[1] / 4.3);
  if (/年内/.test(t)) return Math.floor(now / 12) * 12 + 11;
  if (/来年/.test(t)) return Math.floor(now / 12) * 12 + 14;  // 来年3月ごろを目安
  return null;
}

// 依頼の期間 [from, to]（月の数）。作り始めてよい月・遅くとも受け取りたい月が入っていればそれを使う
function slotWin_(r, now) {
  var due = slotDue_(r.due, now), from = slotN_(r.from), to = slotN_(r.to);
  var fx = r.flex;
  if (from == null) from = fx === 'm1' && due != null ? Math.max(now, due - 1) : now;
  if (to == null) {
    if (fx === 'fixed') to = due != null ? due : from + 1;
    else if (fx === 'm1') to = (due != null ? due : from + 1) + 1;
    else if (fx === 'm3') to = Math.max(due != null ? due : 0, from + 3);
    else if (fx === 'any') to = Math.max(due != null ? due : 0, from + 6);
    else to = due != null ? due : from + 3;
  }
  if (to < from) to = from;
  return [from, to];
}

function slotQty_(t) {
  var ns = String(t || '').replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); }).replace(/(\d),(\d{3})/g, '$1$2').match(/\d+(\.\d+)?\s*(万)?/g) || [];
  var v = ns.map(function (x) { return parseFloat(x) * (/万/.test(x) ? 10000 : 1); }).filter(function (x) { return x > 0 && x < 1e8; });
  return v.length ? Math.max.apply(null, v) : null;
}

function slotMatNorm_(t) {
  return String(t || '').toLowerCase().replace(/[Ａ-Ｚａ-ｚ０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); })
    .replace(/樹脂|素材|材質|材料|わからない|未定|要確認|おまかせ|工場に任せる/g, '').replace(/\s+/g, '');
}
function slotMatOk_(a, b) {
  a = slotMatNorm_(a); b = slotMatNorm_(b);
  if (!a || !b) return true;
  if (a.indexOf(b) >= 0 || b.indexOf(a) >= 0) return true;
  var ta = a.split(/[、,\/・+＋]+/).filter(String), tb = b.split(/[、,\/・+＋]+/).filter(String);
  return ta.some(function (x) { return tb.some(function (y) { return x.indexOf(y) >= 0 || y.indexOf(x) >= 0; }); });
}

// 依頼 reqs = [{id, codes:[], mat, qty, flex, from, to, due, bundle, recv（受付の月の数）}]、空き枠 slots = [{pid, company, code, mat, qmin, qmax, from, to, disc, bundleOk}]
// 戻り値 {pairs:[{req, slot, code, win:[a,b], over:[a,b]}], bundles:[{code, mat, reqs:[...], win:[a,b], qty, slots:[...]}]}
function slotMatch_(reqs, slots, now) {
  var pairs = [], bundles = [];
  reqs.forEach(function (r) {
    r.win = slotWin_(r, r.recv != null ? r.recv : now); r.q = slotQty_(r.qty);  // 期間は受付の月から（古い「急がない」が伸び続けないように）
    if (r.win[1] < now) return;
    slots.forEach(function (sl) {
      if (r.codes.indexOf(sl.code) < 0) return;
      var a = slotN_(sl.from), b = slotN_(sl.to);
      if (a == null) a = b; if (b == null) b = a; if (a == null) return;
      if (b < a) { var t = a; a = b; b = t; }
      var lo = Math.max(a, r.win[0]), hi = Math.min(b, r.win[1]);
      if (lo > hi || hi < now) return;
      if (!slotMatOk_(r.mat, sl.mat)) return;
      if (r.q != null && ((sl.qmin && r.q < sl.qmin) || (sl.qmax && r.q > sl.qmax))) return;
      pairs.push({req: r, slot: sl, code: sl.code, over: [lo, hi]});
    });
  });
  // まとめ候補: まとめてよいと答えた依頼を、工程×材料で分け、期間の重なる順につなぐ
  var groups = {};
  reqs.forEach(function (r) {
    if (r.bundle !== 1 || r.win[1] < now) return;
    r.codes.forEach(function (c) { var k = c + '|' + slotMatNorm_(r.mat); (groups[k] = groups[k] || []).push(r); });
  });
  Object.keys(groups).forEach(function (k) {
    var list = groups[k].slice().sort(function (x, y) { return x.win[0] - y.win[0]; }), cur = null;
    var flush = function () {
      if (cur && cur.reqs.length >= 2) {
        cur.slots = slots.filter(function (sl) {
          var a = slotN_(sl.from), b = slotN_(sl.to); if (a == null) a = b; if (b == null) b = a;
          return sl.code === cur.code && a != null && Math.max(a, cur.win[0]) <= Math.min(b, cur.win[1]) && slotMatOk_(cur.mat, sl.mat) &&
            (!sl.qmax || cur.qty == null || cur.qty <= sl.qmax);
        });
        bundles.push(cur);
      }
    };
    list.forEach(function (r) {
      if (cur && r.win[0] <= cur.win[1]) {
        cur.reqs.push(r); cur.win = [Math.max(cur.win[0], r.win[0]), Math.min(cur.win[1], r.win[1])];
        cur.qty = cur.qty != null && r.q != null ? cur.qty + r.q : null;
      } else { flush(); cur = {code: k.split('|')[0], mat: r.mat, reqs: [r], win: r.win.slice(), qty: r.q}; }
    });
    flush();
  });
  return {pairs: pairs, bundles: bundles};
}

// 時間の引き金（毎朝8時台）を入れる。はじめの1回だけ実行する
function setupSlots() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'matchSlots') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('matchSlots').timeBased().everyDays(1).atHour(8).inTimezone('Asia/Tokyo').create();
  setupOffers();
  slotTab_('依頼の時期', SLOT_REQ_HEAD); slotTab_('空き枠', SLOT_HEAD);
  matchSlots();
}

function matchSlots() {
  var ss = sheet_().getParent(), tz = 'Asia/Tokyo';
  var now = slotN_(Utilities.formatDate(new Date(), tz, 'yyyy-MM'));
  var rows = function (name) { var sh = ss.getSheetByName(name); return sh && sh.getLastRow() > 1 ? sh.getRange(2, 1, sh.getLastRow() - 1, sh.getLastColumn()).getValues() : []; };
  var flexK = {}; Object.keys(SLOT_FLEX).forEach(function (k) { flexK[SLOT_FLEX[k]] = k; });
  var ended = /完了|見送り|取り下げ|対応済み/;
  var reqs = rows('依頼の時期').filter(function (r) { return r[0] && !ended.test(r[11]); }).map(function (r) {
    return {id: String(r[0]), codes: String(r[2]).split(/\s+/).filter(String), mat: r[4], qty: r[5], flex: flexK[r[6]] || '',
      from: slotMonth_(r[7]), to: slotMonth_(r[8]), due: r[9], bundle: r[10] === 'まとめてよい' ? 1 : 0,
      recv: r[1] instanceof Date ? slotN_(Utilities.formatDate(r[1], tz, 'yyyy-MM')) : now};
  });
  var pst = {}; rows('提携申込').forEach(function (r) { pst[String(r[0])] = String(r[PARTNER_HEAD.indexOf('状態')] || ''); });
  var slots = rows('空き枠').filter(function (r) { return r[0] && !/見送り|終了/.test(r[11]) && !/見送り/.test(pst[String(r[0])] || ''); }).map(function (r) {
    return {pid: String(r[0]), company: String(r[2]), code: String(r[3]), mat: r[4], qmin: Number(r[5]) || 0, qmax: Number(r[6]) || 0,
      from: slotMonth_(r[7]), to: slotMonth_(r[8]), disc: String(r[9] || ''), bundleOk: r[10] === 'はい', pstate: pst[String(r[0])] || ''};
  });
  var res = slotMatch_(reqs, slots, now);

  var span = function (w) { return slotYm_(w[0]) + ' 〜 ' + slotYm_(w[1]); };
  var PH = ['見つけた日', '受付番号', '申込番号', '会社名', '提携の状態', '工程コード', '依頼の材料', '空き枠の材料', '依頼の数量', '依頼の期間', '空き枠と重なる期間', '空き時期の値引き', '小口をまとめて受けられる', '打診リンク（工場に送ると、受ける・質問・断るを押せる）'];
  var outP = slotTab_('空き枠に合う', PH);
  outP.getRange(1, 1, 1, PH.length).setValues([PH]);
  var old = {}; if (outP.getLastRow() > 1) outP.getRange(2, 1, outP.getLastRow() - 1, 6).getValues().forEach(function (r) { old[r[1] + '|' + r[2] + '|' + r[5]] = r[0]; });
  var today = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd'), fresh = [];
  var body = res.pairs.map(function (x) {
    var k = x.req.id + '|' + x.slot.pid + '|' + x.code, first = old[k] || today;
    if (!old[k]) fresh.push(x);
    return [first, x.req.id, x.slot.pid, x.slot.company, x.slot.pstate, x.code, String(x.req.mat || ''), String(x.slot.mat || ''), String(x.req.qty || ''),
      span(x.req.win), span(x.over), x.slot.disc, x.slot.bundleOk ? 'はい' : '', offerEnsure_(x.req.id, x.slot.company, x.slot.pid)];
  });
  outP.getRange(2, 1, Math.max(outP.getLastRow() - 1, 1), 14).clearContent();
  if (body.length) outP.getRange(2, 1, body.length, 14).setValues(body.map(function (r) { return r.map(safe_); }));

  var outB = slotTab_('まとめ候補', ['工程コード', '材料', '依頼の件数', '受付番号', '合計の数量（読めた分）', '全員が受けられる期間', '合う空き枠（まとめて受けられる会社に★）']);
  var bb = res.bundles.map(function (g) {
    return [g.code, String(g.mat || '（材料は未記入）'), g.reqs.length, g.reqs.map(function (r) { return r.id; }).join('\n'), g.qty == null ? '' : g.qty, span(g.win),
      g.slots.map(function (sl) { return (sl.bundleOk ? '★' : '') + sl.company + '（' + sl.pid + '）'; }).join('\n')];
  });
  outB.getRange(2, 1, Math.max(outB.getLastRow() - 1, 1), 7).clearContent();
  if (bb.length) outB.getRange(2, 1, bb.length, 7).setValues(bb.map(function (r) { return r.map(safe_); }));

  if (fresh.length) {
    var to = CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail();
    var lines = fresh.map(function (x) { return '・' + x.req.id + ' × ' + x.slot.company + '（' + x.code + '、' + span(x.over) + (x.slot.disc ? '、' + x.slot.disc : '') + '）'; });
    MailApp.sendEmail({to: to, subject: '[KATACHI] 空き枠に合う依頼 ' + fresh.length + '件',
      body: '工場の空き枠と時期が合う依頼が新しく見つかりました。工場への連絡は、内容を確かめてから手で行ってください。\n\n' + lines.join('\n') +
        (bb.length ? '\n\nまとめ候補: ' + bb.length + '組（「まとめ候補」タブ）' : '') + '\n\n一覧（「空き枠に合う」タブ）: ' + ss.getUrl()});
  }
}

// ---------- 工場への打診と返事（受ける／質問する／断る） ----------
// 「工場への打診」タブに 受付番号・会社名 を書くと（申込番号は任意）、打診リンクが自動で入る（setupOffers で編集の引き金を入れる）。
// 「空き枠に合う」の組には、matchSlots が自動で打診リンクを作る。リンクを工場に送るのは担当者（自動では送らない）。
// 工場はリンク（/reply/?k=鍵）で依頼の要点を見て、受ける・質問する・断るを押す。答えはこのタブに入り、運営者にメールが届く。
// 工場に見せるのは依頼の要点だけ。依頼者の名前・メール・電話・会社名・納品先は見せない。
var OFFER_HEAD = ['受付番号', '会社名', '申込番号', '打診リンク', '状態', '回答日時', '着手できる時期', '見積の目安', 'メッセージ・質問・断る理由', '最後に開いた日時', '作成日時', '鍵', '履歴'];
var OFFER_STATE = {accept: '受ける', question: '質問', decline: '断る'};
var OFFER_URL = CONFIG.SITE_URL + 'reply/?k=';

function offerTab_() {
  var sh = slotTab_('工場への打診', OFFER_HEAD);
  return sh;
}

function setupOffers() {
  var sh = offerTab_(), ss = sh.getParent();
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'onOfferEdit') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('onOfferEdit').forSpreadsheet(ss).onEdit().create();
  offerFill_();
}

function onOfferEdit(e) {
  try { if (e && e.range && e.range.getSheet().getName() !== '工場への打診') return; } catch (err) { return; }
  offerFill_();
}

function offerKey_() {
  var A = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789', b = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, ''), k = '';
  for (var i = 0; i < 24; i++) k += A[parseInt(b.substr(i * 2, 2), 16) % A.length];
  return k;
}

// 受付番号と会社名があって鍵のない行に、鍵と打診リンクを入れる
function offerFill_() {
  var sh = offerTab_(), n = sh.getLastRow() - 1;
  if (n < 1) return;
  var rg = sh.getRange(2, 1, n, OFFER_HEAD.length), v = rg.getValues(), ch = false;
  v.forEach(function (r) {
    if (String(r[0]).trim() && String(r[1]).trim() && !r[11]) {
      r[11] = offerKey_(); r[3] = OFFER_URL + r[11]; r[4] = r[4] || '未回答'; r[10] = new Date(); ch = true;
    }
  });
  if (ch) rg.setValues(v);
}

// 受付番号×申込番号（なければ会社名）の打診リンクを返す。なければ行を足す
function offerEnsure_(id, company, pid) {
  var sh = offerTab_(), n = sh.getLastRow() - 1;
  if (n > 0) {
    var v = sh.getRange(2, 1, n, 12).getValues();
    for (var i = 0; i < v.length; i++) {
      if (String(v[i][0]) === String(id) && (pid ? String(v[i][2]) === String(pid) : String(v[i][1]) === String(company)) && v[i][11]) return OFFER_URL + v[i][11];
    }
  }
  var k = offerKey_();
  sh.appendRow([id, company, pid || '', OFFER_URL + k, '未回答', '', '', '', '', '', new Date(), k, ''].map(safe_));
  return OFFER_URL + k;
}

function offerFind_(k) {
  k = String(k || '');
  if (!/^[A-Za-z0-9]{24}$/.test(k)) return null;
  var sh = offerTab_(), n = sh.getLastRow() - 1;
  if (n < 1) return null;
  var keys = sh.getRange(2, 12, n, 1).getValues();
  for (var i = 0; i < keys.length; i++) if (String(keys[i][0]) === k) return {sh: sh, row: i + 2, v: sh.getRange(i + 2, 1, 1, OFFER_HEAD.length).getValues()[0]};
  return null;
}

// 工場に見せてよい依頼の要点（依頼者を特定できる項目は出さない）
var OFFER_HIDE = /メール|電話|会社名|屋号|担当者|お名前|名前|依頼者|納品先|住所|海外への提供|写真・動画・図面|ファイル/;
function offerSummary_(id) {
  var ss = sheet_().getParent(), out = {id: String(id)};
  var find = function (sh, col) {
    if (!sh || sh.getLastRow() < 2) return null;
    var ids = sh.getRange(2, col, sh.getLastRow() - 1, 1).getValues();
    for (var i = ids.length - 1; i >= 0; i--) if (String(ids[i][0]) === String(id)) return sh.getRange(i + 2, 1, 1, sh.getLastColumn()).getValues()[0];
    return null;
  };
  var r = find(sheet_(), 1);
  if (r) {
    out.kind = r[2]; out.summary = String(r[9] || '').slice(0, 2000); out.qty = String(r[10] || '').slice(0, 300); out.due = (r[11] instanceof Date ? Utilities.formatDate(r[11], 'Asia/Tokyo', 'yyyy-MM-dd') : String(r[11] || '')).slice(0, 200);
    out.files = String(r[15] || '') || /\d+件/.test(String(r[17] || '')) ? 1 : 0;
    var items = [], cur = null;
    String(r[14] || '').split('\n').forEach(function (line) {
      var m = line.match(/^([^:\n]{1,40}): ?(.*)$/);
      if (m && !/^\s/.test(line)) { cur = [m[1], m[2]]; items.push(cur); } else if (cur) cur[1] += '\n' + line;
    });
    out.items = items.filter(function (x) { return x[1] && !OFFER_HIDE.test(x[0]); }).slice(0, 40)
      .map(function (x) { return [x[0].slice(0, 60), x[1].slice(0, 3000)]; });
  }
  var t = find(ss.getSheetByName('依頼の時期'), 1);
  if (t) { out.steps = String(t[3] || '').split('\n').filter(String); out.mat = String(t[4] || ''); out.flex = String(t[6] || ''); out.from = slotMonth_(t[7]); out.to = slotMonth_(t[8]); out.bundle = t[10] === 'まとめてよい'; }
  return out;
}

function offerView_(p) {
  if (!limit_('o', 2000)) return {ok: false, error: 'busy'};
  var f = offerFind_(p.k);
  if (!f) return {ok: false, error: 'key'};
  f.sh.getRange(f.row, 10).setValue(new Date());
  var v = f.v, st = String(v[4] || '未回答'), ans = null;
  Object.keys(OFFER_STATE).forEach(function (a) { if (OFFER_STATE[a] === st) ans = a; });
  return {ok: true, company: String(v[1]), state: ans, when: String(v[6] || ''), price: String(v[7] || ''), msg: String(v[8] || ''),
    answered: v[5] instanceof Date ? Utilities.formatDate(v[5], 'Asia/Tokyo', 'yyyy-MM-dd HH:mm') : '', req: offerSummary_(v[0])};
}

function offerReply_(p) {
  if (!limit_('or', 500)) return {ok: false, error: 'busy'};
  var f = offerFind_(p.k);
  if (!f) return {ok: false, error: 'key'};
  var a = String(p.answer || '');
  if (a === 'stop') return mailStop_(f);
  if (!OFFER_STATE[a]) return {ok: false, error: 'answer'};
  var s = function (v, n) { return String(v == null ? '' : v).replace(/[\u0000-\u0008\u000b-\u001f]/g, '').slice(0, n); };
  var msg = s(p.msg, 3000), why = [].concat(p.reasons || []).map(function (x) { return s(x, 40); }).slice(0, 6);
  if (a === 'question' && !msg.trim()) return {ok: false, error: 'msg'};
  if (a === 'decline' && why.length) msg = '理由: ' + why.join('、') + (msg ? '\n' + msg : '');
  var now = new Date(), v = f.v, hist = String(v[12] || '');
  if (v[4] && v[4] !== '未回答') hist = (Utilities.formatDate(v[5] instanceof Date ? v[5] : now, 'Asia/Tokyo', 'MM-dd HH:mm') + ' ' + v[4] + (v[8] ? '：' + String(v[8]).slice(0, 200) : '') + '\n' + hist).slice(0, 5000);
  f.sh.getRange(f.row, 5, 1, 5).setValues([[OFFER_STATE[a], now, s(p.when, 100), s(p.price, 200), msg].map(safe_)]);
  f.sh.getRange(f.row, 13).setValue(safe_(hist));
  try {
    var to = CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail();
    MailApp.sendEmail({to: to, subject: '[KATACHI] 工場の返事：' + OFFER_STATE[a] + ' ' + v[1] + '（' + v[0] + '）',
      body: v[1] + ' から、受付 ' + v[0] + ' の打診に返事がありました。\n\n■ 答え\n' + OFFER_STATE[a] +
        (p.when ? '\n\n■ 着手できる時期\n' + s(p.when, 100) : '') + (p.price ? '\n\n■ 見積の目安\n' + s(p.price, 200) : '') + (msg ? '\n\n■ メッセージ\n' + msg : '') +
        '\n\n一覧（「工場への打診」タブ）: ' + f.sh.getParent().getUrl()});
  } catch (err) { console.error(err); }
  return {ok: true, state: a};
}

// ---------- 見積の依頼を工場へメールで届ける（Nori 2026-11-15「依頼をメールで出せるところは、依頼を出せる作りにしてほしい」） ----------
// 1. 会社の公開メールを集める: 関数 setupMail を1回実行すると、collectMail が10分ごとに動き、サイトの data/companies.json の
//    国内の会社の公式サイト（トップと「お問い合わせ」「会社概要」のページ）を読み、掲載されたメールアドレスを「工場のメール」タブに入れる。
//    公式サイトと同じドメインか、フリーメール・プロバイダ（.ne.jp）のアドレスだけ使う。採用・個人情報の窓口などは使わない。
//    「営業・広告のメールはお断り」のような表示があるページの会社には送らない（状態「営業お断りの表示」）。
//    アドレスは公開リポジトリやサイトには載せない（このシートの中だけ）。状態を手で「送らない（手で止める）」にすれば送らない。
// 2. 依頼者は見積の依頼で「メールのわかる会社にはKATACHIから届ける」を選んで送る（サイトは type:'mailable' で、届けられる会社名だけを聞く）。
//    受付の確認メールに「◯社に送る」ボタン（サイトの ?send=鍵）が入り、押すと type:'rfqsend' でその会社に送る（本人のメールの確認と、送る意思の確認を兼ねる）。
// 3. 工場に送るのは依頼の要点と打診リンク（/reply/）だけ。依頼者の名前・メール・電話・会社名・納品先は送らない（offerSummary_ と同じ）。
//    送った記録は「メール送信」タブと「工場への打診」タブに入り、運営者に控えが届く。工場が配信停止を押すと、その会社には以後送らない。
// 4. 特定電子メール法の表示のため、スクリプトのプロパティ SENDER_NAME（送信者の氏名・名称）と SENDER_ADDRESS（住所）が無いと送らない（サイトにも出さない）。
//    止めたいときは MAIL_SEND を off にする。Gmail の1日の送信数（無料のアカウントは100通）を超えないよう、残りが少ないときは送らない。
var MAIL_HEAD = ['会社名', '都道府県', '公式サイト', 'メール', '見つけたページ', '状態', '確認日', 'メモ'];
var MAIL_OK = '送れる';
var SEND_HEAD = ['受付番号', '会社名', '宛先', '状態', '確認の鍵', '作成日時', '送信日時', '打診リンク', 'メモ'];
var MAIL_CFG = {
  PER_REQUEST: 10,        // 1件の依頼でメールを送る会社の上限
  DAILY: 60,              // 1日に工場へ送るメールの上限
  PER_COMPANY_DAY: 2,     // 同じ会社に1日に送る上限
  PER_REQUESTER_DAY: 3,   // 同じ依頼者（メール）が1日に送れる依頼の数
  RESERVE: 20,            // Gmail の残り送信数がこれ以下なら送らない（受付・控えのメールのため）
  KEY_DAYS: 7,            // 確認メールのボタンが使える日数
  BATCH: 20,              // 集めるとき、一度に読むサイトの数
  RUN_MS: 270000          // 1回の実行で使う時間（6分の上限より短く）
};
var MAIL_FREE = /(^|\.)(gmail\.com|googlemail\.com|yahoo\.co\.jp|ymail\.ne\.jp|icloud\.com|me\.com|outlook\.com|outlook\.jp|hotmail\.com|hotmail\.co\.jp|live\.jp|msn\.com|nifty\.com|ocn\.ne\.jp|biglobe\.ne\.jp|so-net\.ne\.jp|plala\.or\.jp|dion\.ne\.jp|ezweb\.ne\.jp|docomo\.ne\.jp|softbank\.ne\.jp|[a-z0-9-]+\.ne\.jp)$/i;
var MAIL_BAD_LOCAL = /^(recruit|recruiting|saiyo|saiyou|jinji|career|careers|job|jobs|entry|privacy|kojinjoho|personal|noreply|no-reply|donotreply|do-not-reply|postmaster|abuse|mailer-daemon|ir|press|kouhou|koho|hr|newsletter|magazine|mag|unsubscribe|test|sample|example|xxx|yourname|name|email|mail-address)$/i;
var MAIL_BAD_DOMAIN = /(^|\.)(example\.(com|jp|co\.jp|net|org)|sentry\.io|sentry-next\.wixpress\.com|wixpress\.com|domain\.com|xxx\.(com|jp|co\.jp)|sample\.(com|jp))$|\.(png|jpe?g|gif|webp|svg|css|js|ico)$/i;
var MAIL_GOOD_LOCAL = /^(info|information|contact|contacts|sales|eigyo|eigyou|eigyoubu|otoiawase|toiawase|inquiry|inquiries|enquiry|mail|office|order|orders|support|shop|customer|soudan|webinfo|honsha|honbu|seisan|seizo|seizou|kojo|koujou|factory)\b/i;
var MAIL_REFUSE = /((営業|広告|宣伝|セールス|勧誘|売り込み)(目的)?[^。\n<>]{0,25}(メール|ご連絡|連絡|お問い?合わ?せ|問合せ|電話)[^。\n<>]{0,25}(お断り|ご遠慮|遠慮|拒否|受け付けて(お|い)りません|お受けして(お|い)りません|控え)|特定電子メール[^。\n<>]{0,40}(拒否|お断り|同意しない)|未承諾広告)/;

function mailHost_(u) { var m = String(u || '').match(/^https?:\/\/([^\/?#:]+)/i); return m ? m[1].toLowerCase().replace(/^www\d?\./, '') : ''; }
function mailSameDomain_(dom, host) {
  dom = String(dom || '').toLowerCase(); host = String(host || '').toLowerCase();
  if (!dom || !host) return false;
  if (dom === host || host.slice(-dom.length - 1) === '.' + dom || dom.slice(-host.length - 1) === '.' + host) return true;
  // 「会社名.co.jp」と「会社名.jp」のように、名前の部分が同じ
  var core = function (h) { var p = h.split('.'); var n = /^(co|or|ne|ac|go|lg|ed|gr)$/.test(p[p.length - 2] || '') && p.length >= 3 ? p[p.length - 3] : p[p.length - 2]; return n || ''; };
  var a = core(dom), b = core(host);
  return a.length >= 4 && a === b;
}

// ページの文字からメールアドレスを拾う。戻り値 [{email, score}]（よい順）
function mailFind_(html, host, isContact) {
  var s = String(html || '');
  var t = s.replace(/<!--[\s\S]*?-->/g, ' ');
  var raw = [];
  (t.match(/mailto:([^"'?\s>]+)/gi) || []).forEach(function (m) { try { raw.push([decodeURIComponent(m.slice(7)), 2]); } catch (e) { raw.push([m.slice(7), 2]); } });
  var txt = t.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/&#64;|&#x40;|＠/g, '@').replace(/&nbsp;/g, ' ');
  (txt.match(/[A-Za-z0-9._%+-]+\s?@\s?[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}/g) || []).forEach(function (m) { raw.push([m.replace(/\s/g, ''), 0]); });
  var seen = {}, out = [];
  raw.forEach(function (x) {
    var e = String(x[0]).trim().replace(/^[.\-]+|[.\-]+$/g, '').toLowerCase();
    var m = e.match(/^([a-z0-9._%+-]+)@([a-z0-9.-]+\.[a-z]{2,})$/);
    if (!m || e.length > 80) return;
    var local = m[1], dom = m[2];
    if (MAIL_BAD_LOCAL.test(local) || MAIL_BAD_DOMAIN.test(dom)) return;
    var same = mailSameDomain_(dom, host), free = !same && MAIL_FREE.test(dom);
    if (!same && !free) return;
    var sc = (same ? 4 : 1) + (MAIL_GOOD_LOCAL.test(local) ? 2 : 0) + (isContact ? 1 : 0) + x[1];
    if (seen[e] == null || sc > out[seen[e]].score) { if (seen[e] == null) { seen[e] = out.length; out.push({email: e, score: sc}); } else out[seen[e]].score = sc; }
  });
  return out.sort(function (a, b) { return b.score - a.score; });
}

// 「営業メールお断り」のような表示があるか
function mailRefuses_(html) {
  var txt = String(html || '').replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/gi, ' ').replace(/<[^>]+>/g, '').replace(/[\s　]+/g, '');
  return MAIL_REFUSE.test(txt);
}

// 「お問い合わせ」「会社概要」のページのURL（同じサイトの中だけ、よい順に2つまで）
function mailLinks_(html, base) {
  var bm = String(base || '').match(/^(https?:\/\/[^\/?#]+)(\/[^?#]*)?/i);
  if (!bm) return [];
  var origin = bm[1], dir = (bm[2] || '/').replace(/[^\/]*$/, ''), host = mailHost_(base), list = [], seen = {};
  var re = /<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]{0,300}?)<\/a>/gi, m;
  while ((m = re.exec(String(html || ''))) && list.length < 200) {
    var href = m[1].trim(), text = m[2].replace(/<[^>]+>/g, '').replace(/\s+/g, '') + ' ' + ((m[0].match(/alt\s*=\s*["']([^"']*)["']/i) || [])[1] || '');
    if (/^(mailto:|tel:|javascript:|#)/i.test(href) || /\.(pdf|jpe?g|png|gif|zip|docx?|xlsx?)(\?|$)/i.test(href)) continue;
    var u = /^https?:\/\//i.test(href) ? href : /^\/\//.test(href) ? 'https:' + href : href.charAt(0) === '/' ? origin + href : origin + dir + href.replace(/^\.\//, '');
    u = u.replace(/#.*$/, '');
    if (mailHost_(u) !== host || seen[u]) continue;
    var key = (text + ' ' + href).toLowerCase(), sc = 0;
    if (/お問い?合わ?せ|問合|問い合|contact|inquiry|enquiry|toiawase|otoiawase|ご相談/.test(key)) sc = 3;
    else if (/会社概要|会社案内|企業情報|会社情報|company|about|corporate|profile|outline|gaiyou|gaiyo|アクセス|access/.test(key)) sc = 1;
    if (!sc) continue;
    seen[u] = 1; list.push([u, sc]);
  }
  return list.sort(function (a, b) { return b[1] - a[1]; }).slice(0, 2).map(function (x) { return x[0]; });
}

// 文字コード（Shift_JIS・EUC-JP のサイトも読む）
function mailText_(res) {
  var ct = String((res.getHeaders() || {})['Content-Type'] || (res.getHeaders() || {})['content-type'] || '');
  var head = res.getContentText('ISO-8859-1').slice(0, 3000);
  var cs = ((ct.match(/charset=([\w-]+)/i) || head.match(/charset=["']?([\w-]+)/i) || [])[1] || 'UTF-8').toLowerCase();
  cs = /s(hift)?[-_]?jis|x-sjis|windows-31j|cp932|ms932/.test(cs) ? 'Shift_JIS' : /euc-?jp/.test(cs) ? 'EUC-JP' : /iso-2022-jp/.test(cs) ? 'ISO-2022-JP' : 'UTF-8';
  try { return res.getContentText(cs); } catch (e) { return res.getContentText(); }
}

function mailFetch_(urls) {
  var req = urls.map(function (u) { return {url: u, muteHttpExceptions: true, followRedirects: true, headers: {'User-Agent': 'Mozilla/5.0 (compatible; KATACHI-contact-check; +' + CONFIG.SITE_URL + ')'}}; });
  var res;
  try { res = UrlFetchApp.fetchAll(req); } catch (e) {
    res = req.map(function (r) { try { return UrlFetchApp.fetch(r.url, r); } catch (err) { return null; } });
  }
  return res.map(function (r) {
    if (!r || r.getResponseCode() >= 400) return null;
    var ct = String((r.getHeaders() || {})['Content-Type'] || '');
    if (ct && !/html|text/i.test(ct)) return null;
    try { return mailText_(r).slice(0, 600000); } catch (e) { return null; }
  });
}

// 1社ぶんの結果。pages = [{url, html, contact}]
function mailDecide_(web, pages) {
  var host = mailHost_(web), best = null, refuse = '', others = [];
  pages.forEach(function (p) {
    if (!p.html) return;
    if (!refuse && mailRefuses_(p.html)) refuse = p.url;
    mailFind_(p.html, host, p.contact).forEach(function (x) { if (!best || x.score > best.score) best = {email: x.email, score: x.score, page: p.url}; });
    if (!best) (String(p.html).match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g) || []).slice(0, 2).forEach(function (e) { if (others.indexOf(e) < 0) others.push(e); });
  });
  if (!pages.some(function (p) { return p.html; })) return {state: '読めない', email: '', page: '', memo: ''};
  if (!best) return {state: '見つからない', email: '', page: '', memo: others.length ? '別のドメインのアドレスだけ: ' + others.join(' ') : ''};
  if (refuse) return {state: '営業お断りの表示', email: best.email, page: best.page, memo: '表示のあるページ: ' + refuse};
  return {state: MAIL_OK, email: best.email, page: best.page, memo: ''};
}

function mailTab_() { return slotTab_('工場のメール', MAIL_HEAD); }
function sendTab_() { return slotTab_('メール送信', SEND_HEAD); }

// 10分ごとに集める（はじめの1回だけ実行する）。全部読み終わると止まり、運営者にメールが届く
function setupMail() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'collectMail') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('collectMail').timeBased().everyMinutes(10).create();
  mailTab_(); sendTab_();
  collectMail();
}

// もう一度はじめから集め直す（新しい会社が増えたとき。すでにある会社は上書きしない）
function restartMail() { PropertiesService.getScriptProperties().setProperty('MAIL_CURSOR', '0'); setupMail(); }

function collectMail() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    var t0 = Date.now(), props = PropertiesService.getScriptProperties();
    var data = JSON.parse(UrlFetchApp.fetch(CONFIG.SITE_URL + 'data/companies.json').getContentText());
    var list = (data.c || []).filter(function (r) { return (r[1] || 'JP') === 'JP' && /^https?:\/\//i.test(String(r[4] || '')); });
    var sh = mailTab_(), have = {};
    if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues().forEach(function (r) { have[String(r[0])] = 1; });
    var cur = Number(props.getProperty('MAIL_CURSOR') || 0);
    while (cur < list.length && Date.now() - t0 < MAIL_CFG.RUN_MS) {
      var batch = list.slice(cur, cur + MAIL_CFG.BATCH).filter(function (r) { return !have[r[0]]; });
      cur += MAIL_CFG.BATCH;
      if (!batch.length) continue;
      var tops = mailFetch_(batch.map(function (r) { return r[4]; }));
      var next = [], owner = [];
      batch.forEach(function (r, i) { if (tops[i]) mailLinks_(tops[i], r[4]).forEach(function (u) { next.push(u); owner.push(i); }); });
      var subs = next.length ? mailFetch_(next) : [];
      var today = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd');
      var rows = batch.map(function (r, i) {
        var pages = [{url: r[4], html: tops[i], contact: false}];
        next.forEach(function (u, j) { if (owner[j] === i) pages.push({url: u, html: subs[j], contact: true}); });
        var d = mailDecide_(r[4], pages);
        have[r[0]] = 1;
        return [r[0], r[2] || '', r[4], d.email, d.page, d.state, today, d.memo];
      });
      sh.getRange(sh.getLastRow() + 1, 1, rows.length, MAIL_HEAD.length).setValues(rows.map(function (x) { return x.map(safe_); }));
      props.setProperty('MAIL_CURSOR', String(cur));
    }
    if (cur >= list.length) {
      ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'collectMail') ScriptApp.deleteTrigger(t); });
      var n = {}; sh.getRange(2, 6, Math.max(sh.getLastRow() - 1, 1), 1).getValues().forEach(function (r) { n[r[0]] = (n[r[0]] || 0) + 1; });
      MailApp.sendEmail({to: CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail(), subject: '[KATACHI] 工場のメールを集め終わりました',
        body: Object.keys(n).map(function (k) { return k + ': ' + n[k] + '社'; }).join('\n') + '\n\n「工場のメール」タブ: ' + sh.getParent().getUrl()});
    }
  } finally { lock.releaseLock(); }
}

// 送信者の表示（特定電子メール法）が入っていて、止めていないときだけ送る
function mailOn_() { return !!(prop_('SENDER_NAME') && prop_('SENDER_ADDRESS')) && prop_('MAIL_SEND') !== 'off'; }

// 会社名 → {row, email, state, page}
function mailMap_() {
  var sh = mailTab_(), n = sh.getLastRow() - 1, out = {};
  if (n < 1) return out;
  sh.getRange(2, 1, n, 6).getValues().forEach(function (r, i) { var k = String(r[0]); if (k && !out[k]) out[k] = {row: i + 2, email: String(r[3] || '').trim(), state: String(r[5] || ''), page: String(r[4] || '')}; });
  return out;
}
function mailUsable_(m) { return !!(m && m.state === MAIL_OK && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(m.email)); }

// サイトが「メールで届けられる会社」を聞く。アドレスは返さない
function mailable_(p) {
  if (!limit_('m', 3000)) return {ok: false, error: 'busy'};
  if (!mailOn_()) return {ok: true, on: false, names: []};
  var map = mailMap_();
  var names = [].concat(p.names || []).slice(0, 40).map(function (x) { return String(x).slice(0, 120); }).filter(function (n) { return mailUsable_(map[n]); });
  return {ok: true, on: true, names: names, max: MAIL_CFG.PER_REQUEST};
}

// 見積の依頼を受けたとき: メールで届ける会社を「メール送信」タブに「依頼者の確認待ち」で入れ、確認の鍵を返す
function mailPrepare_(id, p, email) {
  if (!mailOn_()) return null;
  var team = {}; (p.team || []).forEach(function (t) { if (t && t.company && (!t.country || t.country === 'JP')) team[String(t.company)] = 1; });
  var map = mailMap_(), names = [];
  [].concat(p.mail || []).forEach(function (n) { n = String(n); if (team[n] && mailUsable_(map[n]) && names.indexOf(n) < 0) names.push(n); });
  names = names.slice(0, MAIL_CFG.PER_REQUEST);
  if (!names.length) return null;
  if (!limit_('mr' + Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, email.toLowerCase())).slice(0, 12), MAIL_CFG.PER_REQUESTER_DAY)) return {names: [], over: true};
  var key = offerKey_(), now = new Date(), sh = sendTab_();
  sh.getRange(sh.getLastRow() + 1, 1, names.length, SEND_HEAD.length).setValues(names.map(function (n) { return [id, n, map[n].email, '依頼者の確認待ち', key, now, '', '', ''].map(safe_); }));
  return {key: key, names: names, url: CONFIG.SITE_URL + '?send=' + key, preview: factoryMail_(id, names[0], OFFER_URL + '（会社ごとのリンク）', CONFIG.SITE_URL + 'reply/?k=…&stop=1', map[names[0]].page).body};
}

// 工場に届くメール（日本の会社だけに送るので日本語）
function factoryMail_(id, company, link, stop, page) {
  var q = offerSummary_(id), L = [];
  var add = function (k, v, n) { v = String(v || '').trim(); if (v) L.push(k + ': ' + clip_(v, n || 300)); };
  add('製品の概要', q.summary, 600); add('段階と数量', q.qty); add('希望の時期', q.due);
  if (q.steps && q.steps.length) add('工程', q.steps.join('、'));
  add('材料', q.mat); if (q.flex) add('時期の幅', q.flex); if (q.from || q.to) add('受け取れる期間', (q.from || '') + ' 〜 ' + (q.to || ''));
  // 「おまかせ」「わからない」の項目は、要点から外して「ご提案ください」にまとめる
  var rest = 0, open = [];
  (q.items || []).forEach(function (x) {
    if (/^(製品の概要|段階と数量|希望の時期)$/.test(x[0])) return;
    if (/おまかせ|わからない|未定/.test(x[1]) && x[1].length < 40) { open.push(x[0].replace(/（.*?）$/, '')); return; }
    var line = x[0] + ': ' + clip_(x[1], /仕様書/.test(x[0]) ? 1500 : 400);
    if (rest < 4000) { rest += line.length; L.push(line); }
  });
  if (q.files) L.push('添付: 写真・図面などがあります（受けていただける場合にお送りします）');
  if (open.length) L.push('', '■ 決まっていない点（ご提案ください）', open.join('、'));
  var sum = clip_(String(q.summary || '').split('\n')[0], 30);
  var body = [company + ' ご担当者さま', '',
    'はじめてご連絡いたします。ものづくりの依頼先を探せるサイト「KATACHI」（' + CONFIG.SITE_URL + '）です。',
    'KATACHI で貴社を依頼先に選んだ方から見積のご相談をお預かりしましたので、お届けします。', '',
    '■ 依頼の要点（受付番号 ' + id + '）', L.join('\n'), '',
    '■ お返事のお願い',
    'お受けできそうか、下のページで「受ける・質問する・断る」をお選びください（1分ほど・登録は不要です）。',
    link, 'このメールへの返信でもかまいません。', '',
    '・依頼者のお名前とご連絡先は、受けていただけると決まってから KATACHI がお伝えします。',
    '・まだ発注は決まっていません。見積をご覧になってから、依頼者が依頼先を決めます。', '',
    '――――――――――',
    'このメールは、貴社のウェブサイトに掲載されているメールアドレス宛てに、KATACHI の利用者の依頼を取り次いでお送りしています。' + (page ? '\n（掲載ページ: ' + page + '）' : ''),
    '今後 KATACHI からの依頼のメールが不要な場合は、こちらからお知らせください。以後はお送りしません。', stop, '',
    '送信者: ' + (prop_('SENDER_NAME') || '') + '（KATACHI）', '住所: ' + (prop_('SENDER_ADDRESS') || ''), 'お問い合わせ: このメールにご返信ください', CONFIG.SITE_URL].join('\n');
  return {subject: '【KATACHI】見積のご相談' + (sum ? '：' + sum : '') + '（受付番号 ' + id + '）', body: body};
}

// 依頼者が確認メールのボタンを押したとき: 「依頼者の確認待ち」の会社にメールを送る
function rfqSend_(p) {
  if (!limit_('rs', 500)) return {ok: false, error: 'busy'};
  var k = String(p.k || '');
  if (!/^[A-Za-z0-9]{24}$/.test(k)) return {ok: false, error: 'key'};
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(20000)) return {ok: false, error: 'busy'};
  try {
    var sh = sendTab_(), n = sh.getLastRow() - 1;
    if (n < 1) return {ok: false, error: 'key'};
    var v = sh.getRange(2, 1, n, SEND_HEAD.length).getValues(), rows = [];
    v.forEach(function (r, i) { if (String(r[4]) === k) rows.push({i: i + 2, r: r}); });
    if (!rows.length) return {ok: false, error: 'key'};
    var id = String(rows[0].r[0]);
    var done = rows.filter(function (x) { return x.r[3] === '送信済み'; }).map(function (x) { return String(x.r[1]); });
    var wait = rows.filter(function (x) { return x.r[3] === '依頼者の確認待ち'; });
    if (!wait.length) return {ok: true, id: id, sent: done, already: true, skipped: rows.filter(function (x) { return x.r[3] !== '送信済み'; }).map(function (x) { return String(x.r[1]); })};
    if (!mailOn_()) return {ok: false, error: 'off'};
    var made = rows[0].r[5] instanceof Date ? rows[0].r[5].getTime() : 0;
    if (Date.now() - made > MAIL_CFG.KEY_DAYS * 864e5) return {ok: false, error: 'expired', id: id};
    var map = mailMap_(), sent = [], skipped = [], now = new Date(), copy = [];
    wait.forEach(function (x) {
      var name = String(x.r[1]), m = map[name], why = '';
      if (!mailUsable_(m)) why = '送れない：' + (m ? m.state : '工場のメールに無い');
      else if (m.email !== String(x.r[2])) why = '送れない：アドレスが変わった';
      else if (MailApp.getRemainingDailyQuota() <= MAIL_CFG.RESERVE) why = '送れない：今日のメールの上限';
      else if (!limit_('md', MAIL_CFG.DAILY)) why = '送れない：今日の工場へのメールの上限';
      else if (!limit_('mc' + Utilities.base64EncodeWebSafe(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, name)).slice(0, 12), MAIL_CFG.PER_COMPANY_DAY)) why = '送れない：この会社に今日は送った';
      if (why) { sh.getRange(x.i, 4).setValue(why); skipped.push(name); return; }
      var link = offerEnsure_(id, name, ''), kk = link.split('k=')[1];
      var mail = factoryMail_(id, name, link, CONFIG.SITE_URL + 'reply/?k=' + kk + '&stop=1', m.page);
      try {
        MailApp.sendEmail({to: m.email, subject: mail.subject, body: mail.body, name: CONFIG.SERVICE_NAME});
        sh.getRange(x.i, 4, 1, 5).setValues([['送信済み', k, x.r[5], now, link]]);
        offerNote_(kk, 'メールで送信 ' + Utilities.formatDate(now, 'Asia/Tokyo', 'MM-dd HH:mm') + '（' + m.email + '）');
        sent.push(name); copy.push('・' + name + ' <' + m.email + '>\n  ' + link);
        if (copy.length === 1) copy.unshift('---- 1社目に送った本文 ----\n件名: ' + mail.subject + '\n\n' + mail.body + '\n---- ここまで ----\n');
      } catch (err) { console.error(err); sh.getRange(x.i, 4).setValue('送れない：' + String(err).slice(0, 80)); skipped.push(name); }
    });
    try {
      MailApp.sendEmail({to: CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail(), subject: '[KATACHI] 工場へメールで送りました ' + id + '（' + sent.length + '社）',
        body: '受付 ' + id + ' の依頼者が確認メールのボタンを押し、次の会社にメールで依頼を送りました（控え）。\n\n' + copy.join('\n') +
          (skipped.length ? '\n\n送れなかった会社（手で打診してください）: ' + skipped.join('、') : '') + '\n\n記録（「メール送信」「工場への打診」タブ）: ' + sh.getParent().getUrl()});
    } catch (err) { console.error(err); }
    return {ok: true, id: id, sent: done.concat(sent), skipped: skipped};
  } finally { lock.releaseLock(); }
}

// 打診の行の「履歴」に書き足す
function offerNote_(k, note) {
  var f = offerFind_(k);
  if (f) f.sh.getRange(f.row, 13).setValue(safe_((note + '\n' + String(f.v[12] || '')).slice(0, 5000)));
}

// 工場が「今後のメールは不要」を押したとき
function mailStop_(f) {
  var name = String(f.v[1]), map = mailMap_(), m = map[name], now = new Date();
  if (m) { var sh = mailTab_(); sh.getRange(m.row, 6).setValue('送らない（配信停止）'); sh.getRange(m.row, 8).setValue('配信停止 ' + Utilities.formatDate(now, 'Asia/Tokyo', 'yyyy-MM-dd HH:mm')); }
  offerNote_(String(f.v[11]), '配信停止 ' + Utilities.formatDate(now, 'Asia/Tokyo', 'MM-dd HH:mm'));
  try {
    MailApp.sendEmail({to: CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail(), subject: '[KATACHI] 配信停止：' + name,
      body: name + ' が、KATACHI からの依頼のメールの配信停止を選びました。以後この会社にはメールで送りません（「工場のメール」タブの状態を「送らない（配信停止）」にしました）。'});
  } catch (err) { console.error(err); }
  return {ok: true, state: 'stop'};
}

// ---------- 見積フォームの調査（Nori 2026-11-15「まずは、国内の工場から共通項見いだしてね」） ----------
// 関数 setupSurvey を1回実行すると、surveyForms が5分ごとに動き、カテゴリごとに国内の会社（公式サイトのある会社から名前の順に依らず選ぶ）の
// 「お見積り」「お問い合わせ」のページを読み、フォームの項目名・選択肢の文字を「見積フォーム調査」タブに入れる。読み終わると止まる。
// 集計（何%のフォームが聞いているか）は、このタブを読んで別に行う。送信はしない（ページを読むだけ）。
var SURVEY_CATS = [
  ['金属切削', ['manufacturing.cnc']], ['板金・溶接', ['manufacturing.sheet_metal', 'manufacturing.welding']], ['金属製品・雑貨', ['crafts.metal_goods']],
  ['樹脂成形', ['manufacturing.injection_molding']], ['シリコーン・ゴム', ['manufacturing.silicone_molding']], ['試作・3Dプリント', ['manufacturing.rapid_proto']],
  ['電子・基板', ['electronics.pcba', 'electronics.pcb_design']], ['縫製・アパレル', ['apparel.garment_oem', 'manufacturing.textile', 'apparel.knit', 'apparel.leather']],
  ['化粧品', ['cosmetics.oem']], ['食品・飲料', ['food.processed_oem', 'food.beverage_oem']], ['木工・家具', ['crafts.wood_furniture']],
  ['印刷・パッケージ', ['packaging.label_print', 'packaging.box', 'packaging.container']], ['ノベルティ・雑貨', ['cosmetics.household']]
];
var SURVEY_PER_CAT = 60;
var SURVEY_HEAD = ['会社名', 'カテゴリ', '公式サイト', '読んだページ', 'フォームの有無', 'フォームの文字（項目名・選択肢）', '外部フォーム', '日時'];

function setupSurvey() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'surveyForms') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('surveyForms').timeBased().everyMinutes(5).create();
  surveyForms();
}

// 名前から決まる並び（毎回同じ順で選ぶ）
function surveyHash_(s) { var h = 0; s = String(s); for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h; }

function surveyList_(data) {
  var caps = data.caps || [], out = [], used = {};
  SURVEY_CATS.forEach(function (c) {
    var rows = (data.c || []).filter(function (r) {
      if ((r[1] || 'JP') !== 'JP' || !/^https?:\/\//i.test(String(r[4] || '')) || used[r[0]]) return false;
      var first = caps[(r[5] || [])[0]];  // 主な工程がこのカテゴリの会社
      return c[1].indexOf(first) >= 0;
    }).sort(function (a, b) { return surveyHash_(a[0]) - surveyHash_(b[0]); }).slice(0, SURVEY_PER_CAT);
    rows.forEach(function (r) { used[r[0]] = 1; out.push([r[0], c[0], r[4]]); });
  });
  return out;
}

// フォームの中の文字（ラベル・見出し・選択肢・入力欄の説明）を取り出す
function surveyFormText_(html) {
  var s = String(html || '').replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<!--[\s\S]*?-->/gi, ' ');
  var forms = s.match(/<form\b[\s\S]*?<\/form>/gi) || [];
  forms = forms.filter(function (f) { return /<(input|textarea|select)\b/i.test(f) && !/type\s*=\s*["']?search/i.test(f) || /<textarea\b/i.test(f); });
  if (!forms.length) return '';
  var f = forms.sort(function (a, b) { return b.length - a.length; })[0];
  var ph = (f.match(/placeholder\s*=\s*["'][^"']{1,80}["']/gi) || []).map(function (x) { return '［例］' + x.replace(/^placeholder\s*=\s*["']|["']$/gi, ''); });
  var txt = f.replace(/<(br|p|div|tr|li|dt|dd|th|td|label|option|h\d|span)\b[^>]*>/gi, '\n').replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/[ \t　]+/g, ' ');
  var lines = txt.split('\n').map(function (x) { return x.trim(); }).filter(function (x) { return x && x.length <= 80; });
  return lines.concat(ph).join(' | ').slice(0, 6000);
}

function surveyForms() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    var t0 = Date.now(), props = PropertiesService.getScriptProperties();
    var data = JSON.parse(UrlFetchApp.fetch(CONFIG.SITE_URL + 'data/companies.json').getContentText());
    var list = surveyList_(data), sh = slotTab_('見積フォーム調査', SURVEY_HEAD);
    var cur = Number(props.getProperty('SURVEY_CURSOR') || 0), B = 40;
    while (cur < list.length && Date.now() - t0 < 200000) {
      var batch = list.slice(cur, cur + B); cur += B;
      var tops = mailFetch_(batch.map(function (r) { return r[2]; }));
      var next = [], owner = [];
      batch.forEach(function (r, i) {
        if (!tops[i]) return;
        // 見積のページを先に、なければお問い合わせ
        var bm = String(r[2]).match(/^(https?:\/\/[^\/?#]+)(\/[^?#]*)?/i), origin = bm[1], dir = (bm[2] || '/').replace(/[^\/]*$/, ''), host = mailHost_(r[2]);
        var re = /<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]{0,300}?)<\/a>/gi, m, best = [];
        while ((m = re.exec(tops[i]))) {
          var href = m[1].trim(), text = m[2].replace(/<[^>]+>/g, '').replace(/\s+/g, '') + ' ' + ((m[0].match(/alt\s*=\s*["']([^"']*)["']/i) || [])[1] || '');
          if (/^(mailto:|tel:|javascript:|#)/i.test(href) || /\.(pdf|jpe?g|png|gif|zip|docx?|xlsx?)(\?|$)/i.test(href)) continue;
          var u = (/^https?:\/\//i.test(href) ? href : /^\/\//.test(href) ? 'https:' + href : href.charAt(0) === '/' ? origin + href : origin + dir + href.replace(/^\.\//, '')).replace(/#.*$/, '');
          if (mailHost_(u) !== host) continue;
          var key = (text + ' ' + href).toLowerCase(), sc = /見積|estimate|mitsumori|quote|quotation/.test(key) ? 4 : /お問い?合わ?せ|問合|contact|inquiry|toiawase|ご相談|ご依頼/.test(key) ? 3 : 0;
          if (sc && !best.some(function (b) { return b[0] === u; })) best.push([u, sc]);
        }
        best.sort(function (a, b) { return b[1] - a[1]; }).slice(0, 2).forEach(function (b) { next.push(b[0]); owner.push(i); });
      });
      var subs = next.length ? mailFetch_(next) : [];
      var now = new Date();
      var rows = batch.map(function (r, i) {
        var pages = [[r[2], tops[i]]];
        next.forEach(function (u, j) { if (owner[j] === i) pages.unshift([u, subs[j]]); });
        var hit = null, ext = '';
        pages.forEach(function (p) {
          if (!p[1]) return;
          var e = String(p[1]).match(/(docs\.google\.com\/forms|form\.run|formrun|formzu|formmailer|form-mailer|tayori|hubspot|mktoweb|pardot|kintone|jotform|questant|ssl\.form-mailer)/i);
          if (e && !ext) ext = e[1];
          if (!hit) { var t = surveyFormText_(p[1]); if (t) hit = [p[0], t]; }
        });
        if (!tops[i]) return [r[0], r[1], r[2], '', '読めない', '', '', now];
        return [r[0], r[1], r[2], hit ? hit[0] : next.filter(function (u, j) { return owner[j] === i; }).join('\n'), hit ? 'あり' : 'なし', hit ? hit[1] : '', ext, now];
      });
      sh.getRange(sh.getLastRow() + 1, 1, rows.length, SURVEY_HEAD.length).setValues(rows.map(function (x) { return x.map(safe_); }));
      props.setProperty('SURVEY_CURSOR', String(cur));
    }
    if (cur >= list.length) ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'surveyForms') ScriptApp.deleteTrigger(t); });
  } finally { lock.releaseLock(); }
}

// 「見積フォーム調査」の集計：フォームの文字に、どの項目が出てくるかを数え、「見積フォーム集計」タブにカテゴリごとの割合を書く（関数 surveyTally を実行）
var SURVEY_ITEMS = [
  ['会社名', /会社名|御社名|貴社名|法人名|団体名|社名|屋号/], ['お名前', /お名前|氏名|ご担当者|担当者名|名前/], ['メール', /メール|e-?mail/i], ['電話', /電話|tel/i],
  ['住所', /住所|所在地|郵便番号|都道府県/], ['FAX', /fax/i], ['部署・役職', /部署|役職/], ['業種', /業種|業態|事業内容/],
  ['問い合わせの種類', /種別|ご用件|お問い?合わ?せ(の)?項目|お問い?合わ?せ(の)?種類|件名|カテゴリ|区分/], ['自由記述', /お問い?合わ?せ内容|ご相談内容|ご依頼内容|内容|詳細|ご質問|ご要望|備考|メッセージ/],
  ['添付ファイル', /添付|ファイル|アップロード|upload/i], ['図面の有無', /図面/], ['品名・製品名', /品名|製品名|商品名|部品名|アイテム|品目|製品の種類/],
  ['数量・ロット', /数量|個数|ロット|枚数|本数|台数|生産数|発注数|lot/i], ['希望納期', /納期|納品日|希望日|納品希望|いつまで|発売予定|スケジュール/],
  ['材質・素材', /材質|材料|素材|生地|樹脂|鋼種|原料|成分/], ['大きさ・寸法', /サイズ|寸法|大きさ|外形|板厚|容量|重量|重さ/],
  ['表面処理・仕上げ', /表面処理|仕上げ|塗装|メッキ|めっき|アルマイト|熱処理|研磨|印刷|刺繍|プリント/], ['精度・公差', /公差|精度/],
  ['予算・単価', /予算|単価|価格|金額|費用/], ['用途・目的', /用途|使用目的|使い道|目的|使用環境/], ['試作か量産か', /試作|量産|サンプル/],
  ['加工・工程の種類', /加工内容|加工方法|加工の種類|工程|製法|加工品目/], ['支給品', /支給|持ち込み|持込/], ['検査・成績書', /検査|成績書|ミルシート/],
  ['知ったきっかけ', /知った|きっかけ|どこで|何で知/], ['連絡方法の希望', /連絡方法|ご希望の連絡|連絡手段/], ['個人情報の同意', /個人情報|プライバシー/],
  ['「見積」の欄・選択肢がある', /見積|見積り|見積もり|お見積/]
];
function surveyTally() {
  var ss = sheet_().getParent(), sh = ss.getSheetByName('見積フォーム調査');
  if (!sh || sh.getLastRow() < 2) return;
  var v = sh.getRange(2, 1, sh.getLastRow() - 1, 6).getValues(), cat = {}, flags = [];
  v.forEach(function (r) {
    var c = String(r[1]), has = r[4] === 'あり', txt = String(r[5] || ''), f = [];
    var k = cat[c] = cat[c] || {n: 0, read: 0, form: 0, hit: SURVEY_ITEMS.map(function () { return 0; })};
    k.n++; if (r[4] !== '読めない') k.read++;
    if (has) { k.form++; SURVEY_ITEMS.forEach(function (it, i) { if (it[1].test(txt)) { k.hit[i]++; f.push(it[0]); } }); }
    flags.push([f.join('、')]);
  });
  sh.getRange(1, 9).setValue('見つけた項目');
  sh.getRange(2, 9, flags.length, 1).setValues(flags);
  var out = slotTab_('見積フォーム集計', ['項目'].concat(Object.keys(cat)).concat(['全体']));
  var tot = {n: 0, read: 0, form: 0, hit: SURVEY_ITEMS.map(function () { return 0; })};
  Object.keys(cat).forEach(function (c) { tot.n += cat[c].n; tot.read += cat[c].read; tot.form += cat[c].form; cat[c].hit.forEach(function (h, i) { tot.hit[i] += h; }); });
  var cols = Object.keys(cat).map(function (c) { return cat[c]; }).concat([tot]);
  var rows = [['調べた会社'].concat(cols.map(function (k) { return k.n; })), ['サイトを読めた'].concat(cols.map(function (k) { return k.read; })), ['フォームがあった'].concat(cols.map(function (k) { return k.form; }))];
  SURVEY_ITEMS.forEach(function (it, i) { rows.push([it[0] + '（%）'].concat(cols.map(function (k) { return k.form ? Math.round(k.hit[i] * 100 / k.form) : ''; }))); });
  out.clear(); out.getRange(1, 1, 1, cols.length + 1).setValues([['項目'].concat(Object.keys(cat)).concat(['全体'])]);
  out.getRange(2, 1, rows.length, cols.length + 1).setValues(rows);
}
