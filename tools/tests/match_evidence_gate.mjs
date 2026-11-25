// Private synthetic regression contract; no user RFQ text or network.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const root=path.resolve(process.argv[2] || '.');
const {siteMatch,setData}=await import(pathToFileURL(path.join(root,'api/src/gen/site.js')));
setData(...['companies','products'].map(x=>JSON.parse(fs.readFileSync(path.join(root,'data',x+'.json')))));
const electronic=c=>/^(electronics|sensing|software)\./.test(c);
const battery=c=>c==='testing.battery_safety';
const animal=c=>c==='testing.animal_trial';
const radio=c=>c==='testing.radio_cert';
const tests=[
 ['generic-noun','装置',[],c=>electronic(c)||battery(c)||animal(c)],
 ['synthetic-vehicle-animal-as-context','犬用の装置。架空車種VA-01で使用。試作1台。',[],c=>electronic(c)||battery(c)||animal(c)],
 ['manual-vehicle-control','手動式の装置を試作1台。架空の車種VA-01に補助具を載せる。',[],c=>electronic(c)||battery(c)||animal(c)],
 ['electric-not-battery','電動モーターで押し出す。商用電源を使用。電池は不要。',[],c=>battery(c)||radio(c)||animal(c)],
 ['ble-firmware-battery-positive','BLE通信対応の基板設計とファームウェア開発、リチウムイオン電池の安全試験が必要。',['electronics.pcb_design','electronics.firmware','electronics.wireless','testing.battery_safety'],animal],
 ['animal-as-context-with-electronics','犬用の温度ロガー。BLE対応基板とファームウェアの開発を依頼する。',['electronics.pcb_design','electronics.firmware','electronics.wireless'],animal],
 ['explicit-animal-trial','犬の移動補助具と獣医監修の動物試験を依頼する。',['testing.animal_trial'],c=>electronic(c)||battery(c)],
 ['timed-control-positive','時刻になったら布を送り出してくれる装置を作りたい。',['electronics.pcb_design','electronics.firmware'],animal],
 ['timing-is-not-control','装置を1台。納品時刻になったら担当者が受け取ります。',[],c=>electronic(c)||battery(c)||animal(c)],
 ['battery-positive','リチウムイオン電池の安全試験が必要。',['testing.battery_safety'],animal],
];
const lift='作業用の手動リフト、試作1台、設計図なし';
const base=siteMatch(lift);
for(const suffix of ['、電池なし','、電子制御なし','、電池・電子制御なし','、電池・電子制御は使わない']){
 const candidate=siteMatch(lift+suffix);
 for(const key of ['plan','one','maker']) assert.deepEqual(candidate[key],base[key],suffix+' '+key);
 assert.deepEqual(candidate.A.codes,base.A.codes,suffix+' capabilities');
}
console.log('PASS paired exclusions preserve engineering scope and candidate ranking');
let failed=0;
for (const [id,t,required,exclude] of tests){
 const a=siteMatch(t).A, bad=a.codes.filter(exclude), missed=required.filter(c=>!a.codes.includes(c));
 const pass=!bad.length&&!missed.length;
 failed+=!pass;
 console.log(JSON.stringify({id,pass,bad,missed,mach:a.mach,byShape:a.byShape,byPdb:a.byPdb,words:a.words}));
}
console.log(`${tests.length-failed}/${tests.length} passing`);
if(failed)process.exitCode=1;
