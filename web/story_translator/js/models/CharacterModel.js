/**
 * CharacterModel.js
 * Quản lý dữ liệu nhân vật, hình ảnh standee, avatar, quote và voice lines
 */

let charactersDict = {};

async function loadCharactersMetadata() {
    try {
        let data = null;
        try {
            const res = await fetch("/api/characters");
            if (res.ok) data = await res.json();
        } catch (_) {}
        if (!data) {
            const res = await fetch("data/characters.json");
            if (res.ok) data = await res.json();
        }
        if (data && Array.isArray(data)) {
            data.forEach(c => {
                charactersDict[c.nameEN.toLowerCase()] = c;
                const firstName = c.nameEN.split(" ").pop().toLowerCase();
                charactersDict[firstName] = c;
            });
            if (typeof renderAvatarGrid === "function") {
                renderAvatarGrid();
            }
        }
    } catch (e) {
        console.error("Lỗi nạp characters:", e);
    }
}
