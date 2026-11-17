import fs from 'node:fs/promises';
import {FileBlob,PresentationFile} from '@oai/artifact-tool';
const root='A:/DBMS/CAPSTONE PROJECT/CODE';
const deck=await PresentationFile.importPptx(await FileBlob.load(root+'/Olist_Capstone_Review_Final.pptx'));
const out=root+'/.presentation-build/review';await fs.mkdir(out,{recursive:true});
for(let i=0;i<deck.slides.items.length;i++){
 const blob=await deck.render({slide:i,format:'png',scale:1});
 await fs.writeFile(out+'/slide-'+String(i+1).padStart(2,'0')+'.png',new Uint8Array(await blob.arrayBuffer()));
}
console.log('rendered',deck.slides.items.length);
