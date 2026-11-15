// サイト（index.html の画面の JS）の読み取り・並べ方を、そのままAPI用に取り出す（デプロイ前に `node api/build.mjs`）。
// サイトとAPIで同じ会社が★・上位に来るよう、コードは写さずに毎回ここで抜き出す
// （Nori 2026-11-15「マッチング精度が命」、MCPの上位3社がサイトの★と違った件）。
// 取り出す元は index.html（tools/template.html に製品・会社の一覧などを入れた生成物。`tools/README.md` の手順で作る）。
import {readFileSync, writeFileSync, mkdirSync, rmSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const lines = readFileSync(join(root, 'index.html'), 'utf8').split('\n');

// 画面の JS のうち、文章の読み取り（analyzeText）・製品DB（pdbMatch）・会社の並べ方（rankFor・fitOf）・
// 一社案（oneOf）・完成品メーカー（makersFor）・★の案（siteTop・recOf）と、それらが使う宣言。
// 足りない名前があると下の確かめで「〜 is not defined」になるので、ここに足す（定数は使われる順に並べる）
const NAMES = ['DENY_V', 'DENY_LINE', 'DENY_IN', 'denyStrip', 'GUIDE', 'GD_META', 'GD_LAB', 'cm', 'shapeConcept', 'DS_WHY', 'MPHASE', 'mphaseOf', 'dsRows', 'DESIGNERS', 'MEMO', 'ideaBase', 'dsFeat', 'dsNeed', 'dsPlan',
  'winOf', 'RL_WHY', 'planRule', 'planOf', 'recOf', 'MAKERS', 'ELEC_RX', 'makersFor', 'capCovers', 'MK_RX', 'axPass', 'axSort', 'FAMS',
  'NOTMK_RX', 'ACC_RX', 'relOf', 'fitOf', 'rankFor', 'KTK', 'relHas', 'RSTOP', 'relTerms', 'relIndex', 'relBuild', 'REGION', 'PREF_RX',
  'CONCEPTS', 'headSegs', 'conceptKind', 'specRead', 'AIMEMO', 'splitAi', 'readConds', 'pdbRx', 'REL_CTX', 'rx', 'CGEN', 'specCore',
  'fillCAPN', 'DOMESTIC_ONLY', 'USER_CT', 'F0', 'S', 'MAT_FAM', 'MAT_RX', 'matsOf', 'relText', 'analyzeText', 'pickConcept', 'flowText', 'mctxBuild', 'secsOf', 'oneOf', 'siteTop',
  'stepAssign', 'pdbMatch', 'jsccRow', 'canOrder', 'useGDB', 'regionOf', 'PREFS', 'kindById', 'specConcept', 'mmc', 'integOf', 'axOf', 'OEM_CAPS'];
const START = /^(async function|function|const|let|var)\s+([A-Za-z_$][\w$]*)/;
const TOP = /^(async function|function|const|let|var|\/\*|\/\/|window\.|document\.|if|for|try|addEventListener|\(|<\/script>|[A-Za-z_$][\w$.]*\()/;
// 行頭の宣言から、次の行頭の文の手前までを1つの宣言として取る（「const CAPN={};const fillCAPN=…」のように1行に複数あるものも）
function grab(name) {
  const own = l => { const m = l.match(START); return m && m[2] === name; };
  const re = new RegExp('(^|[;,]\\s*)(const|let|var)?\\s*' + name.replace('$', '\\$') + '\\s*=');
  let i = lines.findIndex(own);
  if (i < 0) i = lines.findIndex(l => START.test(l) && re.test(l));
  if (i < 0) throw new Error(`index.html に ${name} の宣言がありません（tools/template.html で名前が変わったら api/build.mjs の NAMES も直す）`);
  let j = i + 1;
  while (j < lines.length && !TOP.test(lines[j])) j++;
  return lines.slice(i, j).join('\n');
}
const chunks = [];
for (const n of NAMES) { const g = grab(n); if (!chunks.includes(g)) chunks.push(g); }
// 画面の部品（DOM・計測・保存）はAPIでは使わないので、空のものを置く
const STUB = "const window={};const document={querySelector:()=>null,querySelectorAll:()=>[]};const location={hash:'',search:''};" +
  "const navigator={language:'ja'};const localStorage={getItem:()=>null,setItem(){}};const track=()=>{};const logInput=()=>{};";
// ③と同じ順で読む：工程を読む → 製品の種類 → 並べ方の材料 → 工程ごとの候補 → 一社案 → ★の案（完成品メーカー、なければ一社案か組み合わせ案）
const MATCH = `
export function setData(companies, products){useGDB({...companies, c: companies.c.slice()}); PDB = products;}
export function siteMatch(text, qty){
  S.idea = String(text || ''); S.files = []; S.gf = {area:'', proto:false, lot:false, near:false, sort:''}; S.gmore = {}; S.mkView = null; S.mkPick = null; S.lai = null; S.qty = 'small';
  const A = analyzeText(S.idea); A.concept = pickConcept(flowText(), A); S.anal = A;
  const m = S.idea.match(/(\\d[\\d,]*)\\s*(個|台|枚|本|着|セット|点|pcs|units|まい|こ(?![ぁ-ゖ]))/i);
  const qn = qty || (m ? +m[1].replace(/,/g, '') : 0), qmax = qn > 0 ? qn : 500;
  S.mctx = mctxBuild(A, qmax);
  const secs = secsOf(A, qmax), one = oneOf(secs, qmax), T = siteTop(A, secs, one, qmax);
  // ★の並び：サイトの recBox と同じく、工程の割り当て（stepAssign）で組み立てて仕上げる会社を先に
  let star = T.MKv ? T.MK.rows : T.R3 ? T.R3.rows.map(x => x.r).filter(Boolean) : [];
  if (!T.MKv && T.R3 && T.R3.rows.length && T.secsP.length) { const AS = stepAssign(T.R3, T.secsP);
    if (AS) { const seen = new Set(); star = [...AS].sort((x, y) => (y.integ ? 1 : 0) - (x.integ ? 1 : 0)).map(a => a.r).filter(r => r && !seen.has(r[0]) && seen.add(r[0])); } }
  return {A, qmax, secs: T.secsP, one, maker: T.MKv ? {k: T.MK.k, name: T.MK.name} : null, plan: T.MKv ? 'maker' : T.R3 ? T.R3.kind : '', star};
}
export {pdbMatch, jsccRow, relBuild, fitOf, REGION, CAPN};
`;
const code = STUB + 'let GDB=null,PDB=null;\n' + chunks.filter(c => !/^let (GDB|PDB)=/.test(c)).join('\n') + '\n' + MATCH;

rmSync(join(here, 'src/gen'), {recursive: true, force: true});
mkdirSync(join(here, 'src/gen'), {recursive: true});
writeFileSync(join(here, 'src/gen/site.js'), '// 自動生成（api/build.mjs）。直すときは tools/template.html を直し、index.html を作り直す\n' + code);

// 確かめ：本物のデータで何件か流し、宣言の取りこぼし（〜 is not defined）がないこと
const ctx = vm.createContext({console});
const P = JSON.parse(readFileSync(join(root, 'data/products.json'), 'utf8')), C = JSON.parse(readFileSync(join(root, 'data/companies.json'), 'utf8'));
vm.runInContext(code.replace(/^export function /gm, 'globalThis.').replace(/^globalThis\.(\w+)\(/gm, 'globalThis.$1=function(').replace(/^export \{[^}]*\};$/m, ''), ctx);
ctx.setData(C, P);
const cases = JSON.parse(readFileSync(join(root, 'tools/tests/match_cases.json'), 'utf8'));
const texts = cases.map(c => c.file ? readFileSync(join(root, 'tools/tests/specs', c.file), 'utf8') : c.text);
for (const t of [...texts, 'セントバーナード用のスマートカラーを作りたい', 'かばんつくりたい', '千葉県で犬の車椅子を1台', 'ギター', '化粧水を1000本', '看板', 'LEDのデスクライト', '草刈りロボット',
  '【製品名】\n小型犬用の折りたたみスロープ\n\n【4. 材質】\n木製', 'コーヒー豆を入れるキャニスター']) {
  const r = ctx.siteMatch(t);
  if (!r || !r.A) throw new Error('siteMatch が動きません: ' + t);
}
console.log('api/src/gen/site.js を作りました（宣言 ' + chunks.length + '個・' + code.length + '字）');
