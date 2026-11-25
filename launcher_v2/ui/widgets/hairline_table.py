# -*- coding: utf-8 -*-
"""
Flat Hairline tables, delegate, key-value / 3x3 diagnostic grids, and section bars.

Replaces v1.3.4's nested rounded 1px dark cards with clean flat #FFFFFF / #F8FBFE
rows separated by 1px #D5E0EE / #DCE5F0 hairlines and #D7F1F6 + 3px #12B8C4 selection.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableView,
    QWidget,
)

from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, FS_BODY_SM, FS_CAPTION, FS_META, mono_font, nfc, ui_font


class PorcelainSectionBar(QFrame):
    """#EEF4FA section bar with 3px #264278 left accent, 1px #D5E0EE bottom hairline."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("porcelainSectionBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 7, 14, 7)
        layout.setSpacing(8)

        self.title_label = QLabel(nfc(title).upper(), self)
        self.title_label.setFont(ui_font(FS_BODY_SM, 700))
        self.title_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; background: transparent;")
        layout.addWidget(self.title_label, 1)

        self._right_slot = QHBoxLayout()
        self._right_slot.setContentsMargins(0, 0, 0, 0)
        self._right_slot.setSpacing(6)
        layout.addLayout(self._right_slot, 0)
        self._right_widget: QWidget | None = None

    def set_title(self, title: str) -> None:
        self.title_label.setText(nfc(title).upper())

    def set_right_widget(self, widget: QWidget | None) -> None:
        if self._right_widget is not None:
            self._right_slot.removeWidget(self._right_widget)
            self._right_widget.setParent(None)
        self._right_widget = widget
        if widget is not None:
            self._right_slot.addWidget(widget)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = PORCELAIN_TOKENS
        painter = QPainter(self)
        r = self.rect()
        painter.fillRect(r, QColor(p.ICE_ZEBRA))
        painter.fillRect(0, 0, 3, r.height(), QColor(p.NAVY_SOLID))
        painter.fillRect(0, r.height() - 1, r.width(), 1, QColor(p.HAIRLINE))
        painter.end()


class HairlineListDelegate(QStyledItemDelegate):
    """Custom item delegate painting flat zebra rows, hover #E1F3F8, and 3px #12B8C4 selection."""

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        p = PORCELAIN_TOKENS
        painter.save()

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        row = index.row()

        if selected:
            bg = QColor(p.ICE_SELECTED)
        elif hovered:
            bg = QColor(p.ICE_HOVER)
        elif row % 2 == 1:
            bg = QColor(p.ICE_ROW_ALT)
        else:
            bg = QColor(p.WHITE)

        painter.fillRect(option.rect, bg)

        # 3px cyan left bar on column 0 when selected
        if selected and index.column() == 0:
            painter.fillRect(
                option.rect.left(),
                option.rect.top(),
                3,
                option.rect.height(),
                QColor(p.CYAN_ACCENT),
            )

        # Bottom 1px cell hairline
        pen = QPen(QColor(p.HAIRLINE_CELL), 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawLine(
            option.rect.left(),
            option.rect.bottom(),
            option.rect.right(),
            option.rect.bottom(),
        )
        if index.column() > 0:
            painter.drawLine(
                option.rect.left(),
                option.rect.top(),
                option.rect.left(),
                option.rect.bottom(),
            )

        text = nfc(str(index.data(Qt.ItemDataRole.DisplayRole) or ""))
        fg = index.data(Qt.ItemDataRole.ForegroundRole)
        text_color = fg.color() if hasattr(fg, "color") else QColor(
            p.SLATE_MUTED if index.column() == 0 else p.NAVY_TEXT
        )
        font_data = index.data(Qt.ItemDataRole.FontRole)
        painter.setFont(font_data if font_data is not None else option.font)
        painter.setPen(text_color)

        text_rect = option.rect.adjusted(12, 6, -12, -6)
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap),
            text,
        )
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        text = nfc(str(index.data(Qt.ItemDataRole.DisplayRole) or ""))
        font_data = index.data(Qt.ItemDataRole.FontRole)
        font = font_data if isinstance(font_data, QFont) else option.font
        fm = QFontMetrics(font)

        parent = self.parent()
        if isinstance(parent, QTableView):
            hdr = parent.horizontalHeader()
            if hdr.sectionResizeMode(index.column()) == QHeaderView.ResizeMode.ResizeToContents:
                avail_w = 10000
            else:
                col_w = (
                    parent._effective_column_width(index.column())
                    if isinstance(parent, HairlineTable)
                    else parent.columnWidth(index.column())
                )
                avail_w = max(40, col_w - 24)
        else:
            avail_w = max(40, option.rect.width() - 24) if option.rect.width() > 0 else 10000

        br = fm.boundingRect(
            QRect(0, 0, avail_w, 10000),
            int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap),
            text,
        )
        return QSize(max(1, br.width() + 24), max(34, br.height() + 14))


class HairlineTable(QTableView):
    """Flat hairline table backed by QTableView + HairlineListDelegate (zero nested cards)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("hairlineTable")
        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.setItemDelegate(HairlineListDelegate(self))

        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setMouseTracking(True)
        self.setWordWrap(True)
        self.setFrameShape(QFrame.Shape.Box)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(34)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setFont(ui_font(FS_BODY, 500))

        self.setStyleSheet(
            f"QTableView#hairlineTable {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; border-radius: 4px; outline: none; }}"
        )

        self._reflowing_rows = False
        self._needs_reflow = False
        self._reflow_queued = False
        self._pending_col_widths: dict[int, int] = {}
        self.horizontalHeader().sectionResized.connect(self._on_section_resized)
        self.verticalScrollBar().rangeChanged.connect(self._on_scrollbar_range_changed)

    def _effective_column_width(self, col: int) -> int:
        if col in self._pending_col_widths:
            return self._pending_col_widths[col]
        return self.columnWidth(col)

    def _reflow_rows(self) -> None:
        if self._model.rowCount() <= 0:
            return
        if self._reflowing_rows:
            self._needs_reflow = True
            return
        self._reflowing_rows = True
        try:
            for _ in range(4):
                self._needs_reflow = False
                self.resizeRowsToContents()
                if not self._needs_reflow:
                    break
        finally:
            self._reflowing_rows = False
            self._needs_reflow = False

    def _schedule_reflow(self) -> None:
        if self._reflow_queued or self._model.rowCount() <= 0:
            return
        self._reflow_queued = True
        QTimer.singleShot(0, self._run_queued_reflow)

    def _run_queued_reflow(self) -> None:
        self._reflow_queued = False
        self._reflow_rows()

    def _on_section_resized(self, logical_index: int, _old_size: int, new_size: int) -> None:
        if self._model.rowCount() <= 0:
            return
        self._pending_col_widths[logical_index] = new_size
        try:
            self._reflow_rows()
        finally:
            self._pending_col_widths.pop(logical_index, None)
        self._schedule_reflow()

    def _on_scrollbar_range_changed(self, _minimum: int, _maximum: int) -> None:
        if self._model.rowCount() > 0:
            self._schedule_reflow()

    def set_headers(self, headers: Sequence[str]) -> None:
        self._model.setHorizontalHeaderLabels([nfc(h) for h in headers])
        self.horizontalHeader().setVisible(bool(headers))

    def set_rows(self, rows: Sequence[Sequence[str]], *, key_column_width: int | None = None) -> None:
        self._model.removeRows(0, self._model.rowCount())
        col_count = max((len(r) for r in rows), default=0)
        self._model.setColumnCount(col_count)
        for row_vals in rows:
            items: list[QStandardItem] = []
            for col_idx, val in enumerate(row_vals):
                it = QStandardItem(nfc(str(val)))
                it.setEditable(False)
                it.setFont(ui_font(FS_BODY, 600 if col_idx > 0 else 500))
                items.append(it)
            self._model.appendRow(items)

        hdr = self.horizontalHeader()
        if col_count > 1:
            if key_column_width is not None:
                hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(0, int(key_column_width))
            else:
                hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            for col in range(1, col_count - 1):
                hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            hdr.setSectionResizeMode(col_count - 1, QHeaderView.ResizeMode.Stretch)
        elif col_count == 1:
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._reflow_rows()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._model.rowCount() > 0:
            self._reflow_rows()

    def selected_row_index(self) -> int:
        sm = self.selectionModel()
        if sm is None:
            return -1
        rows = sm.selectedRows()
        return rows[0].row() if rows else -1


_TONE_COLORS: dict[str, str] = {
    "neutral": PORCELAIN_TOKENS.NAVY_TEXT,
    "ok": PORCELAIN_TOKENS.OK_TEXT,
    "warn": PORCELAIN_TOKENS.WARN_ICON,
    "danger": PORCELAIN_TOKENS.DANGER_TEXT,
    "mono": PORCELAIN_TOKENS.NAVY_TEXT,
}


class HairlineKeyValueTable(QFrame):
    """Flat hairline 2-column KV table or 3x3 diagnostic grid with semantic tones."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("hairlineKvTable")
        self.setStyleSheet(
            f"QFrame#hairlineKvTable {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; border-radius: 4px; }}"
        )
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(0)

    def clear_rows(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def set_kv_rows(
        self,
        rows: Sequence[tuple[str, str] | tuple[str, str, str]],
        *,
        key_width_pct: float = 0.38,
    ) -> None:
        """Populate a flat 2-column key-value table with alternating #FFFFFF/#F8FBFE rows."""
        self.clear_rows()
        p = PORCELAIN_TOKENS
        self.setStyleSheet(
            f"QFrame#hairlineKvTable {{ background: {p.WHITE}; "
            f"border: 1px solid {p.HAIRLINE}; border-radius: 4px; }}"
        )
        self._grid.setColumnStretch(2, 0)
        n_rows = len(rows)
        key_stretch = max(1, round(key_width_pct * 100))
        val_stretch = max(1, 100 - key_stretch)
        self._grid.setColumnStretch(0, key_stretch)
        self._grid.setColumnStretch(1, val_stretch)

        for idx, row in enumerate(rows):
            key = nfc(str(row[0]))
            val = nfc(str(row[1]))
            tone = str(row[2]) if len(row) > 2 else "neutral"
            bg = p.ICE_ROW_ALT if idx % 2 == 1 else p.WHITE
            bottom_rule = "" if idx == n_rows - 1 else f"border-bottom: 1px solid {p.HAIRLINE_CELL};"

            k_lbl = QLabel(key, self)
            k_lbl.setFont(ui_font(FS_BODY, 600))
            k_lbl.setWordWrap(True)
            k_lbl.setStyleSheet(
                f"background: {bg}; color: {p.SLATE_MUTED}; padding: 8px 12px; "
                f"border-right: 1px solid {p.HAIRLINE_CELL}; {bottom_rule}"
            )

            v_lbl = QLabel(val, self)
            v_lbl.setFont(mono_font(FS_BODY_SM, 600) if tone == "mono" else ui_font(FS_BODY, 600, tabular=True))
            v_lbl.setWordWrap(True)
            v_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            v_color = _TONE_COLORS.get(tone, p.NAVY_TEXT)
            v_lbl.setStyleSheet(
                f"background: {bg}; color: {v_color}; padding: 8px 12px; {bottom_rule}"
            )

            self._grid.addWidget(k_lbl, idx, 0)
            self._grid.addWidget(v_lbl, idx, 1)

    def set_diagnostic_rows(self, context_rows: Sequence[Mapping[str, Any]]) -> None:
        """Populate SmartErrorDialog's 3x3 diagnostic grid from ErrorReport.context_rows.

        First 6 entries render as two 3-column rows; any 7th+ entry renders as a
        full-width colspan=3 monospace target row (matching Preview r5 diag-table).
        """
        self.clear_rows()
        p = PORCELAIN_TOKENS
        self.setStyleSheet(
            f"QFrame#hairlineKvTable {{ background: {p.WHITE}; "
            f"border: 1px solid {p.HAIRLINE_STRONG}; border-radius: 0px; }}"
        )
        for col in range(3):
            self._grid.setColumnStretch(col, 1)

        items = list(context_rows)
        grid_items = items[:6]
        wide_items = items[6:]
        total_grid_rows = (len(grid_items) + 2) // 3 + len(wide_items)

        for idx, entry in enumerate(grid_items):
            r = idx // 3
            c = idx % 3
            bg = p.ICE_ROW_ALT if r % 2 == 1 else p.WHITE
            right_rule = "" if c == 2 else f"border-right: 1px solid {p.HAIRLINE_CELL};"
            bottom_rule = "" if r == total_grid_rows - 1 else f"border-bottom: 1px solid {p.HAIRLINE_CELL};"

            cell = QFrame(self)
            cell.setStyleSheet(f"QFrame {{ background: {bg}; border: none; {right_rule} {bottom_rule} }}")
            cell_layout = QVBoxLayout_helper(cell)

            lbl = QLabel(nfc(str(entry.get("label", ""))), cell)
            lbl.setFont(ui_font(FS_CAPTION - 0.5, 600))
            lbl.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent; border: none;")

            tone = str(entry.get("tone", "neutral"))
            val = QLabel(nfc(str(entry.get("value", ""))), cell)
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setFont(mono_font(11.0, 700) if tone == "mono" else ui_font(FS_META, 700, tabular=True))
            val.setStyleSheet(
                f"color: {_TONE_COLORS.get(tone, p.NAVY_TEXT)}; background: transparent; border: none;"
            )

            cell_layout.addWidget(lbl)
            cell_layout.addWidget(val)
            self._grid.addWidget(cell, r, c)

        base_row = (len(grid_items) + 2) // 3
        if 0 < len(grid_items) < 6 and len(grid_items) % 3 != 0:
            for pad_idx in range(len(grid_items), base_row * 3):
                r = pad_idx // 3
                c = pad_idx % 3
                bg = p.ICE_ROW_ALT if r % 2 == 1 else p.WHITE
                right_rule = "" if c == 2 else f"border-right: 1px solid {p.HAIRLINE_CELL};"
                bottom_rule = "" if r == total_grid_rows - 1 else f"border-bottom: 1px solid {p.HAIRLINE_CELL};"
                pad_cell = QFrame(self)
                pad_cell.setStyleSheet(
                    f"QFrame {{ background: {bg}; border: none; {right_rule} {bottom_rule} }}"
                )
                self._grid.addWidget(pad_cell, r, c)

        for w_idx, entry in enumerate(wide_items):
            r = base_row + w_idx
            bottom_rule = "" if r == total_grid_rows - 1 else f"border-bottom: 1px solid {p.HAIRLINE_CELL};"
            wide = QFrame(self)
            wide.setStyleSheet(f"QFrame {{ background: {p.WHITE}; border: none; {bottom_rule} }}")
            wl = QHBoxLayout(wide)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setSpacing(0)

            k_lbl = QLabel(nfc(str(entry.get("label", ""))), wide)
            k_lbl.setFont(ui_font(11.0, 600))
            k_lbl.setStyleSheet(
                f"background: {p.ICE_ZEBRA}; color: {p.SLATE_MUTED}; padding: 7px 11px; "
                f"border-right: 1px solid {p.HAIRLINE_CELL}; border-top: none; border-bottom: none;"
            )
            k_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

            v_lbl = QLabel(nfc(str(entry.get("value", ""))), wide)
            v_lbl.setFont(mono_font(11.0, 600))
            v_lbl.setWordWrap(True)
            v_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            v_lbl.setStyleSheet(
                f"background: {p.WHITE}; color: {p.NAVY_TEXT}; padding: 7px 11px; border: none;"
            )

            wl.addWidget(k_lbl, 0)
            wl.addWidget(v_lbl, 1)
            self._grid.addWidget(wide, r, 0, 1, 3)


def QVBoxLayout_helper(parent: QWidget):
    from PySide6.QtWidgets import QVBoxLayout

    lay = QVBoxLayout(parent)
    lay.setContentsMargins(11, 8, 11, 8)
    lay.setSpacing(2)
    return lay
