"""Bundled Vietnamese typography. Pixel sizes are logical DIP, never point-size guesses."""
from pathlib import Path
from PySide6.QtGui import QFont,QFontDatabase
FAMILY='Be Vietnam Pro'
BODY=15
CAPTION=13
TITLE=20
MODAL=29

def font(size=BODY,weight=QFont.Weight.Normal):
    result=QFont(FAMILY);result.setPixelSize(int(size));result.setWeight(weight);return result

def register_fonts(resource_dir):
    import logging
    global FAMILY
    root=Path(resource_dir)/'ui'/'skin_r05'/'fonts';paths=sorted(root.rglob('*.ttf'))
    if len(paths)<4:raise RuntimeError('Thiếu bộ Be Vietnam Pro đi kèm launcher: '+str(root))
    registered=[];regular_families=[]
    for path in paths:
        ident=QFontDatabase.addApplicationFont(str(path))
        if ident<0:raise RuntimeError('Không nạp được font đi kèm: '+str(path))
        families=list(QFontDatabase.applicationFontFamilies(ident));registered.append({'path':str(path),'font_id':ident,'families':families})
        if path.stem.endswith('-Regular'):regular_families=families
    if not regular_families:raise RuntimeError('Font Regular đã nạp nhưng không trả về tên family hợp lệ.')
    FAMILY='Be Vietnam Pro' if 'Be Vietnam Pro' in regular_families else regular_families[0]
    logging.getLogger('launcher.fonts').info('Bundled font family=%s; weight aliases=%s',FAMILY,registered)
    return registered
