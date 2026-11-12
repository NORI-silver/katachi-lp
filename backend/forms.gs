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
    replyUser_(id, email, p);
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

function replyUser_(id, email, p) {
  var en = p.lang === 'en', zh = p.lang === 'zh';
  var subject = en ? '[KATACHI] We received your request (' + id + ')' : zh ? '[KATACHI] 已收到您的委托（' + id + '）' : '【KATACHI】受け付けました（' + id + '）';
  var body = en
    ? 'Thank you for using KATACHI.\n\nReference: ' + id + '\n\nOur staff will check what you sent and contact suitable factories. We will email you when replies arrive (usually 1–2 weeks for quotes).\nIf you have drawings, photos or design files, please reply to this email with them attached.\n\n' + CONFIG.SITE_URL
    : zh
    ? '感谢您使用 KATACHI。\n\n受理编号：' + id + '\n\n工作人员确认内容后，会联系合适的工厂。收到回复后会通过邮件通知您（报价通常需要1〜2周）。\n如有图纸、照片或设计文件，请直接回复本邮件并附上。\n\n' + CONFIG.SITE_URL
    : 'KATACHI をご利用いただきありがとうございます。\n\n受付番号：' + id + '\n\n担当者が内容を確認してから、対応できそうな工場・専門家にお声がけします。返事が届いたらメールでお知らせします（見積はふつう1〜2週間）。\n図面・写真・設計データがあれば、このメールに返信して添付してください。\n\nまだ発注は決まっていません。見積や返事を見てから、依頼するかどうかをお決めください。\n\n' + CONFIG.SITE_URL;
  MailApp.sendEmail({to: email, subject: subject, body: body, name: CONFIG.SERVICE_NAME});
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
