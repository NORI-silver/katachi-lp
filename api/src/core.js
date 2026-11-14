// KATACHI API の中身（HTTP と MCP の両方から呼ぶ）。データはデプロイ時に同梱する。
import P0 from '../../data/products.json' with {type: 'json'};
import C0 from '../../data/companies.json' with {type: 'json'};
import F0 from '../../data/fspec.json' with {type: 'json'};
// Workers では文字列（wrangler.toml の rules）、Node のテストではオブジェクトで来る
const parse = x => typeof x === 'string' ? JSON.parse(x) : x;
const products = parse(P0), companiesRaw = parse(C0), fspec = parse(F0);
import {setPDB, pdbMatch} from './gen/pdb.js';

export const VERSION = '1.0.0';
export const SITE = 'https://katachi.shiokonbu.com';
export const LIMITS = {results: 10, offset: 20, text: 4000, quote: 200};

export class ApiError extends Error {
  constructor(status, code, message) { super(message); this.status = status; this.code = code; }
}

// ---------------------------------------------------------------- データの準備（起動時に1回）
setPDB(products);
pdbMatch('準備');  // 索引を起動時に作っておく（1回目の検索を軽くする）

const C = companiesRaw;
const CAPN = Object.fromEntries(C.caps.map((c, i) => [c, C.names[i]]));
// 利用者が注文できる会社だけ（サイトの canOrder と同じ条件。tools/template.html）
const DOMESTIC_ONLY = /(^|\/\/|\.)(1688\.com|taobao\.com|tmall\.com)/i;
const canOrder = r => {
  const x = r[14] || {};
  if (r[1] === 'JP') return true;
  if (x.ord === 0) return false;
  if (DOMESTIC_ONLY.test((r[4] || '') + ' ' + (r[12] || '')) && !x.ord) return false;
  return x.sh === 1 || x.ord === 1;
};
const seen = new Set();
const ROWS = C.c.filter(r => canOrder(r) && !seen.has(r[0]) && seen.add(r[0]));
const LV = {pub: '公開情報（公式サイト・報道）で確認', unk: '掲載ページのみ（要確認）', gov: '国の登録情報のみ（gBizINFO、要確認）'};
const LV_RANK = {pub: 0, unk: 1, gov: 2};
const GBIZ = '出典: Gビズインフォ（経済産業省）をもとにKATACHI作成';

export const stats = () => ({products: products.products.length + products.jscc.items.filter(i => i[2]).length, companies: ROWS.length, updated: products.updated});

// ---------------------------------------------------------------- 入力
const CTRL = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f​-‏‪-‮⁦-⁩]/g;
export function text(v, field, max, required = false) {
  if (v == null || (typeof v === 'string' && !v.trim())) {
    if (required) throw new ApiError(400, 'invalid_input', `${field} を入力してください`);
    return '';
  }
  if (typeof v !== 'string' && typeof v !== 'number') throw new ApiError(400, 'invalid_input', `${field} は文字列で指定してください`);
  const s = String(v).normalize('NFKC').replace(CTRL, '').trim();
  if (s.length > max) throw new ApiError(400, 'input_too_long', `${field} は${max}文字以内にしてください`);
  return s;
}
const int = (v, field, lo, hi, dflt) => {
  if (v == null || v === '') return dflt;
  const n = Number(v);
  if (!Number.isInteger(n) || n < lo || n > hi) throw new ApiError(400, 'invalid_input', `${field} は${lo}〜${hi}の整数で指定してください`);
  return n;
};

// 扱わない分野（サイトと同じ。企業DBの deferred_kw ＋ 武器の追加語）
export function policy(...texts) {
  const t = texts.filter(Boolean).join('\n').toLowerCase();
  for (const [kws, msg] of C.deferred_kw) if (kws.some(k => t.includes(k.toLowerCase()))) throw new ApiError(422, 'not_handled', msg);
  if (/拳銃|銃器|銃弾|弾薬|爆弾|爆薬|ゴーストガン|firearm|ammunition|explosive/i.test(t)) throw new ApiError(422, 'not_handled', '武器・火薬・刀剣・毒物は扱いません');
  if (/(日本酒|ビール|ワイン|焼酎|ウイスキー|お酒|酒類).{0,6}(造|作|つく|製造|醸造|OEM)/i.test(t)) throw new ApiError(422, 'not_handled', C.deferred['food.alcohol_oem']);
}

// ---------------------------------------------------------------- ① 製品を調べる
const LEVEL = products.levels;
const src = s => s ? {title: s.t, url: s.url || null, level: LEVEL[s.level] || s.level || null} : null;
function productOut(r) {
  if (!r) return null;
  return {
    id: r.id, name: r.name, category: products.ind[r.ind] || r.ind || null, classification: r.cls || null,
    processes: (r.proc || []).map(p => ({code: p, name: CAPN[p] || p})),
    parts: r.parts || [], materials: r.mat || [],
    parts_basis: r.parts && r.parts.length ? (LEVEL[r.pl] || 'AI推定（よくある例）') : '要確認（この分類には構成・素材の情報がありません）',
    lots_and_prices: (r.lot || []).slice(0, 6).map(x => ({process: CAPN[x.proc] || x.proc, kind: {moq: '最小ロット', unit: '単価', init: '初期費用'}[x.k] || x.k,
      label: x.t, low: x.lo, high: x.hi, unit: x.u, source: src(x.src)})),
    regulations: (r.reg || []).map(x => ({text: x.t, source: src(x.src)})),
    sources: (r.src || []).map(src),
    note: '最小ロット・価格は工程ごとの公開例です。この製品の見積ではありません。構成・素材で「AI推定」「要確認」のものは工場への確認が必要です。',
  };
}
const byId = new Map(products.products.map(p => [p.id, p]));
export function lookupProduct({q, id}) {
  if (id) {
    const k = text(id, 'id', 40);
    let r = byId.get(k);
    if (!r && /^j_[0-9A-Z]{2,8}$/.test(k)) {
      const J = products.jscc, code = k.slice(2), i = J.items.findIndex(x => x[0] === code);
      if (i >= 0) r = pdbMatch(J.items[i][1]);
      if (r && r.id !== k) r = null;
    }
    if (!r) throw new ApiError(404, 'not_found', '該当する製品がありません');
    return {product: productOut(r)};
  }
  const s = text(q, 'q', 200, true);
  policy(s);
  const best = pdbMatch(s);
  // 似た名前の候補（最大10件）。DBの全件を引き出せないよう、検索語を含むものだけ
  const qq = s.toLowerCase(), alt = [];
  if (qq.length >= 2) for (const p of products.products) {
    if (alt.length >= LIMITS.results) break;
    if (p.from !== 'concept' && p.id !== best?.id && (p.name.toLowerCase().includes(qq) || (p.kw || '').toLowerCase().split('|').some(k => k && qq.includes(k)))) alt.push({id: p.id, name: p.name});
  }
  if (qq.length >= 2) for (const [code, name, kw] of products.jscc.items) {
    if (alt.length >= LIMITS.results) break;
    if (kw && name.toLowerCase().includes(qq) && 'j_' + code !== best?.id) alt.push({id: 'j_' + code, name});
  }
  return {query: s, product: productOut(best), similar: alt,
    hint: best ? null : '当てはまる製品がありません。製品名を短く（例:「犬の首輪」「化粧水」）して試してください。'};
}

// ---------------------------------------------------------------- ② 会社を探す
export const processes = () => C.caps.map((c, i) => ({code: c, name: C.names[i], keywords: (C.kw[i] || []).slice(0, 8)}));
function codesFor(proc) {
  const out = new Set();
  for (const p of [].concat(proc || [])) {
    const s = text(p, 'process', 60);
    if (!s) continue;
    const exact = C.caps.filter(c => c === s || c.startsWith(s + '.'));
    const byName = C.caps.filter((c, i) => C.names[i].includes(s) || (C.kw[i] || []).includes(s));
    for (const c of (exact.length ? exact : byName)) out.add(C.caps.indexOf(c));
  }
  return [...out];
}
function companyOut(r, matched) {
  const [n, ct, pref, city, web, caps, proto, nodraw, ml, mat, lv, desc, srcUrl, date, x0] = r, x = x0 || {};
  return {
    name: n, country: ct, area: [pref, city].filter(Boolean).join(' ') || null, website: web || null,
    processes: caps.map(i => C.names[i]), matched_processes: matched.map(i => C.names[i]),
    prototype: proto ? '試作・小ロットの記載あり' : '要確認', no_drawing: nodraw ? '図面なしの相談の記載あり' : '要確認',
    min_lot: ml ?? '要確認', material_procurement: {factory: '工場が手配', customer: '依頼者の支給のみ', both: 'どちらも可'}[mat] || '要確認',
    consultation: x.cs ? {free: '技術相談あり（無償の記載）', paid: '技術相談あり（有償）', yes: '技術相談あり'}[x.cs] : '要確認',
    web_order: x.ord === 1 ? 'Webで直接注文できる' : null, ships_to_japan: ct === 'JP' ? null : (x.sh === 1 || x.ord === 1 ? '日本へ発送できる（確認済み）' : null),
    japanese_support: ct !== 'JP' && x.ja ? '日本語対応あり' : null,
    description: desc ? String(desc).slice(0, 200) : null, verification: LV[lv] || '要確認',
    source: srcUrl || null, checked: date || null, attribution: lv === 'gov' ? GBIZ : null,
  };
}
export function searchCompanies({process: proc, product, q, area, prototype, no_drawing, quantity, country, limit, offset}) {
  const lim = int(limit, 'limit', 1, LIMITS.results, LIMITS.results);
  const off = int(offset, 'offset', 0, LIMITS.offset, 0);
  const qty = int(quantity, 'quantity', 1, 10_000_000, null);
  const kw = text(q, 'q', 60);
  const ar = text(area, 'area', 20);
  let idx = codesFor(proc), prod = null;
  if (product) {
    const p = text(product, 'product', 200);
    policy(p);
    prod = pdbMatch(p);
    if (prod) idx = idx.concat(codesFor(prod.proc));
  }
  if (!idx.length && !kw) throw new ApiError(400, 'invalid_input', 'process（工程）・product（製品名）・q（キーワード）のどれかを指定してください。一覧の取得はできません');
  const kwl = kw.toLowerCase(), out = [];
  for (const r of ROWS) {
    const caps = r[5], m = caps.filter(i => idx.includes(i));
    if (idx.length && !m.length) continue;
    if (kwl && !(r[0] + ' ' + (r[11] || '')).toLowerCase().includes(kwl)) continue;
    if (country === 'JP' && r[1] !== 'JP') continue;
    if (country === 'ABROAD' && r[1] === 'JP') continue;
    if (ar && !((r[2] || '') + (r[3] || '')).includes(ar) && r[1] !== ar) continue;
    if (prototype && !r[6]) continue;
    if (no_drawing && !r[7]) continue;
    const ml = r[8];
    const s = m.length * 2 + (r[10] === 'pub' ? 3 : 0) + (r[6] && qty && qty <= 10 ? 1.5 : 0) + (r[7] && no_drawing ? 1 : 0)
      + (ml != null && qty && ml <= qty ? 1 : 0) - (ml != null && qty && ml > qty ? 3 : 0) + (r[1] === 'JP' ? 2 : 0);
    out.push([s, LV_RANK[r[10]] ?? 1, r, m]);
  }
  out.sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  const total = out.length;
  return {
    total_matches: total, offset: off, returned: Math.min(lim, Math.max(0, Math.min(total, off + lim) - off)),
    product: prod ? {id: prod.id, name: prod.name} : null,
    companies: out.slice(off, off + lim).map(([, , r, m]) => companyOut(r, m)),
    note: `1回に${LIMITS.results}社まで、上位${LIMITS.offset + LIMITS.results}社までです。受注の可否・価格・納期は各社への確認で決まります。KATACHIの提携状況は表示していません。`,
  };
}

// ---------------------------------------------------------------- ③ 仕様書を検査する
const W = fspec.levels;  // 原文 1, 回答 1, 製品DB 1, 仮 0.5, 要確認 0
const SHAPED = new Set(['elec', 'metal', 'resin', 'wood']);  // 形が決まらないと見積できない品目
const SX = Object.fromEntries(fspec.common.filter(c => c.sx).map(c => [c.sx, c.k]));
const UNKNOWN = /^(要確認|わからない|不明|未定|まだ決めていない|tbd|unknown|-|ー|なし\?)$/i;

export function specSchema() {
  return {version: fspec.version, unknown_word: fspec.unk, levels: fspec.levels,
    how_to: '各項目を {"value": 値, "basis": "原文|回答|製品DB|仮", "quote": "原文から一字一句の引用（basis=原文のとき）"} で渡す。わからない項目は value を「わからない」にする（推測で埋めない）。',
    common: fspec.common, categories: fspec.cats};
}
const norm = s => String(s || '').normalize('NFKC').replace(/\s+/g, '').toLowerCase();
function cats(spec, srcText) {
  const t = (srcText + ' ' + JSON.stringify(spec)).toLowerCase();
  const p = pdbMatch(String(spec.name?.value || spec.product_name?.value || srcText || '').slice(0, 400));
  const scored = fspec.cats.map(c => {
    let s = 0;
    if (p && ((p.proc || []).some(x => c.proc.some(y => x === y || x.startsWith(y + '.'))) || c.ind.includes(p.ind))) s += 3;
    try { if (new RegExp(c.re, 'i').test(t)) s += 2; } catch { /* 正規表現の誤りは無視 */ }
    return [s, c];
  }).filter(([s]) => s >= 2).sort((a, b) => b[0] - a[0]).slice(0, 2).map(([, c]) => c);
  return {cats: scored, product: p};
}
function field(raw, srcText) {
  // 受け取る形: 文字列 / 配列 / {value, basis, quote}
  if (raw == null) return {value: '', level: '要確認', why: '未記入'};
  if (Array.isArray(raw)) {
    // 配列（素材・部品など）は1件ずつ確かめ、いちばん弱い確かさにそろえる
    const fs = raw.slice(0, 20).map(x => field(x, srcText)).filter(f => f.value);
    if (!fs.length) return {value: '', level: '要確認', why: '未記入'};
    const worst = fs.reduce((a, f) => (W[f.level] ?? 0) < (W[a.level] ?? 0) ? f : a);
    const parts = raw.slice(0, 20).map(x => x && typeof x === 'object' && x.part ? x.part : null);
    return {value: fs.map((f, i) => f.value + (parts[i] ? `（${parts[i]}）` : '')).join('、'), level: worst.level, ...(worst.why ? {why: worst.why} : {}),
      quote: fs.map(f => f.quote).filter(Boolean).join(' / ')};
  }
  const o = typeof raw === 'object' && !Array.isArray(raw) ? raw : {value: raw};
  let v = o.value;
  if (Array.isArray(v)) v = v.map(x => typeof x === 'object' ? (x.value || '') + (x.part ? `（${x.part}）` : '') : x).filter(Boolean).join('、');
  v = text(v == null ? '' : v, 'value', 1000);
  const quote = text(o.quote || '', 'quote', LIMITS.quote);
  const basis = String(o.basis || '').trim();
  if (!v || UNKNOWN.test(v) || v === fspec.unk) return {value: v, level: '要確認', why: v ? 'わからない' : '未記入'};
  if (quote) {
    if (srcText && !norm(srcText).includes(norm(quote))) return {value: v, level: '要確認', why: '根拠の原文が元の文章に見つからない', quote};
    // サイトの sxCheck と同じ：値の数字が引用に無ければ要確認
    for (const n of v.match(/\d+(?:\.\d+)?/g) || []) if (!norm(quote).includes(n)) return {value: v, level: '要確認', why: `根拠の原文に数字「${n}」がない`, quote};
    return {value: v, level: srcText ? '原文' : (W[basis] != null ? basis : '回答'), quote};
  }
  if (basis === '原文') return {value: v, level: '要確認', why: '根拠なし（原文とあるが引用がない）'};
  if (W[basis] != null) return {value: v, level: basis};
  return {value: v, level: '要確認', why: '根拠なし（basis か quote がない値）'};
}
const nums = s => [...String(s).matchAll(/(\d+(?:\.\d+)?)\s*(mm|cm|m|kg|g|個|台|本|枚)?/gi)].map(m => ({n: +m[1], u: (m[2] || '').toLowerCase()}));
const toMm = ({n, u}) => u === 'cm' ? n * 10 : u === 'm' ? n * 1000 : u === 'mm' ? n : null;

export function checkSpec({spec, source_text}) {
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) throw new ApiError(400, 'invalid_input', 'spec（仕様書のJSON）を渡してください');
  if (JSON.stringify(spec).length > 30000) throw new ApiError(413, 'input_too_long', 'spec が大きすぎます（30,000字まで）');
  const srcText = text(source_text || '', 'source_text', LIMITS.text);
  policy(srcText, JSON.stringify(spec).slice(0, 4000));
  // サイトの貼り戻しJSON（product_name など）も受け付ける
  const s = {};
  for (const [k, v] of Object.entries(spec)) s[SX[k] || k] = v;
  if (!s.size && (s.width || s.length || s.height)) {
    const dims = ['width', 'length', 'height'].map(k => s[k]).filter(Boolean);
    const vs = dims.map(d => typeof d === 'object' ? d.value : d).filter(v => v && !UNKNOWN.test(v));
    if (vs.length) s.size = {value: vs.join(' × '), quote: dims.map(d => d.quote).filter(Boolean)[0] || '', basis: dims.map(d => d.basis).filter(Boolean)[0]};
  }
  const catItems = s.category_items || {};
  // category_items はサイトと同じ配列 [{item: 項目名（日本語）, value, quote}] か、{項目キー: {...}}
  const ci = Array.isArray(catItems) ? Object.fromEntries(catItems.map(x => [x && x.item, x])) : catItems;
  const {cats: cs, product} = cats(s, srcText);

  const items = [], missing = [], questions = [], issues = [];
  const push = (def, req, cat) => {
    const f = field(cat ? ci[def.k] ?? ci[def.t] ?? s[def.k] : s[def.k], srcText);
    const it = {key: def.k, label: def.t, required: !!req, category: cat || null, ...f};
    items.push(it);
    if (req && f.level === '要確認') {
      missing.push(def.t);
      if (def.q && questions.length < 5) questions.push({key: def.k, question: def.q, choices: def.ch ? def.ch.concat(fspec.unk) : null, multi: !!def.multi});
    }
    if (f.why && f.why.startsWith('根拠')) issues.push({key: def.k, type: 'no_basis', message: `「${def.t}」${f.why}`});
  };
  for (const d of fspec.common) push(d, d.req);
  for (const c of cs) for (const d of c.items) push(d, d.key, c.id);

  // 矛盾の検査
  const val = k => (items.find(i => i.key === k)?.value || '');
  const scope = val('scope'), docs = val('docs'), qs = val('qs'), qf = val('qf'), size = val('size');
  if (/作るだけ/.test(scope) && !/図面|3D/.test(docs)) issues.push({key: 'scope', type: 'conflict', message: '「図面・データがあり、作るだけ」なのに、手元の資料に図面・3Dデータがありません'});
  if (/試作だけ/.test(scope) && /いらない/.test(qs)) issues.push({key: 'qs', type: 'conflict', message: '「試作だけ先に」なのに、試作の数が「試作はいらない」です'});
  if (/量産だけ/.test(scope) && !/現物|図面|3D/.test(docs)) issues.push({key: 'docs', type: 'conflict', message: '「量産だけ」なのに、図面・3Dデータ・現物がありません'});
  const qsN = nums(qs).map(x => x.n), qfN = nums(qf).map(x => x.n);
  if (qsN.length && qfN.length && Math.max(...qsN) > Math.max(...qfN) && !/〜/.test(qf)) issues.push({key: 'qf', type: 'conflict', message: '試作の数が初回の数より多くなっています'});
  const mm = nums(size).map(toMm).filter(x => x != null);
  if (mm.length && /手のひら/.test(size) && Math.max(...mm) > 150) issues.push({key: 'size', type: 'conflict', message: '「手のひらに乗る」と寸法（150mm超）が合いません'});
  if (/乾電池|充電|コンセント/.test(val('power')) && /apparel|food|cosme/.test(cs.map(c => c.id).join())) issues.push({key: 'power', type: 'check', message: '電源のある製品は電気用品安全法などの確認が必要です'});

  // 工場に出せる度
  const req = items.filter(i => i.required);
  const score = req.length ? Math.round(req.reduce((a, i) => a + (W[i.level] ?? 0), 0) / req.length * 100) : 0;
  const shaped = cs.some(c => SHAPED.has(c.id)) || !cs.length;  // サイトの fsBuild と同じ
  const designFirst = /設計から/.test(scope) || (shaped && !/図面|3D|現物/.test(docs));
  const verdict = designFirst ? '設計から頼む' : score >= 75 ? '見積に出せる' : '項目が足りない';
  const fq = [...new Set(items.filter(i => i.level !== '原文' && i.level !== '回答').map(i => (fspec.common.find(d => d.k === i.key) || cs.flatMap(c => c.items).find(d => d.k === i.key) || {}).fq).filter(Boolean).concat(cs.flatMap(c => c.asks || [])))].slice(0, 10);
  return {
    readiness: score, verdict, categories: cs.map(c => ({id: c.id, name: c.t})),
    product: product ? {id: product.id, name: product.name} : null,
    missing_required: missing, questions_for_user: questions, issues,
    questions_for_factory: fq, items,
    how_scored: '必須項目の確かさの平均×100（原文・回答・製品DB=1、仮=0.5、要確認=0）。75以上で「見積に出せる」。設計からの依頼、または形のある品目で図面・3D・現物がない場合は「設計から頼む」。',
    next: designFirst ? '設計の見積を先に取る依頼にします（設計者が図面を作ってから製造の見積）。' : score >= 75 ? 'send_request で見積依頼を送れます。' : '質問（questions_for_user）に答えて、もう一度検査してください。わからない項目は「わからない」で構いません。',
  };
}

// ---------------------------------------------------------------- ④ 依頼を送る
export function buildRequest(b) {
  const email = text(b.email, 'email', 200, true);
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) throw new ApiError(400, 'invalid_input', 'email の形が正しくありません');
  const who = text(b.requester_type, 'requester_type', 20, true);
  if (!/^(法人|個人)/.test(who)) throw new ApiError(400, 'invalid_input', 'requester_type は「法人」か「個人」にしてください');
  const summary = text(b.summary, 'summary', 2000, true);
  const qty = text(b.quantity, 'quantity', 100, true);
  const due = text(b.due, 'due', 100, true);
  const org = text(b.organization, 'organization', 100), name = text(b.name, 'name', 60), tel = text(b.phone, 'phone', 30);
  const idea = text(b.idea, 'idea', LIMITS.text);
  if (b.agree_privacy !== true) throw new ApiError(400, 'consent_required', `プライバシーポリシー（${SITE}/privacy/）への同意（agree_privacy: true）が必要です`);
  policy(summary, idea);
  const comps = [].concat(b.companies || []).slice(0, 10).map(x => text(x, 'companies', 100)).filter(Boolean);
  let specNote = '';
  if (b.spec) {
    const r = checkSpec({spec: b.spec, source_text: idea});
    specNote = [`工場に出せる度: ${r.readiness}（${r.verdict}）`, ...r.items.filter(i => i.value).map(i => `${i.label}: ${i.value}（${i.level}）`),
      r.missing_required.length ? '未確定: ' + r.missing_required.join('、') : ''].filter(Boolean).join('\n').slice(0, 6000);
  }
  return {
    type: 'rfq', via: 'api', lang: 'ja', idea: idea || summary,
    fields: [
      {id: 'f-who', label: '依頼者の区分', value: /^法人/.test(who) ? '法人（中小企業など）' : '個人事業主・個人'},
      {id: 'f-org', label: '会社名・屋号', value: org}, {id: 'f-name', label: 'ご担当者名', value: name},
      {id: 'f-mail', label: 'メールアドレス', value: email}, {id: 'f-tel', label: '電話番号', value: tel},
      {id: 'f-sum', label: '製品の概要', value: summary}, {id: 'f-qty', label: '段階と数量', value: qty}, {id: 'f-due', label: '希望の時期', value: due},
      {id: 'x-via', label: '受付の経路', value: 'KATACHI API（' + (b._client || 'API') + '）'},
      ...(specNote ? [{id: 'x-spec', label: '仕様書（APIで検査）', value: specNote}] : []),
    ],
    team: comps.map(c => ({step: '希望の会社', company: c, country: 'JP'})),
    page: SITE + '/ (API)',
  };
}
