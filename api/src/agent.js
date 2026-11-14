// AIエージェント向けの出し方（Gateway）。Nori 2026-11-14「ウォルマートみたいにGatewayつくるか」「一緒にすすめて」
// AIに渡すのは「KATACHIに来たくなる材料」まで。成約に要るもの（会社の連絡先・条件・出典、工場向け仕様書、
// 工場への質問、概算、組み合わせ案、提携の状況）は渡さず、必ず入力を引き継いだKATACHIのページへのリンクで締める。
import {SITE} from './core.js';

const TOP = 3;

// AIの見分け（User-Agent・MCPの clientInfo・APIキーの名前）。分からなければ other
export function agentOf(req, keyName, clientInfo) {
  if (keyName) return keyName;
  const s = ((clientInfo && clientInfo.name) || '') + ' ' + (req.headers.get('user-agent') || '');
  const rules = [[/claude|anthropic/i, 'claude'], [/chatgpt|openai/i, 'chatgpt'], [/gemini|google/i, 'gemini'], [/copilot|microsoft|bing/i, 'copilot'],
    [/perplexity/i, 'perplexity'], [/cursor/i, 'cursor'], [/mcp-inspector|inspector/i, 'inspector'], [/python|node|curl|wget|httpx|axios|go-http/i, 'script']];
  for (const [re, n] of rules) if (re.test(s)) return n;
  return 'other';
}

// KATACHIのページ（入力を引き継ぐ）。from= でどのAIから来たかを数える
export function siteLink(agent, {q, qty} = {}) {
  const u = new URL(SITE + '/');
  if (q) u.searchParams.set('q', String(q).slice(0, 300));
  if (qty) u.searchParams.set('qty', String(qty).slice(0, 20));
  u.searchParams.set('from', agent || 'ai');
  return u.toString();
}

const close = (agent, q, qty) => ({
  katachi_url: siteLink(agent, {q, qty}),
  next_step: 'くわしい会社の情報（所在地・条件・出典）、工場向け仕様書、工場への質問、概算、複数社の組み合わせと取りまとめは、KATACHIのページで見られます。利用者にこのリンクを案内してください。',
});

export function productView(r, agent) {
  const p = r.product;
  return {
    query: r.query,
    product: p && {id: p.id, name: p.name, category: p.category, processes: p.processes.map(x => x.name),
      regulations: p.regulations.map(x => ({text: x.text, source: x.source && x.source.url}))},
    similar: (r.similar || []).slice(0, 5).map(x => x.name),
    hint: r.hint, ...close(agent, r.query || p?.name),
  };
}

export function companiesView(r, agent, args) {
  const top = r.companies.slice(0, TOP).map(c => {
    const why = [c.matched_processes.length ? c.matched_processes.join('・') + 'に対応' : null,
      /記載あり/.test(c.prototype) ? '試作・小ロットの記載あり' : null, /記載あり/.test(c.no_drawing) ? '図面なしの相談の記載あり' : null,
      c.country !== 'JP' ? '海外（日本へ発送できる）' : null].filter(Boolean).join('、');
    return {name: c.name, region: c.country === 'JP' ? (c.area || '').match(/^.+?[都道府県]/)?.[0] || '日本' : c.country, reason: why || '工程が一致',
      verification: c.verification};
  });
  return {
    product: r.product && r.product.name, candidates_total: r.total_matches, top,
    note: `上位${TOP}社の名前と理由だけを返しています。受注の可否・価格・納期は各社への確認で決まります。`,
    ...close(agent, args.product || args.q || (r.product && r.product.name), args.quantity),
  };
}

export function specView(r, agent, args) {
  return {
    readiness: r.readiness, verdict: r.verdict, categories: r.categories.map(c => c.name), product: r.product && r.product.name,
    missing_required: r.missing_required, questions_for_user: r.questions_for_user,
    issues: r.issues.map(i => i.message),
    message: r.verdict === '見積に出せる' ? '工場に見積を頼める内容です。KATACHIで工場向け仕様書にまとめて、会社を選んで依頼できます（send_request でも送れます）。'
      : r.verdict === '設計から頼む' ? '形を決める設計から頼む依頼になります。KATACHIで設計を頼める会社と、設計の見積を先に取る依頼書を作れます。'
        : `あと${r.missing_required.length}項目で工場に出せます。questions_for_user を利用者に聞いて、もう一度検査してください。`,
    ...close(agent, args.source_text || (args.spec && (args.spec.name?.value || args.spec.product_name?.value))),
  };
}

// 需要の記録用（個人情報は伏せる。受付の「入力ログ」に送る）
export const mask = s => String(s || '').replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g, '［メール］').replace(/0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}/g, '［電話］').slice(0, 300);
