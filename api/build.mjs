// サイト（tools/template.html）の製品の当て方を、そのままAPI用に取り出す。
// サイトとAPIで同じ製品に当たるよう、コードは写さずに毎回ここで抜き出す（デプロイ前に `node api/build.mjs`）。
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const html = readFileSync(join(root, 'tools/template.html'), 'utf8');
const a = html.indexOf('const pdbRx=');
const b = html.indexOf('window.KATACHI_PDB=');
if (a < 0 || b < 0 || b < a) throw new Error('tools/template.html から製品の当て方（pdbRx〜pdbMatch）が見つかりません');
const code = html.slice(a, b).trim();
for (const fn of ['function jsccRow', 'function pdbMatch']) if (!code.includes(fn)) throw new Error(fn + ' がありません');

mkdirSync(join(here, 'src/gen'), {recursive: true});
writeFileSync(join(here, 'src/gen/pdb.js'),
  '// 自動生成（api/build.mjs）。直すときは tools/template.html の製品の当て方を直す\n' +
  'let PDB=null;\nexport function setPDB(d){PDB=d}\n' + code + '\nexport {pdbMatch, jsccRow};\n');

console.log('api/src/gen/pdb.js を作りました（' + code.length + '字）');

// 会社の並べ方（依頼との近さ・受注の業態・分野・規模・所在地）も、サイトと同じ関数を取り出す（Nori 2026-11-15「マッチング精度が命」。サイトとAPIで同じ会社が上に来るように）
const r0 = html.match(/^const REGION=.*$/m), r1 = html.match(/^const regionOf=.*$/m);
const c = html.indexOf('const PREF_RX='), d = html.indexOf('function rankFor(');
if (!r0 || !r1 || c < 0 || d < 0 || d < c) throw new Error('tools/template.html から会社の並べ方（PREF_RX〜fitOf）が見つかりません');
const fit = html.slice(c, d).trim();
for (const fn of ['function relBuild', 'function relOf', 'function fitOf']) if (!fit.includes(fn)) throw new Error(fn + ' がありません');
writeFileSync(join(here, 'src/gen/fit.js'),
  '// 自動生成（api/build.mjs）。直すときは tools/template.html の relTerms〜fitOf を直す\n' +
  'let GDB=null;const S={gf:{}};export function setGDB(d){GDB=d}\n' + r0[0] + '\n' + fit + '\n' + r1[0] + '\nexport {relBuild, relOf, fitOf, PREF_RX, regionOf, REGION};\n');
console.log('api/src/gen/fit.js を作りました（' + fit.length + '字）');
