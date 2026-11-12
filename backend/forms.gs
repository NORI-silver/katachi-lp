/**
 * KATACHI（katachi.shiokonbu.com）の「見積の依頼」と「相談」の受付（Google Apps Script）
 *
 * 流れ
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
};

var HEAD = ['受付番号', '受付日時', '種類', '言語', 'メール', '会社名・お名前', '依頼者の区分', '電話', 'つくりたいもの（入力文）',
  '製品の概要', '段階と数量', '希望の時期', '送り先（工程: 会社）', '海外への提供に同意', 'その他の項目', '取り込んだ設計ファイル名', '状態'];

function setup() {
  sheet_();
  Logger.log('準備できました: ' + SpreadsheetApp.openById(prop_('SHEET_ID')).getUrl());
}

function doPost(e) {
  var out = {ok: false};
  try {
    var p = JSON.parse((e && e.postData && e.postData.contents) || '{}');
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
    if (p.type === 'consult') other = ['相談したいこと: ' + (p.topic || ''), 'いまの状況: ' + (p.body || ''), '相談先: ' + (p.to || []).join('、'), '会社: ' + (p.company || '')];
    var row = [id, new Date(), p.type === 'rfq' ? '見積の依頼' : '相談', p.lang || 'ja', email,
      p.type === 'rfq' ? [f['f-org'], f['f-name']].filter(String).join(' / ') : (p.org || ''),
      f['f-who'] || '', f['f-tel'] || '', String(p.idea || '').slice(0, 4000), f['f-sum'] || '', f['f-qty'] || '', f['f-due'] || '',
      team, p.abroad_ok ? 'はい' : '', other.join('\n').slice(0, 45000), (p.files || []).join('、'), '未対応'];
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
    '<div style="font:700 14px/1.5 ' + FONT + ';color:' + C.ink + ';">&#128206; ' + esc_(L.att_h) + '</div>' +
    '<div style="margin-top:4px;font:13px/1.7 ' + FONT + ';color:' + C.mute + ';">' + esc_(L.att) + '</div></td></tr></table></td></tr>' +
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
    '■ ' + L.att_h, L.att, '', L.note, '', CONFIG.SITE_URL].filter(function (x, i, a) { return !(x === '' && a[i - 1] === ''); }).join('\n');

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
  return ss.getSheetByName('受付');
}

function prop_(k) { return PropertiesService.getScriptProperties().getProperty(k); }

function limit_() {
  var c = CacheService.getScriptCache();
  var k = 'n' + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd');
  var n = Number(c.get(k) || 0);
  if (n >= CONFIG.DAILY_LIMIT) return false;
  c.put(k, String(n + 1), 21600);
  return true;
}

// 表計算の式として解釈されないようにする
function safe_(v) { return (typeof v === 'string' && /^[=+\-@]/.test(v)) ? "'" + v : v; }

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
