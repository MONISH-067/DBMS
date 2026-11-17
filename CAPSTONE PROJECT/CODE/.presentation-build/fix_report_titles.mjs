import {FileBlob,PresentationFile} from '@oai/artifact-tool';
const file='A:/DBMS/CAPSTONE PROJECT/CODE/Olist_Capstone_Review.pptx';const p=await PresentationFile.importPptx(await FileBlob.load(file));
const titles=['Monthly Orders','Order Status Share','Top 10 States by Orders','Payment Type Share','Avg Delivery Days by Month','On-Time vs Late Deliveries by State','Revenue by Product Category Top 10','Avg Freight Value by State','Delivery-Time Distribution','Avg Review Score by Delivery Outcome'];
const descriptions=['Monthly order volume across the marketplace.','Distribution of orders by status.','Brazilian states ranked by order count.','Payment methods compared by transaction value.','Average delivery duration by purchase month.','Delivered order counts by state and outcome.','Top product categories ranked by revenue.','Average freight value by destination state.','Orders grouped by delivery duration.','Average customer rating by delivery outcome.'];
for(let i=0;i<10;i++){
 const slide=p.slides.items[15+i];
 const shapes=slide.shapes.items;
 shapes.find(x=>String(x.text).includes('R'+String(i+1).padStart(2,'0'))).text='R'+String(i+1).padStart(2,'0')+' · '+titles[i];
 shapes.find(x=>String(x.text).includes('undefined')).text='•  '+descriptions[i];
}
const draft='A:/DBMS/CAPSTONE PROJECT/CODE/.presentation-output/Olist_Capstone_Titled.draft.pptx';await (await PresentationFile.exportPptx(p)).save(draft);console.log('saved',draft,p.slides.items.length);
