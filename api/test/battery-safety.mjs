import assert from 'node:assert/strict';
import fs from 'node:fs';
import {pathToFileURL,fileURLToPath} from 'node:url';
const r=fileURLToPath(new URL('../../',import.meta.url)).replace(/\/$/,'');
const {siteMatch,setData}=await import(pathToFileURL(r+'/api/src/gen/site.js'));
setData(...['companies','products'].map(n=>JSON.parse(fs.readFileSync(r+'/data/'+n+'.json'))));
const tests=[
 ['architectural-access','屋外の段差を越える金属のスロープ。滑り止めと安全な固定。1台。',false],
 ['warehouse-transfer','荷物を手動で棚へ段階移乗する装置。完全には吊り上げない。試作1台。',false],
 ['wearable-sensor','設備の振動を測る装着型センサー。基板・ファームウェア・筐体の試作1台。',false,['electronics.pcb_design','electronics.firmware']],
 ['mains','商用電源の電動モーターで作業する。電池は使わない。',false],
 ['low-power','低消費電力の基板と充電式バッテリーを使用。装置全体の落下安全性を確認。',false],
 ['battery-tests-ja','リチウムイオン電池の安全試験を委託したい。',true],
 ['battery-tests-en','Battery safety testing is required.',true],
 ['battery-tests-zh','需要进行电池安全测试。',true],
 ['certification','電池輸送向けにUN 38.3の試験を依頼。',true],
 ['negative','電池の安全試験は不要。センサーと基板だけ。',false],
 ['negative-en','Battery safety testing is not required. Design the PCB.',false],
 ['future','基板を試作。\n【将来的な追加】\n電池の安全試験。',false],
];
for(const [name,s,want,required=[]] of tests){
 const codes=siteMatch(s).A.codes;
 assert.equal(codes.includes('testing.battery_safety'),want,name+': '+codes);
 for(const code of required)assert.ok(codes.includes(code),name+': '+code);
}
console.log(`PASS ${tests.length}/${tests.length} anonymized scenarios/controls`);
