/**
 * TokenModel.js
 * Quản lý bóc tách mã thẻ kỹ thuật, token hệ thống và thuật toán kiểm tra tính toàn vẹn
 */

const SYSTEM_TOKEN_REGEX = /==[A-Za-z0-9_]+==|<[^<>\n]+>|\{[0-9]+\}|\$\{[^{}\n]+\}|\$[A-Za-z_][\w.]*\$|%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs]|\[\/?(?:color|size|b|i|url|sprite)[^\]\n]*\]/g;

// Extracts all system tokens from a string
function extractTokens(text) {
    if (!text) return [];
    const regex = new RegExp(SYSTEM_TOKEN_REGEX.source, 'g');
    const matches = text.match(regex);
    return matches || [];
}

// Validates if all tokens in sourceText exist in targetText
function validateTokens(sourceText, targetText) {
    const srcTokens = extractTokens(sourceText);
    if (srcTokens.length === 0) {
        return { isValid: true, sourceTokens: [], missing: [] };
    }

    const tgtTokens = extractTokens(targetText);
    const tgtCounts = {};
    tgtTokens.forEach(t => {
        tgtCounts[t] = (tgtCounts[t] || 0) + 1;
    });

    const missing = [];
    const srcCounts = {};
    srcTokens.forEach(t => {
        srcCounts[t] = (srcCounts[t] || 0) + 1;
    });

    for (const [token, count] of Object.entries(srcCounts)) {
        const inTarget = tgtCounts[token] || 0;
        if (inTarget < count) {
            for (let i = 0; i < (count - inTarget); i++) {
                missing.push(token);
            }
        }
    }

    return {
        isValid: missing.length === 0,
        sourceTokens: srcTokens,
        missing: missing
    };
}
