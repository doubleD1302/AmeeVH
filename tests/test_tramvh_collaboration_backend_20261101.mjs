import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {handleCollaboration,normalizeLine,overlayChapter,sourceHash} from '../web/story_translator/worker/collaboration.mjs';
import {onRequest as legacyProxy} from '../web/story_translator/functions/api/[[route]].js';
class Bound {
 constructor(owner,sql,args=[]){Object.assign(this,{owner,sql,args});}
 bind(...args){return new Bound(this.owner,this.sql,args);}
 exec(){const results=this.owner.db.prepare(this.sql).all(...this.args);return {success:true,results,meta:{changes:Number(this.owner.db.prepare('SELECT changes() n').get().n)}};}
 async first(){return this.owner.db.prepare(this.sql).get(...this.args)||null;}
 async all(){return this.exec();}
 async run(){return this.exec();}
}
class D1 {
 constructor(){this.db=new DatabaseSync(':memory:');this.db.exec(readFileSync(new URL('../web/story_translator/worker/schema.sql',import.meta.url),'utf8'));}
 prepare(sql){return new Bound(this,sql);}
 async batch(statements){this.db.exec('BEGIN IMMEDIATE');try{const result=statements.map(s=>s.exec());this.db.exec('COMMIT');return result;}catch(e){this.db.exec('ROLLBACK');throw e;}}
 close(){this.db.close();}
}
const chapterId='Chuong_3_MainStory',lineId='line-1';
function fixture(raw={}){
 const DB=new D1();const line={line_id:lineId,en:'Hello {0}',old_vi:'',new_vi:'',translator:'',status:'Chờ dịch',notes:'',...raw};
 const chapter={chapter_id:chapterId,title:'Test chapter',scenes:[{title:'Test scene',lines:[line]}]};
 const fixtureState={manifest:null,index:[{id:chapterId,total_lines:1}]};
 const env={DB,REVIEWER_KEY:'private-review-code',ASSETS:{async fetch(request){
  const path=new URL(request.url).pathname;
  if(path.endsWith('/dataset-manifest.json'))return fixtureState.manifest?new Response(JSON.stringify(fixtureState.manifest),{headers:{'Content-Type':'application/json'}}):new Response('',{status:404});
  if(path.endsWith('/chapters.json'))return new Response(JSON.stringify(fixtureState.index),{headers:{'Content-Type':'application/json'}});
  return new Response(JSON.stringify(chapter),{headers:{'Content-Type':'application/json'}});
 }}};
 return {env,line,chapter,fixtureState,close:()=>DB.close()};
}
const sessions=new WeakMap();
async function testCookie(env){
 if(!sessions.has(env))sessions.set(env,(async()=>{
  const response=await handleCollaboration(new Request('https://tramvh.test/api/collab/me'),env);
  assert.equal(response.status,200);
  const cookie=response.headers.get('Set-Cookie').split(';')[0];
  const profile=await handleCollaboration(new Request('https://tramvh.test/api/collab/profile',{method:'POST',headers:{'Content-Type':'application/json','Cookie':cookie},body:JSON.stringify({display_name:'Minh'})}),env);
  assert.equal(profile.status,200);
  return cookie;
 })());
 return sessions.get(env);
}
async function call(env,path,body,key,cookie){const headers={'Content-Type':'application/json','Cookie':cookie||await testCookie(env)};if(key)headers['X-Reviewer-Key']=key;const response=await handleCollaboration(new Request('https://tramvh.test'+path,{method:body?'POST':'GET',headers,...(body?{body:JSON.stringify(body)}:{})}),env);return {status:response.status,body:await response.json()};}
const linePath=`/api/collab/line?chapter_id=${chapterId}&line_id=${lineId}`;
const historyPath=`/api/collab/history?chapter_id=${chapterId}&line_id=${lineId}`;
async function current(env){const r=await call(env,linePath);assert.equal(r.status,200,JSON.stringify(r.body));return r.body.line;}
const guarded=(line,extra={})=>({chapter_id:chapterId,line_id:lineId,base_revision:line.revision,base_source_hash:line.source_hash,base_dataset_version:line.dataset_version,request_id:crypto.randomUUID(),...extra});
const translate=(line,text='Xin chào {0}',extra={})=>guarded(line,{text_vi:text,translator:'Minh',origin:'human',notes:'',...extra});
const reviewBody=(line,action,extra={})=>guarded(line,{action,reviewer:'Reviewer',reason:'Đã kiểm tra.',...extra});

test('normalization keeps imported author origin unknown and time unknown',async()=>{const line=await normalizeLine(chapterId,{line_id:lineId,en:'Hello',new_vi:'Xin chào',translator:'Minh',status:'Đã duyệt'});assert.equal(line.translation_origin,'unknown');assert.equal(line.updated_at,null);assert.equal(line.approved_by,null);assert.equal(line.status,'approved');assert.equal(line.provenance,'legacy_import');assert.equal(line.source_hash,await sourceHash('Hello'));});
test('v1 database migration keeps existing proposals and enables v2 identity fields',()=>{
 const db=new DatabaseSync(':memory:');
 try{
  db.exec("CREATE TABLE collaboration_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);INSERT INTO collaboration_meta VALUES('schema_version','1');CREATE TABLE proposals(id TEXT PRIMARY KEY,chapter_id TEXT,line_id TEXT,text_vi TEXT);INSERT INTO proposals VALUES('old','chapter','line','Bản cũ');");
  db.exec(readFileSync(new URL('../web/story_translator/worker/migrations/0002_dataset_identity.sql',import.meta.url),'utf8'));
  assert.equal(db.prepare("SELECT value FROM collaboration_meta WHERE key='schema_version'").get().value,'2');
  assert.equal(db.prepare("SELECT text_vi FROM proposals WHERE id='old'").get().text_vi,'Bản cũ');
  assert.equal(db.prepare('SELECT version,phase FROM dataset_state WHERE id=1').get().phase,'open');
  for(const name of ['user_id','dataset_version','updated_at'])assert.ok(db.prepare('PRAGMA table_info(proposals)').all().some(column=>column.name===name));
 }finally{db.close();}
});
test('identity is server owned and each user sees only their own proposal',async()=>{
 const f=fixture({new_vi:'Xin chào {0}',status:'Đã duyệt'});
 try{
  const firstCookie=await testCookie(f.env);
  const secondResponse=await handleCollaboration(new Request('https://tramvh.test/api/collab/me'),f.env);
  const secondCookie=secondResponse.headers.get('Set-Cookie').split(';')[0];
  assert.notEqual(secondCookie,firstCookie);
  const second=await call(f.env,'/api/collab/me',undefined,undefined,secondCookie);
  assert.notEqual(second.body.user.id,(await call(f.env,'/api/collab/me')).body.user.id);
  const line=await current(f.env);
  const saved=await call(f.env,'/api/collab/submit',translate(line,'Chào bạn {0}',{translator:'Forged',reason:'naturalness'}));
  assert.equal(saved.status,200,JSON.stringify(saved.body));
  assert.equal(saved.body.proposal.translator,'Minh');
  const mine=await call(f.env,`/api/collab/my-proposal?chapter_id=${chapterId}&line_id=${lineId}`);
  const theirs=await call(f.env,`/api/collab/my-proposal?chapter_id=${chapterId}&line_id=${lineId}`,undefined,undefined,secondCookie);
  assert.equal(mine.body.proposal.id,saved.body.proposal.id);
  assert.equal(theirs.body.proposal,null);
  const updated=await call(f.env,'/api/collab/submit',translate(saved.body.line,'Chào nhé {0}',{reason:'naturalness'}));
  assert.equal(updated.body.result,'proposal_updated');
  assert.equal(updated.body.proposal.id,saved.body.proposal.id);
  assert.equal((await f.env.DB.prepare('SELECT count(*) n FROM proposals').first()).n,1);
 }finally{f.close();}
});
test('release lock drains proposals, checks deployed manifest and rejects old drafts',async()=>{
 const f=fixture({new_vi:'Xin chào {0}',status:'Đã duyệt'});
 try{
  const original=await current(f.env);
  const proposal=await call(f.env,'/api/collab/submit',translate(original,'Chào bạn {0}',{reason:'naturalness'}));
  assert.equal(proposal.status,200);
  const release=async(action,extra={})=>{
   const state=(await call(f.env,'/api/collab/release',undefined,'private-review-code')).body.dataset;
   return call(f.env,'/api/collab/release',{action,reason:'Kiểm thử chuyển phiên',expected_version:state.version,expected_phase:state.phase,...extra},'private-review-code');
  };
  assert.equal((await release('lock')).body.dataset.phase,'locked');
  assert.equal((await call(f.env,'/api/collab/submit',translate(proposal.body.line,'Xin chào lại {0}',{reason:'naturalness'}))).status,423);
  const blocked=await release('publish');assert.equal(blocked.status,409);assert.equal(blocked.body.code,'pending_proposals');
  const rejected=await call(f.env,'/api/collab/review',reviewBody(await current(f.env),'reject',{proposal_id:proposal.body.proposal.id}),'private-review-code');
  assert.equal(rejected.status,200,JSON.stringify(rejected.body));
  assert.equal((await release('publish')).body.dataset.phase,'publishing');
  const hash='a'.repeat(64);
  const missing=await release('activate',{new_version:'release-2',manifest_hash:hash});
  assert.equal(missing.status,409);assert.equal(missing.body.code,'manifest_missing');
  const indexText=JSON.stringify(f.fixtureState.index),chapterText=JSON.stringify(f.chapter),encoder=new TextEncoder();
  const files=[{path:'chapters.json',bytes:encoder.encode(indexText).length,sha256:await sourceHash(indexText)},{path:`chapters/${chapterId}.json`,bytes:encoder.encode(chapterText).length,sha256:await sourceHash(chapterText),lines:1}];
  const payload={schema:1,version:'release-2',files};
  f.fixtureState.manifest={...payload,hash:await sourceHash(JSON.stringify(payload)),chapters:1,lines:1};
  const invalid=await release('activate',{new_version:'release-2',manifest_hash:hash});
  assert.equal(invalid.status,409);assert.equal(invalid.body.code,'manifest_mismatch');
  f.chapter.scenes[0].lines[0].en='Tampered {0}';
  const tampered=await release('activate',{new_version:'release-2',manifest_hash:f.fixtureState.manifest.hash});
  assert.equal(tampered.status,409);assert.equal(tampered.body.code,'asset_mismatch');
  f.chapter.scenes[0].lines[0].en='Hello {0}';
  assert.equal((await release('activate',{new_version:'release-2',manifest_hash:f.fixtureState.manifest.hash})).body.dataset.phase,'locked');
  assert.equal((await release('open')).body.dataset.phase,'open');
  const stale=await call(f.env,'/api/collab/submit',translate(original,'Câu cũ {0}',{reason:'naturalness'}));
  assert.equal(stale.status,409);assert.equal(stale.body.code,'dataset_stale');
  const fresh=await current(f.env);assert.equal(fresh.dataset_version,'release-2');
  const accepted=await call(f.env,'/api/collab/submit',translate(fresh,'Câu mới {0}',{reason:'naturalness'}));
  assert.equal(accepted.status,200,JSON.stringify(accepted.body));
 }finally{f.close();}
});
test('publishing can be aborted only after the previous manifest is restored',async()=>{
 const f=fixture();
 try{
  await testCookie(f.env);
  const release=async(action)=>{
   const state=(await call(f.env,'/api/collab/release',undefined,'private-review-code')).body.dataset;
   return call(f.env,'/api/collab/release',{action,reason:'Kiểm thử rollback',expected_version:state.version,expected_phase:state.phase},'private-review-code');
  };
  assert.equal((await release('lock')).status,200);
  assert.equal((await release('open')).body.code,'manifest_missing');
  assert.equal((await release('publish')).status,200);
  f.fixtureState.manifest={schema:1,version:'release-2',files:[{path:'chapters.json',bytes:1,sha256:'a'.repeat(64)},{path:'chapters/x.json',bytes:1,sha256:'a'.repeat(64)}],hash:'a'.repeat(64)};
  assert.equal((await release('abort')).body.code,'manifest_invalid');
  const indexText=JSON.stringify(f.fixtureState.index),chapterText=JSON.stringify(f.chapter),encoder=new TextEncoder();
  const files=[{path:'chapters.json',bytes:encoder.encode(indexText).length,sha256:await sourceHash(indexText)},{path:`chapters/${chapterId}.json`,bytes:encoder.encode(chapterText).length,sha256:await sourceHash(chapterText),lines:1}];
  const payload={schema:1,version:'legacy-1',files};
  f.fixtureState.manifest={...payload,hash:await sourceHash(JSON.stringify(payload)),chapters:1,lines:1};
  assert.equal((await release('abort')).body.dataset.phase,'locked');
  assert.equal((await release('open')).body.dataset.phase,'open');
 }finally{f.close();}
});
test('first save is pending; valid reviewer alone can approve; replay does not duplicate',async()=>{const f=fixture();try{const line=await current(f.env),body=translate(line);const saved=await call(f.env,'/api/collab/submit',body);assert.equal(saved.status,200,JSON.stringify(saved.body));assert.equal(saved.body.result,'saved');assert.equal(saved.body.line.status,'pending');assert.equal(saved.body.line.translator,'Minh');assert.equal(saved.body.line.revision,1);const repeated=await call(f.env,'/api/collab/submit',body);assert.equal(repeated.body.replayed,true);assert.equal(repeated.body.line.revision,1);const denied=await call(f.env,'/api/collab/review',reviewBody(saved.body.line,'approve'),'wrong');assert.equal(denied.status,403);const approved=await call(f.env,'/api/collab/review',reviewBody(saved.body.line,'approve'),'private-review-code');assert.equal(approved.body.line.status,'approved');assert.equal(approved.body.line.approved_by,'Minh');const history=await call(f.env,historyPath);assert.equal(history.body.history.length,2);assert.deepEqual(history.body.history.map(h=>h.event_type),['approved','translation_saved']);}finally{f.close();}});
test('simultaneous stale saves produce exactly one saved translation and one409',async()=>{const f=fixture();try{const line=await current(f.env);const results=await Promise.all([call(f.env,'/api/collab/submit',translate(line,'Xin chào {0}')),call(f.env,'/api/collab/submit',translate(line,'Chào bạn {0}',{translator:'Lan'}))]);assert.deepEqual(results.map(r=>r.status).sort(),[200,409]);const fresh=await current(f.env);assert.equal(fresh.revision,1);assert.ok(['Xin chào {0}','Chào bạn {0}'].includes(fresh.new_vi));const history=await call(f.env,historyPath);assert.equal(history.body.history.length,1);}finally{f.close();}});
test('concurrent identical request id is applied once',async()=>{const f=fixture();try{const line=await current(f.env),body=translate(line);const responses=await Promise.all([call(f.env,'/api/collab/submit',body),call(f.env,'/api/collab/submit',body)]);assert.ok(responses.every(r=>r.status===200));assert.equal((await current(f.env)).revision,1);assert.equal((await call(f.env,historyPath)).body.history.length,1);assert.equal(responses.filter(r=>r.body.replayed).length,1);}finally{f.close();}});
test('editing approved line creates proposal without replacing current translation',async()=>{const f=fixture({new_vi:'Xin chào {0}',translator:'Original',status:'Đã duyệt'});try{const old=await current(f.env);const proposal=await call(f.env,'/api/collab/submit',translate(old,'Chào bạn {0}',{reason:'naturalness'}));assert.equal(proposal.status,200,JSON.stringify(proposal.body));assert.equal(proposal.body.result,'proposed');assert.equal(proposal.body.line.new_vi,old.new_vi);assert.equal(proposal.body.line.translator,'Original');assert.equal(proposal.body.line.status,'approved');assert.equal(proposal.body.line.pending_proposals,1);const accepted=await call(f.env,'/api/collab/review',reviewBody(proposal.body.line,'accept',{proposal_id:proposal.body.proposal.id}),'private-review-code');assert.equal(accepted.status,200,JSON.stringify(accepted.body));assert.equal(accepted.body.line.new_vi,'Chào bạn {0}');assert.equal(accepted.body.line.translator,'Minh');assert.equal(accepted.body.line.status,'approved');assert.equal(accepted.body.line.pending_proposals,0);}finally{f.close();}});
test('reviewer rejection preserves text and cannot be repeated with a fresh request',async()=>{const f=fixture({new_vi:'Xin chào {0}',status:'Đã duyệt'});try{const old=await current(f.env),p=await call(f.env,'/api/collab/submit',translate(old,'Chào bạn {0}',{reason:'meaning'}));const rejected=await call(f.env,'/api/collab/review',reviewBody(p.body.line,'reject',{proposal_id:p.body.proposal.id}),'private-review-code');assert.equal(rejected.status,200);assert.equal(rejected.body.line.new_vi,old.new_vi);assert.equal(rejected.body.line.status,'approved');assert.equal(rejected.body.proposal.state,'rejected');const again=await call(f.env,'/api/collab/review',reviewBody(rejected.body.line,'reject',{proposal_id:p.body.proposal.id}),'private-review-code');assert.equal(again.status,409);}finally{f.close();}});
test('machine input is labelled machine_pending until reviewer approves',async()=>{const f=fixture();try{const saved=await call(f.env,'/api/collab/submit',translate(await current(f.env),'Xin chào {0}',{origin:'machine'}));assert.equal(saved.body.line.status,'machine_pending');assert.equal(saved.body.line.translation_origin,'machine');const approved=await call(f.env,'/api/collab/review',reviewBody(saved.body.line,'approve'),'private-review-code');assert.equal(approved.body.line.status,'approved');assert.equal(approved.body.line.translation_origin,'machine');}finally{f.close();}});
test('source change retains active text, clears approval and prevents stale proposal acceptance',async()=>{const f=fixture({new_vi:'Xin chào {0}',translator:'Original',status:'Đã duyệt',approved_by:'Old reviewer',approved_at:'2026-01-01T00:00:00.000Z'});try{const old=await current(f.env),proposal=await call(f.env,'/api/collab/submit',translate(old,'Chào bạn {0}',{reason:'meaning'}));f.line.en='Welcome {0}';const fresh=await current(f.env);assert.equal(fresh.new_vi,old.new_vi);assert.equal(fresh.status,'needs_review');assert.equal(fresh.approved_by,null);assert.notEqual(fresh.source_hash,old.source_hash);const stale=await call(f.env,'/api/collab/submit',translate(old,'Xin chào lại {0}'));assert.equal(stale.status,409);const acceptance=await call(f.env,'/api/collab/review',reviewBody(fresh,'accept',{proposal_id:proposal.body.proposal.id}),'private-review-code');assert.equal(acceptance.status,409);assert.equal(acceptance.body.code,'proposal_stale');const history=await call(f.env,historyPath);assert.ok(history.body.history.some(h=>h.event_type==='source_changed'));}finally{f.close();}});
test('restore creates a new revision and preserves immutable old history',async()=>{const f=fixture();try{let r=await call(f.env,'/api/collab/submit',translate(await current(f.env)));r=await call(f.env,'/api/collab/review',reviewBody(r.body.line,'approve'),'private-review-code');const beforeHistory=await call(f.env,historyPath),restoreTarget=beforeHistory.body.history.find(h=>h.event_type==='approved');let p=await call(f.env,'/api/collab/submit',translate(r.body.line,'Chào bạn {0}',{reason:'naturalness'}));r=await call(f.env,'/api/collab/review',reviewBody(p.body.line,'accept',{proposal_id:p.body.proposal.id}),'private-review-code');const beforeRestore=(await call(f.env,historyPath)).body.history;const restored=await call(f.env,'/api/collab/review',reviewBody(r.body.line,'restore',{history_id:restoreTarget.id}),'private-review-code');assert.equal(restored.status,200,JSON.stringify(restored.body));assert.equal(restored.body.line.new_vi,'Xin chào {0}');assert.equal(restored.body.line.status,'needs_review');assert.equal(restored.body.line.revision,r.body.line.revision+1);const after=(await call(f.env,historyPath)).body.history;assert.equal(after.length,beforeRestore.length+1);for(const entry of beforeRestore)assert.deepEqual(after.find(h=>h.id===entry.id),entry);assert.equal(after[0].event_type,'restored');}finally{f.close();}});
test('report preserves translation and disables approval status',async()=>{const f=fixture({new_vi:'Xin chào {0}',status:'Đã duyệt',approved_by:'Old reviewer'});try{const old=await current(f.env),reported=await call(f.env,'/api/collab/report',guarded(old,{reason:'Có vấn đề về nghĩa.',translator:'Lan'}));assert.equal(reported.status,200);assert.equal(reported.body.line.status,'needs_review');assert.equal(reported.body.line.new_vi,old.new_vi);assert.equal(reported.body.line.approved_by,null);}finally{f.close();}});
test('missing guards, empty text, missing tokens and extra tokens never mutate',async()=>{const f=fixture();try{const line=await current(f.env);for(const bad of [{...translate(line),base_revision:undefined},{...translate(line),base_source_hash:undefined},{...translate(line),request_id:undefined},translate(line,''),translate(line,'Xin chào'),translate(line,'Xin chào {0} {0}'),translate(line,'Xin chào {0} {1}')]){const result=await call(f.env,'/api/collab/submit',bad);assert.equal(result.status,400,JSON.stringify(result.body));}assert.equal((await current(f.env)).revision,0);assert.equal((await call(f.env,historyPath)).body.history.length,0);}finally{f.close();}});
test('idempotency id cannot be reused for changed payload',async()=>{const f=fixture();try{const body=translate(await current(f.env));assert.equal((await call(f.env,'/api/collab/submit',body)).status,200);const changed=await call(f.env,'/api/collab/submit',{...body,text_vi:'Chào bạn {0}'});assert.equal(changed.status,409);assert.equal(changed.body.code,'request_reused');assert.equal((await current(f.env)).new_vi,'Xin chào {0}');}finally{f.close();}});
test('review key is server enforced, absent configuration fails closed',async()=>{const f=fixture({new_vi:'Xin chào {0}',status:'Đã dịch'});try{const line=await current(f.env);assert.equal((await call(f.env,'/api/collab/role')).body.can_review,false);assert.equal((await call(f.env,'/api/collab/role',undefined,'private-review-code')).body.can_review,true);assert.equal((await call(f.env,'/api/collab/review',reviewBody(line,'approve'))).status,403);delete f.env.REVIEWER_KEY;assert.equal((await call(f.env,'/api/collab/review',reviewBody(line,'approve'),'private-review-code')).status,503);assert.equal((await current(f.env)).status,'pending');}finally{f.close();}});
test('unknown and ambiguous source IDs are rejected; traversal cannot select assets',async()=>{const f=fixture();try{assert.equal((await call(f.env,'/api/collab/line?chapter_id=../secrets&line_id=x')).status,400);assert.equal((await call(f.env,`/api/collab/line?chapter_id=${chapterId}&line_id=missing`)).status,404);f.chapter.scenes[0].lines.push({...f.line});assert.equal((await call(f.env,linePath)).status,409);}finally{f.close();}});
test('chapter overlay returns durable state, not stale static VI',async()=>{const f=fixture();try{const saved=await call(f.env,'/api/collab/submit',translate(await current(f.env)));const chapter=await overlayChapter(f.chapter,f.env);assert.equal(chapter.scenes[0].lines[0].new_vi,saved.body.line.new_vi);assert.equal(chapter.scenes[0].lines[0].revision,1);assert.equal(chapter.scenes[0].lines[0].status,'pending');}finally{f.close();}});
test('history pagination retains every revision with no duplicate cursor boundary',async()=>{const f=fixture({new_vi:'Xin chào {0}',status:'Đã dịch'});try{let line=await current(f.env);for(let i=0;i<105;i++){const r=await call(f.env,'/api/collab/report',guarded(line,{reason:'Issue '+i,translator:'Tester'}));assert.equal(r.status,200);line=r.body.line;}const first=await call(f.env,historyPath);assert.equal(first.body.history.length,100);assert.ok(first.body.next_cursor);const second=await call(f.env,historyPath+'&cursor='+encodeURIComponent(first.body.next_cursor));assert.equal(second.body.history.length,5);assert.equal(new Set([...first.body.history,...second.body.history].map(h=>h.id)).size,105);assert.equal(second.body.next_cursor,null);}finally{f.close();}});

test('approved VI identical to EN remains protected by proposal workflow',async()=>{const f=fixture({en:'OK',new_vi:'OK',status:'Đã duyệt',translator:'Original'});try{const old=await current(f.env);const result=await call(f.env,'/api/collab/submit',translate(old,'Được',{reason:'naturalness'}));assert.equal(result.status,200);assert.equal(result.body.result,'proposed');assert.equal(result.body.line.new_vi,'OK');assert.equal(result.body.line.status,'approved');assert.equal(result.body.line.translator,'Original');}finally{f.close();}});

test('same token counts cannot cross formatting tags',async()=>{const f=fixture({en:'<b>Hello</b> <i>{0}</i>'});try{const line=await current(f.env);const result=await call(f.env,'/api/collab/submit',translate(line,'<b>Xin <i>chào</b> {0}</i>'));assert.equal(result.status,400);assert.equal((await current(f.env)).revision,0);}finally{f.close();}});


test('pending proposal pages remain reachable after over100 newer closed proposals',async()=>{
 const f=fixture({new_vi:'Xin chào {0}',status:'Đã duyệt'});try{
  const line=await current(f.env),insert=f.env.DB.db.prepare("INSERT INTO proposals(id,chapter_id,line_id,text_vi,translator,origin,notes,reason,created_at,state,base_revision,base_source_hash,base_text) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)");
  for(let i=0;i<105;i++)insert.run('pending-'+String(i).padStart(3,'0'),chapterId,lineId,'Chào {0}','QA','human','','naturalness','2026-10-30T00:00:00.000Z','pending',0,line.source_hash,line.new_vi);
  for(let i=0;i<110;i++)insert.run('closed-'+i,chapterId,lineId,'Chào {0}','QA','human','','naturalness','2026-10-31T00:00:00.000Z','rejected',0,line.source_hash,line.new_vi);
  const first=await call(f.env,historyPath);assert.equal(first.status,200);assert.equal(first.body.proposals.length,100);assert.ok(first.body.proposals.every(p=>p.state==='pending'));assert.ok(first.body.proposals_next_cursor);
  const second=await call(f.env,historyPath+'&proposal_cursor='+encodeURIComponent(first.body.proposals_next_cursor));assert.equal(second.body.proposals.length,5);assert.equal(second.body.proposals_next_cursor,null);assert.equal(new Set([...first.body.proposals,...second.body.proposals].map(p=>p.id)).size,105);
  assert.equal((await call(f.env,historyPath+'&proposal_cursor=invalid')).status,400);
 }finally{f.close();}
});

test('legacy Pages proxy cannot save lines or route arbitrary actions to GAS',async()=>{
 const originalFetch=globalThis.fetch;let forwarded=0;
 globalThis.fetch=async()=>{forwarded++;throw Error('unexpected proxy request');};
 try{
  for(const path of ['/api/save_line','/api/save_line?action=add_glossary_term','/api/collab/submit']){
   const response=await legacyProxy({request:new Request('https://tramvh.test'+path,{method:'POST',body:'{}'}),env:{}});
   assert.equal(response.status,path.startsWith('/api/save_line')?426:404);
  }
  assert.equal(forwarded,0);
 }finally{globalThis.fetch=originalFetch;}
});

test('Pages glossary proxy ignores caller actions in query and body',async()=>{
 const originalFetch=globalThis.fetch;let target,payload;
 globalThis.fetch=async(url,options)=>{target=new URL(url);payload=options.body?JSON.parse(options.body):null;return new Response(JSON.stringify({success:true,terms:[]}),{headers:{'Content-Type':'application/json'}});};
 try{
  let response=await legacyProxy({request:new Request('https://tramvh.test/api/glossary?action=save_line'),env:{}});
  assert.equal(response.status,200);assert.equal(target.searchParams.get('action'),'get_glossary');
  response=await legacyProxy({request:new Request('https://tramvh.test/api/add_glossary_term',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'save_line',en:'A',vi:'B'})}),env:{}});
  assert.equal(response.status,200);assert.equal(target.searchParams.get('action'),'add_glossary_term');assert.equal(payload.action,'add_glossary_term');
 }finally{globalThis.fetch=originalFetch;}
});

test('other reason accepts empty explanation and preserves supplied context',async()=>{
 const f=fixture({new_vi:'Xin chào {0}',status:'Đã duyệt',notes:'Bối cảnh có sẵn'});
 try {
  const result=await call(f.env,'/api/collab/submit',translate(await current(f.env),'Chào bạn {0}',{reason:'other',reason_detail:'',notes:'Bối cảnh có sẵn'}));
  assert.equal(result.status,200,JSON.stringify(result.body));
  assert.equal(result.body.proposal.reason,'other');
  assert.equal(result.body.proposal.reason_detail,'');
  assert.equal(result.body.proposal.notes,'Bối cảnh có sẵn');
  assert.equal(result.body.line.new_vi,'Xin chào {0}');
 } finally { f.close(); }
});


test('multiple admin secrets retain the existing key and reject invalid keys',async()=>{
 const f=fixture();
 try {
  f.env.REVIEWER_KEY_2='test-admin-two'; f.env.REVIEWER_KEY_3='test-admin-three';
  for(const key of ['private-review-code','test-admin-two','test-admin-three']) assert.equal((await call(f.env,'/api/collab/role',undefined,key)).body.can_review,true);
  assert.equal((await call(f.env,'/api/collab/role',undefined,'invalid-key')).body.can_review,false);
  delete f.env.REVIEWER_KEY;
  const saved=await call(f.env,'/api/collab/submit',translate(await current(f.env)));
  const approved=await call(f.env,'/api/collab/review',reviewBody(saved.body.line,'approve'),'test-admin-three');
  assert.equal(approved.status,200,JSON.stringify(approved.body));
 } finally { f.close(); }
});
test('admin portal APIs are server enforced and exports replay immutably',async()=>{
 const f=fixture({new_vi:'Xin chào {0}',status:'Đã duyệt'});
 try {
  await current(f.env);
  const overview=await call(f.env,'/api/admin/overview',undefined,'private-review-code');
  assert.equal(overview.status,200,JSON.stringify(overview.body));
  assert.equal(overview.body.data.approved,1);
  const queue=await call(f.env,`/api/admin/queue?chapter_id=${chapterId}`,undefined,'private-review-code');
  assert.equal(queue.status,200); assert.equal(queue.body.data.total,0);
  const denied=await call(f.env,'/api/admin/overview',undefined,'invalid-key'); assert.equal(denied.status,403);
  const created=await call(f.env,'/api/admin/exports',{kind:'handoff',chapter_id:chapterId},'private-review-code');
  assert.equal(created.status,201,JSON.stringify(created.body));
  const id=created.body.data.export_id; assert.ok(created.body.data.manifest.files['changes.jsonl']);
  const first=await call(f.env,`/api/admin/exports/${id}/download?file=manifest.json`,undefined,'private-review-code');
  const second=await call(f.env,`/api/admin/exports/${id}/download?file=manifest.json`,undefined,'private-review-code');
  assert.equal(first.status,200); assert.equal(second.status,200); assert.deepEqual(second.body,first.body);
  const listed=await call(f.env,'/api/admin/exports',undefined,'private-review-code'); assert.equal(listed.body.data.items[0].id,id);
 } finally { f.close(); }
});
