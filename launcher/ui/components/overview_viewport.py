"""Scale the complete logical overview canvas into one non-scrolling viewport."""
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView,QGraphicsScene,QFrame,QSizePolicy

class OverviewViewport(QGraphicsView):
    def __init__(self,overview,parent=None):
        super().__init__(parent);self.overview=overview
        self.canvas_size=overview.size()
        self.scene_root=QGraphicsScene(self);self.setScene(self.scene_root)
        self.proxy=self.scene_root.addWidget(overview)
        self.scene_root.setSceneRect(QRectF(0,0,self.canvas_size.width(),self.canvas_size.height()))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.TextAntialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        self.setBackgroundBrush(Qt.BrushStyle.NoBrush);self.scene_root.setBackgroundBrush(Qt.BrushStyle.NoBrush)
        self.setStyleSheet('QGraphicsView{background:transparent;border:0;}')
        self.setAutoFillBackground(False);self.viewport().setAutoFillBackground(False)
        self.setMinimumSize(0,0);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
    def fit_canvas(self):
        if self.viewport().width()>0 and self.viewport().height()>0:
            self.resetTransform();self.fitInView(self.scene_root.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
    def resizeEvent(self,event):
        super().resizeEvent(event);self.fit_canvas()
    def showEvent(self,event):
        super().showEvent(event);self.fit_canvas()
    def wheelEvent(self,event):
        # This scene has no content beyond its canvas and never scrolls or zooms.
        event.ignore()
