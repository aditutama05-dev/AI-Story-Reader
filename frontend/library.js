(() => {
"use strict";
const KEY="ai-story-reader-library-v1";
const $=id=>document.getElementById(id);
const status=$("libraryStatus");
const read=()=>{try{const value=JSON.parse(localStorage.getItem(KEY)||"[]");return Array.isArray(value)?value:[]}catch{return []}};
const write=value=>localStorage.setItem(KEY,JSON.stringify(value));
const id=()=>crypto.randomUUID?crypto.randomUUID():"item-"+Date.now()+"-"+Math.random().toString(36).slice(2);
const esc=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
function render(){
 const tree=$("libraryTree");if(!tree)return;
 const series=read();tree.replaceChildren();
 if(!series.length){tree.textContent="Perpustakaan masih kosong. Buat seri pertama untuk mulai mengelompokkan cerita.";return}
 for(const s of series){
  const box=document.createElement("details");box.className="library-series";box.open=true;
  const summary=document.createElement("summary");summary.textContent=s.title+" ("+(s.arcs||[]).reduce((n,a)=>n+(a.volumes||[]).reduce((m,v)=>m+(v.chapters||[]).length,0),0)+" chapter)";
  box.append(summary);
  const actions=document.createElement("div");actions.className="library-actions";
  const addArc=document.createElement("button");addArc.className="secondary";addArc.textContent="Tambah arc";addArc.onclick=()=>addArcTo(s.id);
  const rename=document.createElement("button");rename.className="secondary";rename.textContent="Ubah seri";rename.onclick=()=>renameSeries(s.id);
  const remove=document.createElement("button");remove.className="secondary";remove.textContent="Hapus seri";remove.onclick=()=>removeSeries(s.id);
  actions.append(addArc,rename,remove);box.append(actions);
  for(const a of s.arcs||[]){
   const arc=document.createElement("details");arc.className="library-arc";arc.open=true;
   const as=document.createElement("summary");as.textContent="Arc: "+a.title;arc.append(as);
   const aa=document.createElement("div");aa.className="library-actions";
   const av=document.createElement("button");av.className="secondary";av.textContent="Tambah volume";av.onclick=()=>addVolume(s.id,a.id);
   const ar=document.createElement("button");ar.className="secondary";ar.textContent="Ubah arc";ar.onclick=()=>renameNode(s.id,a.id,"arc");
   aa.append(av,ar);arc.append(aa);
   for(const v of a.volumes||[]){
    const vol=document.createElement("div");vol.className="library-volume";
    const vh=document.createElement("strong");vh.textContent="Volume: "+v.title;vol.append(vh);
    const va=document.createElement("div");va.className="library-actions";
    const ch=document.createElement("button");ch.className="secondary";ch.textContent="Tambah chapter";ch.onclick=()=>addChapter(s.id,a.id,v.id);
    const vr=document.createElement("button");vr.className="secondary";vr.textContent="Ubah volume";vr.onclick=()=>renameNode(s.id,v.id,"volume");
    va.append(ch,vr);vol.append(va);
    for(const c of v.chapters||[]){
     const row=document.createElement("div");row.className="library-chapter";
     const open=document.createElement("button");open.className="secondary";open.textContent="Buka: "+c.title;open.onclick=()=>openChapter(c);
     const del=document.createElement("button");del.className="secondary";del.textContent="Hapus";del.onclick=()=>deleteChapter(s.id,a.id,v.id,c.id);
     row.append(open,narration,del);vol.append(row);
    }
    arc.append(vol);
   }
   box.append(arc);
  }
  tree.append(box);
 }
}
function ask(label,initial=""){const value=prompt(label,initial);return value===null?null:value.trim()}
function addSeries(){const title=ask("Nama seri / judul karya:");if(!title)return;const all=read();all.push({id:id(),title,arcs:[],createdAt:new Date().toISOString()});write(all);render();status.textContent="Seri ditambahkan."}
function addArcTo(sid){const title=ask("Nama arc:");if(!title)return;const all=read(),s=all.find(x=>x.id===sid);s.arcs.push({id:id(),title,volumes:[]});write(all);render()}
function addVolume(sid,aid){const title=ask("Nama atau nomor volume:");if(!title)return;const all=read(),a=all.find(x=>x.id===sid)?.arcs.find(x=>x.id===aid);a.volumes.push({id:id(),title,chapters:[]});write(all);render()}
function addChapter(sid,aid,vid){const title=ask("Nama chapter / bagian:");if(!title)return;const all=read(),v=all.find(x=>x.id===sid)?.arcs.find(x=>x.id===aid)?.volumes.find(x=>x.id===vid);v.chapters.push({id:id(),title,text:"",createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()});write(all);render();status.textContent="Chapter kosong dibuat. Buka chapter untuk mengisi teksnya."}
function renameSeries(sid){const all=read(),s=all.find(x=>x.id===sid),title=ask("Nama seri:",s.title);if(!title)return;s.title=title;write(all);render()}
function renameNode(sid,nid,type){const all=read();let node=null;for(const s of all){if(s.id!==sid)continue;for(const a of s.arcs||[]){if(type==="arc"&&a.id===nid)node=a;for(const v of a.volumes||[])if(type==="volume"&&v.id===nid)node=v}}if(!node)return;const title=ask("Nama:",node.title);if(!title)return;node.title=title;write(all);render()}
function removeSeries(sid){if(!confirm("Hapus seri beserta semua arc, volume, dan chapter di dalamnya?"))return;write(read().filter(x=>x.id!==sid));render()}
function deleteChapter(sid,aid,vid,cid){if(!confirm("Hapus chapter ini?"))return;const all=read(),v=all.find(x=>x.id===sid)?.arcs.find(x=>x.id===aid)?.volumes.find(x=>x.id===vid);v.chapters=v.chapters.filter(x=>x.id!==cid);write(all);render()}
function openChapter(c){$("title").value=c.title;$("source").value=c.originalSource||c.text||"";$("libraryStatus").textContent="Teks sumber asli dimuat ke editor. Narasi yang pernah dibuat tetap tersimpan terpisah.";$("editor-heading").scrollIntoView({behavior:"smooth"});$("source").focus()}\nfunction openNarration(c){if(!c.narration)return;$("title").value=c.title;const output=$("output");output.replaceChildren();String(c.narration).split(/\\n{2,}/).filter(Boolean).forEach((part,index)=>{const p=document.createElement("p");p.id="narration-paragraph-"+index;p.dataset.paragraphIndex=String(index);p.textContent=part;output.append(p)});$("libraryStatus").textContent="Narasi tersimpan dibuka. Sumber asli tidak diubah.";$("result-heading").scrollIntoView({behavior:"smooth"})}
function saveChapter(title,narration,originalSource){
 const all=read();let target=null;
 for(const s of all)for(const a of s.arcs||[])for(const v of a.volumes||[])for(const c of v.chapters||[])if(c.title===title)target=c;
 if(!target){const s=all[0]||{id:id(),title:"Cerita saya",arcs:[]};if(!all.length)all.push(s);let a=s.arcs[0];if(!a){a={id:id(),title:"Arc 1",volumes:[]};s.arcs.push(a)}let v=a.volumes[0];if(!v){v={id:id(),title:"Volume 1",chapters:[]};a.volumes.push(v)}target={id:id(),title,createdAt:new Date().toISOString()};v.chapters.push(target)}
 target.narration=narration;target.originalSource=originalSource||target.originalSource||"";target.text=target.originalSource;target.updatedAt=new Date().toISOString();write(all);render();status.textContent="Narasi disimpan ke perpustakaan lokal.";
}
function exportLibrary(){const blob=new Blob([JSON.stringify({format:"ai-story-reader-library",version:1,exportedAt:new Date().toISOString(),series:read()},null,2)],{type:"application/json"});const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="ai-story-reader-library.json";a.click();URL.revokeObjectURL(url);status.textContent="Cadangan perpustakaan diunduh."}
async function importLibrary(file){if(!file)return;try{const data=JSON.parse(await file.text()),items=Array.isArray(data)?data:data.series;if(!Array.isArray(items))throw new Error("Format cadangan tidak dikenali.");const current=read();const merged=[...current,...items.filter(item=>!current.some(old=>old.id===item.id))];write(merged);render();status.textContent="Cadangan berhasil digabung ke perpustakaan."}catch(e){status.textContent="Impor cadangan gagal: "+e.message}}
$("addSeries").addEventListener("click",addSeries);$("exportLibrary").addEventListener("click",exportLibrary);$("importLibrary").addEventListener("change",e=>importLibrary(e.target.files[0]));
window.storyLibrary={saveChapter,render};render();
})();