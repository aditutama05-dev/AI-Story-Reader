(() => {
"use strict";
const DB_NAME="ai-story-reader-library-db-v1";
const LEGACY_KEY="ai-story-reader-library-v1";
const $=id=>document.getElementById(id);
const status=$("libraryStatus");
let dbPromise=null;
let seriesState=[];
const id=()=>crypto.randomUUID?crypto.randomUUID():"item-"+Date.now()+"-"+Math.random().toString(36).slice(2);
function openDB(){
 if(!("indexedDB" in window))return Promise.reject(new Error("IndexedDB tidak tersedia pada browser ini."));
 if(dbPromise)return dbPromise;
 dbPromise=new Promise((resolve,reject)=>{
  const request=indexedDB.open(DB_NAME,1);
  request.onupgradeneeded=()=>{if(!request.result.objectStoreNames.contains("state"))request.result.createObjectStore("state",{keyPath:"id"})};
  request.onsuccess=()=>resolve(request.result);
  request.onerror=()=>reject(request.error||new Error("Database perpustakaan gagal dibuka."));
 });
 return dbPromise;
}
async function loadState(){
 const db=await openDB();
 const saved=await new Promise((resolve,reject)=>{
  const request=db.transaction("state","readonly").objectStore("state").get("library");
  request.onsuccess=()=>resolve(request.result?.series||[]);
  request.onerror=()=>reject(request.error||new Error("Gagal membaca perpustakaan."));
 });
 if(saved.length){seriesState=saved;return}
 try{
  const legacy=JSON.parse(localStorage.getItem(LEGACY_KEY)||"[]");
  if(Array.isArray(legacy)&&legacy.length){await persist(legacy);localStorage.removeItem(LEGACY_KEY)}
 }catch(error){status.textContent="Cadangan perpustakaan lama tidak dapat dimigrasikan: "+error.message}
}
async function persist(next){
 const db=await openDB();
 await new Promise((resolve,reject)=>{
  const tx=db.transaction("state","readwrite");
  tx.objectStore("state").put({id:"library",series:next,updatedAt:new Date().toISOString()});
  tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error||new Error("Gagal menyimpan perpustakaan."));tx.onabort=()=>reject(tx.error||new Error("Penyimpanan dibatalkan."));
 });
 seriesState=next;render();
}
function read(){return seriesState}
function render(){
 const tree=$("libraryTree");if(!tree)return;
 tree.replaceChildren();
 if(!seriesState.length){tree.textContent="Perpustakaan masih kosong. Buat seri pertama untuk mulai mengelompokkan cerita.";return}
 for(const s of seriesState){
  const box=document.createElement("details");box.className="library-series";box.open=true;
  const summary=document.createElement("summary");summary.textContent=s.title+" ("+(s.arcs||[]).reduce((n,a)=>n+(a.volumes||[]).reduce((m,v)=>m+(v.chapters||[]).length,0),0)+" chapter)";box.append(summary);
  const actions=document.createElement("div");actions.className="library-actions";
  const addArc=document.createElement("button");addArc.className="secondary";addArc.textContent="Tambah arc";addArc.onclick=()=>safe(()=>addArcTo(s.id));
  const rename=document.createElement("button");rename.className="secondary";rename.textContent="Ubah seri";rename.onclick=()=>safe(()=>renameSeries(s.id));
  const remove=document.createElement("button");remove.className="secondary";remove.textContent="Hapus seri";remove.onclick=()=>safe(()=>removeSeries(s.id));
  actions.append(addArc,rename,remove);box.append(actions);
  for(const a of s.arcs||[]){
   const arc=document.createElement("details");arc.className="library-arc";arc.open=true;
   const as=document.createElement("summary");as.textContent="Arc: "+a.title;arc.append(as);
   const aa=document.createElement("div");aa.className="library-actions";
   const av=document.createElement("button");av.className="secondary";av.textContent="Tambah volume";av.onclick=()=>safe(()=>addVolume(s.id,a.id));
   const ar=document.createElement("button");ar.className="secondary";ar.textContent="Ubah arc";ar.onclick=()=>safe(()=>renameNode(s.id,a.id,"arc"));
   aa.append(av,ar);arc.append(aa);
   for(const v of a.volumes||[]){
    const vol=document.createElement("div");vol.className="library-volume";
    const vh=document.createElement("strong");vh.textContent="Volume: "+v.title;vol.append(vh);
    const va=document.createElement("div");va.className="library-actions";
    const ch=document.createElement("button");ch.className="secondary";ch.textContent="Tambah chapter";ch.onclick=()=>safe(()=>addChapter(s.id,a.id,v.id));
    const vr=document.createElement("button");vr.className="secondary";vr.textContent="Ubah volume";vr.onclick=()=>safe(()=>renameNode(s.id,v.id,"volume"));
    va.append(ch,vr);vol.append(va);
    for(const chapter of v.chapters||[]){
     const row=document.createElement("div");row.className="library-chapter";
     const open=document.createElement("button");open.className="secondary";open.textContent="Buka "+(chapter.partType||"Chapter")+": "+chapter.title;open.onclick=()=>openChapter(chapter);
     const narration=document.createElement("button");narration.className="secondary";narration.textContent="Buka narasi";narration.disabled=!chapter.narration;narration.onclick=()=>safe(()=>openNarration(chapter));
     const del=document.createElement("button");del.className="secondary";del.textContent="Hapus";del.onclick=()=>safe(()=>deleteChapter(s.id,a.id,v.id,chapter.id));
     const notes=document.createElement("button");notes.className="secondary";notes.textContent="Catatan kontinuitas";notes.onclick=()=>safe(()=>editNotes(s.id,a.id,v.id,chapter.id));row.append(open,narration,notes,del);vol.append(row);if(chapter.notes){const note=document.createElement("p");note.className="hint";note.textContent="Catatan: "+chapter.notes;vol.append(note)}
    }
    arc.append(vol);
   }
   box.append(arc);
  }
  tree.append(box);
 }
}
async function safe(action){try{await action()}catch(error){status.textContent="Operasi perpustakaan gagal: "+error.message}}
function ask(label,initial=""){const value=prompt(label,initial);return value===null?null:value.trim()}
async function addSeries(){const title=ask("Nama seri / judul karya:");if(!title)return;await persist([...read(),{id:id(),title,arcs:[],createdAt:new Date().toISOString()}]);status.textContent="Seri ditambahkan."}
async function addArcTo(sid){const title=ask("Nama arc:");if(!title)return;const all=read().map(s=>s.id===sid?{...s,arcs:[...(s.arcs||[]),{id:id(),title,volumes:[]}]}:s);await persist(all)}
async function addVolume(sid,aid){const title=ask("Nama atau nomor volume:");if(!title)return;const all=read().map(s=>s.id!==sid?s:{...s,arcs:s.arcs.map(a=>a.id!==aid?a:{...a,volumes:[...(a.volumes||[]),{id:id(),title,chapters:[]}]})});await persist(all)}
async function addChapter(sid,aid,vid){const partType=ask("Jenis bagian (Chapter, Interlude, Ending, Epilogue, Prologue, Side Story, Other):","Chapter");if(!partType)return;const title=ask("Nama atau nomor bagian:");if(!title)return;const all=read().map(s=>s.id!==sid?s:{...s,arcs:s.arcs.map(a=>a.id!==aid?a:{...a,volumes:a.volumes.map(v=>v.id!==vid?v:{...v,chapters:[...(v.chapters||[]),{id:id(),partType,title,originalSource:"",narration:"",notes:"",createdAt:new Date().toISOString()}]})})});await persist(all);status.textContent="Bagian cerita dibuat. Impor atau tempel teks sumber, lalu buat narasi."}
async function renameSeries(sid){const all=read(),s=all.find(x=>x.id===sid),title=ask("Nama seri:",s.title);if(!title)return;await persist(all.map(x=>x.id===sid?{...x,title}:x))}
async function renameNode(sid,nid,type){let found=false;const all=read().map(s=>s.id!==sid?s:{...s,arcs:s.arcs.map(a=>{if(type==="arc"&&a.id===nid){found=true;const title=ask("Nama arc:",a.title);return title?{...a,title}:a}return {...a,volumes:a.volumes.map(v=>{if(type==="volume"&&v.id===nid){found=true;const title=ask("Nama volume:",v.title);return title?{...v,title}:v}return v})}})});if(found)await persist(all)}
async function removeSeries(sid){if(!confirm("Hapus seri beserta semua arc, volume, dan chapter di dalamnya?"))return;await persist(read().filter(s=>s.id!==sid))}
async function editNotes(sid,aid,vid,cid){const all=read();let current="";for(const s of all)if(s.id===sid)for(const a of s.arcs||[])if(a.id===aid)for(const v of a.volumes||[])if(v.id===vid)for(const ch of v.chapters||[])if(ch.id===cid)current=ch.notes||"";const notes=prompt("Catatan kontinuitas chapter ini (tokoh, relasi, lokasi, istilah, kejadian):",current);if(notes===null)return;const updated=all.map(s=>s.id!==sid?s:{...s,arcs:s.arcs.map(a=>a.id!==aid?a:{...a,volumes:a.volumes.map(v=>v.id!==vid?v:{...v,chapters:v.chapters.map(ch=>ch.id===cid?{...ch,notes,notesUpdatedAt:new Date().toISOString()}:ch)})})});await persist(updated)}
async function deleteChapter(sid,aid,vid,cid){if(!confirm("Hapus chapter ini?"))return;const all=read().map(s=>s.id!==sid?s:{...s,arcs:s.arcs.map(a=>a.id!==aid?a:{...a,volumes:a.volumes.map(v=>v.id!==vid?v:{...v,chapters:v.chapters.filter(c=>c.id!==cid)})})});await persist(all)}
function buildContinuityContext(chapterId){
 let selected=null,selectedSeries=null,ordered=[];
 for(const series of read()){
  const parts=[];
  for(const arc of series.arcs||[])for(const volume of arc.volumes||[])for(const chapter of volume.chapters||[])parts.push(chapter);
  const index=parts.findIndex(chapter=>chapter.id===chapterId);
  if(index>=0){selected=parts[index];selectedSeries=series;ordered=parts.slice(0,index);break}
 }
 if(!selected||!selectedSeries)return "";
 const entries=ordered.filter(chapter=>chapter.notes?.trim()).slice(-12).map(chapter=>"- "+(chapter.partType||"Chapter")+" "+chapter.title+": "+chapter.notes.trim());
 if(selected.notes?.trim())entries.push("- Catatan bagian aktif ("+(selected.partType||"Chapter")+" "+selected.title+"): "+selected.notes.trim());
 if(!entries.length)return "";
 return ("Seri: "+selectedSeries.title+"\\n"+entries.join("\\n")).slice(0,12000);
}
function openChapter(chapter){$("title").value=chapter.title;$("source").value=chapter.originalSource||chapter.text||"";window.currentLibraryChapterId=chapter.id;status.textContent="Teks sumber asli dimuat ke editor. Narasi tersimpan terpisah.";$("editor-heading").scrollIntoView({behavior:"smooth"});$("source").focus()}
async function openNarration(chapter){if(!chapter.narration)return;$("title").value=chapter.title;window.currentLibraryChapterId=chapter.id;await window.restoreStoryNarration?.(chapter.title,chapter.narration,chapter.id);status.textContent="Narasi tersimpan dibuka. Progres dan bookmark chapter ini dipulihkan secara terpisah.";$("result-heading").scrollIntoView({behavior:"smooth"})}
async function saveChapter(title,narration,originalSource){
 let found=false;
 let next=read().map(s=>({...s,arcs:(s.arcs||[]).map(a=>({...a,volumes:(a.volumes||[]).map(v=>({...v,chapters:(v.chapters||[]).map(ch=>{
  const selected=window.currentLibraryChapterId&&ch.id===window.currentLibraryChapterId&&ch.title===title;
  const titleMatch=!window.currentLibraryChapterId&&ch.title===title;
  if(selected||titleMatch){found=true;return {...ch,narration,originalSource:originalSource||ch.originalSource||"",updatedAt:new Date().toISOString()}}
  return ch;
 })}))}))}));
 if(!found){
  if(!next.length)next.push({id:id(),title:"Cerita saya",arcs:[]});
  let series=next[0];if(!series.arcs)series.arcs=[];
  if(!series.arcs.length)series.arcs.push({id:id(),title:"Arc 1",volumes:[]});
  let arc=series.arcs[0];if(!arc.volumes)arc.volumes=[];
  if(!arc.volumes.length)arc.volumes.push({id:id(),title:"Volume 1",chapters:[]});
  const chapterId=id();
  arc.volumes[0].chapters.push({id:chapterId,partType:"Chapter",title,originalSource:originalSource||"",narration,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()});
  window.currentLibraryChapterId=chapterId;
 }
 await persist(next);
 status.textContent="Sumber asli dan narasi disimpan terpisah di perpustakaan.";
}
function exportLibrary(){const blob=new Blob([JSON.stringify({format:"ai-story-reader-library",version:1,exportedAt:new Date().toISOString(),series:read()},null,2)],{type:"application/json"});const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="ai-story-reader-library.json";a.click();URL.revokeObjectURL(url);status.textContent="Cadangan perpustakaan diunduh."}
async function importLibrary(file){if(!file)return;try{const data=JSON.parse(await file.text()),items=Array.isArray(data)?data:data.series;if(!Array.isArray(items))throw new Error("Format cadangan tidak dikenali.");const current=read(),merged=[...current,...items.filter(item=>item&&item.id&&!current.some(old=>old.id===item.id))];await persist(merged);status.textContent="Cadangan berhasil digabung ke perpustakaan."}catch(error){status.textContent="Impor cadangan gagal: "+error.message}}
$("addSeries").addEventListener("click",()=>safe(addSeries));
$("exportLibrary").addEventListener("click",exportLibrary);
$("importLibrary").addEventListener("change",event=>safe(()=>importLibrary(event.target.files[0])));
window.storyLibrary={saveChapter,render,getContinuityContext:buildContinuityContext};
status.textContent="Memuat perpustakaan cerita...";
$("addSeries").disabled=true;$("exportLibrary").disabled=true;$("importLibrary").disabled=true;
loadState().then(()=>{render();$("addSeries").disabled=false;$("exportLibrary").disabled=false;$("importLibrary").disabled=false;status.textContent="Perpustakaan siap. Data disimpan di IndexedDB perangkat ini."}).catch(error=>{status.textContent="Perpustakaan tidak dapat dibuka: "+error.message;render()});
})();