/* Keep the SQL explanation separate from the dashboard's data and chart code. */
window.updateQueryPanel = (queries, path) => {
  const list = document.getElementById('query-list');
  list.replaceChildren();
  document.getElementById('query-action').textContent = 'Data request: ' + path;
  queries.forEach((query, index) => {
    const detail = document.createElement('details');
    detail.open = index === 0;
    const summary = document.createElement('summary');
    summary.textContent = 'Query ' + (index + 1);
    const sql = document.createElement('pre');
    sql.textContent = query.sql;
    const values = document.createElement('pre');
    values.textContent = 'Bound values\n' + JSON.stringify(query.parameters ?? {}, null, 2);
    detail.append(summary, sql, values);
    list.append(detail);
  });
};

function describeLocalAction(text) {
  document.getElementById('query-action').textContent = text + ' — no new SQL query. The query definitions below produced the displayed data.';
}

document.addEventListener('click', event => {
  if (event.target.closest('[data-chart-point], .share-choice, .chart-choice')) describeLocalAction('Selected a chart value');
  if (event.target.closest('#theme-toggle')) describeLocalAction('Changed appearance');
  if (event.target.closest('summary')) describeLocalAction('Expanded or collapsed details');
  if (event.target.closest('a[href*="format="]')) {
    document.getElementById('query-action').textContent = 'Export requested — uses this report’s SQL and bound values; cached results may be reused.';
  }
});
document.getElementById('filters').addEventListener('change', () => describeLocalAction('Edited filters; Apply filters runs the data request'));

window.setupChartZoom = () => {
  const svg = document.querySelector('#report-visual .report-line, #overview-monthly .report-line');
  if (!svg) return;
  const points = [...svg.querySelectorAll('circle')];
  const monthlySelection = document.getElementById('monthly-selection');
  if (monthlySelection) points.forEach(point => {
    point.setAttribute('role', 'button');
    point.setAttribute('aria-label', 'Show exact orders for ' + point.dataset.month);
    point.setAttribute('aria-controls', 'monthly-selection');
    point.addEventListener('click', () => {
      monthlySelection.textContent = point.dataset.month + ': ' + new Intl.NumberFormat('en').format(Number(point.dataset.value)) + ' orders';
      describeLocalAction('Selected a month');
    });
    point.addEventListener('keydown', event => {
      if (!event.shiftKey && (event.key === 'Enter' || event.key === ' ')) {
        event.preventDefault(); point.dispatchEvent(new MouseEvent('click', {bubbles:true}));
      }
    });
  });
  if (points.length < 2) return;
  const values = points.map(point => Number(point.dataset.value));
  const labels = [...svg.querySelectorAll('text')];
  let first = 0, last = points.length - 1, anchor = null, dragged = false;
  svg.setAttribute('role', 'group');
  svg.setAttribute('aria-label', 'Monthly chart. Drag to select a range, double-click a point to zoom, or use the month selectors. Escape resets.');
  const controls = document.createElement('div');
  controls.className = 'range-zoom';
  controls.innerHTML = '<p>Drag across months or double-click a point to zoom into the values. A single click shows exact values.</p><label>From month<select class="zoom-from"></select></label><label>Through month<select class="zoom-through"></select></label><button type="button" class="zoom-apply">Zoom to range</button><button type="button" class="zoom-reset">Reset zoom</button><output aria-live="polite"></output>';
  svg.before(controls);
  const from = controls.querySelector('.zoom-from'), through = controls.querySelector('.zoom-through');
  points.forEach((point, index) => {
    from.add(new Option(point.dataset.month, index));
    through.add(new Option(point.dataset.month, index));
    point.addEventListener('keydown', event => {
      if (event.key === 'Enter' && event.shiftKey) { event.preventDefault(); zoomAround(index); }
    });
  });
  function setRange(start, end) {
    first = Math.min(start, end); last = Math.max(start, end);
    if (first === last) { first = Math.max(0, first - 1); last = Math.min(points.length - 1, last + 1); }
    const maximum = Math.max(1, ...values.slice(first, last + 1));
    const coordinates = [];
    points.forEach((point, index) => {
      const visible = index >= first && index <= last;
      point.style.display = visible ? '' : 'none';
      point.setAttribute('tabindex', visible ? '0' : '-1');
      if (!visible) return;
      const x = 50 + (index - first) * 700 / (last - first), y = 230 - values[index] * 190 / maximum;
      point.setAttribute('cx', x); point.setAttribute('cy', y);
      coordinates.push(x + ',' + y);
    });
    svg.querySelector('polyline').setAttribute('points', coordinates.join(' '));
    svg.querySelector('polygon')?.setAttribute('points', '50,230 ' + coordinates.join(' ') + ' 750,230');
    labels.slice(0, 3).forEach((label, index) => { label.textContent = new Intl.NumberFormat('en', {maximumFractionDigits:1}).format(maximum * (2-index)/2); });
    labels.at(-2).textContent = points[first].dataset.month;
    labels.at(-1).textContent = points[last].dataset.month;
    from.value = first; through.value = last;
    controls.querySelector('output').textContent = points[first].dataset.month + ' – ' + points[last].dataset.month + ' · ' + (last-first+1) + ' months';
  }
  function zoomAround(index) {
    const count = Math.max(2, Math.ceil((last-first+1)/2));
    const start = Math.max(first, Math.min(index - Math.floor(count/2), last-count+1));
    setRange(start, start+count-1);
    describeLocalAction('Zoomed into a month range');
  }
  const reset = () => { setRange(0, points.length-1); describeLocalAction('Reset chart range'); };
  controls.querySelector('.zoom-reset').addEventListener('click', reset);
  controls.querySelector('.zoom-apply').addEventListener('click', () => { setRange(Number(from.value), Number(through.value)); describeLocalAction('Selected a month range'); });
  svg.addEventListener('keydown', event => { if (event.key === 'Escape') reset(); });
  const xAt = event => {
    const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse());
    return Math.max(50, Math.min(750, p.x));
  };
  const indexAt = x => first + Math.round((x-50)/700*(last-first));
  const brush = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  brush.setAttribute('class', 'range-brush'); brush.setAttribute('y', '40'); brush.setAttribute('height', '190');
  brush.setAttribute('width', '0'); brush.setAttribute('aria-hidden', 'true'); svg.append(brush);
  svg.addEventListener('pointerdown', event => {
    if (event.button !== 0 || !event.isPrimary) return;
    anchor = xAt(event); dragged = false;
  });
  svg.addEventListener('pointermove', event => {
    if (anchor === null) return;
    const x = xAt(event);
    if (Math.abs(x-anchor) > 8) {
      dragged = true;
      svg.setPointerCapture(event.pointerId);
      brush.setAttribute('x', Math.min(anchor,x)); brush.setAttribute('width', Math.abs(x-anchor));
    }
  });
  svg.addEventListener('pointerup', event => {
    if (anchor === null) return;
    const start = indexAt(anchor), end = indexAt(xAt(event)); anchor = null;
    brush.setAttribute('width','0');
    if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
    if (dragged) { setRange(start,end); describeLocalAction('Selected a month range'); }
  });
  svg.addEventListener('pointercancel', () => { anchor = null; dragged = false; brush.setAttribute('width','0'); });
  svg.addEventListener('pointerleave', () => { if (!dragged) anchor = null; });
  svg.addEventListener('click', event => { if (dragged) { event.stopImmediatePropagation(); dragged = false; } }, true);
  svg.addEventListener('dblclick', event => { event.preventDefault(); zoomAround(indexAt(xAt(event))); });
  setRange(0,points.length-1);
};
