#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cập nhật index.html, style.css và các file liên quan:
1. Thêm danh sách phát 5 bài nhạc vòng lặp vào web trạm dịch
2. Thêm nút chuyển bài BGM (Next BGM)
3. Thêm thanh tra cứu thuật ngữ nhanh (Quick Glossary Search)
4. Thêm CSS hỗ trợ cho tra cứu nhanh và highlight
"""

from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent.parent / "web" / "story_translator"
INDEX_HTML = WEB_DIR / "index.html"
STYLE_CSS = WEB_DIR / "css" / "style.css"

def update_index_html():
    content = INDEX_HTML.read_text(encoding="utf-8")
    
    # 1. Audio tag
    old_audio = '<audio id="bgmAudio" loop src="official_assets/bgm-90e5d63f.mp3"></audio>'
    new_audio = '<audio id="bgmAudio" preload="auto" src="official_assets/bgm/bgm_01_launch_title.mp3"></audio>'
    if old_audio in content:
        content = content.replace(old_audio, new_audio)
        print("[+] Đã cập nhật thẻ audio BGM sang bài số 1 trong danh sách 5 bài.")

    # 2. BGM next button
    old_bgm_btn = '<button id="bgmToggleBtn" class="btn-circle" title="Bật/Tắt Nhạc Nền Game" aria-label="Bật/Tắt Nhạc Nền Game" onclick="toggleBgm()"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18V5l10-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/></svg></button>'
    new_bgm_btn = '<button id="bgmToggleBtn" class="btn-circle" title="Bật/Tắt Nhạc Nền Game (Alt+M)" aria-label="Bật/Tắt Nhạc Nền Game" onclick="toggleBgm()"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18V5l10-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/></svg></button>\n            <button id="bgmNextBtn" class="btn-circle" title="Chuyển bài nhạc kế tiếp (danh sách 5 bài vòng lặp)" aria-label="Bài nhạc kế tiếp" onclick="nextBgm()"><svg viewBox="0 0 24 24" aria-hidden="true"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg></button>'
    if old_bgm_btn in content:
        content = content.replace(old_bgm_btn, new_bgm_btn)
        print("[+] Đã thêm nút nextBgm() vào HUD header.")

    # 3. Quick Glossary Search Bar
    sugg_anchor = '<!-- Gợi ý thuật ngữ từ điển xuất hiện trong câu -->'
    quick_search_block = '''<!-- Tra cứu thuật ngữ nhanh & Gợi ý từ điển xuất hiện trong câu -->
                    <div class="quick-glossary-search-wrap">
                        <span class="quick-search-icon">🔍</span>
                        <input type="text" class="quick-glossary-input" id="quickGlossaryInput" placeholder="Tra cứu nhanh thuật ngữ (gõ từ cần tra, click để chèn, Alt+G mở đầy đủ)..." oninput="onQuickGlossarySearch(this.value)">
                        <button class="quick-search-clear" id="quickGlossaryClear" onclick="clearQuickGlossarySearch()" style="display:none;">✕</button>
                    </div>
                    <div class="quick-glossary-results-tray" id="quickGlossaryResultsTray" style="display:none;"></div>'''
    if sugg_anchor in content and "quick-glossary-search-wrap" not in content:
        content = content.replace(sugg_anchor, quick_search_block)
        print("[+] Đã thêm thanh tra cứu nhanh thuật ngữ vào khung dịch.")

    # 4. Bump versions
    content = content.replace("?v=1.2.1", "?v=1.3.0")

    INDEX_HTML.write_text(content, encoding="utf-8")
    print("[OK] Đã lưu index.html thành công.")

def update_style_css():
    css = STYLE_CSS.read_text(encoding="utf-8")
    
    extra_css = """
/* ================= QUICK GLOSSARY SEARCH & HIGHLIGHT ================= */
.quick-glossary-search-wrap {
    display: flex;
    align-items: center;
    position: relative;
    background: rgba(14, 23, 38, 0.55);
    border: 1px solid rgba(86, 204, 242, 0.25);
    border-radius: 8px;
    padding: 2px 10px;
    margin-bottom: 6px;
    transition: all 0.2s ease;
}
.quick-glossary-search-wrap:focus-within {
    border-color: var(--cyan-primary);
    box-shadow: 0 0 10px rgba(86, 204, 242, 0.25);
    background: rgba(14, 23, 38, 0.85);
}
.quick-glossary-search-wrap .quick-search-icon {
    font-size: 0.85rem;
    color: var(--cyan-primary);
    margin-right: 6px;
}
.quick-glossary-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-main);
    font-size: 0.82rem;
    padding: 6px 0;
}
.quick-glossary-input::placeholder {
    color: rgba(160, 180, 205, 0.55);
    font-style: italic;
}
.quick-search-clear {
    background: transparent;
    border: none;
    color: var(--text-sub);
    cursor: pointer;
    font-size: 0.85rem;
    padding: 2px 6px;
    border-radius: 4px;
}
.quick-search-clear:hover {
    color: var(--red-coral);
    background: rgba(255, 107, 107, 0.15);
}
.quick-glossary-results-tray {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(86, 204, 242, 0.2);
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 8px;
    max-height: 140px;
    overflow-y: auto;
}
.glossary-kw-highlight {
    background: rgba(255, 215, 0, 0.35);
    color: #fff;
    font-weight: 700;
    padding: 0 2px;
    border-radius: 3px;
}
html:not([data-theme="dark"]) .quick-glossary-search-wrap {
    background: rgba(240, 246, 252, 0.85);
    border-color: rgba(0, 120, 212, 0.25);
}
html:not([data-theme="dark"]) .quick-glossary-input {
    color: #1e293b;
}
html:not([data-theme="dark"]) .quick-glossary-results-tray {
    background: rgba(241, 245, 249, 0.95);
    border-color: rgba(0, 120, 212, 0.25);
}
html:not([data-theme="dark"]) .glossary-kw-highlight {
    background: #fef08a;
    color: #0f172a;
}
"""
    if ".quick-glossary-search-wrap" not in css:
        css += extra_css
        STYLE_CSS.write_text(css, encoding="utf-8")
        print("[+] Đã thêm CSS tra cứu nhanh vào style.css.")

def main():
    update_index_html()
    update_style_css()

if __name__ == "__main__":
    main()
