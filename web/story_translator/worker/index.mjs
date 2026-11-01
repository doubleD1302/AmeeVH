import { handleCollaboration, overlayChapter } from './collaboration.mjs';
const GAS = 'https://script.google.com/macros/s/AKfycbwhB90dQ5YL27wBkeXeQIoI18TZO3KXXhgwdb0iG96rqwBQUfk7ztZwGjdG_tEwElDhFw/exec';
const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
async function assetJSON(env, request, path){const response=await env.ASSETS.fetch(new Request(new URL(path,request.url)));if(!response.ok)throw Error('Không tìm thấy dữ liệu.');return response.json();}
async function chapter(env,request,id){
    const chapters=await assetJSON(env,request,'/data/chapters.json');
    if(!chapters.some(c=>c.id===id))throw Error('Chương không hợp lệ.');
    const data=await assetJSON(env,request,'/data/chapters/'+encodeURIComponent(id)+'.json');
    return overlayChapter(data,env);
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
        const proxy={ '/api/glossary':'get_glossary','/api/sync_glossary':'get_glossary','/api/leaderboard':'get_leaderboard','/api/add_glossary_term':'add_glossary_term' };
        if(proxy[path]){
            if(path==='/api/add_glossary_term'&&request.method!=='POST')return json({success:false,error:'POST required'},405);
            const target=new URL(GAS);target.searchParams.set('action',proxy[path]);
            const options={method:path==='/api/add_glossary_term'?'POST':'GET',redirect:'follow',signal:AbortSignal.timeout(15000)};
            if(options.method==='POST'){const body=await request.json();options.body=JSON.stringify({...body,action:'add_glossary_term'});options.headers={'Content-Type':'text/plain;charset=utf-8'};}
            const response=await fetch(target,options);if(!response.ok)throw Error('Kho thuật ngữ chưa phản hồi.');const data=await response.json();return json(data);
        }
        return json({success:false,error:'Không tìm thấy API.'},404);
    }catch(error){return json({success:false,code:'service_unavailable',error:error.message || 'Máy chủ chưa sẵn sàng.'},503);}
 }
};
