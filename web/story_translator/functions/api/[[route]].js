/**
 * Cloudflare Pages Functions - API Proxy Router
 * Đường dẫn: functions/api/[[route]].js
 * 
 * Chỉ proxy các API thuật ngữ và bảng xếp hạng còn dùng Google Apps Script.
 * Mọi lệnh ghi bản dịch phải đi qua Worker/D1.
 */

// URL mặc định của Google Apps Script Web App (Có thể ghi đè bằng Cloudflare Environment Variable 'GAS_WEB_APP_URL')
const DEFAULT_GAS_URL = "https://script.google.com/macros/s/AKfycbwhB90dQ5YL27wBkeXeQIoI18TZO3KXXhgwdb0iG96rqwBQUfk7ztZwGjdG_tEwElDhFw/exec";

export async function onRequest(context) {
    const { request, env } = context;
    const url = new URL(request.url);
    const allowed = {
        "/api/glossary": { action: "get_glossary", method: "GET" },
        "/api/sync_glossary": { action: "get_glossary", method: "GET" },
        "/api/leaderboard": { action: "get_leaderboard", method: "GET" },
        "/api/add_glossary_term": { action: "add_glossary_term", method: "POST" },
    };
    const route = url.pathname;
    const apiHeaders = { "Content-Type": "application/json;charset=utf-8", "Cache-Control": "no-store" };
    if (route === "/api/save_line") return new Response(JSON.stringify({ success: false, code: "upgrade_required", error: "Luồng lưu cũ đã đóng. Tải lại TramVH để gửi qua Worker/D1." }), { status: 426, headers: apiHeaders });
    const endpoint = allowed[route];
    if (!endpoint) return new Response(JSON.stringify({ success: false, code: "not_found", error: "Không tìm thấy API." }), { status: 404, headers: apiHeaders });
    if (request.method !== endpoint.method) return new Response(JSON.stringify({ success: false, code: "method_not_allowed", error: "Phương thức không được hỗ trợ." }), { status: 405, headers: apiHeaders });
    const origin = request.headers.get("Origin");
    if (request.method === "POST" && origin && origin !== url.origin) return new Response(JSON.stringify({ success: false, code: "cross_origin", error: "Yêu cầu khác nguồn bị từ chối." }), { status: 403, headers: apiHeaders });
    const gasUrl = (env && env.GAS_WEB_APP_URL) ? env.GAS_WEB_APP_URL : DEFAULT_GAS_URL;

    if (!gasUrl) {
        return new Response(JSON.stringify({
            success: false,
            error: "Chưa cấu hình GAS_WEB_APP_URL trong Cloudflare Pages Settings hoặc DEFAULT_GAS_URL!"
        }), {
            status: 500,
            headers: {
                "Content-Type": "application/json;charset=utf-8",
                "Access-Control-Allow-Origin": "*"
            }
        });
    }

    try {
        const targetUrl = new URL(gasUrl);

        targetUrl.searchParams.set("action", endpoint.action);

        let fetchOptions = {
            method: endpoint.method,
            headers: {
                "Content-Type": "text/plain;charset=utf-8"
            },
            redirect: "follow"
        };

        if (fetchOptions.method === "POST") {
            let body;
            try { body = await request.json(); } catch { return new Response(JSON.stringify({success:false,code:"invalid_json"}), {status:400,headers:apiHeaders}); }
            if (!body || typeof body !== "object" || Array.isArray(body)) return new Response(JSON.stringify({success:false,code:"invalid_payload"}), {status:400,headers:apiHeaders});
            fetchOptions.body = JSON.stringify({
                action: endpoint.action,
                en: body.en,
                vi: body.vi,
                category: body.category,
                notes: body.notes,
                status: body.status,
                translator: body.translator,
            });
        }

        // Gọi sang Google Apps Script
        const gasResponse = await fetch(targetUrl.toString(), fetchOptions);
        const responseBody = await gasResponse.text();

        return new Response(responseBody, {
            status: gasResponse.status,
            headers: {
                "Content-Type": "application/json;charset=utf-8",
                "Cache-Control": "no-store"
            }
        });

    } catch (err) {
        return new Response(JSON.stringify({
            success: false,
            error: "Lỗi Proxy Cloudflare Functions: " + err.message
        }), {
            status: 502,
            headers: {
                "Content-Type": "application/json;charset=utf-8",
                "Cache-Control": "no-store"
            }
        });
    }
}
