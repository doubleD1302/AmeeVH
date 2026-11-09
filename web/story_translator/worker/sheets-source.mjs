// Read-only access to the published workbook. D1 remains the collaboration store.
const BOOK = '13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM';
const GLOSSARY = 1254346151;
const MERGE = {Chuong_STm00:2101040006,Chuong_STm01:2101040005,Chuong_STm02:2101040007,'03_BangText_UI_KyNang':2101040008};
const LEGACY = {'Chương 0 - Mở Đầu':226895355,'Chương 1':2054958777,'Chương 2':218907429,'Chương 3':38347008,'Chương 4':961830816,'Chương 5':1537834455,'Chương 6':1027289011,'Chương 7':588497757,'Chương 8':996772565,'Chương 9':1778905308,'Ngoại Truyện':1699026156,'Ủy Thác Hội Quán':801579187,'Hẹn Hò Nhân Vật':433256131,'Tin Nhắn Điện Thoại':1999742602,'Cốt Truyện Sự Kiện':1471986453,'Kịch Bản Ký Ức (CG)':499773622};
const MERGE_HEADERS=['file_id','block_order','kind','speaker_en','speaker_jp','speaker_cn','speaker_vi','text_vi','text_cn','text_jp','text_en','source_refs_json'];
const str=x=>typeof x==='string'?x:'';
const SHEET_CACHE_TTL=15000;
const SHEET_MAX_BYTES=10_000_000;
const sheetCache=new Map();

export function parseGviz(body){
 const match=body.match(/^\s*\/\*O_o\*\/\s*google\.visualization\.Query\.setResponse\(([\s\S]*)\);?\s*$/);
 if(!match)throw Error('Phản hồi Google Sheet không hợp lệ.');
 const result=JSON.parse(match[1]);
 if(result.status!=='ok'||!Array.isArray(result.table?.rows)||!Array.isArray(result.table?.cols))throw Error('Google Sheet không sẵn sàng.');
 return result.table;
}
async function readSheet(gid,headers=1,fetcher=fetch){
 const key=`${gid}:${headers}`;
 if(fetcher===fetch){
  const cached=sheetCache.get(key);
  if(cached&&cached.expires>Date.now())return cached.table;
 }
 const u=new URL(`https://docs.google.com/spreadsheets/d/${BOOK}/gviz/tq`);
 u.searchParams.set('gid',String(gid));u.searchParams.set('headers',String(headers));u.searchParams.set('tqx','out:json');
 const response=await fetcher(u.toString(),{headers:{'Cache-Control':'no-cache'},signal:AbortSignal.timeout(20000)});
 if(!response.ok)throw Error('Không thể đọc Google Sheet.');
 const body=await response.text();
 if(new TextEncoder().encode(body).byteLength>SHEET_MAX_BYTES)throw Error('Google Sheet trả về dữ liệu quá lớn.');
 const table=parseGviz(body);
 if(fetcher===fetch)sheetCache.set(key,{expires:Date.now()+SHEET_CACHE_TTL,table});
 return table;
}
const cells=row=>(row.c||[]).map(c=>c?.v??'');
export function parseGlossary(table){
 const rows=table.rows.map(cells),head=rows[2]||[];
 if(head[0]!=='Danh từ gốc (EN)'||head[1]!=='Bản dịch Tiếng Việt chuẩn'||head[2]!=='Phân loại nhóm'||head[4]!=='Trạng thái')throw Error('Cấu trúc glossary trên Sheet đã thay đổi.');
 const terms=[];
 for(let i=3;i<rows.length;i++){
  const r=rows[i],en=str(r[0]),vi=str(r[1]);if(!en||en.startsWith('---'))continue;
  terms.push({id:str(r[7]),en,vi,category:str(r[2])||'Chung',notes:str(r[3]),status:str(r[4])||'pending',cn:str(r[5]),jp:str(r[6])});
 }
 return terms;
}
export async function getGlossary(fetcher=fetch){return parseGlossary(await readSheet(GLOSSARY,0,fetcher));}

export function parseMerge(table,group){
 if(table.cols.length!==12||MERGE_HEADERS.some((h,i)=>table.cols[i]?.label!==h))throw Error('Cấu trúc trang Merge không hợp lệ.');
 const files=[],byId=new Map(),seen=new Set();
 for(const row of table.rows){const r=cells(row),id=str(r[0]),order=r[1];if(!id&&!order)continue;
  if(!id||!Number.isSafeInteger(order)||order<1||seen.has(`${id}\0${order}`))throw Error('Khóa khối Merge thiếu hoặc trùng.');
  seen.add(`${id}\0${order}`);let f=byId.get(id);if(!f){f={file_id:id,blocks:[]};byId.set(id,f);files.push(f);}
  f.blocks.push({order,kind:str(r[2]),speaker_en:str(r[3]),speaker_jp:str(r[4]),speaker_cn:str(r[5]),speaker_vi:str(r[6]),vi:str(r[7]),cn:str(r[8]),jp:str(r[9]),en:str(r[10]),source_refs_json:str(r[11])});
 }
 for(const f of files){for(let i=0;i<f.blocks.length;i++)if(f.blocks[i].order!==i+1)throw Error('Thứ tự khối Merge không liên tục.');}
 return {group,files,source:'google_sheet'};
}
export async function getMerge(group,fetcher=fetch){if(!Object.hasOwn(MERGE,group))throw Error('Trang nguồn không hợp lệ.');return parseMerge(await readSheet(MERGE[group],1,fetcher),group);}

export function overlayReferences(chapter,table){
 const cols=table.cols.map(c=>c.label||'');
 if(cols[1]!=='Mã câu (ID) [Khóa]'||cols[3]!=='Nguồn EN'||!cols[4]?.startsWith('Nguồn CN')||!cols[5]?.startsWith('Nguồn JP'))throw Error('Cấu trúc trang truyện không hợp lệ.');
 const byId=new Map();
 for(const row of table.rows){let r=cells(row),id=str(r[1]);if(!id)continue;if(byId.has(id)){byId.set(id,null);continue}byId.set(id,r);}
 let matched=0;
 const scenes=(chapter.scenes||[]).map(scene=>({...scene,lines:(scene.lines||[]).map(line=>{
  const r=byId.get(String(line.line_id));if(!r||str(r[3])!==line.en)return line;
  matched++;return {...line,cn:str(r[4]),jp:str(r[5]),sheet_vi:str(r[7]),sheet_old_vi:str(r[6]),sheet_source_cn:str(r[11]),sheet_source_jp:str(r[12])};
 })}));
 return {...chapter,scenes,sheet_sync:{status:'ok',matched}};
}
export function overlayMergeReferences(chapter,merge){
 let matched=0;
 const scenes=(chapter.scenes||[]).map(scene=>{
  const file=merge.files.find(item=>item.file_id===scene.scene_id);
  const byEn=new Map();
  for(const block of file?.blocks||[]){
   const key=str(block.en);if(!key)continue;
   if(byEn.has(key))byEn.set(key,null);else byEn.set(key,block);
  }
  return {...scene,lines:(scene.lines||[]).map(line=>{
   const block=byEn.get(str(line.en));
   if(!block)return line;
   matched++;
   return {...line,cn:block.cn,jp:block.jp,sheet_vi:block.vi,sheet_old_vi:'',sheet_source_cn:'',sheet_source_jp:'',sheet_merge:{group:merge.group,file_id:file.file_id,block_order:block.order}};
  })};
 });
 return {...chapter,scenes,sheet_sync:{status:'ok',matched,source:'merge'}};
}
export async function getChapterReferences(chapter,fetcher=fetch){
 // Chương 0 was exported to the new Merge tab with stable file IDs, while its
 // legacy review tab uses SRT/BBm IDs and cannot be joined safely.
 if((chapter.scenes||[]).some(scene=>/^STm00_/.test(scene.scene_id))){
  return overlayMergeReferences(chapter,await getMerge('Chuong_STm00',fetcher));
 }
 const gid=LEGACY[chapter.sheet_name];
 if(!gid)return {...chapter,sheet_sync:{status:'unsupported',matched:0}};
 return overlayReferences(chapter,await readSheet(gid,1,fetcher));
}
