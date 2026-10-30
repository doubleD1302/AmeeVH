"""Bundled Vietnamese-capable Baloo 2 typography."""
from pathlib import Path
import hashlib
from PySide6.QtGui import QFont, QFontDatabase
FAMILY = 'Baloo 2'
BODY, CAPTION, TITLE, MODAL = 15, 13, 20, 29
EXPECTED_SHA256 = 'd47a6852548059b1db49a1319d06d499d546c3fa2237cf9eee9c43c8abb025c2'
def soft_weight(weight):
    return weight
def font(size=BODY, weight=QFont.Weight.Normal):
    result=QFont(FAMILY);result.setPixelSize(int(size)+2);result.setWeight(weight)
    result.setStyleStrategy(QFont.StyleStrategy.PreferQuality | QFont.StyleStrategy.PreferAntialias);result.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return result
def register_fonts(resource_dir):
    path=Path(resource_dir)/'ui'/'journey_r01'/'fonts'/'Baloo2.ttf'
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=EXPECTED_SHA256:
        raise RuntimeError('Thiếu hoặc sai tệp font Baloo 2 đi kèm: '+str(path))
    ident=QFontDatabase.addApplicationFont(str(path))
    families=list(QFontDatabase.applicationFontFamilies(ident)) if ident>=0 else []
    if not any(f.casefold()==FAMILY.casefold() for f in families):
        raise RuntimeError('Không nạp được họ font Baloo 2: '+str(path))
    return [{'path':str(path),'font_id':ident,'families':families}]
