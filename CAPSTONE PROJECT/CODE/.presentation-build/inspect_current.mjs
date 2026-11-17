import {FileBlob,PresentationFile} from '@oai/artifact-tool';const p=await PresentationFile.importPptx(await FileBlob.load('A:/DBMS/CAPSTONE PROJECT/CODE/.presentation-output/Olist_Capstone_Titled.draft.pptx'));let s=p.slides.items[15];for(const x of s.shapes.items)console.log({id:x.id,geom:x.geometry,pos:JSON.stringify(x.position),text:String(x.text),plain:x.text?.getText?.(),runs:x.text?.paragraphs?.items?.map(a=>a.runs?.items?.map(r=>r.text))});


