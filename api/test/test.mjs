// node api/test/test.mjs  （先に node api/build.mjs）
// Workers の caches と受付（Apps Script）を差し替えて、HTTP と MCP の両方を確かめる
import assert from 'node:assert/strict';

const store = new Map();
globalThis.caches = {default: {match: async u => store.has(u) ? new Response(store.get(u)) : undefined, put: async (u, r) => store.set(u, await r.text())}};
const sent = [];
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, init) => {
  if (String(url).includes('script.google.com')) { sent.push(JSON.parse(init.body)); return new Response(JSON.stringify({ok: true, id: 'K261114-TEST'})); }
  return realFetch(url, init);
};
const {default: worker} = await import('../src/index.js');
const env = {GAS_URL: 'https://script.google.com/macros/s/x/exec'};
let ipN = 0;
const call = async (path, {method = 'GET', body, ip} = {}) => {
  const r = await worker.fetch(new Request('https://api.test' + path, {method, body: body && JSON.stringify(body),
    headers: {'content-type': 'application/json', 'cf-connecting-ip': ip || '10.0.0.' + (++ipN % 250)}}), env, {});
  return {status: r.status, j: r.status === 202 ? null : await r.json(), h: r.headers};
};
const rpc = (method, params, id = 1, ip) => call('/mcp', {method: 'POST', body: {jsonrpc: '2.0', id, method, params}, ip});
let n = 0;
const t = async (name, f) => { await f(); n++; console.log('OK', name); };

await t('トップ', async () => { const {status, j} = await call('/'); assert.equal(status, 200); assert.ok(j.products > 20000, j.products); assert.ok(j.companies > 10000); });
await t('製品: 犬の首輪（工程と法規制まで、リンクで締める）', async () => {
  const {j} = await call('/v1/products?q=' + encodeURIComponent('犬の首輪'));
  assert.match(j.product.name, /首輪/); assert.ok(j.product.processes.length); assert.ok(!('lots_and_prices' in j.product) && !('parts' in j.product));
  assert.match(j.katachi_url, /^https:\/\/katachi\.shiokonbu\.com\/\?q=.+&from=/);
});
await t('製品: 分類から（ボールベアリング）', async () => { const {j} = await call('/v1/products?q=' + encodeURIComponent('ボールベアリング')); assert.match(j.product.name, /軸受/); });
await t('製品ID', async () => { const {j} = await call('/v1/products/c_pet_leash'); assert.equal(j.product.id, 'c_pet_leash'); });
await t('製品: 扱わない分野', async () => { const {status, j} = await call('/v1/products?q=' + encodeURIComponent('日本酒を造りたい')); assert.equal(status, 422); assert.match(j.error.message, /酒/); });
await t('会社: 上位3社の名前と理由だけ', async () => {
  const {j} = await call('/v1/companies?product=' + encodeURIComponent('アクリルスタンド') + '&quantity=50');
  assert.ok(j.top.length > 0 && j.top.length <= 3); assert.ok(j.candidates_total >= j.top.length);
  for (const c of j.top) { assert.deepEqual(Object.keys(c).sort(), ['name', 'reason', 'region', 'verification']); assert.ok(c.reason); }
  assert.ok(!JSON.stringify(j).includes('http://') && !/website|source|min_lot/.test(JSON.stringify(j)));
  assert.match(j.katachi_url, /from=/);
});
await t('会社: 一覧の取得は不可・ずらしても上位3社のまま', async () => {
  assert.equal((await call('/v1/companies')).status, 400);
  const a = (await call('/v1/companies?process=manufacturing')).j, b = (await call('/v1/companies?process=manufacturing&offset=20&limit=10')).j;
  assert.deepEqual(a.top, b.top); assert.equal(b.top.length, 3);
});
await t('会社: 1688等は出さない', async () => {
  for (const q of ['青島', '有限公司', '深セン', 'Co., Ltd']) {
    const {j} = await call('/v1/companies?q=' + encodeURIComponent(q) + '&country=ABROAD');
    for (const c of j.top || []) assert.match(c.reason, /日本へ発送できる/, c.name);
  }
});
await t('AIの見分け', async () => {
  const {agentOf} = await import('../src/agent.js');
  const R = ua => new Request('https://x', {headers: {'user-agent': ua}});
  assert.equal(agentOf(R('Claude-User/1.0'), null), 'claude'); assert.equal(agentOf(R('ChatGPT-User/1.0; openai-mcp'), null), 'chatgpt');
  assert.equal(agentOf(R('curl/8'), null), 'script'); assert.equal(agentOf(R('x'), 'partner1'), 'partner1');
});
const spec = {name: {value: '犬用の光る首輪', quote: '犬用の光る首輪'}, purpose: {value: '自社の商品として売る', basis: '回答'},
  size: {value: '首回り30〜45cm、幅2cm', quote: '首回り30〜45cm'}, mat: {value: 'ナイロン', basis: '回答'}, scope: {value: '設計から（図面がない）', basis: '回答'},
  docs: {value: '手書きのスケッチ', basis: '回答'}, qs: {value: '2〜5個', basis: '回答'}, qf: {value: '〜500個', basis: '回答'}, due: {value: '3か月以内', basis: '回答'},
  category_items: {power: {value: '充電式', basis: '回答'}, target: {value: '中型犬', basis: '回答'}}};
const src = '犬用の光る首輪を作りたい。首回り30〜45cmくらい。夜の散歩で目立つように、USBで充電したい。';
await t('仕様書: 検査（設計から頼む）', async () => {
  const {j} = await call('/v1/spec/check', {method: 'POST', body: {spec, source_text: src}});
  assert.equal(j.verdict, '設計から頼む'); assert.ok(j.readiness > 50, j.readiness); assert.ok(j.categories.includes('ペット用品'));
  assert.ok(j.questions_for_user.length <= 5); assert.ok(!('questions_for_factory' in j) && !('items' in j)); assert.ok(j.katachi_url);
});
await t('仕様書: 根拠なし・引用ちがい・矛盾', async () => {
  const bad = {...spec, size: {value: '10cm', quote: '10cmくらい'}, mat: {value: '革'}, scope: {value: '図面・データがあり、作るだけ', basis: '回答'}};
  const {j} = await call('/v1/spec/check', {method: 'POST', body: {spec: bad, source_text: src}});
  const m = j.issues.join('\n');
  assert.match(m, /「大きさ」根拠/); assert.match(m, /「素材」根拠/); assert.match(m, /作るだけ/);
});
await t('仕様書: サイトの貼り戻しJSONも読める', async () => {
  const sx = {product_name: {value: 'アクリルスタンド', quote: 'アクリルスタンド'}, width: {value: '80mm', quote: '幅80mm'}, materials: [{part: '本体', value: 'アクリル', quote: 'アクリル'}]};
  const {checkSpec} = await import('../src/core.js');
  const j = checkSpec({spec: sx, source_text: 'アクリルスタンドを作りたい。幅80mm、アクリル。'});
  const it = k => j.items.find(i => i.key === k);
  assert.equal(it('name').level, '原文'); assert.equal(it('size').level, '原文'); assert.equal(it('mat').level, '原文');
});
await t('依頼: 同意なしは送らない', async () => {
  const {status} = await call('/v1/requests', {method: 'POST', body: {email: 'a@example.com', requester_type: '個人', summary: 'x', quantity: '3', due: '未定'}});
  assert.equal(status, 400); assert.equal(sent.length, 0);
});
await t('依頼: 送る・1日3件まで', async () => {
  const b = {email: 'a@example.com', requester_type: '法人', organization: 'テスト', summary: '犬用の光る首輪', quantity: '試作3個', due: '3か月以内', agree_privacy: true, spec, idea: src, companies: ['A社']};
  for (let i = 0; i < 3; i++) { const {status, j} = await call('/v1/requests', {method: 'POST', body: b, ip: '10.9.9.9'}); assert.equal(status, 201, JSON.stringify(j)); }
  const {status} = await call('/v1/requests', {method: 'POST', body: b, ip: '10.9.9.9'}); assert.equal(status, 429);
  assert.equal(sent.length, 3); assert.equal(sent[0].type, 'rfq'); assert.ok(sent[0].fields.some(f => f.id === 'x-spec' && /工場に出せる度/.test(f.value)));
});
await t('依頼: CORSを付けない', async () => { const {h} = await call('/v1/requests', {method: 'POST', body: {}}); assert.equal(h.get('access-control-allow-origin'), null); });
await t('MCP: initialize / tools/list', async () => {
  const {j} = await rpc('initialize', {protocolVersion: '2025-06-18', capabilities: {}, clientInfo: {name: 't', version: '1'}});
  assert.equal(j.result.protocolVersion, '2025-06-18'); assert.equal(j.result.serverInfo.name, 'katachi');
  const l = await rpc('tools/list', {}); assert.deepEqual(l.j.result.tools.map(x => x.name), ['lookup_product', 'search_companies', 'list_processes', 'get_spec_schema', 'check_spec', 'send_request']);
  assert.equal((await call('/mcp', {method: 'POST', body: {jsonrpc: '2.0', method: 'notifications/initialized'}})).status, 202);
});
await t('MCP: tools/call', async () => {
  const {j} = await rpc('tools/call', {name: 'search_companies', arguments: {product: '化粧水'}});
  assert.ok(j.result.structuredContent.top.length <= 3); assert.ok(!j.result.isError); assert.ok(j.result.structuredContent.katachi_url);
  const e = await rpc('tools/call', {name: 'lookup_product', arguments: {q: ''}}); assert.equal(e.j.result.isError, true);
  const u = await rpc('tools/call', {name: 'drop_table', arguments: {}}); assert.equal(u.j.error.code, -32602);
});
await t('MCP: バッチ・GETは不可', async () => {
  assert.equal((await call('/mcp', {method: 'POST', body: [{jsonrpc: '2.0', id: 1, method: 'ping'}]})).status, 400);
  assert.equal((await call('/mcp')).status, 405);
});
await t('回数制限: 1分30回 → 429、違反が続くと遮断', async () => {
  const codes = [];
  for (let i = 0; i < 60; i++) codes.push((await call('/v1/processes', {ip: '10.7.7.7'})).status);
  assert.equal(codes.filter(c => c === 200).length, 30); assert.ok(codes.includes(429)); assert.ok(codes.includes(403));
  assert.equal((await call('/v1/processes', {ip: '10.7.7.8'})).status, 200);  // 別のIPは通る
});
await t('丸ごと取得: 製品の似た候補は5件まで', async () => { const {j} = await call('/v1/products?q=' + encodeURIComponent('ねじ')); assert.ok(j.similar.length <= 5); });
await t('需要の記録: 受付に送る（個人情報は伏せる）', async () => {
  const logs = [];
  const w = async (path, ua) => worker.fetch(new Request('https://api.test' + path, {headers: {'user-agent': ua, 'cf-connecting-ip': '10.3.3.3'}}), env, {waitUntil: p => logs.push(p)});
  const before = sent.length;
  await w('/v1/products?q=' + encodeURIComponent('名刺入れ a@example.com 090-1234-5678'), 'Claude-User');
  await Promise.all(logs);
  const l = sent.slice(before).find(x => x.type === 'idea');
  assert.ok(l); assert.equal(l.mode, 'api'); assert.match(l.note, /AI: claude \/ lookup_product/); assert.ok(!/example\.com|1234/.test(l.text), l.text);
});
console.log(`すべてOK（${n}件）`);
