import fs from 'node:fs/promises';
import sharp from 'sharp';
import {FileBlob,PresentationFile} from '@oai/artifact-tool';

const root='A:/DBMS/CAPSTONE PROJECT/CODE';
const live=root+'/.presentation-build/live';
const crops=root+'/.presentation-build/crops';
await fs.mkdir(crops,{recursive:true});
const deck=await PresentationFile.importPptx(await FileBlob.load(root+'/.presentation-output/Olist_Capstone_Titled.draft.pptx'));
for(const slide of deck.slides.items)for(const shape of slide.shapes.items){
  if(String(shape.text||'').includes('A custom local website provides filters'))shape.text='•  A deployed website provides filters and order details.';
  if(String(shape.text||'').includes('Custom local website connected to MySQL.'))shape.text='•  Deployed website connected to live MySQL.';
}
const shots={2:'overview',3:'orders',4:'R01',5:'database',6:'overview',7:'database',8:'database',9:'database',10:'R07',11:'R10',12:'overview',13:'orders',25:'R10',26:'database',27:'overview',28:'R04',29:'overview',31:'overview'};
for(const [index,shot] of Object.entries(shots)){
  const slide=deck.slides.items[Number(index)];
  const bullets=slide.shapes.items.filter(x=>String(x.text||'').startsWith('•'));
  if(!bullets.length)continue;
  const count=bullets.length;
  bullets.forEach((shape,i)=>{
    shape.position={left:55,top:145+i*(345/count),width:420,height:345/count};
    shape.text.style={typeface:'Times New Roman',fontSize:count>5?19:21,color:'#000000'};
  });
  const src=live+'/'+shot+'.jpg';
  const meta=await sharp(src).metadata();
  const crop=shot==='overview'?{left:270,top:375,width:940,height:810}:shot==='database'?{left:270,top:365,width:940,height:Math.min(800,meta.height-365)}:shot==='orders'?{left:270,top:350,width:940,height:Math.min(780,meta.height-350)}:shot==='R10'?{left:295,top:655,width:895,height:Math.min(350,meta.height-655)}:{left:295,top:665,width:895,height:Math.min(470,meta.height-665)};
  const dest=crops+'/content-'+index+'.png';
  await sharp(src).extract(crop).resize(800,600,{fit:'contain',background:'#ffffff'}).png().toFile(dest);
  slide.images.add({blob:new Uint8Array(await fs.readFile(dest)),contentType:'image/png',alt:'Live '+shot+' dashboard screenshot',position:{left:490,top:145,width:420,height:330}});
}
for(let i=1;i<=10;i++){
  const name='R'+String(i).padStart(2,'0');
  const src=live+'/'+name+'.jpg';
  const meta=await sharp(src).metadata();
  const crop=i===4?{left:465,top:680,width:560,height:450}:i===10?{left:295,top:688,width:895,height:248}:i===7?{left:295,top:670,width:895,height:450}:{left:295,top:670,width:895,height:Math.min(410,meta.height-670)};
  const dest=crops+'/'+name+'.png';
  await sharp(src).extract(crop).resize(1400,620,{fit:'contain',background:'#ffffff'}).png().toFile(dest);
  deck.slides.items[14+i].images.add({blob:new Uint8Array(await fs.readFile(dest)),contentType:'image/png',alt:'Live '+name+' chart screenshot',position:{left:75,top:158,width:810,height:345}});
}
const output=root+'/Olist_Capstone_Review_Final.pptx';
await (await PresentationFile.exportPptx(deck)).save(output);
console.log(output,deck.slides.items.length);
