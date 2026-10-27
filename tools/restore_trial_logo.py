"""
Standalone script to restore the missing typography in ui_activity_trial__zs_activity_trial_logo.png.
Uses Pretendard-Black.ttf (the exact font used in the game logo).
"""

from pathlib import Path
from PIL import Image, ImageFont, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = ROOT / "work/research/fonts/Pretendard-Black.ttf"
ORIG_PNG = ROOT / "dist/StellaSora_Texture_VI/03_TieuDe_Logos_Headers_VI/ui_activity_trial__zs_activity_trial_logo.png"

def generate_restored_logo(output_path=None):
    orig = Image.open(ORIG_PNG).convert("RGBA")
    w, h = orig.size # 472, 255
    
    # Character placements matching the exact in-game stem positions
    char_placements = [
        ("T", 10, 56),
        ("h", 33, 56),
        ("ử", 88, 56),
        ("T", 133, 56),
        ("à", 178, 56),
        ("i", 228, 56),
    ]
    
    # Render the text mask at 4x resolution for super-smooth anti-aliasing and precise styling
    scale = 4
    sw, sh = w * scale, h * scale
    f_hi = ImageFont.truetype(str(FONT_PATH), 57 * scale)
    
    text_mask_hi = Image.new("L", (sw, sh), 0)
    draw_hi = ImageDraw.Draw(text_mask_hi)
    for char, cx, cy in char_placements:
        draw_hi.text((cx * scale, cy * scale), char, font=f_hi, fill=255)
        
    # We only want to restore elements in the UPPER region (Y < 76 in original image)
    # Specifically, elements above Y=74 (ascenders, diacritics, top of crossbars)
    # Plus a small blend overlap into Y=74..78 to seamlessly weld with existing stems
    clip_mask_hi = Image.new("L", (sw, sh), 0)
    clip_draw = ImageDraw.Draw(clip_mask_hi)
    y_cutoff = 74 * scale
    y_blend = 78 * scale
    clip_draw.rectangle([0, 0, sw, y_cutoff], fill=255)
    for y in range(y_cutoff, y_blend):
        alpha = int(255 * (1.0 - (y - y_cutoff) / (y_blend - y_cutoff)))
        clip_draw.line([(0, y), (sw, y)], fill=alpha)
        
    # Apply clip mask to text mask
    restore_mask_hi = Image.new("L", (sw, sh), 0)
    for y in range(0, y_blend):
        m_row = [text_mask_hi.getpixel((x, y)) for x in range(sw)]
        c_row = [clip_mask_hi.getpixel((x, y)) for x in range(sw)]
        for x in range(sw):
            if m_row[x] > 0 and c_row[x] > 0:
                restore_mask_hi.putpixel((x, y), int(m_row[x] * c_row[x] / 255))
                
    # Downscale mask to 1x with high-quality resampling
    restore_mask = restore_mask_hi.resize((w, h), Image.Resampling.LANCZOS)
    
    # Border width is 3.5px
    border_mask = restore_mask.filter(ImageFilter.MaxFilter(7))
    
    # Shadow: blurred and offset (dx=2, dy=2)
    shadow_mask = border_mask.filter(ImageFilter.GaussianBlur(2.0))
    shadow_layer = Image.new("RGBA", (w, h), (10, 20, 50, 160))
    
    # Border color: #11255B -> (17, 37, 91)
    border_layer = Image.new("RGBA", (w, h), (17, 37, 91, 255))
    
    # Fill: White (#FFFFFF) at top (Y=50) transitioning to subtle pale cyan (#E8F6FE) at Y=75
    fill_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        factor = min(1.0, max(0.0, (y - 50) / 30.0))
        r = int(255 - factor * 18)
        g = int(255 - factor * 8)
        b = 255
        for x in range(w):
            if restore_mask.getpixel((x, y)) > 20:
                a = restore_mask.getpixel((x, y))
                fill_layer.putpixel((x, y), (r, g, b, a))
                
    # Composite the styled addition
    restored_patch = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # 1. Shadow
    restored_patch.paste(shadow_layer, (2, 2), shadow_mask)
    # 2. Border
    restored_patch.paste(border_layer, (0, 0), border_mask)
    # 3. Fill
    restored_patch.paste(fill_layer, (0, 0), fill_layer)
    
    # Composite restored_patch OVER the original image
    final_img = Image.alpha_composite(orig, restored_patch)
    
    if output_path:
        final_img.save(output_path)
        print(f"Saved restored logo to {output_path}")
        
    return final_img

if __name__ == "__main__":
    out_test = ROOT / "test_restored_logo.png"
    generate_restored_logo(out_test)
    # Also save directly to target VI path
    generate_restored_logo(ORIG_PNG)
    print("Updated dist/StellaSora_Texture_VI/03_TieuDe_Logos_Headers_VI/ui_activity_trial__zs_activity_trial_logo.png")
