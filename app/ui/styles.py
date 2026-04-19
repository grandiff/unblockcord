"""
UnblockCord — Dark Theme (QSS)
Discord'dan ilham alan koyu renk paleti.
"""

# ---------------------------------------------------------------------------
# Renk paleti
# ---------------------------------------------------------------------------
COLORS = {
    # Arka planlar
    "bg_primary":   "#0d1117",
    "bg_secondary": "#161b22",
    "bg_tertiary":  "#21262d",
    "bg_card":      "#1c2128",

    # Vurgu
    "accent":         "#5865F2",
    "accent_hover":   "#4752C4",
    "accent_pressed": "#3c45a5",
    "accent_glow":    "rgba(88,101,242,0.15)",

    # Durum renkleri
    "green":  "#57F287",
    "red":    "#ED4245",
    "yellow": "#FEE75C",

    # Metin
    "text_primary":   "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted":     "#484f58",

    # Çerçeve
    "border":       "#30363d",
    "border_focus": "#5865F2",

    # Scrollbar
    "scrollbar":       "#30363d",
    "scrollbar_hover": "#484f58",
}

C = COLORS  # kısayol

# ---------------------------------------------------------------------------
# Ana stylesheet
# ---------------------------------------------------------------------------
MAIN_STYLESHEET = f"""
/* ─── Genel ─────────────────────────────────────── */
* {{
    box-sizing: border-box;
}}

QWidget {{
    background-color: {C['bg_primary']};
    color: {C['text_primary']};
    font-family: 'Segoe UI', 'Inter', 'Arial', sans-serif;
    font-size: 13px;
    border: none;
    outline: none;
}}

QMainWindow {{
    background-color: {C['bg_primary']};
}}

/* ─── Etiket ─────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {C['text_primary']};
}}

/* ─── Düğmeler ───────────────────────────────────── */
QPushButton {{
    background-color: {C['accent']};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 13px;
    min-height: 36px;
}}

QPushButton:hover {{
    background-color: {C['accent_hover']};
}}

QPushButton:pressed {{
    background-color: {C['accent_pressed']};
}}

QPushButton:disabled {{
    background-color: {C['bg_tertiary']};
    color: {C['text_muted']};
}}

QPushButton#btn_danger {{
    background-color: {C['red']};
}}

QPushButton#btn_danger:hover {{
    background-color: #c73c3f;
}}

QPushButton#btn_secondary {{
    background-color: {C['bg_tertiary']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
}}

QPushButton#btn_secondary:hover {{
    background-color: {C['bg_card']};
    border-color: {C['text_secondary']};
}}

/* ─── Tablo ──────────────────────────────────────── */
QTableWidget {{
    background-color: {C['bg_secondary']};
    gridline-color: transparent;
    border: 1px solid {C['border']};
    border-radius: 10px;
    alternate-background-color: {C['bg_card']};
    selection-background-color: {C['bg_tertiary']};
    selection-color: {C['text_primary']};
}}

QTableWidget::item {{
    padding: 7px 14px;
    border-bottom: 1px solid {C['border']};
}}

QTableWidget::item:selected {{
    background-color: {C['bg_tertiary']};
    color: {C['text_primary']};
}}

QHeaderView::section {{
    background-color: {C['bg_tertiary']};
    color: {C['text_secondary']};
    padding: 9px 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.8px;
    border: none;
    border-bottom: 1px solid {C['border']};
}}

QHeaderView::section:first {{
    border-top-left-radius: 10px;
}}

QHeaderView::section:last {{
    border-top-right-radius: 10px;
}}

/* ─── Log / Text alanı ───────────────────────────── */
QTextEdit {{
    background-color: {C['bg_secondary']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 10px;
    padding: 10px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}}

/* ─── ComboBox ───────────────────────────────────── */
QComboBox {{
    background-color: {C['bg_tertiary']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 7px;
    padding: 6px 12px;
    min-width: 160px;
    min-height: 34px;
}}

QComboBox:hover {{
    border-color: {C['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    border-left:  5px solid transparent;
    border-right: 5px solid transparent;
    border-top:   6px solid {C['text_secondary']};
    width: 0;
    height: 0;
}}

QComboBox QAbstractItemView {{
    background-color: {C['bg_tertiary']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 7px;
    selection-background-color: {C['accent']};
    outline: none;
    padding: 4px;
}}

/* ─── CheckBox ───────────────────────────────────── */
QCheckBox {{
    color: {C['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {C['border']};
    background-color: {C['bg_tertiary']};
}}

QCheckBox::indicator:checked {{
    background-color: {C['accent']};
    border-color:     {C['accent']};
}}

/* ─── Scrollbar ──────────────────────────────────── */
QScrollBar:vertical {{
    background: {C['bg_secondary']};
    width: 7px;
    border-radius: 4px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {C['scrollbar']};
    border-radius: 4px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background: {C['scrollbar_hover']};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    height: 0;
}}

/* ─── Kartlar (QFrame#card) ──────────────────────── */
QFrame#card {{
    background-color: {C['bg_secondary']};
    border: 1px solid {C['border']};
    border-radius: 12px;
}}

/* ─── Menü ───────────────────────────────────────── */
QMenu {{
    background-color: {C['bg_secondary']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 5px;
}}

QMenu::item {{
    padding: 8px 18px;
    border-radius: 5px;
    color: {C['text_primary']};
}}

QMenu::item:selected {{
    background-color: {C['accent']};
}}

QMenu::separator {{
    height: 1px;
    background: {C['border']};
    margin: 5px 10px;
}}

/* ─── ToolTip ─────────────────────────────────────── */
QToolTip {{
    background-color: {C['bg_tertiary']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}}
"""
