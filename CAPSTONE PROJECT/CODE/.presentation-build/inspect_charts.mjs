import fs from 'node:fs/promises';import {FileBlob,PresentationFile} from '@oai/artifact-tool';
const p=await PresentationFile.importPptx(await FileBlob.load('A:/DBMS/CAPSTONE PROJECT/CODE/Olist_Capstone_Review.pptx'));
console.log('slides',p.slides.items.length);
for(let i=14;i<27;i++){let s=p.slides.items[i];console.log(i+1,s.shapes.items.map(x=>x.text?.text).filter(Boolean).join(' | '),s.charts.items.map(c=>c.title));}
