"""Quiet glass panels for the launcher."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QFrame
class GlassCard(QFrame):
    def __init__(self, parent=None, border_color=None, bg_color=None, decorated=True, asset_id='panels/plain'):
        super().__init__(parent); self.asset_id=asset_id; self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    def paintEvent(self, event):
        from ..journal_paint import panel,panel_asset,ornaments
        p=QPainter(self);r=QRectF(self.rect())
        kind={'panels/notification':'notice','panels/install':'action'}.get(self.asset_id)
        if not kind or not panel_asset(p,r,kind):panel(p,r);ornaments(p,r)
