/** TramVH original icon set. Only known asset IDs can enter markup. */
const TRAM_ICON_IDS = new Set(["home", "chapters", "scenes", "visual-novel", "list", "previous", "next", "menu", "dialogue", "translate", "edit", "quill", "save", "save-next", "glossary", "tokens", "copy", "undo", "search", "filter", "sync", "upload", "download", "sheet", "external-link", "settings", "close", "help", "approved", "translated", "pending", "warning", "error", "info", "check", "profile", "community", "trophy", "medal", "star", "xp", "sun", "moon", "music", "music-off", "volume", "volume-off", "play", "pause"]);
function tramIcon(id) {
    const name = TRAM_ICON_IDS.has(id) ? id : "info";
    const base = "assets/tramvh-icons-r01/svg/";
    return `<span class="tram-icon" aria-hidden="true"><img class="tram-icon-light" src="${base}light/${name}.svg" alt=""><img class="tram-icon-dark" src="${base}dark/${name}.svg" alt=""></span>`;
}
