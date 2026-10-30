"""Starlit Glass theme constants and QSS stylesheet generator."""

from __future__ import annotations


class Theme:
    # Color palette
    BG_NAVY = "#06182f"
    GLASS_BG = "rgba(10, 32, 60, 0.78)"
    GLASS_BG_SOLID = "#0a203c"
    GLASS_CARD_BG = "rgba(14, 42, 78, 0.82)"
    GLASS_CARD_BORDER = "#c6bba4"
    GLASS_CARD_BORDER_HOVER = "#b6a379"

    PRIMARY_CYAN = "#0ab8c1"
    PRIMARY_CYAN_HOVER = "#8ae2ff"
    PRIMARY_CYAN_PRESSED = "#3fb6e8"
    PRIMARY_CYAN_DISABLED = "#25506e"

    SECONDARY_BTN_BG = "rgba(22, 64, 110, 0.65)"
    SECONDARY_BTN_BG_HOVER = "rgba(35, 95, 160, 0.85)"
    SECONDARY_BTN_BORDER = "#c5b79c"

    DANGER_RED = "#ff5470"
    DANGER_RED_HOVER = "#ff7998"
    DANGER_RED_BG = "rgba(180, 30, 60, 0.6)"

    SUCCESS_GREEN = "#3af0bc"
    WARNING_AMBER = "#ffce79"

    TEXT_WHITE = "#304679"
    TEXT_MUTED = "#687c9e"
    TEXT_DARK = "#06182f"

    FONT_FAMILY = '"Nunito"'

    @classmethod
    def get_application_stylesheet(cls) -> str:
        from .assets import AssetManager
        from .typography import FAMILY
        family='"'+FAMILY+'"'
        tooltip=(AssetManager.get().ui_dir/AssetManager.get().meta("controls/tooltip")["png_2x"]).as_posix()
        return f"""
        QWidget {{
            font-family: {family};

            color: {cls.TEXT_WHITE};
            outline: none;
            background-color: transparent;
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: rgba(8, 24, 48, 0.4);
            width: 8px;
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(180, 164, 139, 0.5);
            min-height: 24px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(160, 143, 115, 0.7);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* Tooltip */
        QToolTip {{
            background-color: #fbf8ef;
            color: {cls.TEXT_WHITE};
            border: 1px solid #c6bba4;
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 15px;
        }}

        /* Input fields */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: rgba(238, 242, 246, 0.95);
            border: 1px solid {cls.GLASS_CARD_BORDER};
            border-radius: 6px;
            padding: 8px 12px;
            color: {cls.TEXT_WHITE};
            selection-background-color: {cls.PRIMARY_CYAN};
            selection-color: {cls.TEXT_DARK};
            font-size: 17px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {cls.PRIMARY_CYAN};
            background-color: rgba(255, 252, 246, 0.98);
        }}

        /* List views */
        QListWidget {{
            background-color: transparent;
            border: none;
        }}
        QListWidget::item {{
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 4px;
            background: rgba(16, 48, 86, 0.3);
            border: 1px solid transparent;
        }}
        QListWidget::item:hover {{
            background: rgba(30, 80, 138, 0.45);
            border: 1px solid {cls.GLASS_CARD_BORDER};
        }}
        QListWidget::item:selected {{
            background: rgba(40, 105, 175, 0.6);
            border: 1px solid {cls.PRIMARY_CYAN};
        }}

        /* Progress Bar */
        QProgressBar {{
            background-color: rgba(223, 233, 242, 0.95);
            border: 1px solid {cls.GLASS_CARD_BORDER};
            border-radius: 6px;
            text-align: center;
            color: {cls.TEXT_WHITE};
            font-size: 15px;
            font-weight: 500;
            height: 18px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #2aa8d6,
                stop: 1 #62d4ff
            );
            border-radius: 5px;
        }}
        """
