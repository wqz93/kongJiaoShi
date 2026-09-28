/* 在 Node 中用 vm 真实执行工具里的应用 JS，验证统计逻辑 */
const fs = require('fs'), vm = require('vm'), path = require('path');
const XLSX = require('xlsx');

const html = fs.readFileSync(path.join(__dirname, '..', 'outputs', '空教室查询工具.html'), 'utf8');
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const app = blocks[blocks.length - 1];
console.log('app script len:', app.length, '| blocks:', blocks.length);

/* --- DOM 桩 --- */
const mkEl = (id) => ({
  id, innerHTML: '', textContent: '', className: '', style: {}, dataset: {}, checked: false,
  value: id === 'target' ? '8' : (id === 'ovmin' ? '30' : ''),
  classList: { add() {}, remove() {}, contains: () => false },
  addEventListener() {}, removeEventListener() {}, appendChild() {}, remove() {},
  querySelectorAll: () => [], querySelector: () => null, scrollIntoView() {}, click() {}, files: [],
});
const els = {};
const document = {
  getElementById: id => (els[id] = els[id] || mkEl(id)),
  querySelector: () => ({ innerHTML: '/*css*/' }),
  querySelectorAll: () => [],
  createElement: () => mkEl('tmp'),
  body: { appendChild() {} },
};
const ctx = { XLSX, document, window: {}, console, setTimeout, Date, Math, JSON,
  Blob: function () {}, URL: { createObjectURL: () => 'blob:x', revokeObjectURL() {} } };
ctx.window = ctx; ctx.globalThis = ctx;
vm.createContext(ctx);

/* --- 载入应用代码 --- */
vm.runInContext(app, ctx);

/* --- 用真实 xls 数据驱动 --- */
const buf = fs.readFileSync("E:/桌面/temp1790577877287招生简章.xls");
const wb = XLSX.read(new Uint8Array(buf), { type: 'array', codepage: 936 });
const raw = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { header: 1, defval: '', raw: false, blankrows: false });

vm.runInContext('RAW = ' + JSON.stringify(raw) + '; detectHeader();', ctx);
const info = vm.runInContext('({hr: COLS._hr, region: COLS.region, time: COLS.time, room: COLS.room, name: COLS.name, teacher: COLS.teacher, rows: ROWS.length, head: HEADER.slice(0,6)})', ctx);
console.log('表头行(0基):', info.hr, '| 列映射 region/time/room/name/teacher =',
  info.region, info.time, info.room, info.name, info.teacher, '| 数据行:', info.rows);
console.log('表头片段:', JSON.stringify(info.head));

vm.runInContext('runStat();', ctx);
const R = vm.runInContext('({empty: RESULT.empty.length, regions: RESULT.regions, matrix: RESULT.matrix.map(r=>({区域:r.区域,教室:r.教室,已排:r.已排,空闲:r.空闲,达标:r.达标})), nonstd: RESULT.nonstd.length, target: RESULT.target})', ctx);

console.log('\n=== 校验 ===');
console.log('区域:', R.regions.join(' / '), '| 达标要求:', R.target);
console.log('周末空档条数:', R.empty, '(Python 结果 79)');
console.log('未匹配标准节次:', R.nonstd, '条（含工作日，故可能多于 Python 的 2 条）');
for (const rg of R.regions) {
  const s = R.matrix.filter(x => x.区域 === rg);
  console.log(`[${rg}] 教室 ${s.length} | 达标 ${s.filter(x => x.达标).length} | 有空档 ${s.filter(x => !x.达标).length} | 空档节次 ${s.reduce((a, x) => a + x.空闲, 0)}`);
}
const expect = { '厦港校区': [30, 13, 17, 43], '镇海校区': [21, 7, 14, 36] };
let ok = (R.empty === 79);
for (const rg of R.regions) {
  const s = R.matrix.filter(x => x.区域 === rg);
  const got = [s.length, s.filter(x => x.达标).length, s.filter(x => !x.达标).length, s.reduce((a, x) => a + x.空闲, 0)];
  const exp = expect[rg];
  const pass = exp && JSON.stringify(got) === JSON.stringify(exp);
  console.log(`  ${rg}: got ${JSON.stringify(got)} expect ${JSON.stringify(exp)} -> ${pass ? 'PASS' : 'FAIL'}`);
  if (!pass) ok = false;
}
/* --- 全周 / 工作日 / 晚课 统计 --- */
console.log('\n=== 全周 / 工作日 / 晚课 ===');
const W = vm.runInContext(`(() => {
  const wd = SHOWDAYS.filter(d => WORKDAYS.includes(d));
  const out = [];
  for (const rg of RESULT.regions) {
    const rooms = RESULT.roomsByRegion[rg];
    let wk = 0, ev = 0, all = 0;
    for (const rm of rooms) {
      for (const d of wd) for (const sl of RESULT.DLIST) if (get(rg, rm, d, sl.k).length) wk++;
      for (const d of SHOWDAYS) for (const sl of RESULT.ELIST) if (get(rg, rm, d, sl.k).length) ev++;
      for (const d of SHOWDAYS) for (const sl of RESULT.ALL) if (get(rg, rm, d, sl.k).length) all++;
    }
    const n = rooms.length;
    out.push({ 区域: rg, 教室: n,
      工作日: wk + '/' + (n * wd.length * RESULT.DLIST.length) + ' (' + Math.round(wk / (n * wd.length * RESULT.DLIST.length) * 100) + '%)',
      晚课: ev + '/' + (n * SHOWDAYS.length * RESULT.ELIST.length) + ' (' + Math.round(ev / (n * SHOWDAYS.length * RESULT.ELIST.length) * 100) + '%)',
      全周: all + '/' + (n * SHOWDAYS.length * RESULT.ALL.length) + ' (' + Math.round(all / (n * SHOWDAYS.length * RESULT.ALL.length) * 100) + '%)' });
  }
  return out;
})()`, ctx);
console.table(W);

/* --- 晚课 / 工作日 明细分布 --- */
const dist = vm.runInContext(`(() => {
  const out = {};
  for (const d of SHOWDAYS) {
    let ev = 0, day = 0;
    for (const rg of RESULT.regions) for (const rm of RESULT.roomsByRegion[rg]) {
      for (const sl of RESULT.ELIST) if (get(rg, rm, d, sl.k).length) ev++;
      for (const sl of RESULT.DLIST) if (get(rg, rm, d, sl.k).length) day++;
    }
    out[d] = { 白天占用: day, 晚课占用: ev };
  }
  return out;
})()`, ctx);
console.log('\n=== 各星期占用节次（两校区合计）===');
console.table(dist);

/* --- 四个视图渲染 --- */
console.log('\n=== 视图渲染 ===');
for (const v of ['weekend', 'full', 'workday', 'evening']) {
  try {
    vm.runInContext(`curView='${v}'; render();`, ctx);
    const len = ctx.document.getElementById('main').innerHTML.length;
    console.log(`视图 ${v}: OK (${len} 字符)`);
    if (len < 500) { ok = false; console.log('  !! 内容过短，可能异常'); }
  } catch (e) { ok = false; console.log(`视图 ${v} FAIL:`, e.message); }
}
try {
  vm.runInContext("curView='workday'; inclEve=true; render();", ctx);
  console.log('工作日+含晚课: OK (' + ctx.document.getElementById('main').innerHTML.length + ' 字符)');
  vm.runInContext("inclEve=false;", ctx);
} catch (e) { ok = false; console.log('含晚课切换 FAIL:', e.message); }
vm.runInContext("curView='weekend'; render();", ctx);

/* --- 导出冒烟测试 --- */
console.log('\n=== 导出冒烟 ===');
try { vm.runInContext('exportXlsx();', ctx); console.log('exportXlsx: OK'); } catch (e) { ok = false; console.log('exportXlsx FAIL:', e.message); }
try { vm.runInContext('window._curEmpty = RESULT.empty; exportCsv();', ctx); console.log('exportCsv: OK'); } catch (e) { ok = false; console.log('exportCsv FAIL:', e.message); }
try { vm.runInContext('exportHtml();', ctx); console.log('exportHtml: OK'); } catch (e) { ok = false; console.log('exportHtml FAIL:', e.message); }
const xf = fs.readdirSync(process.cwd()).filter(f => /^空教室统计_.*\.xlsx$/.test(f));
console.log('生成的 xlsx:', xf);
if (xf.length) {
  const b = XLSX.read(fs.readFileSync(xf[0]), { type: 'buffer' });
  console.log('  sheets:', b.SheetNames.join(' / '), '| 明细行数:', XLSX.utils.sheet_to_json(b.Sheets[b.SheetNames[0]]).length);
  fs.unlinkSync(xf[0]);
}
try { vm.runInContext("render();", ctx); console.log('render 二次调用: OK'); } catch (e) { ok = false; console.log('render FAIL:', e.message); }

console.log('\n总判定:', ok ? 'ALL PASS ✅' : 'FAIL ❌');
