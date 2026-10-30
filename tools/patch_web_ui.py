#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

index_path = Path("StellaSora_VietHoa/web/story_translator/index.html")
text = index_path.read_text(encoding="utf-8")

# 1. Add js/config.js before UserModel.js
old_script = '<script src="js/models/UserModel.js"></script>'
new_script = '<script src="js/config.js"></script>\n    <script src="js/models/UserModel.js"></script>'
if 'js/config.js' not in text:
    text = text.replace(old_script, new_script)

# 2. Add inputGasUrl in Profile Modal
old_profile_input = '<input type="text" id="inputUsername" placeholder="Ví dụ: KhaiMinh, Arthur, Noya_Fan..." style="background:#050912; border:1px solid rgba(255,255,255,0.2); border-radius:12px; padding:12px 16px; color:#ffffff; font-family:var(--font-main); font-size:1.05rem; outline:none;">\r\n            </div>'

if old_profile_input not in text:
    # Try LF
    old_profile_input = '<input type="text" id="inputUsername" placeholder="Ví dụ: KhaiMinh, Arthur, Noya_Fan..." style="background:#050912; border:1px solid rgba(255,255,255,0.2); border-radius:12px; padding:12px 16px; color:#ffffff; font-family:var(--font-main); font-size:1.05rem; outline:none;">\n            </div>'

gas_block = '''<input type="text" id="inputUsername" placeholder="Ví dụ: KhaiMinh, Arthur, Noya_Fan..." style="background:#050912; border:1px solid rgba(255,255,255,0.2); border-radius:12px; padding:12px 16px; color:#ffffff; font-family:var(--font-main); font-size:1.05rem; outline:none;">
            </div>

            <div style="display:flex; flex-direction:column; gap:8px;">
                <label style="font-size:0.82rem; color:var(--cyan-primary); font-weight:700;">GOOGLE APPS SCRIPT WEB APP URL (TÙY CHỌN)</label>
                <input type="text" id="inputGasUrl" placeholder="https://script.google.com/macros/s/.../exec" style="background:#050912; border:1px solid rgba(255,255,255,0.2); border-radius:12px; padding:10px 14px; color:#ffffff; font-family:var(--font-code); font-size:0.85rem; outline:none;">
                <span style="font-size:0.75rem; color:var(--text-sub);">Để trống nếu dùng proxy Cloudflare Pages (/api/save_line), hoặc dán URL Web App để đồng bộ trực tiếp.</span>
            </div>'''

if 'id="inputGasUrl"' not in text:
    text = text.replace(old_profile_input, gas_block)

index_path.write_text(text, encoding="utf-8")
print("✓ Successfully patched index.html with config.js & inputGasUrl!")
