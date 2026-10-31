"""Export guide icons matching TramVH's existing Soft Sky vector palette."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'web/story_translator/assets/translation-guide-r01'
PATHS = {
    'guide': '<path d="M16 9c-4-3-8-3-12-1v16c4-2 8-2 12 1 4-3 8-3 12-1V8c-4-2-8-2-12 1Z"/><path d="M16 10v15M7 12l5 1M7 16l5 1M20 13l5-2M20 17l5-2"/>',
    'workflow': '<path d="M5 23h6l4-7h6l5-8"/><circle cx="6" cy="23" r="3"/><circle cx="16" cy="16" r="3"/><path d="m25 3 1.5 3.5L30 8l-3.5 1.5L25 13l-1.5-3.5L20 8l3.5-1.5Z"/>',
    'style': '<path d="M5 26c1-7 4-14 13-20 6-4 10-2 9 3-2 8-9 13-18 14M8 23l-3 5M10 21 23 8M16 16l6 1M19 12l1-6"/>',
    'pronouns': '<path d="M3 6h16v11H9l-5 4v-4H3ZM22 12h7v13h-3v4l-5-4h-8v-5M7 10h8M7 13h5M21 17h4M17 21h8"/>',
    'tokens': '<path d="m9 6-6 10 6 10M23 6l6 10-6 10"/><path d="m16 7 5 9-5 9-5-9ZM11 16h10M16 7v18"/>',
    'checklist': '<rect x="6" y="5" width="21" height="24" rx="3"/><path d="M12 5V3h9v4h-9ZM10 13l2 2 3-4M18 13h5M10 22l2 2 3-4M18 22h5"/>',
    'search': '<circle cx="14" cy="14" r="9"/><path d="m21 21 7 7M11 14h6M14 11v6"/>',
    'close': '<path d="m9 9 14 14M23 9 9 23"/>',
}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for theme, ink, gold in [('light', '#28687b', '#b8873d'), ('dark', '#a3d9e3', '#e6c184')]:
        for name, geometry in PATHS.items():
            extra = '' if name in ('close', 'search') else f'<circle cx="16" cy="16" r="14" fill="{gold}" opacity=".10"/>'
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">{extra}<g stroke="{ink}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{geometry}</g></svg>\n'
            (DEST / f'{name}-{theme}.svg').write_text(svg, encoding='utf-8')
    files = []
    for file in sorted(DEST.iterdir()):
        if file.suffix != '.svg':
            continue
        files.append({'file': file.name, 'bytes': file.stat().st_size, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    manifest = {'schema': 1, 'name': 'TramVH Translation Guide Icons r01', 'date': '2026-10-31', 'authoring': 'Original project-native SVG matching existing Soft Sky icons', 'themes': ['light', 'dark'], 'icons': len(PATHS), 'files': files}
    (DEST / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'assets': len(files), 'manifest': str(DEST / 'manifest.json')}))


if __name__ == '__main__':
    main()
