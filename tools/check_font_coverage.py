import os
from fontTools.ttLib import TTFont

def main():
    fonts_dir = 'work/research/fonts'
    test_file = 'templates/VI_GLYPH_TEST.txt'
    
    with open(test_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Extract only letters and symbols, excluding whitespace
    chars_to_test = sorted(list(set(c for c in text if not c.isspace())))
    
    print(f"Total unique characters to test: {len(chars_to_test)}")
    print(f"Characters: {''.join(chars_to_test)}\n")
    
    # Vietnamese specific vowels + D/d
    vi_special = [c for c in chars_to_test if ord(c) > 127]
    print(f"Vietnamese accented/special characters: {len(vi_special)}")
    print(f"Special characters: {''.join(vi_special)}\n")
    
    print(f"{'Font File':<32} | {'Total Cov':<12} | {'VI Accents':<12} | {'Missing VI'}")
    print("-" * 80)
    
    for fname in sorted(os.listdir(fonts_dir)):
        if not fname.endswith('.ttf'):
            continue
        fpath = os.path.join(fonts_dir, fname)
        try:
            font = TTFont(fpath)
            cmap = font['cmap'].getBestCmap() if 'cmap' in font else None
            if not cmap:
                print(f"{fname:<32} | NO CMAP")
                continue
            
            missing_all = [c for c in chars_to_test if ord(c) not in cmap]
            missing_vi = [c for c in vi_special if ord(c) not in cmap]
            
            tot_cov = f"{len(chars_to_test)-len(missing_all)}/{len(chars_to_test)}"
            vi_cov = f"{len(vi_special)-len(missing_vi)}/{len(vi_special)}"
            
            miss_sample = "".join(missing_vi[:15]) + ("..." if len(missing_vi) > 15 else "")
            print(f"{fname:<32} | {tot_cov:<12} | {vi_cov:<12} | {miss_sample}")
        except Exception as e:
            print(f"{fname:<32} | Error: {e}")

if __name__ == '__main__':
    main()
