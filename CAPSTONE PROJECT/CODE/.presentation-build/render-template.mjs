import fs from 'node:fs';import {getDocument} from 'pdfjs-dist/legacy/build/pdf.mjs';import {createCanvas} from '@napi-rs/canvas';
const pdf=await getDocument({data:new Uint8Array(fs.readFileSync('C:/Users/Monish/Downloads/CAPSTONE PP TEMPLATE.pdf')),useSystemFonts:true}).promise;
const canvas=createCanvas(960*4,540*6),ctx=canvas.getContext('2d');
for(let i=1;i<=pdf.numPages;i++){const p=await pdf.getPage(i),v=p.getViewport({scale:1}),c=createCanvas(v.width,v.height);await p.render({canvasContext:c.getContext('2d'),viewport:v}).promise;fs.writeFileSync(`.presentation-build/template-${i}.png`,c.toBuffer('image/png'));ctx.drawImage(c,((i-1)%4)*960,Math.floor((i-1)/4)*540);if(i===3){console.log(JSON.stringify((await p.getTextContent()).items.slice(0,8)));}}
fs.writeFileSync('.presentation-build/template-montage.png',canvas.toBuffer('image/png'));
