const COOKIE_NAME = 'tramvh_session';
const sharedCookie = (request, token) => `${COOKIE_NAME}=${token}; Path=/api; HttpOnly; SameSite=Lax; Max-Age=31536000${new URL(request.url).protocol === 'https:' ? '; Secure' : ''}`;
const legacyCookie = request => `${COOKIE_NAME}=; Path=/api/collab; HttpOnly; SameSite=Lax; Max-Age=0${new URL(request.url).protocol === 'https:' ? '; Secure' : ''}`;
const stmt = (env, sql, values=[]) => env.DB.prepare(sql).bind(...values);
const sha256 = async text => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map(byte=>byte.toString(16).padStart(2,'0')).join('');

export async function sessionUser(request, env, create=false) {
    const cookie = request.headers.get('Cookie') || '';
    const token = cookie.split(';').map(part=>part.trim()).find(part=>part.startsWith(COOKIE_NAME+'='))?.slice(COOKIE_NAME.length+1);
    if (token && /^[a-f0-9]{64}$/.test(token)) {
        const user = await stmt(env,'SELECT id,display_name FROM users WHERE session_hash=?',[await sha256(token)]).first();
        if (user) {
            const migrate = new URL(request.url).pathname === '/api/collab/me';
            return {user,cookie:migrate ? sharedCookie(request,token) : null,legacyCookie:migrate ? legacyCookie(request) : null,created:false};
        }
    }
    if (!create) return {user:null,cookie:null,created:false};
    const bytes = crypto.getRandomValues(new Uint8Array(32));
    const newToken = [...bytes].map(byte=>byte.toString(16).padStart(2,'0')).join('');
    const user = {id:crypto.randomUUID(),display_name:'Dịch giả'};
    const time = new Date().toISOString();
    await stmt(env,'INSERT INTO users(id,session_hash,display_name,created_at,updated_at) VALUES(?,?,?,?,?)',[user.id,await sha256(newToken),user.display_name,time,time]).run();
    return {user,cookie:sharedCookie(request,newToken),legacyCookie:legacyCookie(request),created:true};
}

export function attachSession(response, session) {
    if (!session?.cookie) return response;
    const headers = new Headers(response.headers);
    headers.set('Set-Cookie',session.cookie);
    if (session.legacyCookie) headers.append('Set-Cookie',session.legacyCookie);
    return new Response(response.body,{status:response.status,statusText:response.statusText,headers});
}
