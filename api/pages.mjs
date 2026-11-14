// Cloudflare Pages 用に1ファイル（dist/_worker.js）へまとめる。Nori 2026-11-14「katachi.shiokonbuだけを対象にしたい」
// Pages ならさくらのDNSに CNAME（api.katachi → katachi-api.pages.dev）を1件足すだけで独自ドメインが使え、shiokonbu.com 本体には触れない。
// 使い方: node build.mjs && node pages.mjs （Pages のビルドコマンド。出力先は api/dist）
import {readFileSync, writeFileSync, mkdirSync, rmSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {build} from 'esbuild';

const here = dirname(fileURLToPath(import.meta.url));
// wrangler.toml の [vars] をそのまま既定値にする（Pages の設定画面で上書きできる）
const toml = readFileSync(join(here, 'wrangler.toml'), 'utf8');
const vars = Object.fromEntries([...toml.matchAll(/^([A-Z_]+)\s*=\s*"([^"]*)"/gm)].map(m => [m[1], m[2]]));

mkdirSync(join(here, '.pages'), {recursive: true});
writeFileSync(join(here, '.pages/entry.js'),
  `import w from '../src/index.js';\nconst VARS = ${JSON.stringify(vars)};\n` +
  `const SITE = 'https://katachi.shiokonbu.com';\n` +
  // サイトが読む会社DB・製品DB（/site/*.json）。公開リポジトリには置かず、非公開の katachi-data から dist/site/ に入れる（Nori 2026-11-14）。
  // サイトの画面からの読み込みだけに渡す（Referer/Origin が katachi.shiokonbu.com。手元の確認用に localhost も通す）
  `const fromSite = req => /^(https:\\/\\/katachi\\.shiokonbu\\.com|http:\\/\\/(localhost|127\\.0\\.0\\.1)(:\\d+)?)(\\/|$)/.test(req.headers.get('origin') || req.headers.get('referer') || '');\n` +
  `async function site(req, env) {\n` +
  `  const o = req.headers.get('origin'); const cors = {'access-control-allow-origin': o && fromSite(req) ? o : SITE, 'vary': 'Origin'};\n` +
  `  if (req.method === 'OPTIONS') return new Response(null, {status: 204, headers: {...cors, 'access-control-allow-methods': 'GET'}});\n` +
  `  if (req.method !== 'GET' || !fromSite(req) || !env.ASSETS) return new Response(JSON.stringify({error: 'forbidden', message: 'KATACHIのサイトからだけ読めます。AI・プログラムからは /mcp か /v1/ を使ってください。'}), {status: 403, headers: {...cors, 'content-type': 'application/json; charset=utf-8'}});\n` +
  `  const r = await env.ASSETS.fetch(req); const h = new Headers(r.headers); for (const [k, v] of Object.entries(cors)) h.set(k, v);\n` +
  `  h.set('cache-control', 'private, max-age=3600'); h.set('x-robots-tag', 'noindex'); return new Response(r.body, {status: r.status, headers: h});\n` +
  `}\n` +
  `export default {fetch: (req, env, ctx) => new URL(req.url).pathname.startsWith('/site/') ? site(req, env) : w.fetch(req, {...VARS, ...env}, ctx)};\n`);

rmSync(join(here, 'dist'), {recursive: true, force: true});
await build({
  entryPoints: [join(here, '.pages/entry.js')], outfile: join(here, 'dist/_worker.js'),
  bundle: true, format: 'esm', platform: 'neutral', charset: 'utf8', logLevel: 'warning',
});
writeFileSync(join(here, 'dist/_routes.json'), JSON.stringify({version: 1, include: ['/*'], exclude: []}));
console.log('api/dist/_worker.js を作りました');
