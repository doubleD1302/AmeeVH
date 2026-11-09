import { handleCollaboration, overlayChapter } from './collaboration.mjs';
import { getGlossary, getMerge, getChapterReferences } from './sheets-source.mjs';
const GAS = 'https://script.google.com/macros/s/AKfycbwhB90dQ5YL27wBkeXeQIoI18TZO3KXXhgwdb0iG96rqwBQUfk7ztZwGjdG_tEwElDhFw/exec';
const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
async function assetJSON(env, request, path){const response=await env.ASSETS.fetch(new Request(new URL(path,request.url)));if(!response.ok)throw Error('Không tìm thấy dữ liệu.');return response.json();}
async function chapter(env,request,id){
    const chapters=await assetJSON(env,request,'/data/chapters.json');
    if(!chapters.some(c=>c.id===id))throw Error('Chương không hợp lệ.');
    const data=await assetJSON(env,request,'/data/chapters/'+encodeURIComponent(id)+'.json');
    const live=await overlayChapter(data,env);
    try{return await getChapterReferences(live);}catch{return {...live,sheet_sync:{status:'unavailable',matched:0}};}
}
export default {
 async fetch(request,env){
    const url=new URL(request.url),path=url.pathname;
    if(!path.startsWith('/api/'))return env.ASSETS.fetch(request);
    try{
        const origin=request.headers.get('Origin');
        if(request.method!=='GET'&&origin&&origin!==url.origin)return json({success:false,error:'Yêu cầu khác nguồn bị từ chối.'},403);
        if(path.startsWith('/api/collab/'))return await handleCollaboration(request,env);
        if(path==='/api/save_line')return json({success:false,code:'upgrade_required',error:'Luồng lưu cũ đã đóng. Tải lại TramVH để gửi bản dịch có kiểm tra phiên bản.'},426);
        if((path==='/api/glossary'||path==='/api/sync_glossary')&&request.method==='GET')return json({success:true,terms:await getGlossary(),source:'google_sheet'});
        if(path==='/api/sheet_reference'&&request.method==='GET')return json(await getMerge(url.searchParams.get('group')));
        if(path==='/api/add_glossary_term')return json({success:false,code:'read_only',error:'Glossary trên web chỉ đọc từ Google Sheet; chưa bật ghi hai chiều.'},501);
        if(path==='/api/chapter_data'&&request.method==='GET')return json({...await chapter(env,request,url.searchParams.get('id')),collaboration_available:true});
        if(path==='/api/export_chapter'&&request.method==='GET'){
            const data=await chapter(env,request,url.searchParams.get('id'));
            return new Response(JSON.stringify(data,null,2),{headers:{...headers,'Content-Disposition':'attachment; filename="TramVH-'+data.chapter_id+'.json"'}});
        }
        if(path==='/api/chapters'&&request.method==='GET'){
            const chapters=await assetJSON(env,request,'/data/chapters.json');
            const stats=(await env.DB.prepare("SELECT chapter_id,count(*) AS total_lines,sum(CASE WHEN length(trim(new_vi))>0 THEN 1 ELSE 0 END) AS translated_lines,sum(CASE WHEN status='approved' THEN 1 ELSE 0 END) AS approved_lines FROM lines GROUP BY chapter_id").all()).results || [];
            const byId=new Map(stats.map(row=>[row.chapter_id,row]));
            return json(chapters.map(item=>{const counts=byId.get(item.id);return counts?{...item,...counts,progress_pct:counts.total_lines?Math.round(counts.translated_lines*1000/counts.total_lines)/10:0}:item;}));
        }
        if(path==='/api/characters'&&request.method==='GET')return json(await assetJSON(env,request,'/data/characters.json'));
        // Preserve the existing glossary/leaderboard integration, never proxy old line saves.
        const proxy={ '/api/leaderboard':'get_leaderboard' };
        if(proxy[path]){
            const target=new URL(GAS);target.searchParams.set('action',proxy[path]);
            const options={method:'GET',redirect:'follow',signal:AbortSignal.timeout(15000)};
            const response=await fetch(target,options);if(!response.ok)throw Error('Kho thuật ngữ chưa phản hồi.');const data=await response.json();return json(data);
        }
        return json({success:false,error:'Không tìm thấy API.'},404);
    }catch(error){return json({success:false,code:'service_unavailable',error:error.message || 'Máy chủ chưa sẵn sàng.'},503);}
 }
};
