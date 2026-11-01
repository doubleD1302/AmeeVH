// Prepare an additive initial import; never execute against a remote database here.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {normalizeLine} from '../web/story_translator/worker/collaboration.mjs';
const root=path.resolve(import.meta.dirname,'..');
const arg=name=>{const i=process.argv.indexOf(name);return i<0?null:process.argv[i+1];};
const snapshot=path.resolve(root,arg('--snapshot')||'work/runs/tramvh_collaboration_20261101_r01/legacy_snapshot');
const out=path.resolve(root,arg('--out')||'work/runs/tramvh_collaboration_20261101_r01/prepared_import_r01');
if(!out.startsWith(root+path.sep)||!snapshot.startsWith(root+path.sep))throw Error('Paths must stay in project');
await fs.mkdir(out,{recursive:false});
const cols=['chapter_id','line_id','en','source_hash','new_vi','translator','status','translation_origin','notes','revision','updated_at','approved_by','approved_at','legacy_status','provenance'];
const hcols=['id','chapter_id','line_id','event_type','actor','created_at','reason','old_text','new_text','old_status','new_status','revision','source_hash','snapshot_json'];
const quote=value=>value===null||value===undefined?'NULL':typeof value==='number'?String(value):String(value).includes('\0')?`CAST(X'${Buffer.from(String(value),'utf8').toString('hex')}' AS TEXT)`:`'${String(value).replaceAll("'","''")}'`;
const sha=text=>createHash('sha256').update(text).digest('hex');
const statements=[],summary=[],archived=[];const importedAt=new Date().toISOString();
function bulk(table,fields,rows){let batch=[],size=0;const flush=()=>{if(batch.length)statements.push(`INSERT OR IGNORE INTO ${table}(${fields.join(',')}) VALUES\n${batch.join(',\n')};\n`);batch=[];size=0;};for(const row of rows){const value='('+fields.map(f=>quote(row[f])).join(',')+')';if(size+Buffer.byteLength(value)>75000)flush();batch.push(value);size+=Buffer.byteLength(value);}flush();}
const files=(await fs.readdir(path.join(root,'web/story_translator/data/chapters'))).filter(f=>f.endsWith('.json')).sort();
for(const filename of files){
 const chapter=JSON.parse(await fs.readFile(path.join(root,'web/story_translator/data/chapters',filename),'utf8'));const chapterId=chapter.chapter_id || filename.slice(0,-5);
 const rows=JSON.parse(await fs.readFile(path.join(snapshot,chapterId+'.json'),'utf8'));const byId=new Map();
 for(const row of rows.slice(1)){if(row.length<4||!row[1]?.trim())continue;const id=row[1].trim();if(!byId.has(id))byId.set(id,[]);byId.get(id).push(row);}
 const records=[],histories=[],used=new Set();const report={chapter_id:chapterId,lines:0,sheet_updates_applied:0,sheet_ambiguities:0,source_mismatch:0,empty_sheet_preserved:0,status_counts:{}};
 for(const scene of chapter.scenes){for(const staticLine of scene.lines){
  const raw={...staticLine},candidates=byId.get(raw.line_id)||[];used.add(raw.line_id);
  const filled=candidates.filter(row=>(row[5]||'').trim());const unique=[...new Map(filled.map(row=>[JSON.stringify([row[3],row[5],row[6],row[7],row[8]]),row])).values()];
  let issue='';
  if(unique.length===1&&unique[0][3]===raw.en){const row=unique[0],changed=row[5]!==raw.new_vi;raw.new_vi=row[5];raw.translator=(row[6]||'').trim() || (changed?'':raw.translator);raw.status=row[7] || raw.status;if(row[8])raw.notes=row[8];report.sheet_updates_applied++;}
  else if(unique.length>1){report.sheet_ambiguities++;issue='Có nhiều bản khác nhau cùng ID trong Sheets; giữ bản đang dùng để đối chiếu.';archived.push({chapter_id:chapterId,line_id:raw.line_id,reason:'duplicate_sheet_candidates',rows:unique});}
  else if(unique.length===1){report.source_mismatch++;issue='Nguồn EN trong Sheets khác nguồn hiện tại; bản dịch cũ được giữ để xem lại.';archived.push({chapter_id:chapterId,line_id:raw.line_id,reason:'source_mismatch',rows:unique});}
  else report.empty_sheet_preserved++;
  const normalized=await normalizeLine(chapterId,raw);
  normalized.provenance='legacy_import';normalized.updated_at=null;normalized.approved_by=null;normalized.approved_at=null;
  if(issue){normalized.status='needs_review';normalized.notes=[normalized.notes,issue].filter(Boolean).join('\n');}
  const reason='Nhập trạng thái hiện có từ catalog web và snapshot Sheets; thời gian/người duyệt trước đây chưa được xác minh.';
  const history={id:'import-'+sha(chapterId+'\0'+raw.line_id),chapter_id:chapterId,line_id:raw.line_id,event_type:'legacy_import',actor:'Nhập dữ liệu cũ',created_at:importedAt,reason,old_text:'',new_text:normalized.new_vi,old_status:'untranslated',new_status:normalized.status,revision:0,source_hash:normalized.source_hash,snapshot_json:JSON.stringify(normalized)};
  records.push(normalized);histories.push(history);report.lines++;report.status_counts[normalized.status]=(report.status_counts[normalized.status]||0)+1;
 }}
 for(const [id,unmapped]of byId)if(!used.has(id))archived.push({chapter_id:chapterId,line_id:id,reason:'no_matching_static_id',rows:unmapped});
 bulk('lines',cols,records);bulk('history',hcols,histories);summary.push(report);
 await fs.writeFile(path.join(out,chapterId+'.json'),JSON.stringify(records));
}
const sql=statements.join('\n');await fs.writeFile(path.join(out,'initial_import.sql'),sql);
const report={prepared_at_utc:importedAt,snapshot:path.relative(root,snapshot),lines:summary.reduce((n,c)=>n+c.lines,0),history_rows:summary.reduce((n,c)=>n+c.lines,0),sql_bytes:Buffer.byteLength(sql),sql_sha256:sha(sql),chapters:summary,archived_groups:archived.length};
await fs.writeFile(path.join(out,'IMPORT_MANIFEST.json'),JSON.stringify(report,null,2));await fs.writeFile(path.join(out,'UNRESOLVED_SHEET_ROWS.json'),JSON.stringify(archived,null,2));console.log(JSON.stringify({lines:report.lines,sql_bytes:report.sql_bytes,archived_groups:archived.length,out}));
