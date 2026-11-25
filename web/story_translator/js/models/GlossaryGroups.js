/**
 * GlossaryGroups.js
 * Bộ lọc 9 nhóm rõ ràng cho từ điển thuật ngữ TramVH.
 *
 * Nhóm là trường PHÁI SINH (term.group), ưu tiên phân loại chuẩn từ build_canonical_glossary.py
 * và giữ tương thích ngược với dữ liệu Google Sheets / chỉnh sửa cục bộ trong localStorage.
 * Thứ tự quyết định nhóm cho một mục:
 *   1. `term.group` hợp lệ và khớp `term.category` (đã phân loại sẵn ở backend/build)
 *   2. `term.category` là nhãn của một nhóm (người dùng chọn hoặc nhãn chuẩn mới/cũ)
 *   3. bảng chỉ định tên chính xác (GLOSSARY_GROUP_OVERRIDES)
 *   4. người nói là quái vật → Quái vật & Thủ lĩnh (`monsters`)
 *   5. `raw_category` / `category` kỹ thuật của Sheet (`character_name`, `gender_*`, `ui_text`)
 *   6. EN trùng tên nhân vật trong `character_name`
 *   7. quy tắc từ khóa (GLOSSARY_GROUP_RULES, khớp đầu tiên thắng)
 *   8. mặc định: Cốt truyện & Lore (`lore`)
 */

const GLOSSARY_GROUPS = [
    {
        id: "characters",
        label: "Nhân vật, NPC & Xưng hô",
        shortLabel: "Nhân vật",
        labelEn: "Characters & Pronouns",
        desc: "Tên nhân vật, NPC, danh xưng, chức danh và đại từ xưng hô"
    },
    {
        id: "organizations",
        label: "Tổ chức & Phe phái",
        shortLabel: "Tổ chức",
        labelEn: "Organizations & Factions",
        desc: "Phe phái, giáo hội, học viện, thương hội và đội nhóm"
    },
    {
        id: "world",
        label: "Thế giới & Địa danh",
        shortLabel: "Địa danh",
        labelEn: "World & Geography",
        desc: "Lục địa, thành phố, quận, địa điểm và công trình"
    },
    {
        id: "lore",
        label: "Cốt truyện & Lore",
        shortLabel: "Lore",
        labelEn: "Lore & Terminology",
        desc: "Thế giới quan, thần linh, hiện tượng và thuật ngữ cốt truyện"
    },
    {
        id: "items",
        label: "Vật phẩm, Đĩa nhạc & Trang phục",
        shortLabel: "Vật phẩm & Đĩa",
        labelEn: "Items, Discs & Skins",
        desc: "Vật phẩm, nguyên liệu, Đĩa nhạc (Disc), trang phục và tiền tệ"
    },
    {
        id: "skills",
        label: "Kỹ năng, Tiềm năng & Chiến đấu",
        shortLabel: "Kỹ năng & Chiến đấu",
        labelEn: "Skills, Potentials & Combat",
        desc: "Kỹ năng, Tiềm năng, nốt nhạc (Melody), chỉ số, nguyên tố và hiệu ứng"
    },
    {
        id: "monsters",
        label: "Quái vật & Thủ lĩnh",
        shortLabel: "Quái & Boss",
        labelEn: "Monsters & Bosses",
        desc: "Kẻ địch, quái thường, tinh anh và Thủ lĩnh chiến đấu"
    },
    {
        id: "gameplay",
        label: "Giao diện, Chế độ & Hệ thống",
        shortLabel: "Giao diện & Chế độ",
        labelEn: "Gameplay, Modes & UI",
        desc: "Nút giao diện, chế độ chơi, cửa hàng, chiêu mộ và tính năng"
    },
    {
        id: "events",
        label: "Sự kiện, Chương & Thời gian",
        shortLabel: "Sự kiện & Chương",
        labelEn: "Events, Chapters & Timeline",
        desc: "Tên sự kiện, chương truyện, lễ hội và lịch Tháp Sao"
    }
];

const GLOSSARY_DEFAULT_GROUP = "lore";

/** Nhãn cũ & biến thể dấu gạch chéo → id nhóm chuẩn (giữ tương thích dữ liệu đã lưu). */
const GLOSSARY_LEGACY_CATEGORY_GROUPS = {
    "nhân vật & danh xưng": "characters",
    "nhân vật & đại từ": "characters",
    "nhân vật, npc & xưng hô": "characters",
    "chức danh": "characters",
    "tổ chức & phe phái": "organizations",
    "tổ chức / phe phái": "organizations",
    "thế giới & địa lý": "world",
    "thế giới & địa danh": "world",
    "địa danh & bản đồ": "world",
    "địa danh": "world",
    "lore & thuật ngữ cốt truyện": "lore",
    "cốt truyện & lore": "lore",
    "cốt truyện & thế giới": "lore",
    "thần linh": "lore",
    "vật phẩm & trang bị": "items",
    "vật phẩm, đĩa nhạc & trang phục": "items",
    "vật phẩm": "items",
    "vật phẩm / cơ chế": "items",
    "kỹ năng, tiềm năng & chiến đấu": "skills",
    "chiến đấu & kỹ năng": "skills",
    "chiến đấu": "skills",
    "kỹ năng / thẻ": "skills",
    "quái vật & boss": "monsters",
    "quái vật & thủ lĩnh": "monsters",
    "gameplay & giao diện": "gameplay",
    "giao diện, chế độ & hệ thống": "gameplay",
    "giao diện & hệ thống": "gameplay",
    "chế độ chơi": "gameplay",
    "hệ thống": "gameplay",
    "sự kiện & thời gian": "events",
    "sự kiện, chương & thời gian": "events"
};

/** Category kỹ thuật trong Sheet "01. Glossary" → nhóm. */
const GLOSSARY_SHEET_CATEGORY_GROUPS = {
    "character_name": "characters",
    "gender_female": "characters",
    "gender_male": "characters",
    "ui_text": "gameplay"
};

/** Nhãn hiển thị gọn cho category kỹ thuật gốc. */
const GLOSSARY_RAW_SUBTYPE_LABELS = {
    "character_name": "Nhân vật",
    "gender_female": "Đại từ (Nữ)",
    "gender_male": "Đại từ (Nam)",
    "ui_text": "Giao diện"
};

/** Chỉ định đích danh (khóa = EN viết thường). Ưu tiên cao hơn quy tắc. */
const GLOSSARY_GROUP_OVERRIDES = (() => {
    const map = {};
    const add = (group, names) => names.forEach(n => { map[n.toLowerCase()] = group; });

    add("characters", [
        "Captain", "Archon", "Archons", "Archon Olympia", "Director Knight", "Masked Knight", "Grand Inspector",
        "Grand Inspector Matilda", "Grand Priest", "Grand Priest Coppelius", "Saintess", "Saintess Leita",
        "Granny Marlene", "Sentinel of Dawn", "The Sentinel of Dawn", "Snowish Festival Messenger",
        "Snowish Tree Spirit", "Snowish Laru", "Firstlight Noya", "Lady Gray", "The Boss", "Boss",
        "Treasure Hunter", "Treasure Hunter Leader", "Treasure Hunters", "Crow Rider", "Bunny Duo",
        "Arbiter", "Arbiters", "Arbiter Gerie", "Dusk Arbiter", "Dusk Arbiters", "Senators", "CEO",
        "Freelance Trekker", "Whally", "Matsukawa", "Flavio", "Springseek Coronis", "Suntide Willow",
        "Imperial Guard Knights", "Imperial Guard Squire", "Snowish Festival Tyrant"
    ]);

    add("organizations", [
        "Society for the Study of Life", "Trekker Association", "Trekkers' House", "Senate",
        "Imperial Guard", "The Imperial Guard", "Grace Imperium", "The Grace Imperium", "Neo Grace Organization",
        "New Star Guild", "United Harvest", "Creta Trading", "Platinum Academy", "Grace Light Academy",
        "Boss Accord Staffing Co.", "Tyrant Accord Staffing Co.", "Night Watch", "Holy See",
        "Ashwind Clan", "Ashwind", "Petal Bloom", "White Cat Troupe", "Goodwind Homecare",
        "Dusk Arbiter Tribunal", "Deepsea Finance", "Goodwind Homecare Philae Branch"
    ]);

    add("world", [
        "Nova", "Nova Continent", "The White Room", "Wilds", "Mirage",
        "City of a Thousand Monoliths", "Lucky Oasis", "Nocturn Eterna",
        "Frozen Ruins", "Parasitic Garden", "The Retreat", "Waterway Bridge",
        "Cangwu", "Cang Wu", "Cangwu City", "Carlo Town", "Emor", "Norstheim", "Philae", "Dorra",
        "Philanis", "Filanis", "Ash District", "Emor Ash District", "Tyrant's Tower",
        "Fenghuang Diner", "Daisy Orphanage", "Ash Orphanage",
        "Creta Trading Corridor", "Creta Trading Lobby", "Greenhouse District",
        "East 1st Street", "Emor Monolith #25", "Thousand Monoliths"
    ]);

    add("lore", [
        "Grace", "God of Grace", "Eye of Grace", "Stellaroid", "Trekker", "Tyrant", "Monolith", "The Monolith",
        "Eternity", "Boss Accord", "The Boss Accord", "Tyrant Accord", "Soul trading", "Tetrad Aspects", "Knight's Code",
        "Chronicles of New Nova", "Frozen Path", "white lie",
        "Chariot", "Ebony Star", "Horizon", "Sinister Ritual", "tamago", "sageo",
        "franchise patent", "Ghost", "Wraith", "Kun", "Loong", "Novian", "Novians", "Bayan",
        "Cuteness Dependency Syndrome", "Messis Syndrome", "Artifacts", "Big Three"
    ]);

    add("items", [
        "Artifact", "Xuan Shi", "Stellanite Lumina", "Stellanite Dust", "Runic Disc", "Disc",
        "Soul Key", "Soul Stone", "Seal of Grace", "Journey Ticket", "Cerulean Ticket", "Sprout Ticket",
        "Travel Permit", "Expert Permit", "Monolith Coins", "Stella Coin", "Rabbit Pie", "Super Action Pie",
        "Pep Pep Juice", "Tawny Nightingale", "Package", "Wishing Box", "Enhancement Machine",
        "Character Skin", "FateCard", "Penguin Card", "Chess Piece of Skill", "Miracle Puppet",
        "Gauntlet of Rage", "Record", "Average Record", "Advanced Record", "Expert Record", "Master Record"
    ]);

    add("skills", [
        "Disc Harmony Skill", "Harmony Skill", "Resilience", "Resilience Break",
        "AoE build", "Support build", "Basic ATK build", "Burst build", "Crit build",
        "Forbidden Beauty", "Mark", "Support", "Versatile", "Vanguard",
        "Spirit of Brutality", "Blade of Jade", "Wild Rush", "Repeated Performance", "Total Bombardment",
        "Aqua", "Ignis", "Terra", "Ventus", "Lux", "Umbra",
        "Aura", "Great Sword Aura", "Cross Great Sword Aura", "Dragon Slash", "Galloping Wind Strike"
    ]);

    add("monsters", [
        "Armadillo Fish", "Count of the Duloos", "Enforcer of Silence", "Evernight Emberflies",
        "Fierce Long-Tailed Scorpion", "Gobble Hexhorn Whale", "Golem of Nightmares", "Grotesque Dancer",
        "Guardian of Thorns", "Hexhorn Whale", "The Hexhorn Whale", "Lithe Beauty", "Magishark", "Master Digger",
        "Megahand Enforcer", "Nian", "Nightmare Executioner", "Opera Ghost: Rovina", "Oppressor of Torrents",
        "Plundering Dual Blades", "Protector of Radiance", "Shrubshrew Slinger", "Shrubshrew Warrior",
        "Spellbound Golem", "Subjugator of Firmament", "Suppressor of Lava", "Tainted Mandrake", "Tusk Stomper",
        "Whimagus", "Whirling Crawler", "Whirling Great Glopo", "Wrath Juggernaut", "King Glopo",
        "Rotting Silencer", "Abyssal Sea Sovereign", "Shadow Poison Pool", "Golem Guard", "Gloomfiend",
        "Cursipot", "Lux Stealer", "Crispy Hooves", "Crispy Hooves Deluxe", "Flavor Dread", "Gale Owl",
        "Lucky Rubbi", "Projectile Striker", "Space Walker", "Steam Pot Hammer"
    ]);

    add("gameplay", [
        "Soul Shop", "Monolith Shop", "Monolith Log", "Anecdote", "Authorization", "Recruitment", "Tyrant Growth",
        "Well of Worlds Tyrant Development System", "Infinite Arena", "Infinity Tower", "Star Tower", "Menace Arena",
        "Ascension", "Tier-up Trial", "Skill Trial", "Basic Trial", "Emblem Trial", "Proving Grounds",
        "Crescendo", "Everbright Wishes", "Clearance Points", "Vigor", "Heartlink", "Affinity", "Breakthrough",
        "Boss", "Battle Pass", "Trial Character", "Garden of Parasite", "Midas",
        "Back", "Cancel", "Confirm", "Hide", "Authorization Lv."
    ]);

    add("events", [
        "Boss Blitz", "Currents and Shadows", "Dust and Flames", "Elegance and Flow", "Flames and Beats",
        "Storm and Thunder", "Shake The Floor", "Thrilling Beat", "Upbeat Party", "Petal Bloom", "Star Pluck",
        "Star Pluck Conquest", "Misstep On One", "Post Haste", "Autumn Equinox", "Monolith Calendar",
        "Monolith Calendar Year", "Never Ending Summer", "Tech Convention", "Monolith Meltdown", "company war",
        "Operation: Shadow Siege", "Through Hostile Depths", "A Future Without Trekkers",
        "Overture of a Shadowy Enigma", "Ghost Ship", "The Ghost Ship", "nautical log", "Cataclysm Survivor",
        "Snowish Festival", "Happy Snowish Festival", "Springseek Festival", "Swimming Fish Festival",
        "A Finale Echoing", "Call for Best Records"
    ]);

    return map;
})();

/** Quy tắc từ khóa trên EN (khớp đầu tiên thắng, không phân biệt hoa thường). */
const GLOSSARY_GROUP_RULES = [
    // Thời gian / sự kiện
    { group: "events", test: /\bmonth$/i },
    { group: "events", test: /\b(festival|equinox|calendar|convention|anniversary)\b/i },

    // Nốt nhạc (SubNoteSkill) thuộc Kỹ năng & Chiến đấu
    { group: "skills", test: /^melody of /i },

    // Vật phẩm đặc thù
    { group: "items", test: /\b(coins?|ticket|juice|pie|skin|patent|lumina|record|disc)\b/i },

    // Thế giới / địa lý đặt TRƯỚC tổ chức để 'Creta Trading Corridor/Lobby' vào đúng Địa danh
    { group: "world", test: /\b(city|town|district|continent|harbor|market|gate|bridge|street|corridor|lobby|prison|ruins|greenhouse|oasis|wilds|branch|office|stall|tower)\b/i },

    // Tổ chức / phe phái
    { group: "organizations", test: /\b(clan|orphanage|bureau|guild|association|troupe|organization|studio|media|academy|company|co\.|society|imperium|finance|homecare|trading|staffing|tribunal)\b/i },

    // Danh xưng
    { group: "characters", test: /\b(captain|archon|arbiter|inspector|knight|director|senators?|ceo|lord|lady|gentleman|granny|messenger|treasure hunters?|sentinel|rider|priest|saintess)\b/i },

    // Kỹ năng / chỉ số / chiến đấu
    { group: "skills", test: /\b(atk|def|hp|dmg|crit|spd|res|pen|cd|cooldown|energy|shield|dodge|evasion|freeze|frozen|stun|shock|burn|bleed|burst|build|skill|ultimate|attack|dash|resilience|penetration|accuracy|charge|magazine|capacity|aqua|ignis|terra|ventus|lux|umbra|incapacitated|derivative|vul|minion|boost|reduction|dealt|taken|elemental|ignore|aura|slash|strike|potential|talent)\b/i },

    // Gameplay: chế độ, giao diện, hệ thống
    { group: "gameplay", test: /\b(domain|trial|arena|shop|inventory|mailbox|mall|mission|quest|task|claim|deploy|draw|pull|gacha|banner|sweep|quick clear|upgrade|enhance|breakthrough|affinity|heartlink|achievement|settings|notice|vigor|leaderboard|console|interaction)\b/i }
];

/** Nhãn người nói trong "character_name" thực chất là quái vật / kẻ địch → Quái vật & Thủ lĩnh. */
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
    const direct = GLOSSARY_GROUPS.find(g =>
        g.label.toLowerCase() === key ||
        (g.shortLabel && g.shortLabel.toLowerCase() === key) ||
        g.labelEn.toLowerCase() === key ||
        g.id === key
    );
    if (direct) return direct.id;
    return GLOSSARY_LEGACY_CATEGORY_GROUPS[key] || null;
}

function buildGlossaryCharacterNameSet(terms) {
    const size = (terms || []).length;
    if (_glossaryCharacterNameSet && _glossaryCharacterNameSource === terms && _glossaryCharacterNameSize === size) return _glossaryCharacterNameSet;
    const set = new Set();
    (terms || []).forEach(t => {
        if (!t || !t.en) return;
        const cat = String(t.category || "").trim();
        const rawCat = String(t.raw_category || "").trim();
        if (cat === "character_name" || rawCat === "character_name") {
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
 * @param {Object} term - { en, vi, category, group, raw_category, ... }
 * @param {Array} allTerms - toàn bộ từ điển (dùng để nhận diện tên nhân vật)
 */
function classifyGlossaryGroup(term, allTerms) {
    if (!term) return GLOSSARY_DEFAULT_GROUP;

    const declaredGroup = term.group && getGlossaryGroupById(term.group) ? term.group : null;
    const fromCategory = glossaryGroupFromCategory(term.category);
    if (declaredGroup && (!fromCategory || fromCategory === declaredGroup)) {
        return declaredGroup;
    }
    if (fromCategory) return fromCategory;

    const en = String(term.en || "").trim();
    const enKey = en.toLowerCase();

    if (GLOSSARY_GROUP_OVERRIDES[enKey]) return GLOSSARY_GROUP_OVERRIDES[enKey];

    const sheetCategory = String(term.category || term.raw_category || "").trim();
    if ((sheetCategory === "character_name" || String(term.raw_category || "").trim() === "character_name") && GLOSSARY_MONSTER_SPEAKER_RE.test(en)) {
        return "monsters";
    }

    const sheetGroup = GLOSSARY_SHEET_CATEGORY_GROUPS[sheetCategory];
    if (sheetGroup) return sheetGroup;

    if (buildGlossaryCharacterNameSet(allTerms).has(enKey)) return "characters";

    for (const rule of GLOSSARY_GROUP_RULES) {
        if (rule.test.test(en)) return rule.group;
    }
    return GLOSSARY_DEFAULT_GROUP;
}

/** Lấy nhóm (có nhớ đệm trên chính mục). Gọi lại classify khi category/EN/group đổi. */
function glossaryGroupOf(term, allTerms) {
    if (!term) return GLOSSARY_DEFAULT_GROUP;
    const sig = `${term.en || ""}\u0000${term.category || ""}\u0000${term.group || ""}`;
    if (term._groupSig !== sig || !term.group) {
        term.group = classifyGlossaryGroup(term, allTerms);
        term._groupSig = sig;
    }
    return term.group;
}

/** Nhãn phụ gọn, dễ hiểu cho từng thẻ thuật ngữ (ẩn hoàn toàn tên cột/tag nội bộ). */
function getGlossarySubTypeLabel(term) {
    if (!term) return "";
    const sub = String(term.sub_type || "").trim();
    if (sub) return sub;
    const raw = String(term.raw_category || term.category || "").trim();
    if (!raw) return "";
    return GLOSSARY_RAW_SUBTYPE_LABELS[raw] || "";
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        GLOSSARY_GROUPS,
        GLOSSARY_DEFAULT_GROUP,
        classifyGlossaryGroup,
        glossaryGroupOf,
        glossaryGroupFromCategory,
        getGlossaryGroupById,
        getGlossarySubTypeLabel
    };
}
