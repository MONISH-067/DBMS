const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../marketplace/app.js'), 'utf8');
const helpers = source.slice(source.indexOf('const number ='), source.indexOf('function url('));
const states = source.slice(source.indexOf('const stateNames ='), source.indexOf('for (const [code, name]'));
const charts = source.slice(source.indexOf('const donutColors ='), source.indexOf('async function showReports'));
const context = vm.createContext({Intl});
vm.runInContext(helpers + states + charts, context);
(async () => {
  for (let i = 1; i <= 10; i++) {
    const id = 'R' + String(i).padStart(2, '0');
    const response = await fetch('http://127.0.0.1:8503/api/reports/' + id);
    assert.equal(response.status, 200);
    const {rows} = await response.json();
    assert.ok(rows.length, id + ' must have data');
    context.rows = rows;
    context.id = id;
    const html = vm.runInContext('reportGraphic(rows, id)', context);
    const types = {R01:'report-line',R02:'share-chart',R03:'report-bars',R04:'waffle-chart',R05:'area-chart',R06:'delivery-groups',R07:'treemap-chart',R08:'lollipop-chart',R09:'histogram',R10:'dot-chart'};
    assert.ok(html.includes(types[id]), id + ' expected ' + types[id]);
    if (id === 'R01') assert.ok(!html.includes('<polygon'));
    if (id === 'R05') assert.ok(html.includes('<polygon'));
    if (id === 'R04') assert.equal((html.match(/linear-gradient/g) || []).length, 100);
    if (id === 'R07') assert.equal((html.match(/<rect /g) || []).length, rows.length);
    assert.doesNotMatch(html, /NaN|Infinity|undefined/);
    if (id === 'R01' || id === 'R05') {
      assert.ok(rows.length > 1);
      assert.ok(rows.every(row => /^\d{4}-\d{2}$/.test(row.order_month)));
    }
    if (id === 'R10') assert.match(html, /fixed scale from 0 to 5/);
    context.rows = [];
    assert.match(vm.runInContext('reportGraphic(rows, id)', context), /No data matches/);
    console.log(id + ': chart rendered from live data; empty state passed');
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
