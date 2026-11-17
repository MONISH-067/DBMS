import fs from 'node:fs/promises';
import {FileBlob,PresentationFile} from '@oai/artifact-tool';
const file='A:/DBMS/CAPSTONE PROJECT/CODE/Olist_Capstone_Review.pptx';
const p=await PresentationFile.importPptx(await FileBlob.load(file));
const reports=[];for(let i=1;i<=10;i++){const r=await fetch('http://127.0.0.1:8503/api/reports/R'+String(i).padStart(2,'0'));reports.push(await r.json());}
const names={AC:'Acre',AL:'Alagoas',AM:'Amazonas',AP:'Amapá',BA:'Bahia',CE:'Ceará',DF:'Distrito Federal',ES:'Espírito Santo',GO:'Goiás',MA:'Maranhão',MG:'Minas Gerais',MS:'Mato Grosso do Sul',MT:'Mato Grosso',PA:'Pará',PB:'Paraíba',PE:'Pernambuco',PI:'Piauí',PR:'Paraná',RJ:'Rio de Janeiro',RN:'Rio Grande do Norte',RO:'Rondônia',RR:'Roraima',RS:'Rio Grande do Sul',SC:'Santa Catarina',SE:'Sergipe',SP:'São Paulo',TO:'Tocantins'};
const configs=[
['line','Monthly order volume',r=>r.order_month,[['Orders',r=>+r.order_count]]],
['doughnut','Order status share',r=>r.order_status,[['Orders',r=>+r.order_count]]],
['bar','Orders by state',r=>names[r.state]||r.state,[['Orders',r=>+r.order_count]]],
['doughnut','Payment value by method',r=>r.payment_type,[['Payment value (BRL)',r=>+r.total_value]]],
['area','Average delivery days by month',r=>r.order_month,[['Days',r=>+r.avg_delivery_days]]],
['bar','On-time and late deliveries by state',r=>names[r.state]||r.state,[['On time',r=>+(r.delivery_outcome==='on_time'?r.cnt:0)],['Late',r=>+(r.delivery_outcome==='late'?r.cnt:0)]]],
['treemap','Revenue by product category',r=>r.category_name_en,[['Revenue (BRL)',r=>+r.total_revenue]]],
['bar','Average freight by state (BRL)',r=>names[r.state]||r.state,[['Freight (BRL)',r=>+r.avg_freight]]],
['bar','Orders by delivery duration',r=>r.delivery_bucket,[['Orders',r=>+r.order_count]]],
['bar','Average review score by delivery outcome',r=>r.delivery_outcome,[['Review score (out of 5)',r=>+r.avg_review_score]]]
];
const colors=['#4A7E63','#6F9FCF','#D49A72','#C7B56C','#CC8292','#68B5B3','#A4AD7C','#AB8EAD','#648D8C','#AF825D'];
const titles=p.slides.items.map(s=>s.shapes.items.map(x=>x.text?.text||'').find(Boolean)||'');
const old=p.slides.items;
const added=[];
for(let k=0;k<10;k++){
 const [type,title,label,seriesFns]=configs[k],rows=reports[k].rows,s=p.slides.add();s.background.fill='#ffffff';
 s.images.add({path:'A:/DBMS/CAPSTONE PROJECT/CODE/.presentation-build/left.png',position:{left:0,top:0,width:100,height:120}});
 s.images.add({path:'A:/DBMS/CAPSTONE PROJECT/CODE/.presentation-build/right.png',position:{left:830,top:0,width:130,height:120}});
 const t=s.shapes.add({geometry:'textbox',position:{left:105,top:25,width:730,height:82}});t.text='R'+String(k+1).padStart(2,'0')+' · '+reports[k].title;t.text.style={typeface:'Times New Roman',fontSize:36,bold:true,color:'#000000',alignment:'center'};
 const desc=s.shapes.add({geometry:'textbox',position:{left:70,top:112,width:820,height:40}});desc.text='•  '+reports[k].description;desc.text.style={typeface:'Times New Roman',fontSize:20,color:'#000000'};
 const categories=rows.map(label);
 const series=seriesFns.map(([name,fn],j)=>({name,categories,values:rows.map(fn),fill:colors[(k+j)%colors.length]}));
 s.charts.add(type,{position:{left:90,top:165,width:780,height:320},title,hasLegend:series.length>1||k===1||k===3,series,categories,barOptions:{direction:'bar',grouping:'clustered',varyColors:series.length===1},doughnutOptions:{holeSize:58},dataLabels:{showValue:true,showPercent:type==='doughnut',position:'outEnd',textStyle:{typeface:'Times New Roman',fontSize:13}}});
 s.speakerNotes.text=reports[k].sql+'\nSource: MySQL report '+reports[k].id+' from the current project dashboard.';
 added.push(s);
}
const order=[...old.slice(0,15),...added,...old.slice(15)];p.slides.reorder(order.map(s=>s.id));
const draft='A:/DBMS/CAPSTONE PROJECT/CODE/.presentation-output/Olist_Capstone_Visualizations.draft.pptx';await (await PresentationFile.exportPptx(p)).save(draft);
console.log('slides',p.slides.items.length,'added charts',added.length,draft);
