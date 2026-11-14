/**
 * KATACHI（katachi.shiokonbu.com）の「見積の依頼」と「相談」の受付（Google Apps Script）
 *
 * 流れ（提携の申込み type:'partner' は「提携申込」タブへ。下の partner_ を参照）
 *   1. サイトのフォーム → doPost で、スプレッドシート「KATACHI 受付」の「受付」タブに1行追加
 *   2. 運営者に「新しい受付」のメール
 *   3. 依頼した人に「受け付けました」のメール（受付番号つき）
 *   会社への打診は、担当者が内容を確認してから手で行う（自動では送らない）。
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
    notifyAdmin_(id, row, sh);
    replyUser_(id, email, p, f);
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

function notifyAdmin_(id, row, sh) {
  var to = CONFIG.ADMIN_EMAIL || Session.getEffectiveUser().getEmail();
  var body = HEAD.map(function (h, i) { return '■ ' + h + '\n' + (row[i] instanceof Date ? Utilities.formatDate(row[i], 'Asia/Tokyo', 'yyyy-MM-dd HH:mm') : row[i]); }).join('\n\n');
  MailApp.sendEmail({to: to, subject: '[KATACHI] 新しい' + row[2] + ' ' + id, body: body + '\n\n一覧: ' + sh.getParent().getUrl()});
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
    btn: '打开 KATACHI', foot: '您收到此邮件是因为有人在 KATACHI 的表单中填写了此邮箱。如非本人操作，请回复告知我们。'
  }
};

function esc_(v) { return String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/\n/g, '<br>'); }
function clip_(v, n) { v = String(v || '').trim(); return v.length > n ? v.slice(0, n) + '…' : v; }

function replyUser_(id, email, p, f) {
  var mail = buildReplyMail_(id, p, f || {});
  MailApp.sendEmail({to: email, subject: mail.subject, body: mail.text, htmlBody: mail.html, name: CONFIG.SERVICE_NAME});
}

function buildReplyMail_(id, p, f) {
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
    summary +
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
