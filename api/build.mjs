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
