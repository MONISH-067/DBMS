const byId = id => document.getElementById(id);

const params = new URLSearchParams(location.search);

const views = {

  overview: ["Overview", "Orders, revenue and delivery performance across Brazil."],

  orders: ["Orders", "Find an order and inspect how it was fulfilled."],

  reports: ["Reports", "Analyze marketplace activity and export the results."],

  database: ["Database", "Trace the analysis to the normalized MySQL schema and views."],

};

const view = Object.hasOwn(views, params.get("view")) ? params.get("view") : "overview";

const filterKeys = ["start_date", "end_date", "state", "q", "outcome", "status", "category"];

const form = byId("filters");

const content = byId("content");

const number = new Intl.NumberFormat("en", {maximumFractionDigits: 1});

const money = new Intl.NumberFormat("en", {style: "currency", currency: "BRL"});

const format = (value, formatter = number) => value == null ? "—" : formatter.format(value);

const escape = value => String(value ?? "—").replace(/[&<>"']/g, char => ({

  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",

})[char]);

const label = value => String(value).replaceAll("_", " ").replace(/^./, char => char.toUpperCase());



function url(path, changes = {}, keep = filterKeys) {

  const search = new URLSearchParams();

  for (const key of keep) if (params.get(key)) search.set(key, params.get(key));

  for (const [key, value] of Object.entries(changes)) if (value != null && value !== "") search.set(key, value);

  return search.size ? path + "?" + search : path;

}

async function get(path) {

  const response = await fetch(path);

  const data = await response.json();

  if (!response.ok) throw new Error(data.error);

  if (data.queries) window.updateQueryPanel?.(data.queries, path);

  return data;

}

function table(rows, title, linkOrders = false) {

  if (!rows.length) return "<p>No records match this selection.</p>";

  const headers = Object.keys(rows[0]);

  return '<div class="data" tabindex="0" role="region" aria-label="' + escape(title) +

    '"><table><thead><tr>' + headers.map(key => '<th scope="col">' + escape(label(key)) + "</th>").join("") +

    "</tr></thead><tbody>" + rows.map(row => "<tr>" + headers.map(key => {

      const value = row[key];

      const detail = linkOrders && key === "order_id";

      const shown = typeof value === "number" ? format(value, /price|freight|payment_value|revenue/.test(key) ? money : number) : value;

      return '<td class="' + (typeof value === "number" ? 'numeric' : '') + '">' + (detail

        ? '<a href="' + escape(url("/", {view: "orders", order: value, page: params.get("page")})) + '">' + escape(value) + '</a>'

        : escape(key === "state" ? stateLabel(shown) : shown)) + "</td>";

    }).join("") + "</tr>").join("") + "</tbody></table></div>";

}

function panel(title, body) {

  return '<section class="panel"><h2>' + escape(title) + "</h2>" + body + "</section>";

}

function trend(rows) {

  if (!rows.length) return "<p>No orders match these filters.</p>";

  return '<div id="overview-monthly">' + reportChart(rows, 'order_count') +
    '<p id="monthly-selection" role="status">Select a month to see its exact order count.</p></div>' +
    '<details><summary>View monthly values</summary>' + table(rows, 'Monthly order volume') + '</details>';

}

const stateNames = {

  AC:"Acre", AL:"Alagoas", AM:"Amazonas", AP:"Amapá", BA:"Bahia", CE:"Ceará",

  DF:"Distrito Federal", ES:"Espírito Santo", GO:"Goiás", MA:"Maranhão",

  MG:"Minas Gerais", MS:"Mato Grosso do Sul", MT:"Mato Grosso", PA:"Pará",

  PB:"Paraíba", PE:"Pernambuco", PI:"Piauí", PR:"Paraná", RJ:"Rio de Janeiro",

  RN:"Rio Grande do Norte", RO:"Rondônia", RR:"Roraima", RS:"Rio Grande do Sul",

  SC:"Santa Catarina", SE:"Sergipe", SP:"São Paulo", TO:"Tocantins",

};

const stateLabel = code => stateNames[code] ? stateNames[code] + " (" + code + ")" : code;

const displayLabel = value => stateNames[value] ? stateLabel(value) : label(value);

for (const [code, name] of Object.entries(stateNames).sort((a,b) => a[1].localeCompare(b[1])))

  byId("state").add(new Option(name + " (" + code + ")", code));

for (const key of filterKeys) form.elements[key].value = params.get(key) ?? "";

for (const name of ["start_date", "end_date"]) {

  const input = form.elements[name];

  input.min = "2016-09-04";

  input.max = "2018-10-17";

  if (input.value && input.value < input.min) input.value = input.min;

  if (input.value && input.value > input.max) input.value = input.max;

}

const periods = document.createElement("div");

periods.className = "periods";

periods.setAttribute("aria-label", "Dataset year shortcuts");

periods.innerHTML = '<span>Dataset period</span>' + ["All years", "2016", "2017", "2018"].map(year =>

  '<button type="button" data-year="' + year + '">' + year + '</button>').join("");

form.prepend(periods);

periods.addEventListener("click", event => {

  const year = event.target.dataset.year;

  if (!year) return;

  form.elements.start_date.value = year === "All years" || year === "2016" ? "2016-09-04" : year + "-01-01";

  form.elements.end_date.value = year === "All years" || year === "2018" ? "2018-10-17" : year + "-12-31";

  form.requestSubmit();

});



function enableFilters(names, extras = {}) {

  form.hidden = false;

  for (const key of filterKeys) {

    const input = form.elements[key];

    input.disabled = !names.includes(key);

    input.closest("label").hidden = input.disabled;

  }

  byId("reset").href = url("/", {view, ...extras}, []);

  form.addEventListener("submit", event => {

    event.preventDefault();

    const values = Object.fromEntries(new FormData(form));

    if (values.start_date && values.end_date && values.start_date > values.end_date) {

      byId("message").textContent = "Start date must be on or before the end date.";

      form.elements.end_date.focus();

      return;

    }

    location.href = url("/", {view, ...extras, ...values}, []);

  });

}



async function showOverview() {

  enableFilters(["start_date", "end_date", "state"]);

  const data = await get(url("/api/overview"));

  const {metrics, monthly, outcomes} = data;

  const cards = [

    ["Orders", format(metrics.orders)],

    ["Item revenue", format(metrics.revenue, money)],

    ["Avg delivery time", metrics.delivery_days == null ? "—" : format(metrics.delivery_days) + " days"],

    ["Avg review score", metrics.review == null ? "—" : format(metrics.review) + " / 5"],

  ];

  const colors = {on_time:"#68b5a0", late:"#d49a72", not_delivered:"#6f9fcf"};

  let angle = 0;

  const segments = outcomes.map(row => {

    const start = angle;

    angle += metrics.orders ? row.orders / metrics.orders * 360 : 0;

    return colors[row.outcome] + " " + start + "deg " + angle + "deg";

  });

  const bars = outcomes.length ? '<div class="donut-wrap"><div class="donut" role="img" aria-label="Delivery outcome shares; choose a category below to inspect orders" style="background:conic-gradient(' + segments.join(",") + ')"><div><strong>' + escape(format(metrics.orders)) + '</strong><span>orders</span></div></div></div><ul class="outcome-cards">' + outcomes.map(row =>

    '<li><a href="' + escape(url("/", {view:"orders", outcome:row.outcome})) + '" style="--outcome-color:' + colors[row.outcome] + '"><span class="color-key" aria-hidden="true"></span><span>' + escape(label(row.outcome)) +

    '</span><strong>' + escape(format(row.orders)) + '</strong><small>' + escape(format(metrics.orders ? row.orders / metrics.orders * 100 : 0)) + '% · View orders →</small></a></li>').join("") + "</ul>" : "<p>No orders match these filters.</p>";

  content.innerHTML = '<div class="metrics">' + cards.map(([name,value]) =>

    '<div class="metric"><span>' + escape(name) + '</span><strong>' + escape(value) + "</strong></div>").join("") +

    '</div><div class="grid">' + panel("Monthly orders", trend(monthly)) + panel("Delivery outcomes", bars) + "</div>";

}



async function showOrders() {

  const order = params.get("order");

  if (order) {

    byId("heading").textContent = "Order details";

    const data = await get("/api/orders/" + encodeURIComponent(order));

    const {city, state, order_status, delivery_outcome, ...timeline} = data.order;

    delete timeline.order_id;

    byId("intro").textContent = [city, stateLabel(state), label(order_status), label(delivery_outcome)].join(" · ");

    content.innerHTML = '<div class="stack"><a class="button" href="' + escape(url("/", {view:"orders", page:params.get("page")})) +

      '">Back to orders</a>' + panel("Delivery timeline", "<p><code>" + escape(order) + "</code></p><dl>" +

      Object.entries(timeline).map(([key,value]) => "<dt>" + escape(label(key)) + "</dt><dd>" + escape(value) + "</dd>").join("") + "</dl>") +

      panel("Items", table(data.items, "Order items")) + panel("Payments", table(data.payments, "Order payments")) +

      panel("Reviews", table(data.reviews, "Order reviews")) + "</div>";

    return;

  }

  enableFilters(filterKeys.slice(0,5));

  const page = Number(params.get("page") ?? "1");

  const data = await get(url("/api/orders", {page}));

  content.innerHTML = panel("Order records", table(data.rows, "Order records", true) +

    '<nav class="pager" aria-label="Order pages">' +

    (page > 1 ? '<a class="button" href="' + escape(url("/", {view, page:page - 1})) + '">Previous page</a>' : "") +

    "<span>Page " + page + "</span>" +

    (data.has_more ? '<a class="button" href="' + escape(url("/", {view, page:page + 1})) + '">Next page</a>' : "") + "</nav>");

}



const donutColors = ["#6f9fcf", "#d49a72", "#68b5b3", "#c7b56c", "#cc8292", "#87b397", "#ab8ead", "#919eae"];

const reportColors = ["#68b5a0", "#6f9fcf", "#d49a72", "#c7b56c", "#cc8292", "#68b5b3", "#a4ad7c", "#ab8ead"];


function distinctGraphic(rows,id) {
  const legend=(name,key)=>'<div class="chart-legend">'+rows.map((row,i)=>'<button class="chart-choice" data-row-index="'+i+'"><span class="color-key" style="background:'+reportColors[i%8]+'"></span>'+ (i+1)+'. '+escape(label(row[name]))+'<strong>'+escape(format(row[key],money))+'</strong></button>').join('')+'</div>';
  if(id==='R04') {
    const total=rows.reduce((sum,row)=>sum+Number(row.total_value||0),0);
    if(!total)return '<p>No payment value to plot.</p>';
    let end=0;
    const shares=rows.map((row,i)=>{const start=end;end+=Number(row.total_value||0)/total*100;return {start,end,color:reportColors[i%8]};});
    return '<p class="chart-unit">Payment value composition. Each square is 1%; partial squares preserve small shares.</p><div class="waffle-chart" role="img" aria-label="Payment method shares">'+Array.from({length:100},(_,i)=>{
      const stops=shares.filter(s=>s.end>i&&s.start<i+1).flatMap(s=>[s.color+' '+Math.max(0,(s.start-i)*100)+'%',s.color+' '+Math.min(100,(s.end-i)*100)+'%']);
      return '<span style="background:linear-gradient(to right,'+stops.join(',')+')"></span>';
    }).join('')+'</div>'+legend('payment_type','total_value');
  }
  if(id==='R07') {
    const boxes=[];
    const split=(items,x,y,w,h)=>{
      if(items.length===1){boxes[items[0].i]={x,y,w,h};return;}
      const total=items.reduce((sum,item)=>sum+item.value,0);
      let cut=1,subtotal=items[0].value;
      while(cut<items.length-1&&subtotal<total/2)subtotal+=items[cut++].value;
      const ratio=total?subtotal/total:cut/items.length;
      if(w>=h){split(items.slice(0,cut),x,y,w*ratio,h);split(items.slice(cut),x+w*ratio,y,w*(1-ratio),h);}
      else{split(items.slice(0,cut),x,y,w,h*ratio);split(items.slice(cut),x,y+h*ratio,w,h*(1-ratio));}
    };
    split(rows.map((row,i)=>({i,value:Math.max(0,Number(row.total_revenue)||0)})),0,0,800,400);
    return '<p class="chart-unit">Area represents revenue within the top categories. Numbers match the legend.</p><svg class="treemap-chart" viewBox="0 0 800 400" role="group" aria-label="Category revenue treemap">'+boxes.map((b,i)=>'<g class="chart-choice" data-row-index="'+i+'"><title>'+escape(label(rows[i].category_name_en)+': '+format(rows[i].total_revenue,money))+'</title><rect x="'+b.x+'" y="'+b.y+'" width="'+b.w+'" height="'+b.h+'" fill="'+reportColors[i%8]+'" stroke="var(--card)" stroke-width="3"/><text x="'+(b.x+b.w/2)+'" y="'+(b.y+b.h/2)+'" text-anchor="middle" fill="#111" font-size="22">'+(i+1)+'</text></g>').join('')+'</svg>'+legend('category_name_en','total_revenue');
  }
  if(id==='R10') {
    return '<p class="chart-unit">Average customer rating out of five stars. Partial stars represent the exact average.</p><div class="star-rating-chart">'+rows.map((row,i)=>{
      const score=Math.max(0,Math.min(5,Number(row.avg_review_score)||0));
      const stars=Array.from({length:5},(_,star)=>{
        const fill=Math.max(0,Math.min(1,score-star))*100;
        const shape='<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2 15.1 8.3 22 9.3 17 14.2 18.2 21 12 17.8 5.8 21 7 14.2 2 9.3 8.9 8.3Z" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>';
        return '<span class="rating-star" style="--star-delay:'+(i*120+star*110)+'ms;--star-percent:'+fill+'%" aria-hidden="true">'+shape+'<span class="rating-star-fill">'+shape+'</span></span>';
      }).join('');
      return '<button type="button" class="chart-choice star-rating-row" data-row-index="'+i+'"><span class="rating-outcome">'+escape(label(row.delivery_outcome))+'</span><span class="rating-stars" aria-hidden="true">'+stars+'</span><strong>'+escape(new Intl.NumberFormat("en",{maximumFractionDigits:20}).format(score))+' / 5</strong><small>'+escape(format(row.review_count))+' reviews</small></button>';
    }).join('')+'</div>';
  }
  if(id==='R08'){
    const key='avg_freight';
    const max=Math.max(1,...rows.map(row=>Number(row[key])||0));
    return '<p class="chart-unit">Average freight in BRL; stems start at zero</p><div class="lollipop-chart">'+rows.map((row,i)=>'<button class="chart-choice plot-row" data-row-index="'+i+'"><span>'+escape(stateLabel(row.state))+'</span><span class="plot-track" style="--point:'+Math.max(0,Number(row[key])||0)/max*100+'%;--plot-color:'+reportColors[i%8]+'"><span class="plot-stem"></span><span class="plot-dot"></span></span><strong>'+escape(format(row[key],money))+'</strong></button>').join('')+'<div class="plot-axis"><span>0</span><span>'+escape(format(max,money))+'</span></div></div>';
  }
  return null;
}

function reportGraphic(rows, id) {

  if (!rows.length) return "<p>No data matches these filters.</p>";

  const distinct = distinctGraphic(rows, id);
  if (distinct !== null) return distinct;
  if (id === "R02") {

    const name = id === "R02" ? "order_status" : "payment_type";

    const value = id === "R02" ? "order_count" : "total_value";

    const formatter = id === "R02" ? number : money;

    const total = rows.reduce((sum, row) => sum + Number(row[value] ?? 0), 0);

    if (total <= 0) return reportChart(rows);

    let angle = -Math.PI / 2;

    const slices = rows.map((row, index) => {

      const share = Number(row[value] ?? 0) / total;

      const start = angle;

      angle += share * Math.PI * 2;

      const middle = (start + angle) / 2;

      const point = (radius, theta) => [150 + radius * Math.cos(theta), 150 + radius * Math.sin(theta)].join(" ");

      const large = share > 0.5 ? 1 : 0;

      const color = donutColors[index % donutColors.length];

      const shape = share >= 0.999999999

        ? '<circle cx="150" cy="150" r="100" fill="none" stroke="' + color + '" stroke-width="44"/>'

        : '<path d="M ' + point(122,start) + ' A 122 122 0 ' + large + ' 1 ' + point(122,angle) + ' L ' + point(78,angle) + ' A 78 78 0 ' + large + ' 0 ' + point(78,start) + ' Z" fill="' + color + '"/>';

      return '<g class="donut-slice" data-index="' + index + '" style="--slice-x:' + Math.cos(middle)*10 + 'px;--slice-y:' + Math.sin(middle)*10 +

        'px"><title>' + escape(label(row[name]) + ": " + format(share*100) + "%") + '</title>' + (share > 0 ? shape : "") + '</g>';

    }).join("");

    return '<div class="share-chart"><div class="donut-wrap"><div class="slice-donut"><svg viewBox="0 0 300 300" role="img" aria-label="' + escape(id === "R02" ? "Order status shares" : "Payment value shares") +

      '">' + slices + '</svg><div class="slice-center"><strong id="share-value">100%</strong><span id="share-name" aria-live="polite">All categories</span></div></div></div><ul class="share-legend">' +

      rows.map((row, index) => {

        const share = format(Number(row[value] ?? 0) / total * 100) + "%";

        return '<li><button type="button" class="share-choice" aria-pressed="false" data-index="' + index + '" style="--slice-color:' + donutColors[index % donutColors.length] + '" data-share="' + escape(share) + '" data-name="' + escape(label(row[name])) +

          '"><span class="color-key" style="background:' + donutColors[index % donutColors.length] + '" aria-hidden="true"></span><span>' + escape(label(row[name])) +

          '</span><strong>' + escape(share) + '</strong><small>' + escape(format(row[value], formatter)) +

          (id === "R04" ? " · " + escape(format(row.payment_count)) + " payments" : " orders") + '</small></button></li>';

      }).join("") + '</ul></div><p class="chart-hint">Select a category to inspect its share.</p>';

  }

  if (id === "R06") {

    const states = [...new Set(rows.map(row => row.state))];

    const maximum = Math.max(1, ...rows.map(row => Number(row.cnt)));

    return '<p class="chart-unit">Delivered orders · teal = on time · coral = late</p><div class="delivery-groups">' + states.map(state =>

      '<section class="delivery-group"><h3>' + escape(stateLabel(state)) + '</h3>' +

      ["on_time", "late"].map(outcome => {

        const count = rows.find(row => row.state === state && row.delivery_outcome === outcome)?.cnt ?? 0;

        return '<div class="bar-row" tabindex="0"><span>' + escape(label(outcome)) + '</span><div class="bar-track"><div class="bar-fill" style="background:' +

          (outcome === "on_time" ? "#68b5a0" : "#d49a72") + ';width:' + count / maximum * 100 + '%"></div></div><strong>' + escape(format(count)) + '</strong></div>';

      }).join("") + '</section>').join("") + '</div>';

  }

  if (id === "R09") {

    const maximum = Math.max(1, ...rows.map(row => row.order_count));

    return '<p class="chart-unit">Orders by delivery duration</p><div class="histogram" role="group" aria-label="Delivery duration distribution">' + rows.map((row, i) =>

      '<div class="histogram-bin" tabindex="0"><strong>' + escape(format(row.order_count)) + '</strong><div class="histogram-track"><div style="height:' +

      row.order_count / maximum * 100 + '%;background:' + reportColors[i % reportColors.length] + '"></div></div><span>' + escape(row.delivery_bucket) + '</span></div>').join("") + '</div>';

  }

  const valueKeys = {R01:"order_count", R03:"order_count", R05:"avg_delivery_days", R07:"total_revenue", R08:"avg_freight"};

  return reportChart(rows, valueKeys[id], id === "R05");

}



function reportChart(rows, metric, area = false) {

  if (!rows.length) return "<p>No data matches these filters.</p>";

  const keys = Object.keys(rows[0]);

  const valueKey = metric || keys.find((key, index) => index > 0 && rows.some(row => typeof row[key] === "number"));

  if (!valueKey) return "";

  const maximum = Math.max(1, ...rows.map(row => Number(row[valueKey]) || 0));

  const monthly = keys[0].includes("month");

  if (monthly) {

    const points = rows.map((row, index) => [50 + index * 700 / Math.max(1, rows.length - 1), 230 - Number(row[valueKey] || 0) * 190 / maximum]);

    return '<p class="chart-unit">' + escape(label(valueKey)) + '</p><svg class="report-line' + (area ? ' area-chart' : '') + '" viewBox="0 0 800 280" role="img" aria-label="' + escape(label(valueKey) + " by month; exact values in Report data") + '">' +

      [40, 135, 230].map((y, i) => '<path d="M50 ' + y + 'H750" stroke="#dce4e8"/><text x="42" y="' + (y + 4) + '" text-anchor="end" font-size="11" fill="#526775">' + escape(format(maximum * (2-i)/2)) + '</text>').join("") +

      (area ? '<polygon points="50,230 ' + points.map(p => p.join(",")).join(" ") + ' 750,230" fill="#dceceb"/>' : '') + '<polyline points="' + points.map(p => p.join(",")).join(" ") + '" fill="none" stroke="#087f79" stroke-width="3"/>' +

      points.map(([x,y], i) => '<circle data-month="' + escape(rows[i][keys[0]]) + '" data-value="' + Number(rows[i][valueKey] || 0) + '" cx="' + x + '" cy="' + y + '" r="4" fill="#087f79" tabindex="0"><title>' + escape(rows[i][keys[0]] + ": " + format(rows[i][valueKey])) + '</title></circle>').join("") +

      '<text x="50" y="260" font-size="12" fill="#526775">' + escape(rows[0][keys[0]]) + '</text><text x="750" y="260" text-anchor="end" font-size="12" fill="#526775">' + escape(rows.at(-1)[keys[0]]) + '</text></svg>';

  }

  return '<p class="chart-unit">' + escape(label(valueKey)) + '</p><div class="report-bars">' + rows.map((row, i) =>

    '<div class="bar-row" tabindex="0"><span>' + escape(keys.slice(0, keys.indexOf(valueKey)).map(key => displayLabel(row[key] ?? "Unknown")).join(" · ")) +

    '</span><div class="bar-track"><div class="bar-fill tone-' + i % 3 + '" style="width:' + Math.max(0, Number(row[valueKey]) / maximum * 100) +

    '%"></div></div><strong>' + escape(format(row[valueKey], /revenue|freight/.test(valueKey) ? money : number)) + '</strong></div>').join("") + '</div>';

}



async function showReports() {

  const reports = await get("/api/reports");

  const report = reports.find(item => item.id === params.get("report")) ?? reports[0];

  enableFilters(report.filters, {report:report.id});

  const selected = await get(url("/api/reports/" + report.id));

  const links = ["csv", "xlsx", "pdf"].map(ext => '<a class="button" href="' +

    escape(url("/api/reports/" + report.id, {format:ext})) + '">Download ' + (ext === "xlsx" ? "Excel" : ext.toUpperCase()) + '</a>').join("");

  content.innerHTML = '<div class="stack"><label>Choose a report<select id="report">' + reports.map(item =>

    '<option value="' + item.id + '"' + (item.id === report.id ? " selected" : "") + ">" +

    escape(item.id + " · " + item.title) + "</option>").join("") + '</select></label>' +

    panel(report.title, "<p>" + escape(report.description) + '</p><div class="actions">' + links +

      '</div><div id="report-visual">' + reportGraphic(selected.rows, report.id) + '</div><section class="chart-selection" aria-live="polite" aria-label="Selected chart values"><h3>Explore a data point</h3><p>Click a chart element or use Tab and Enter to see its exact values.</p></section><details><summary>View exact values</summary>' +

      table(selected.rows, report.title) + '</details><details><summary>View report SQL</summary><pre>' +

      escape(selected.sql) + "</pre></details>") + "</div>";

  const exactNumber = new Intl.NumberFormat("en", {maximumFractionDigits: 20});

  const exactMoney = new Intl.NumberFormat("en", {style:"currency", currency:"BRL", minimumFractionDigits:2, maximumFractionDigits:20});

  const selection = content.querySelector(".chart-selection");

  selection.id = "selected-chart-values";

  selection.hidden = true;

  let selectionAnimation;

  const showExact = (row, element) => {

    if (!row) return;

    selection.innerHTML = '<h3>Selected values</h3><dl>' + Object.entries(row).map(([key,value]) => {

      const numeric = typeof value === "number";

      const monetary = /revenue|freight|total_value|payment_value/.test(key);

      const shown = value == null ? "Not available" : numeric

        ? (monetary ? exactMoney : exactNumber).format(value)

        : key === "state" ? stateLabel(value) : label(value);

      return '<dt>' + escape(label(key)) + '</dt><dd>' + escape(shown) + '</dd>';

    }).join("") + '</dl>';

    const anchor = element.closest(".histogram") || element.closest("svg") || element;

    anchor.insertAdjacentElement("afterend", selection);

    selection.hidden = false;

    selectionAnimation?.cancel();

    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {

      selectionAnimation = selection.animate(

        [{opacity:0, transform:"translateY(-6px)"}, {opacity:1, transform:"translateY(0)"}],

        {duration:220, easing:"cubic-bezier(0.16, 1, 0.3, 1)"}

      );

    }

    content.querySelectorAll("[data-chart-point]").forEach(point => {

      const active = point === element;

      point.classList.toggle("chart-point-selected", active);

      point.setAttribute("aria-pressed", String(active));

      point.setAttribute("aria-expanded", String(active));

    });

  };

  const pointSelector = ["R04", "R07", "R08", "R10"].includes(report.id) ? ".chart-choice"
    : report.id === "R02" ? ".share-choice"

    : report.id === "R09" ? ".histogram-bin"

    : report.id === "R01" || report.id === "R05" ? ".report-line circle"

    : ".bar-row";

  content.querySelectorAll(pointSelector).forEach((point,index) => {

    let row = selected.rows[point.dataset.rowIndex ?? index];

    if (report.id === "R06") {

      const group = point.closest(".delivery-group");

      const state = [...new Set(selected.rows.map(item => item.state))][[...group.parentElement.children].indexOf(group)];

      const outcome = index % 2 === 0 ? "on_time" : "late";

      row = selected.rows.find(item => item.state === state && item.delivery_outcome === outcome)

        ?? {state, delivery_outcome:outcome, cnt:0};

    }

    if (!row) return;

    point.dataset.chartPoint = String(index);

    point.setAttribute("aria-label", "Show exact values for " + Object.entries(row).filter(([,v]) => typeof v !== "number").map(([k,v]) => k === "state" ? stateLabel(v) : label(v)).join(", "));

    point.setAttribute("aria-pressed","false");

    point.setAttribute("aria-expanded","false");

    point.setAttribute("aria-controls","selected-chart-values");

    if (point.tagName.toLowerCase() !== "button") {

      point.setAttribute("role","button");

      point.setAttribute("tabindex","0");

      point.addEventListener("keydown", event => {

        if (event.key === "Enter" || event.key === " ") {

          event.preventDefault();

          point.dispatchEvent(new MouseEvent("click", {bubbles:true}));

        }

      });

    }

    point.addEventListener("click", () => showExact(row, point));

  });

  content.querySelectorAll(".share-choice").forEach(button => {

    const inspect = () => {

      byId("share-value").textContent = button.dataset.share;

      byId("share-name").textContent = button.dataset.name;

      content.querySelectorAll(".share-choice").forEach(item => {

        item.classList.toggle("selected", item === button);

        item.setAttribute("aria-pressed", String(item === button));

      });

      content.querySelectorAll(".donut-slice").forEach(slice => {

        slice.classList.toggle("selected", slice.dataset.index === button.dataset.index);

        slice.classList.toggle("muted", slice.dataset.index !== button.dataset.index);

      });

    };

    button.addEventListener("click", inspect);

    button.addEventListener("focus", inspect);



  });

  content.querySelectorAll(".donut-slice").forEach(slice => {

    slice.addEventListener("click", () => content.querySelector('.share-choice[data-index="' + slice.dataset.index + '"]').click());

  });

  byId("report").addEventListener("change", event => { location.href = url("/", {view, report:event.target.value}, filterKeys.slice(0,3)); });

}



async function showDatabase() {

  const data = await get("/api/schema");

  const entities = new Map();

  for (const row of data.columns) {

    if (!entities.has(row.entity)) entities.set(row.entity, []);

    entities.get(row.entity).push(row);

  }

  const definition = name => ({

    v_delivery_performance: "Connects orders to customer locations and compares actual and estimated delivery.",

    v_order_summary: "Aggregates item count, item prices and freight by order.",

  })[name] ?? "View registered in MySQL.";

  content.innerHTML = '<div class="stack">' + panel("How the data is organized", "<p>The ETL loads nine Olist CSVs into MySQL. Foreign keys connect orders to customers and items to products and sellers. Payments and reviews reference the order independently so either can have multiple records.</p>") +

    panel("MySQL views", table(data.views.map(({name}) => ({view:name, purpose:definition(name)})), "MySQL views")) +

    panel("Foreign keys", table(data.relationships, "Foreign keys")) +

    panel("Tables and columns", Array.from(entities, ([name, columns]) => "<details><summary>" +

      escape(name) + "</summary>" + table(columns.map(({field,type,key_type}) => ({field,type,key:key_type || "—"})), name) + "</details>").join("")) + "</div>";

}



byId("heading").textContent = views[view][0];

byId("intro").textContent = views[view][1];

document.title = views[view][0] + " · Marketplace Operations";

document.querySelector('[data-view="' + view + '"]').setAttribute("aria-current", "page");

byId("message").textContent = "Loading marketplace data…";

({overview:showOverview, orders:showOrders, reports:showReports, database:showDatabase})[view]()

  .then(() => { byId("message").textContent = ""; window.setupChartZoom?.(); })

  .catch(error => {
    byId("message").textContent = error.message || "Unable to load marketplace data.";
    byId("query-action").textContent = "The data request failed. No query result is available for this action.";
  });

