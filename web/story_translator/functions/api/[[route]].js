/**
 * Cloudflare Pages Functions - API Proxy Router
 * Đường dẫn: functions/api/[[route]].js
 * 
 * Chức năng:
 * Proxy mọi request từ Web Trạm Dịch (/api/save_line, /api/status, /api/glossary...) 
 * sang Google Apps Script Web App của dự án Stella Sora.
 */

// URL mặc định của Google Apps Script Web App (Có thể ghi đè bằng Cloudflare Environment Variable 'GAS_WEB_APP_URL')
const DEFAULT_GAS_URL = "https://script.google.com/macros/s/AKfycbwhB90dQ5YL27wBkeXeQIoI18TZO3KXXhgwdb0iG96rqwBQUfk7ztZwGjdG_tEwElDhFw/exec";

export async function onRequest(context) {
    const { request, env } = context;
    const gasUrl = (env && env.GAS_WEB_APP_URL) ? env.GAS_WEB_APP_URL : DEFAULT_GAS_URL;

    // 1. Xử lý preflight CORS OPTIONS request
    if (request.method === "OPTIONS") {
        return new Response(null, {
            status: 204,
            headers: {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Max-Age": "86400",
            }
        });
    }

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
        const url = new URL(request.url);
        const targetUrl = new URL(gasUrl);

        // Copy query parameters
        url.searchParams.forEach((value, key) => {
            targetUrl.searchParams.set(key, value);
        });

        // Xác định action từ subpath (ví dụ: /api/save_line -> action=save_line)
        const pathSegments = url.pathname.replace(/^\/api\/?/, "").split("/").filter(Boolean);
        const subAction = pathSegments.length > 0 ? pathSegments[0] : "";
        if (subAction && !targetUrl.searchParams.has("action")) {
            if (subAction === "sync_glossary" || subAction === "glossary") {
                targetUrl.searchParams.set("action", "get_glossary");
            } else {
                targetUrl.searchParams.set("action", subAction);
            }
        }

        let fetchOptions = {
            method: (subAction === "sync_glossary" || subAction === "glossary") ? "GET" : request.method,
            headers: {
                "Content-Type": "text/plain;charset=utf-8"
            },
            redirect: "follow"
        };

        if (fetchOptions.method === "POST" || fetchOptions.method === "PUT") {
            const bodyText = await request.text();
            fetchOptions.body = bodyText;
        }

        // Gọi sang Google Apps Script
        const gasResponse = await fetch(targetUrl.toString(), fetchOptions);
        const responseBody = await gasResponse.text();

        return new Response(responseBody, {
            status: gasResponse.status,
            headers: {
                "Content-Type": "application/json;charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
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
                "Access-Control-Allow-Origin": "*"
            }
        });
    }
}
