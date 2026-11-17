/**
 * GlossaryGroups.js
 * Bộ lọc 7 nhóm cho từ điển thuật ngữ.
 *
 * Nhóm là trường PHÁI SINH (term.group), không ghi đè `category` gốc của Sheet.
 * Thứ tự quyết định nhóm cho một mục:
 *   1. category đã là nhãn của một nhóm (người dùng chọn khi thêm/sửa thuật ngữ)
 *   2. bảng chỉ định tên chính xác (GLOSSARY_GROUP_OVERRIDES)
 *   3. EN trùng tên nhân vật trong category "character_name"
 *   4. category kỹ thuật của Sheet (character_name, gender_*, ui_text); người nói là quái vật → Gameplay
 *   5. quy tắc từ khóa (GLOSSARY_GROUP_RULES, khớp đầu tiên thắng)
 *   6. mặc định: Lore & Thuật ngữ cốt truyện
 */

const GLOSSARY_GROUPS = [
    { id: "characters",    label: "Nhân vật & Danh xưng",           labelEn: "Characters & Titles" },
    { id: "organizations", label: "Tổ chức & Phe phái",             labelEn: "Organizations & Factions" },
    { id: "world",         label: "Thế giới & Địa lý",              labelEn: "World & Geography" },
    { id: "lore",          label: "Lore & Thuật ngữ cốt truyện",    labelEn: "Lore & Terminology" },
    { id: "items",         label: "Vật phẩm & Trang bị",            labelEn: "Items & Equipment" },
    { id: "gameplay",      label: "Gameplay & Giao diện",           labelEn: "Gameplay & UI" },
    { id: "events",        label: "Sự kiện & Thời gian",            labelEn: "Events & Timeline" }
];

const GLOSSARY_DEFAULT_GROUP = "lore";

/** Nhãn cũ của ô chọn "Phân loại danh mục" → nhóm mới (giữ tương thích dữ liệu đã lưu). */
const GLOSSARY_LEGACY_CATEGORY_GROUPS = {
    "cốt truyện & thế giới": "lore",
    "chiến đấu & kỹ năng": "gameplay",
    "nhân vật & đại từ": "characters",
    "quái vật & boss": "gameplay",
    "giao diện & hệ thống": "gameplay",
    "địa danh & bản đồ": "world",
    "vật phẩm & trang bị": "items"
};

/** Category kỹ thuật trong Sheet "01. Glossary" → nhóm. */
const GLOSSARY_SHEET_CATEGORY_GROUPS = {
    "character_name": "characters",
    "gender_female": "characters",
    "gender_male": "characters",
    "ui_text": "gameplay"
};

/** Chỉ định đích danh (khóa = EN viết thường). Ưu tiên cao hơn quy tắc. */
const GLOSSARY_GROUP_OVERRIDES = (() => {
    const map = {};
    const add = (group, names) => names.forEach(n => { map[n.toLowerCase()] = group; });

    add("characters", [
        "Captain", "Archon", "Director Knight", "Masked Knight", "Grand Inspector", "Granny Marlene",
        "Sentinel of Dawn", "Snowish Festival Messenger", "Snowish Tree Spirit", "Snowish Laru",
        "Treasure Hunter", "Treasure Hunter Leader", "Treasure Hunters", "Crow Rider", "Bunny Duo",
        "Arbiter Gerie", "Dusk Arbiter", "Senators", "CEO", "Freelance Trekker", "Whally", "Matsukawa", "Flavio",
        "Springseek Coronis", "Suntide Willow"
    ]);

    add("organizations", [
        "Society for the Study of Life", "Trekker Association", "Trekkers' House", "Senate",
        "Imperial Guard", "Grace Imperium", "Neo Grace Organization", "New Star Guild", "United Harvest",
        "Fenghuang Diner", "Creta Trading", "Platinum Academy", "Grace Light Academy",
        "Boss Accord Staffing Co.", "Tyrant Accord Staffing Co.", "Daisy Orphanage", "Ash Orphanage"
    ]);

    add("world", [
        "Nova", "Nova Continent", "The White Room", "Wilds", "Mirage",
        "City of a Thousand Monoliths", "Lucky Oasis", "Nocturn Eterna",
        "Frozen Ruins", "Parasitic Garden", "The Retreat", "Waterway Bridge",
        "Cangwu", "Emor", "Norstheim", "Philae", "Dorra"
    ]);

    add("lore", [
        "Grace", "God of Grace", "Eye of Grace", "Stellaroid", "Trekker", "Tyrant", "Monolith", "The Monolith",
        "Eternity", "Boss Accord", "Tyrant Accord", "Soul trading", "Tetrad Aspects", "Knight's Code",
        "Chronicles of New Nova", "Frozen Path", "white lie",
        "Chariot", "Ebony Star", "Horizon", "Sinister Ritual", "tamago", "sageo",
        "franchise patent", "Ghost", "Wraith", "Kun", "Loong", "Novian", "Novians", "Bayan",
        "Cuteness Dependency Syndrome", "Messis Syndrome"
    ]);

    add("items", [
        "Artifact", "Xuan Shi", "Stellanite Lumina", "Runic Disc", "Soul Key", "Soul Stone", "Seal of Grace", "Journey Ticket", "Monolith Coins",
        "Stella Coin", "Rabbit Pie", "Super Action Pie", "Pep Pep Juice", "Tawny Nightingale",
        "Package", "Wishing Box", "Enhancement Machine",
        "Character Skin", "FateCard", "Penguin Card",
        "Record", "Average Record", "Advanced Record", "Expert Record", "Master Record"
    ]);

    add("gameplay", [
        "Soul Shop", "Monolith Shop", "Monolith Log", "Anecdote", "Authorization", "Recruitment", "Tyrant Growth",
        "Well of Worlds Tyrant Development System", "Disc Harmony Skill", "Wild Rush",
        "Repeated Performance", "Total Bombardment", "Infinite Arena", "Infinity Tower", "Star Tower",
        "Support", "Versatile", "Vanguard", "Boss", "Battle Pass", "Trial Character",
        "Garden of Parasite", "Spirit of Brutality", "Blade of Jade", "Mark", "Proving Grounds",
        "Midas", "Back", "Cancel", "Confirm", "Authorization Lv."
    ]);

    // Quái vật & Boss: không có nhóm riêng trong 7 tiêu chí, xếp vào Gameplay (đối tượng chiến đấu).
    add("gameplay", [
        "Armadillo Fish", "Count of the Duloos", "Enforcer of Silence", "Evernight Emberflies",
        "Fierce Long-Tailed Scorpion", "Gobble Hexhorn Whale", "Golem of Nightmares", "Grotesque Dancer",
        "Guardian of Thorns", "Hexhorn Whale", "The Hexhorn Whale", "Lithe Beauty", "Magishark", "Master Digger",
        "Megahand Enforcer", "Nian", "Nightmare Executioner", "Opera Ghost: Rovina", "Oppressor of Torrents",
        "Plundering Dual Blades", "Protector of Radiance", "Shrubshrew Slinger", "Shrubshrew Warrior",
        "Spellbound Golem", "Subjugator of Firmament", "Suppressor of Lava", "Tainted Mandrake", "Tusk Stomper",
        "Whimagus", "Whirling Crawler", "Whirling Great Glopo", "Wrath Juggernaut", "King Glopo",
        "Rotting Silencer", "Abyssal Sea Sovereign", "Shadow Poison Pool", "Golem Guard", "Gloomfiend",
        "Cursipot", "Lux Stealer", "Crispy Hooves", "Crispy Hooves Deluxe", "Flavor Dread", "Gale Owl", "Lucky Rubbi", "Projectile Striker",
        "Space Walker", "Steam Pot Hammer"
    ]);

    add("events", [
        "Boss Blitz", "Currents and Shadows", "Dust and Flames", "Elegance and Flow", "Flames and Beats",
        "Storm and Thunder", "Shake The Floor", "Thrilling Beat", "Upbeat Party", "Petal Bloom", "Star Pluck",
        "Star Pluck Conquest", "Misstep On One", "Post Haste", "Autumn Equinox", "Monolith Calendar",
        "Never Ending Summer", "Tech Convention", "Monolith Meltdown", "company war",
        "Operation: Shadow Siege", "Through Hostile Depths", "A Future Without Trekkers",
        "Overture of a Shadowy Enigma", "Ghost Ship", "The Ghost Ship", "nautical log", "Cataclysm Survivor",
        "Snowish Festival", "Springseek Festival", "Swimming Fish Festival"
    ]);

    return map;
})();

/** Quy tắc từ khóa trên EN (khớp đầu tiên thắng, không phân biệt hoa thường). */
const GLOSSARY_GROUP_RULES = [
    // Thời gian / sự kiện
    { group: "events", test: /\bmonth$/i },
    { group: "events", test: /\b(festival|equinox|calendar|convention|anniversary)\b/i },

    // Vật phẩm đặc thù trước các từ khóa gameplay (Melody of Lux ≠ Lux)
    { group: "items", test: /^melody of /i },
    { group: "items", test: /\b(coins?|ticket|juice|pie|skin|patent|lumina)\b/i },

    // Thế giới / địa lý
    { group: "world", test: /\b(city|town|district|continent|harbor|market|gate|bridge|street|prison|ruins|greenhouse|oasis|wilds)\b/i },

    // Tổ chức / phe phái
    { group: "organizations", test: /\b(clan|orphanage|bureau|guild|association|troupe|organization|studio|media|academy|company|co\.|society|imperium|finance|homecare|trading|staffing)\b/i },

    // Danh xưng
    { group: "characters", test: /\b(captain|archon|arbiter|inspector|knight|director|senators?|ceo|lord|lady|gentleman|granny|messenger|treasure hunters?|sentinel|rider)\b/i },

    // Gameplay: chỉ số, kỹ năng, chế độ, giao diện
    { group: "gameplay", test: /\b(atk|def|hp|dmg|crit|spd|res|pen|cd|cooldown|energy|shield|dodge|evasion|freeze|frozen|stun|shock|burn|bleed|burst|build|skill|ultimate|attack|dash|resilience|vigor|penetration|accuracy|charge|magazine|capacity|aqua|ignis|terra|ventus|lux|umbra|incapacitated|derivative|vul|minion|boost|reduction|dealt|taken|elemental|ignore|domain|trial|arena|shop|inventory|mailbox|mall|mission|quest|task|claim|deploy|draw|pull|gacha|banner|sweep|quick clear|upgrade|enhance|breakthrough|talent|potential|affinity|heartlink|achievement|settings|notice)\b/i }
];

/** Nhãn người nói trong "character_name" thực chất là quái vật / kẻ địch → Gameplay (cùng nhóm với Boss ở General). */
const GLOSSARY_MONSTER_SPEAKER_RE = /^(Shrubshrew|Glopo Duke|Meadow Blade|Hermit Crab|Weed (Shooter|Brawler)|Alpha Boar|Oven Mimic|Mechanical Dog|Electric Specter|Opera Ghost|Breezy Owl|Gale Owl|Titan-Hand Enforcer|Gauntlet of Rage|Forbidden Beauty|Furnace's Delirium|Entity of Prosperity|Spectral Envoy|Sea Hare|Associated Tree|Symbiotic Tree|Ventus Weed|Water Tower Stellaroid|Ranged Grass|Puppet Soldier|Space Walker|Crispy Hooves|Flavor Dread|Lucky Rubbi|Projectile Striker|Steam Pot Hammer)\b/i;

let _glossaryCharacterNameSet = null;
let _glossaryCharacterNameSource = null;
let _glossaryCharacterNameSize = -1;

function getGlossaryGroups() {
    return GLOSSARY_GROUPS;
}

function getGlossaryGroupById(id) {
    return GLOSSARY_GROUPS.find(g => g.id === id) || null;
}

/** Nhãn nhóm mà category đang trùng (nhãn mới hoặc nhãn cũ của ô chọn), nếu có. */
function glossaryGroupFromCategory(category) {
    const key = String(category || "").trim().toLowerCase();
    if (!key) return null;
    const direct = GLOSSARY_GROUPS.find(g => g.label.toLowerCase() === key || g.labelEn.toLowerCase() === key || g.id === key);
    if (direct) return direct.id;
    return GLOSSARY_LEGACY_CATEGORY_GROUPS[key] || null;
}

function buildGlossaryCharacterNameSet(terms) {
    const size = (terms || []).length;
    if (_glossaryCharacterNameSet && _glossaryCharacterNameSource === terms && _glossaryCharacterNameSize === size) return _glossaryCharacterNameSet;
    const set = new Set();
    (terms || []).forEach(t => {
        if (t && String(t.category || "").trim() === "character_name" && t.en) {
            set.add(String(t.en).trim().toLowerCase());
        }
    });
    _glossaryCharacterNameSet = set;
    _glossaryCharacterNameSource = terms;
    _glossaryCharacterNameSize = size;
    return set;
}

/**
 * Phân nhóm một thuật ngữ → id nhóm.
 * @param {Object} term - { en, vi, category, ... }
 * @param {Array} allTerms - toàn bộ từ điển (dùng để nhận diện tên nhân vật)
 */
function classifyGlossaryGroup(term, allTerms) {
    if (!term) return GLOSSARY_DEFAULT_GROUP;
    const fromCategory = glossaryGroupFromCategory(term.category);
    if (fromCategory) return fromCategory;

    const en = String(term.en || "").trim();
    const enKey = en.toLowerCase();

    if (GLOSSARY_GROUP_OVERRIDES[enKey]) return GLOSSARY_GROUP_OVERRIDES[enKey];

    const sheetCategory = String(term.category || "").trim();
    if (sheetCategory === "character_name" && GLOSSARY_MONSTER_SPEAKER_RE.test(en)) return "gameplay";

    const sheetGroup = GLOSSARY_SHEET_CATEGORY_GROUPS[sheetCategory];
    if (sheetGroup) return sheetGroup;

    if (buildGlossaryCharacterNameSet(allTerms).has(enKey)) return "characters";

    for (const rule of GLOSSARY_GROUP_RULES) {
        if (rule.test.test(en)) return rule.group;
    }
    return GLOSSARY_DEFAULT_GROUP;
}

/** Lấy nhóm (có nhớ đệm trên chính mục). Gọi lại classify khi category/EN đổi. */
function glossaryGroupOf(term, allTerms) {
    if (!term) return GLOSSARY_DEFAULT_GROUP;
    const sig = `${term.en || ""}\u0000${term.category || ""}`;
    if (term._groupSig !== sig || !term.group) {
        term.group = classifyGlossaryGroup(term, allTerms);
        term._groupSig = sig;
    }
    return term.group;
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { GLOSSARY_GROUPS, classifyGlossaryGroup, glossaryGroupOf, glossaryGroupFromCategory, getGlossaryGroupById };
}
