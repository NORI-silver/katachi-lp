// 空き枠×時期の幅×小口まとめ（backend/forms.gs の slot*_）の回帰テスト。 node tools/tests/slot_cases.js
const fs=require('fs'),vm=require('vm'),path=require('path');
const ctx={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../backend/forms.gs'),'utf8'),ctx);
const N=ym=>ctx.slotN_(ym),Y=n=>ctx.slotYm_(n),now=N('2026-11');let ng=0;
const eq=(name,got,want)=>{const g=JSON.stringify(got),w=JSON.stringify(want);console.log((g===w?'OK ':'NG ')+name+(g===w?'':`  got ${g} want ${w}`));if(g!==w)ng++};
// 希望の時期の読み取り
eq('2027年3月',Y(ctx.slotDue_('2027年3月までに試作品',now)),'2027-03');
eq('2月（来年に回る）',Y(ctx.slotDue_('2月中',now)),'2027-02');
eq('3か月以内',Y(ctx.slotDue_('3か月以内',now)),'2027-02');
eq('6週間',Y(ctx.slotDue_('6週間で',now)),'2027-01');
eq('年内',Y(ctx.slotDue_('年内',now)),'2026-12');
eq('読めない',ctx.slotDue_('なるべく早く',now),null);
// 期間
const W=r=>ctx.slotWin_(r,now).map(Y);
eq('動かせない',W({flex:'fixed',due:'2027年1月'}),['2026-11','2027-01']);
eq('1か月前後',W({flex:'m1',due:'2027年3月'}),['2027-02','2027-04']);
eq('2〜3か月',W({flex:'m3',due:''}),['2026-11','2027-02']);
eq('急がない',W({flex:'any',due:''}),['2026-11','2027-05']);
eq('月の指定が優先',W({flex:'any',from:'2027-04',to:'2027-06'}),['2027-04','2027-06']);
// 数量・材料
eq('数量 範囲',ctx.slotQty_('試作 1〜10個'),10);eq('数量 カンマ',ctx.slotQty_('初回 3,000個'),3000);eq('数量 万',ctx.slotQty_('年1.2万個'),12000);
eq('材料 ABS',ctx.slotMatOk_('ABS樹脂','ABS、PP'),true);eq('材料 違う',ctx.slotMatOk_('SUS304','アルミ A5052'),false);eq('材料 未定は通す',ctx.slotMatOk_('わからない','綿'),true);
// 照らし合わせ：品目の違う5種類（樹脂成形・板金・縫製・基板実装・木工）
const slots=[
 {pid:'P1',company:'成形A',code:'molding.injection',mat:'ABS、PP',qmin:100,qmax:5000,from:'2027-01',to:'2027-02',disc:'目安 10%',bundleOk:true},
 {pid:'P2',company:'板金B',code:'metal.sheet',mat:'SUS304',qmin:0,qmax:300,from:'2026-12',to:'2026-12',disc:'',bundleOk:false},
 {pid:'P3',company:'縫製C',code:'textile.sewing',mat:'綿',qmin:50,qmax:0,from:'2027-02',to:'2027-03',disc:'値引きは相談可',bundleOk:true},
 {pid:'P4',company:'実装D',code:'electronics.pcba',mat:'',qmin:0,qmax:1000,from:'2027-01',to:'2027-01',disc:'',bundleOk:true},
 {pid:'P5',company:'木工E',code:'crafts.wood_furniture',mat:'ナラ',qmin:0,qmax:20,from:'2027-06',to:'2027-07',disc:'',bundleOk:false}];
const R=(id,codes,mat,qty,flex,due,bundle,extra)=>Object.assign({id,codes,mat,qty,flex,due,bundle,from:'',to:''},extra||{});
const reqs=[
 R('K1',['molding.injection'],'ABS','初回 500個','m3','',1),        // 2026-11〜2027-02 → P1と重なる
 R('K2',['molding.injection'],'ABS樹脂','300個','any','',1),        // まとめ候補 K1+K2
 R('K3',['molding.injection'],'ABS','50個','any','',1),             // 数量がP1の下限未満 → P1に合わない、まとめには入る
 R('K4',['metal.sheet'],'SUS304','20個','fixed','2026年12月',0),     // P2と12月で一致
 R('K5',['metal.sheet'],'アルミ','20個','any','',0),                 // 材料違い → 合わない
 R('K6',['textile.sewing'],'綿','100枚','m1','2027年3月',1),          // P3
 R('K7',['electronics.pcba','mechanical.enclosure_design'],'','試作 5台','fixed','2026年12月',0), // 12月までに必要 → 1月のP4に合わない
 R('K8',['crafts.wood_furniture'],'ナラ','2台','m3','',0),           // 6月の空きとは重ならない
 R('K9',['textile.sewing'],'綿','30枚','fixed','2026年11月',1),       // 期間が合わず縫製のまとめにも入らない
];
const res=ctx.slotMatch_(reqs,slots,now);
eq('空き枠に合う組',res.pairs.map(x=>x.req.id+'×'+x.slot.pid+' '+Y(x.over[0])+'〜'+Y(x.over[1])).sort(),['K1×P1 2027-01〜2027-02','K2×P1 2027-01〜2027-02','K4×P2 2026-12〜2026-12','K6×P3 2027-02〜2027-03']);
eq('まとめ候補',res.bundles.map(b=>b.code+':'+b.reqs.map(r=>r.id).join('+')+' '+Y(b.win[0])+'〜'+Y(b.win[1])+' 計'+b.qty+' '+b.slots.map(s=>s.pid).join(',')),['molding.injection:K1+K2+K3 2026-11〜2027-02 計850 P1']);
// 古い依頼：2026-05受付の「急がない」は 2026-11 までで終わり、今日から伸びない
eq('古い依頼は伸びない',ctx.slotMatch_([R('K0',['molding.injection'],'ABS','500個','any','',1,{recv:N('2026-05')})],slots,now).pairs.length,0);
console.log(ng?`${ng} NG`:'all OK');process.exit(ng?1:0);
