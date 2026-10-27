"""Bundled Nunito variable typography; logical pixel sizes and a softer weight scale."""
from pathlib import Path
import hashlib,json,logging
from PySide6.QtGui import QFont,QFontDatabase
FAMILY='Nunito'
BODY=15
CAPTION=13
TITLE=20
MODAL=29

def soft_weight(weight):
    value=weight.value if hasattr(weight,'value') else int(weight)
    # Legacy DemiBold/Bold requests become Medium/SemiBold respectively.
    if value>=700:return QFont.Weight.DemiBold
    if value>=500:return QFont.Weight.Medium
    return QFont.Weight.Normal

def font(size=BODY,weight=QFont.Weight.Normal):
    result=QFont(FAMILY);result.setPixelSize(int(size));result.setWeight(soft_weight(weight));result.setStyleStrategy(QFont.StyleStrategy.PreferAntialias);return result

def register_fonts(resource_dir):
    global FAMILY
    root=Path(resource_dir)/'ui'/'typography_r08'
    try:provenance=json.loads((root/'SOURCE_PROVENANCE.json').read_text(encoding='utf8'))
    except (OSError,ValueError) as exc:raise RuntimeError('Không đọc được nguồn gốc font Nunito đi kèm launcher: '+str(root)) from exc
    declared=provenance.get('family','Nunito');font_files=[entry for entry in provenance.get('files',[]) if Path(entry.get('path','')).suffix.lower() in ('.ttf','.otf')]
    if not font_files:raise RuntimeError('Thiếu font Nunito biến thiên đi kèm launcher: '+str(root))
    registered=[];matching=[]
    for entry in font_files:
        path=root/entry['path']
        if not path.is_file():raise RuntimeError('Thiếu tệp font đi kèm: '+str(path))
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry.get('sha256'):raise RuntimeError('Tệp font Nunito bị hỏng hoặc không khớp nguồn đi kèm: '+str(path))
        ident=QFontDatabase.addApplicationFont(str(path))
        if ident<0:raise RuntimeError('Không nạp được font Nunito đi kèm: '+str(path))
        families=list(QFontDatabase.applicationFontFamilies(ident))
        registered.append({'path':str(path),'font_id':ident,'families':families})
        matching.extend(f for f in families if f.casefold()==declared.casefold() or f.casefold().startswith(declared.casefold()+' '))
    if not matching:raise RuntimeError('Font Nunito đã nạp nhưng không trả về family hoặc alias Nunito hợp lệ.')
    FAMILY=next((family for family in matching if family.casefold()==declared.casefold()),matching[0])
    logging.getLogger('launcher.fonts').info('Bundled variable font family=%s; registered=%s; weight scale=400/500/600',FAMILY,registered)
    return registered
