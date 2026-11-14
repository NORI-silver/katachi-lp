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
  `export default {fetch: (req, env, ctx) => w.fetch(req, {...VARS, ...env}, ctx)};\n`);

rmSync(join(here, 'dist'), {recursive: true, force: true});
await build({
  entryPoints: [join(here, '.pages/entry.js')], outfile: join(here, 'dist/_worker.js'),
  bundle: true, format: 'esm', platform: 'neutral', charset: 'utf8', logLevel: 'warning',
});
writeFileSync(join(here, 'dist/_routes.json'), JSON.stringify({version: 1, include: ['/*'], exclude: []}));
console.log('api/dist/_worker.js を作りました');
