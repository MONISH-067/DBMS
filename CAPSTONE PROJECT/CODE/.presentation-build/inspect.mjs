import fs from 'node:fs';
import {getDocument} from 'pdfjs-dist/legacy/build/pdf.mjs';
const pdf=await getDocument({data:new Uint8Array(fs.readFileSync('C:/Users/Monish/Downloads/CAPSTONE PP TEMPLATE.pdf')),useSystemFonts:true}).promise;
for(let i=1;i<=pdf.numPages;i++){const p=await pdf.getPage(i);const t=await p.getTextContent(); console.log(JSON.stringify({page:i,size:p.view,text:t.items.map(x=>x.str).join('\n')}));}
