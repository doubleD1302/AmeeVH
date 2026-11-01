// D1 collaboration adapter. Author: collab_backend agent; persisted by root executor.
const CHAPTERS = new Set(['Chuong_0_MainStory','Chuong_1_MainStory','Chuong_2_MainStory','Chuong_3_MainStory','Chuong_4_MainStory','Chuong_5_MainStory','Chuong_6_MainStory','Chuong_7_MainStory','Chuong_8_MainStory','Chuong_9_MainStory','Ngoai_Truyen_STsp','Uy_Thac_Hoi_Quan_BBm','Hen_Ho_Dating_DP','Tin_Nhan_Dien_Thoai_PM','Cot_Truyen_Su_Kien_STev','Kich_Ban_CG_Memory']);
const STATES = new Set(['untranslated','pending','approved','needs_review','machine_pending']);
const ORIGINS = new Set(['human','machine','unknown']);
const TOKEN = /==[A-Za-z0-9_]+==|<[^<>\n]+>|\$\{[^{}\n]+\}|\{[A-Za-z0-9_]+\}|\$[A-Za-z_][\w.]*\$|%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs]|\[\/?(?:color|size|b|i|url|sprite)[^\]\n]*\]|\\n/g;
const COLS = ['chapter_id','line_id','en','source_hash','new_vi','translator','status','translation_origin','notes','revision','updated_at','approved_by','approved_at','legacy_status','provenance'];
const json = (data,status=200) => new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}});
class DomainError extends Error { constructor(status,code,message,line){super(message);Object.assign(this,{status,code,line});} }
const fail = (status,code,message,line) => {throw new DomainError(status,code,message,line);};
const now = () => new Date().toISOString();
const uuid = () => crypto.randomUUID();
export async function sourceHash(text){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,'0')).join('');}
const validId = (value,max=240) => typeof value==='string' && value.length>0 && value.length<=max && !/[\u0000-\u001f\u007f]/.test(value);
function ids(chapter,line){if(!CHAPTERS.has(chapter)||!validId(line))fail(400,'invalid_id','Chương hoặc ID câu không hợp lệ.');}
function bounded(value,name,max,required=false){if(typeof value!=='string'||value.length>max||/[\u0000]/.test(value)||(required&&!value.trim()))fail(400,'invalid_payload',`${name} không hợp lệ.`);return value.trim();}
function hasTranslation(line){return !!line.new_vi.trim();}
export async function normalizeLine(chapter_id,raw){
 ids(chapter_id,String(raw.line_id||''));
 const en=String(raw.en||'');
 let new_vi=String(raw.new_vi||raw.old_vi||'');
 if(new_vi===en && ['Chờ dịch','Chưa dịch','untranslated'].includes(raw.status))new_vi='';
 const origin=ORIGINS.has(raw.translation_origin)?raw.translation_origin:ORIGINS.has(raw.origin)?raw.origin:'unknown';
 const has=!!new_vi.trim();
 let status=STATES.has(raw.status)?raw.status:raw.status==='Đã duyệt'?'approved':raw.status==='Cần xem lại'?'needs_review':'pending';
 if(!has)status='untranslated';else if(origin==='machine'&&status==='pending')status='machine_pending';
 return {chapter_id,line_id:String(raw.line_id),en,source_hash:await sourceHash(en),new_vi,translator:String(raw.translator||''),status,translation_origin:origin,notes:String(raw.notes||''),revision:0,updated_at:raw.updated_at||null,approved_by:raw.approved_by||null,approved_at:raw.approved_at||null,legacy_status:String(raw.legacy_status||raw.status||''),provenance:raw.provenance||'legacy_import'};
}
const stmt=(env,sql,values=[])=>env.DB.prepare(sql).bind(...values);
async function getLine(env,chapter,line){return stmt(env,`SELECT l.*,(SELECT count(*) FROM proposals p WHERE p.chapter_id=l.chapter_id AND p.line_id=l.line_id AND p.state='pending') AS pending_proposals FROM lines l WHERE l.chapter_id=? AND l.line_id=?`,[chapter,line]).first();}
async function rawLine(env,chapter,line){
 ids(chapter,line);const response=await env.ASSETS.fetch(new Request(`https://assets.invalid/data/chapters/${chapter}.json`));
 if(!response.ok)fail(404,'not_found','Không tìm thấy chương.');const data=await response.json();
 const matches=(data.scenes||[]).flatMap(s=>s.lines||[]).filter(row=>String(row.line_id)===line);
 if(matches.length>1)fail(409,'ambiguous_id','ID câu bị trùng trong nguồn; cần kiểm tra dữ liệu.');if(matches.length===1)return matches[0];
 fail(404,'not_found','Không tìm thấy ID câu trong nguồn hiện tại.');
}
async function insertBaseline(env,line){
 const values=COLS.map(k=>line[k]??null);
 await stmt(env,`INSERT OR IGNORE INTO lines (${COLS.join(',')}) VALUES (${COLS.map(()=>'?').join(',')})`,values).run();
}
function eventStatement(env,before,after,type,actor,reason,id,time,guardSql='',guardValues=[]){
 return stmt(env,`INSERT INTO history(id,chapter_id,line_id,event_type,actor,created_at,reason,old_text,new_text,old_status,new_status,revision,source_hash,snapshot_json) SELECT ?,?,?,?,?,?,?,?,?,?,?,?,?,? ${guardSql}`,[id,before.chapter_id,before.line_id,type,actor,time,reason,before.new_vi,after.new_vi,before.status,after.status,after.revision,after.source_hash,JSON.stringify(after),...guardValues]);
}
async function ensureLine(env,chapter,line,raw){
 const base=await normalizeLine(chapter,raw||await rawLine(env,chapter,line));await insertBaseline(env,base);
 let current=await getLine(env,chapter,line);
 if(current.source_hash!==base.source_hash){
  const after={...current,en:base.en,source_hash:base.source_hash,status:'needs_review',revision:current.revision+1,approved_by:null,approved_at:null,previous_source_hash:current.source_hash,previous_source_en:current.en};
  const token=uuid(),time=now();
  const inserted=stmt(env,`INSERT OR IGNORE INTO operations(request_id,payload_hash,nonce,chapter_id,line_id,result_kind,created_at) SELECT ?,?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM lines WHERE chapter_id=? AND line_id=? AND revision=? AND source_hash=?)`,[token,base.source_hash,token,chapter,line,'source_changed',time,chapter,line,current.revision,current.source_hash]);
  const guard='WHERE EXISTS(SELECT 1 FROM operations WHERE request_id=? AND nonce=?)';
  await env.DB.batch([inserted,eventStatement(env,current,after,'source_changed','Hệ thống','Câu nguồn đã thay đổi.',uuid(),time,guard,[token,token]),stmt(env,'UPDATE lines SET en=?,source_hash=?,status=?,revision=?,approved_by=NULL,approved_at=NULL WHERE chapter_id=? AND line_id=? AND revision=? AND EXISTS(SELECT 1 FROM operations WHERE request_id=? AND nonce=?)',[base.en,base.source_hash,'needs_review',after.revision,chapter,line,current.revision,token,token])]);
  current=await getLine(env,chapter,line);
 }
 return current;
}
export async function overlayChapter(chapter,env){
 if(!env.DB)fail(503,'unavailable','Chưa kết nối kho cộng tác.');
 const chapterId=chapter.chapter_id||chapter.id; if(!CHAPTERS.has(chapterId))fail(400,'invalid_id','Chương không hợp lệ.');
 const rows=(await stmt(env,'SELECT * FROM lines WHERE chapter_id=?',[chapterId]).all()).results||[];
 const byId=new Map(rows.map(l=>[l.line_id,l]));
 const counts=(await stmt(env,"SELECT line_id,count(*) AS n FROM proposals WHERE chapter_id=? AND state='pending' GROUP BY line_id",[chapterId]).all()).results||[];
 const pending=new Map(counts.map(l=>[l.line_id,l.n]));
 const scenes=[];
 for(const scene of chapter.scenes||[]){const lines=[];for(const raw of scene.lines||[]){let state=byId.get(String(raw.line_id));if(!state||state.en!==String(raw.en||''))state=await ensureLine(env,chapterId,String(raw.line_id),raw);lines.push({...raw,...state,pending_proposals:pending.get(String(raw.line_id))||0});}scenes.push({...scene,lines});}
 return {...chapter,scenes};
}
async function reviewerAllowed(request,env){
 const supplied=request.headers.get('X-Reviewer-Key')||'';
 if(!env.REVIEWER_KEY||!supplied)return false;
 const a=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(supplied)));
 const b=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(env.REVIEWER_KEY)));
 let difference=0;for(let i=0;i<a.length;i++)difference|=a[i]^b[i];return difference===0;
}
function guards(body,current){
 if(!Number.isSafeInteger(body.base_revision)||body.base_revision<0||typeof body.base_source_hash!=='string'||!/^[a-f0-9]{64}$/.test(body.base_source_hash))fail(400,'missing_guard','Thiếu phiên bản hoặc hash nguồn.');
 if(body.base_revision!==current.revision||body.base_source_hash!==current.source_hash)fail(409,'conflict','Câu đã được cập nhật. Hãy xem bản mới trước khi gửi lại.',current);
}
function validateTranslation(en,text){
 const target=bounded(text,'Bản dịch',20000,true).normalize('NFC');
 const count=value=>{const m=new Map();for(const token of value.match(TOKEN)||[])m.set(token,(m.get(token)||0)+1);return m;};
 const source=count(en),translated=count(target);
 for(const [token,n]of source)if(translated.get(token)!==n)fail(400,'tokens','Bản dịch cần giữ nguyên mã và số lần xuất hiện: '+token);
 for(const [token,n]of translated)if(source.get(token)!==n)fail(400,'tokens','Bản dịch có mã hệ thống thừa: '+token);
 const tags=value=>(value.match(TOKEN)||[]).filter(token=>token.startsWith('<')||/^\[\/?(?:color|size|b|i|url|sprite)/.test(token));
 if(JSON.stringify(tags(en))!==JSON.stringify(tags(target)))fail(400,'tokens','Giữ đúng thứ tự và cặp thẻ định dạng của nguồn.');
 return target;
}
async function operationResult(env,op,replayed){
 const line=await getLine(env,op.chapter_id,op.line_id);
 const proposal=op.proposal_id?await stmt(env,'SELECT * FROM proposals WHERE id=?',[op.proposal_id]).first():null;
 return json({success:true,result:op.result_kind,line,...(proposal?{proposal}:{}),replayed});
}
async function mutationContext(request,env,body,kind){
 ids(body.chapter_id,body.line_id);bounded(body.request_id,'Mã yêu cầu',128,true);
 const payload_hash=await sourceHash(JSON.stringify({kind,body}));
 const old=await stmt(env,'SELECT * FROM operations WHERE request_id=?',[body.request_id]).first();
 if(old){if(old.payload_hash!==payload_hash)fail(409,'request_reused','Mã yêu cầu đã dùng cho nội dung khác.');return {replay:await operationResult(env,old,true)};}
 const current=await ensureLine(env,body.chapter_id,body.line_id);
 const raced=await stmt(env,'SELECT * FROM operations WHERE request_id=?',[body.request_id]).first();if(raced){if(raced.payload_hash!==payload_hash)fail(409,'request_reused','Mã yêu cầu đã dùng cho nội dung khác.');return {replay:await operationResult(env,raced,true)};}
 guards(body,current);
 return {current,payload_hash};
}
async function commitMutation(env,body,payload_hash,current,after,eventType,actor,reason,resultKind,extra=[],proposalId=null){
 const nonce=uuid(),time=now();
 const guard='WHERE EXISTS(SELECT 1 FROM operations WHERE request_id=? AND nonce=?)';
 const values=[body.request_id,payload_hash,nonce,current.chapter_id,current.line_id,resultKind,proposalId,time,current.chapter_id,current.line_id,current.revision,current.source_hash];
 const insert=stmt(env,'INSERT OR IGNORE INTO operations(request_id,payload_hash,nonce,chapter_id,line_id,result_kind,proposal_id,created_at) SELECT ?,?,?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM lines WHERE chapter_id=? AND line_id=? AND revision=? AND source_hash=?)',values);
 const extras=extra.map(make=>make(guard,[body.request_id,nonce]));
 const columns=COLS.filter(k=>k!=='chapter_id'&&k!=='line_id');
 const update=stmt(env,`UPDATE lines SET ${columns.map(k=>k+'=?').join(',')} WHERE chapter_id=? AND line_id=? AND revision=? AND source_hash=? AND EXISTS(SELECT 1 FROM operations WHERE request_id=? AND nonce=?)`,[...columns.map(k=>after[k]??null),current.chapter_id,current.line_id,current.revision,current.source_hash,body.request_id,nonce]);
 await env.DB.batch([insert,...extras,eventStatement(env,current,after,eventType,actor,reason,uuid(),time,guard,[body.request_id,nonce]),update]);
 const operation=await stmt(env,'SELECT * FROM operations WHERE request_id=?',[body.request_id]).first();
 if(!operation)fail(409,'conflict','Câu đã được người khác cập nhật. Bản đang nhập chưa được ghi đè.',await getLine(env,current.chapter_id,current.line_id));
 if(operation.payload_hash!==payload_hash)fail(409,'request_reused','Mã yêu cầu đã dùng cho nội dung khác.');
 return operationResult(env,operation,operation.nonce!==nonce);
}
async function submit(request,env,body){
 const actor=bounded(body.translator,'Người dịch',80,true);
 if(!['human','machine'].includes(body.origin))fail(400,'invalid_origin','Hãy chọn nguồn bản dịch.');
 const notes=bounded(body.notes??'','Ghi chú',4000),detail=bounded(body.reason_detail??'','Lý do chi tiết',2000);
 const ctx=await mutationContext(request,env,body,'submit');if(ctx.replay)return ctx.replay;
 const current=ctx.current,text=validateTranslation(current.en,body.text_vi),time=now();
 if(!hasTranslation(current)){
  const after={...current,new_vi:text,translator:actor,status:body.origin==='machine'?'machine_pending':'pending',translation_origin:body.origin,notes,revision:current.revision+1,updated_at:time,approved_by:null,approved_at:null,provenance:'contributor'};
  return commitMutation(env,body,ctx.payload_hash,current,after,'translation_saved',actor,'Bản dịch đầu tiên.','saved');
 }
 if(!['meaning','pronouns','naturalness','other'].includes(body.reason))fail(400,'reason_required','Chọn lý do đề xuất sửa.');
 if(body.reason==='other'&&!detail)fail(400,'reason_required','Nhập lý do đề xuất sửa.');
 if(text===current.new_vi&&notes===current.notes)fail(400,'no_change','Đề xuất chưa có thay đổi.');
 const id=uuid(),after={...current,revision:current.revision+1};
 const extra=(guard,bind)=>stmt(env,`INSERT INTO proposals(id,chapter_id,line_id,text_vi,translator,origin,notes,reason,reason_detail,created_at,state,base_revision,base_source_hash,base_text) SELECT ?,?,?,?,?,?,?,?,?,?,'pending',?,?,? ${guard}`,[id,current.chapter_id,current.line_id,text,actor,body.origin,notes,body.reason,detail,time,current.revision,current.source_hash,current.new_vi,...bind]);
 return commitMutation(env,body,ctx.payload_hash,current,after,'proposal_created',actor,body.reason+(detail?': '+detail:''),'proposed',[extra],id);
}
async function report(request,env,body){
 const actor=bounded(body.translator,'Người báo',80,true),reason=bounded(body.reason,'Lý do',2000,true);
 const ctx=await mutationContext(request,env,body,'report');if(ctx.replay)return ctx.replay;
 const after={...ctx.current,status:'needs_review',revision:ctx.current.revision+1,approved_by:null,approved_at:null};
 return commitMutation(env,body,ctx.payload_hash,ctx.current,after,'reported',actor,reason,'reported');
}
async function review(request,env,body){
 if(!env.REVIEWER_KEY)fail(503,'review_unavailable','Chưa cấu hình quyền duyệt.');
 if(!await reviewerAllowed(request,env))fail(403,'forbidden','Mã quản trị không hợp lệ hoặc chưa được nhập.');
 const actor=bounded(body.reviewer,'Người duyệt',80,true),reason=bounded(body.reason??'','Lý do',2000);
 if(!['approve','accept','reject','restore'].includes(body.action))fail(400,'invalid_action','Thao tác duyệt không hợp lệ.');
 const ctx=await mutationContext(request,env,body,'review');if(ctx.replay)return ctx.replay;
 const current=ctx.current,time=now();let after={...current,revision:current.revision+1},eventType,resultKind,proposalId=null;const extra=[];
 if(body.action==='approve'){
  if(!hasTranslation(current))fail(400,'empty_translation','Câu chưa có bản dịch để duyệt.');
  validateTranslation(current.en,current.new_vi);
  after={...after,status:'approved',approved_by:actor,approved_at:time};eventType='approved';resultKind='approved';
 }else if(body.action==='accept'||body.action==='reject'){
  bounded(body.proposal_id,'ID đề xuất',128,true);
  const proposal=await stmt(env,'SELECT * FROM proposals WHERE id=? AND chapter_id=? AND line_id=?',[body.proposal_id,current.chapter_id,current.line_id]).first();
  if(!proposal)fail(404,'not_found','Không tìm thấy đề xuất của câu này.');
  if(proposal.state!=='pending')fail(409,'proposal_closed','Đề xuất đã được xử lý.',current);
  if(body.action==='accept'){
   if(proposal.base_source_hash!==current.source_hash||proposal.base_text!==current.new_vi)fail(409,'proposal_stale','Bản đang dùng hoặc câu nguồn đã thay đổi. Cần tạo đề xuất mới dựa trên bản hiện tại.',current);
   const text=validateTranslation(current.en,proposal.text_vi);
   after={...after,new_vi:text,translator:proposal.translator,translation_origin:proposal.origin,notes:proposal.notes,status:'approved',updated_at:time,approved_by:actor,approved_at:time,provenance:'contributor'};
   eventType='proposal_accepted';resultKind='accepted';
  }else{if(!reason)fail(400,'reason_required','Nhập lý do từ chối.');eventType='proposal_rejected';resultKind='rejected';}
  proposalId=proposal.id;const state=body.action==='accept'?'accepted':'rejected';
  extra.push((guard,bind)=>stmt(env,`UPDATE proposals SET state=?,reviewed_by=?,reviewed_at=? WHERE id=? AND state='pending' ${guard.replace(/^WHERE/,'AND')}`,[state,actor,time,proposal.id,...bind]));
 }else{
  bounded(body.history_id,'ID lịch sử',128,true);if(!reason)fail(400,'reason_required','Nhập lý do khôi phục.');
  const history=await stmt(env,'SELECT * FROM history WHERE id=? AND chapter_id=? AND line_id=?',[body.history_id,current.chapter_id,current.line_id]).first();
  if(!history)fail(404,'not_found','Không tìm thấy phiên bản cần khôi phục.');
  let snapshot;try{snapshot=JSON.parse(history.snapshot_json);}catch{fail(400,'invalid_snapshot','Phiên bản lịch sử không có dữ liệu khôi phục.');}
  if(snapshot.source_hash!==current.source_hash)fail(409,'source_changed','Câu nguồn của phiên bản cũ đã thay đổi. Hãy tạo đề xuất mới.',current);
  const text=validateTranslation(current.en,snapshot.new_vi);
  after={...after,new_vi:text,translator:snapshot.translator||'',translation_origin:ORIGINS.has(snapshot.translation_origin)?snapshot.translation_origin:'unknown',notes:snapshot.notes||'',status:'needs_review',updated_at:time,approved_by:null,approved_at:null,provenance:'restored'};
  eventType='restored';resultKind='restored';
 }
 return commitMutation(env,body,ctx.payload_hash,current,after,eventType,actor,reason,resultKind,extra,proposalId);
}
async function historyResponse(env,chapter,line,cursor,proposalCursor){
 const current=await ensureLine(env,chapter,line);let condition='',values=[chapter,line];
 if(cursor){const split=cursor.indexOf(':');const revision=Number(cursor.slice(0,split)),id=cursor.slice(split+1);if(split<1||!Number.isSafeInteger(revision)||revision<0||!validId(id,128))fail(400,'invalid_cursor','Mốc lịch sử không hợp lệ.');condition=' AND (revision<? OR (revision=? AND id<?))';values.push(revision,revision,id);}
 const records=(await stmt(env,`SELECT * FROM history WHERE chapter_id=? AND line_id=?${condition} ORDER BY revision DESC,id DESC LIMIT 101`,values).all()).results||[];
 const more=records.length>100,visible=records.slice(0,100);const last=visible.at(-1);
 const history=visible.map(row=>{const{snapshot_json,...entry}=row;let snapshot=null;try{snapshot=JSON.parse(snapshot_json);}catch{}return {...entry,snapshot};});
 let proposalCondition='',proposalValues=[chapter,line];
 if(proposalCursor){const split=proposalCursor.indexOf('|'),created=proposalCursor.slice(0,split),id=proposalCursor.slice(split+1);if(split<1||created.length>40||!Number.isFinite(Date.parse(created))||!validId(id,128))fail(400,'invalid_cursor','Mốc đề xuất không hợp lệ.');proposalCondition=' AND (created_at<? OR (created_at=? AND id<?))';proposalValues.push(created,created,id);}
 const proposalRows=(await stmt(env,`SELECT * FROM proposals WHERE chapter_id=? AND line_id=? AND state='pending'${proposalCondition} ORDER BY created_at DESC,id DESC LIMIT 101`,proposalValues).all()).results||[];
 const proposals=proposalRows.slice(0,100),lastProposal=proposals.at(-1),proposals_next_cursor=proposalRows.length>100?lastProposal.created_at+'|'+lastProposal.id:null;
 return json({success:true,line:current,history,proposals,proposals_next_cursor,next_cursor:more?`${last.revision}:${last.id}`:null,history_provenance:'History records reflect operations since collaboration was enabled; earlier edits may be unavailable.'});
}
export async function handleCollaboration(request,env){
 try{
  const url=new URL(request.url),path=url.pathname;
  if(path==='/api/collab/role'&&request.method==='GET')return json({success:true,can_review:await reviewerAllowed(request,env)});
  if(path==='/api/collab/status'&&request.method==='GET'){let available=false;if(env.DB){try{available=!!await stmt(env,"SELECT value FROM collaboration_meta WHERE key='schema_version'").first();}catch{}}return json({success:true,version:1,can_write:available});}
  if(!env.DB)fail(503,'unavailable','Kho cộng tác chưa khả dụng. Bản nháp chưa được gửi.');
  if(request.method==='GET'){
   const chapter=url.searchParams.get('chapter_id'),line=url.searchParams.get('line_id');ids(chapter,line);
   if(path==='/api/collab/line')return json({success:true,line:await ensureLine(env,chapter,line)});
   if(path==='/api/collab/history')return await historyResponse(env,chapter,line,url.searchParams.get('cursor'),url.searchParams.get('proposal_cursor'));
   fail(404,'not_found','Không tìm thấy API.');
  }
  if(request.method!=='POST')return json({success:false,code:'method_not_allowed',message:'Phương thức không được hỗ trợ.'},405);
  const origin=request.headers.get('Origin');if(origin&&origin!==url.origin)fail(403,'cross_origin','Yêu cầu không cùng website.');
  const declared=Number(request.headers.get('Content-Length')||0);if(declared>48000)fail(413,'payload_too_large','Nội dung quá dài.');
  const raw=await request.text();if(raw.length>48000)fail(413,'payload_too_large','Nội dung quá dài.');
  let body;try{body=JSON.parse(raw);}catch{fail(400,'invalid_json','Nội dung gửi không phải JSON hợp lệ.');}
  if(!body||typeof body!=='object'||Array.isArray(body))fail(400,'invalid_payload','Nội dung gửi không hợp lệ.');
  if(path==='/api/collab/submit')return await submit(request,env,body);
  if(path==='/api/collab/report')return await report(request,env,body);
  if(path==='/api/collab/review')return await review(request,env,body);
  fail(404,'not_found','Không tìm thấy API.');
 }catch(error){
  if(error instanceof DomainError)return json({success:false,code:error.code,message:error.message,...(error.line?{line:error.line}:{})},error.status);
  return json({success:false,code:'internal_error',message:'Không thể lưu lúc này. Bản nháp chưa bị thay đổi; hãy thử lại.'},500);
 }
}
