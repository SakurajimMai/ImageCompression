"""
应用主题 — 现代高端主题系统

设计理念：
- 浅色主题：干净明亮 + 柔和阴影 + 蓝紫渐变强调色
- 深色主题：深邃优雅 + 微光边框 + 靛蓝渐变强调色
"""

# ================================================================
#  浅色主题 — 现代简约 + 柔和阴影 + 蓝紫渐变
# ================================================================
LIGHT_STYLESHEET = """
/* ========== 全局字体与基底 ========== */
* {
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-size: 13px;
    outline: none;
}

QMainWindow {
    background-color: #F2F2F7;
    color: #1C1C1E;
}

QWidget {
    color: #1E293B;
}

/* ========== 标签页 — 底部渐变高亮 ========== */
QTabWidget::pane {
    border: none;
    background-color: transparent;
    padding: 0px;
    margin-top: 10px;
}

QTabBar {
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background-color: transparent;
    color: #64748B;
    padding: 10px 28px;
    margin-right: 2px;
    border: none;
    border-bottom: 3px solid transparent;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #6366F1;
    border-bottom: 3px solid #6366F1;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #F1F5F9;
    color: #475569;
}

/* ========== 卡片视图 ========== */
QWidget#card {
    background-color: #FFFFFF;
    border-radius: 12px;
}

QLabel#groupTitle {
    font-weight: 600; 
    font-size: 13px; 
    color: #8E8E93; 
    padding-left: 4px;
}

/* ========== 分组框 — 卡片化 ========== */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 8px;
    padding: 8px 10px 10px 10px;
    padding-top: 24px;
    font-weight: 600;
    font-size: 12px;
    color: #334155;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    left: 8px;
    background-color: #FFFFFF;
    border-radius: 4px;
    color: #6366F1;
    font-weight: 700;
    font-size: 12px;
}

/* ========== 输入框 — 圆角柔和 ========== */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 8px 12px;
    color: #1C1C1E;
    min-height: 22px;
    selection-background-color: #007AFF;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border-color: #818CF8;
    background-color: #FFFFFF;
}

QLineEdit::placeholder {
    color: #94A3B8;
}

QLineEdit:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

/* ========== 下拉框 ========== */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 8px 12px;
    color: #1C1C1E;
    min-height: 22px;
    min-width: 80px;
}

QComboBox:focus, QComboBox:on {
    border-color: #818CF8;
    background-color: #FFFFFF;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    border-left: 1px solid #E2E8F0;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    selection-background-color: #EEF2FF;
    selection-color: #4F46E5;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #F1F5F9;
}

/* ========== 数字输入框 ========== */
QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 8px 8px;
    color: #1C1C1E;
    min-height: 22px;
    min-width: 60px;
}

QSpinBox:focus {
    border-color: #818CF8;
    background-color: #FFFFFF;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
    border: none;
    border-radius: 3px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #EEF2FF;
}

/* ========== 按钮 — 柔和圆角 + 过渡 ========== */
QPushButton {
    background-color: #FFFFFF;
    color: #007AFF;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #CBD5E1;
    color: #1E293B;
}

QPushButton:pressed {
    background-color: #F1F5F9;
    border-color: #94A3B8;
}

QPushButton:disabled {
    background-color: #F8FAFC;
    color: #CBD5E1;
    border-color: #F1F5F9;
}

/* 主操作按钮 — 渐变 */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 24px;
    font-size: 13px;
    border-radius: 8px;
    letter-spacing: 1px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4F46E5, stop:1 #7C3AED);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4338CA, stop:1 #6D28D9);
}

QPushButton#primaryBtn:disabled {
    background: #CBD5E1;
    color: #F8FAFC;
}

/* 操作按钮 — 渐变 */
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 6px 20px;
    border-radius: 6px;
}

QPushButton#actionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4F46E5, stop:1 #7C3AED);
}

QPushButton#actionBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4338CA, stop:1 #6D28D9);
}

QPushButton#actionBtn:disabled {
    background: #CBD5E1;
    color: #F8FAFC;
}

/* ========== 复选框 — 圆角方块 ========== */
QCheckBox {
    spacing: 6px;
    color: #334155;
    min-height: 22px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #CBD5E1;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #6366F1;
    border-color: #6366F1;
}

QCheckBox::indicator:hover {
    border-color: #818CF8;
}

QCheckBox::indicator:checked:hover {
    background-color: #4F46E5;
    border-color: #4F46E5;
}

/* ========== 单选框 ========== */
QRadioButton {
    spacing: 6px;
    color: #334155;
    min-height: 22px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #CBD5E1;
    background-color: #FFFFFF;
}

QRadioButton::indicator:checked {
    background-color: #6366F1;
    border-color: #6366F1;
}

QRadioButton::indicator:hover {
    border-color: #818CF8;
}

/* ========== 进度条 — 圆角渐变 ========== */
QProgressBar {
    background-color: #EEF2FF;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
    font-size: 1px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:0.5 #8B5CF6, stop:1 #A78BFA);
    border-radius: 6px;
}

/* ========== 文本编辑框 ========== */
QTextEdit {
    background-color: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 6px;
    padding: 6px;
    color: #1E293B;
    font-family: "Cascadia Code", "Consolas", "Fira Code", monospace;
    font-size: 12px;
    selection-background-color: #818CF8;
    selection-color: #FFFFFF;
}

QTextEdit:focus {
    border-color: #818CF8;
}

/* ========== 滚动条 — 极细圆润 ========== */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 3px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 0;
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    width: 0;
    background: transparent;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #F8FAFC;
    color: #64748B;
    border-top: 1px solid #E2E8F0;
    padding: 3px 10px;
    font-size: 11px;
}

/* ========== Label ========== */
QLabel {
    color: #334155;
}

QLabel#secondaryLabel {
    color: #64748B;
    font-size: 11px;
}

QLabel#successLabel {
    color: #059669;
    font-weight: 600;
}

QLabel#errorLabel {
    color: #DC2626;
    font-weight: 600;
}

QLabel#headerLabel {
    font-size: 18px;
    font-weight: 800;
    color: #1E293B;
    letter-spacing: 0.5px;
}

/* ========== Tooltip ========== */
QToolTip {
    background-color: #1E293B;
    color: #F8FAFC;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ========== ScrollArea ========== */
QScrollArea {
    background-color: transparent;
    border: none;
}

QStackedWidget {
    background-color: transparent;
}

/* ========== TextBrowser (说明页) ========== */
QTextBrowser {
    background-color: #FFFFFF;
    border: none;
    padding: 10px;
}

/* ========== Slider ========== */
QSlider::groove:horizontal {
    height: 6px;
    background: #E2E8F0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #6366F1;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #4F46E5;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    border-radius: 3px;
}
"""

# ================================================================
#  深色主题 — 深邃优雅 + 微光边框 + 靛蓝渐变
# ================================================================
DARK_STYLESHEET = """
/* ========== 全局 ========== */
* {
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-size: 13px;
    outline: none;
}

QMainWindow {
    background-color: #000000;
    color: #FFFFFF;
}

QWidget {
    color: #E2E8F0;
}

/* ========== 标签页 ========== */
QTabWidget::pane {
    border: none;
    background-color: transparent;
    padding: 0px;
    margin-top: 10px;
}

QTabBar {
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background-color: transparent;
    color: #64748B;
    padding: 10px 28px;
    margin-right: 2px;
    border: none;
    border-bottom: 3px solid transparent;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #1E293B;
    color: #A5B4FC;
    border-bottom: 3px solid #818CF8;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #1E293B;
    color: #94A3B8;
}

/* ========== 卡片视图 ========== */
QWidget#card {
    background-color: #1C1C1E;
    border-radius: 12px;
}

QLabel#groupTitle {
    font-weight: 600; 
    font-size: 13px; 
    color: #98989D; 
    padding-left: 4px;
}

/* ========== 分组框 ========== */
QGroupBox {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 8px;
    padding: 8px 10px 10px 10px;
    padding-top: 24px;
    font-weight: 600;
    font-size: 12px;
    color: #CBD5E1;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    left: 8px;
    background-color: #1E293B;
    border-radius: 4px;
    color: #A5B4FC;
    font-weight: 700;
    font-size: 12px;
}

/* ========== 输入框 ========== */
QLineEdit {
    background-color: #1C1C1E;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    padding: 8px 12px;
    color: #FFFFFF;
    min-height: 22px;
    selection-background-color: #0A84FF;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border-color: #818CF8;
    background-color: #1E293B;
}

QLineEdit::placeholder {
    color: #475569;
}

QLineEdit:disabled {
    background-color: #0F172A;
    color: #475569;
    border-color: #1E293B;
}

/* ========== 下拉框 ========== */
QComboBox {
    background-color: #1C1C1E;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    padding: 8px 12px;
    color: #FFFFFF;
    min-height: 22px;
    min-width: 80px;
}

QComboBox:focus, QComboBox:on {
    border-color: #818CF8;
    background-color: #1E293B;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    border-left: 1px solid #334155;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    selection-background-color: #312E81;
    selection-color: #A5B4FC;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #334155;
}

/* ========== 数字输入框 ========== */
QSpinBox {
    background-color: #1C1C1E;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    padding: 8px 8px;
    color: #FFFFFF;
    min-height: 22px;
    min-width: 60px;
}

QSpinBox:focus {
    border-color: #818CF8;
    background-color: #1E293B;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
    border: none;
    border-radius: 3px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #334155;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #1C1C1E;
    color: #0A84FF;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #475569;
    color: #E2E8F0;
}

QPushButton:pressed {
    background-color: #475569;
}

QPushButton:disabled {
    background-color: #0F172A;
    color: #475569;
    border-color: #1E293B;
}

/* 主操作按钮 — 渐变 */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 24px;
    font-size: 13px;
    border-radius: 8px;
    letter-spacing: 1px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4F46E5, stop:1 #7C3AED);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4338CA, stop:1 #6D28D9);
}

QPushButton#primaryBtn:disabled {
    background: #334155;
    color: #64748B;
}

/* 操作按钮 */
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 6px 20px;
    border-radius: 6px;
}

QPushButton#actionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4F46E5, stop:1 #7C3AED);
}

QPushButton#actionBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4338CA, stop:1 #6D28D9);
}

QPushButton#actionBtn:disabled {
    background: #334155;
    color: #64748B;
}

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 6px;
    color: #CBD5E1;
    min-height: 22px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #475569;
    background-color: #0F172A;
}

QCheckBox::indicator:checked {
    background-color: #6366F1;
    border-color: #6366F1;
}

QCheckBox::indicator:hover {
    border-color: #818CF8;
}

QCheckBox::indicator:checked:hover {
    background-color: #4F46E5;
    border-color: #4F46E5;
}

/* ========== 单选框 ========== */
QRadioButton {
    spacing: 6px;
    color: #CBD5E1;
    min-height: 22px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #475569;
    background-color: #0F172A;
}

QRadioButton::indicator:checked {
    background-color: #6366F1;
    border-color: #6366F1;
}

QRadioButton::indicator:hover {
    border-color: #818CF8;
}

/* ========== 进度条 ========== */
QProgressBar {
    background-color: #1E293B;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
    font-size: 1px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:0.5 #8B5CF6, stop:1 #A78BFA);
    border-radius: 6px;
}

/* ========== 文本编辑框 ========== */
QTextEdit {
    background-color: #0F172A;
    border: 1.5px solid #334155;
    border-radius: 6px;
    padding: 6px;
    color: #E2E8F0;
    font-family: "Cascadia Code", "Consolas", "Fira Code", monospace;
    font-size: 12px;
    selection-background-color: #818CF8;
    selection-color: #FFFFFF;
}

QTextEdit:focus {
    border-color: #818CF8;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 3px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 0;
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background: #475569;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    width: 0;
    background: transparent;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #0F172A;
    color: #64748B;
    border-top: 1px solid #1E293B;
    padding: 3px 10px;
    font-size: 11px;
}

/* ========== Label ========== */
QLabel {
    color: #CBD5E1;
}

QLabel#secondaryLabel {
    color: #64748B;
    font-size: 11px;
}

QLabel#successLabel {
    color: #34D399;
    font-weight: 600;
}

QLabel#errorLabel {
    color: #F87171;
    font-weight: 600;
}

QLabel#headerLabel {
    font-size: 18px;
    font-weight: 800;
    color: #F1F5F9;
    letter-spacing: 0.5px;
}

/* ========== Tooltip ========== */
QToolTip {
    background-color: #334155;
    color: #F1F5F9;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ========== ScrollArea ========== */
QScrollArea {
    background-color: transparent;
    border: none;
}

QStackedWidget {
    background-color: transparent;
}

/* ========== TextBrowser ========== */
QTextBrowser {
    background-color: #1E293B;
    color: #E2E8F0;
    border: none;
    padding: 10px;
}

/* ========== Slider ========== */
QSlider::groove:horizontal {
    height: 6px;
    background: #334155;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #818CF8;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #6366F1;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    border-radius: 3px;
}
"""

# ================================================================
#  灰色主题 — 中性钢灰 + 青蓝强调色
# ================================================================
GRAY_STYLESHEET = """
/* ========== 全局 ========== */
* {
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-size: 13px;
    outline: none;
}

QMainWindow {
    background-color: #111827;
    color: #D1D5DB;
}

QWidget {
    color: #D1D5DB;
}

/* ========== 标签页 ========== */
QTabWidget::pane {
    border: none;
    background-color: transparent;
    padding: 0px;
    margin-top: 10px;
}

QTabBar {
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background-color: transparent;
    color: #6B7280;
    padding: 10px 28px;
    margin-right: 2px;
    border: none;
    border-bottom: 3px solid transparent;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #1F2937;
    color: #67E8F9;
    border-bottom: 3px solid #06B6D4;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #1F2937;
    color: #9CA3AF;
}

/* ========== 卡片视图 ========== */
QWidget#card {
    background-color: #1F2937;
    border-radius: 12px;
}

QLabel#groupTitle {
    font-weight: 600; 
    font-size: 13px; 
    color: #9CA3AF; 
    padding-left: 4px;
}

/* ========== 分组框 ========== */
QGroupBox {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 8px;
    margin-top: 8px;
    padding: 8px 10px 10px 10px;
    padding-top: 24px;
    font-weight: 600;
    font-size: 12px;
    color: #D1D5DB;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    left: 8px;
    background-color: #1F2937;
    border-radius: 4px;
    color: #22D3EE;
    font-weight: 700;
    font-size: 12px;
}

/* ========== 输入框 ========== */
QLineEdit {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 8px 12px;
    color: #F8FAFC;
    min-height: 22px;
    selection-background-color: #06B6D4;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border-color: #06B6D4;
    background-color: #1F2937;
}

QLineEdit::placeholder {
    color: #4B5563;
}

QLineEdit:disabled {
    background-color: #111827;
    color: #4B5563;
    border-color: #1F2937;
}

/* ========== 下拉框 ========== */
QComboBox {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 8px 12px;
    color: #F8FAFC;
    min-height: 22px;
    min-width: 80px;
}

QComboBox:focus, QComboBox:on {
    border-color: #06B6D4;
    background-color: #1F2937;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    border-left: 1px solid #374151;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox QAbstractItemView {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 6px;
    selection-background-color: #164E63;
    selection-color: #67E8F9;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #374151;
}

/* ========== 数字输入框 ========== */
QSpinBox {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 8px 8px;
    color: #F8FAFC;
    min-height: 22px;
    min-width: 60px;
}

QSpinBox:focus {
    border-color: #06B6D4;
    background-color: #1F2937;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
    border: none;
    border-radius: 3px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #374151;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #1F2937;
    color: #38BDF8;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #374151;
    border-color: #4B5563;
    color: #E5E7EB;
}

QPushButton:pressed {
    background-color: #4B5563;
}

QPushButton:disabled {
    background-color: #111827;
    color: #4B5563;
    border-color: #1F2937;
}

/* 主操作按钮 — 渐变 */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891B2, stop:1 #06B6D4);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 24px;
    font-size: 13px;
    border-radius: 8px;
    letter-spacing: 1px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0E7490, stop:1 #0891B2);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #155E75, stop:1 #0E7490);
}

QPushButton#primaryBtn:disabled {
    background: #374151;
    color: #6B7280;
}

/* 操作按钮 */
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891B2, stop:1 #06B6D4);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 6px 20px;
    border-radius: 6px;
}

QPushButton#actionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0E7490, stop:1 #0891B2);
}

QPushButton#actionBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #155E75, stop:1 #0E7490);
}

QPushButton#actionBtn:disabled {
    background: #374151;
    color: #6B7280;
}

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 6px;
    color: #D1D5DB;
    min-height: 22px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #4B5563;
    background-color: #111827;
}

QCheckBox::indicator:checked {
    background-color: #06B6D4;
    border-color: #06B6D4;
}

QCheckBox::indicator:hover {
    border-color: #22D3EE;
}

QCheckBox::indicator:checked:hover {
    background-color: #0891B2;
    border-color: #0891B2;
}

/* ========== 单选框 ========== */
QRadioButton {
    spacing: 6px;
    color: #D1D5DB;
    min-height: 22px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #4B5563;
    background-color: #111827;
}

QRadioButton::indicator:checked {
    background-color: #06B6D4;
    border-color: #06B6D4;
}

QRadioButton::indicator:hover {
    border-color: #22D3EE;
}

/* ========== 进度条 ========== */
QProgressBar {
    background-color: #1F2937;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
    font-size: 1px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891B2, stop:0.5 #06B6D4, stop:1 #22D3EE);
    border-radius: 6px;
}

/* ========== 文本编辑框 ========== */
QTextEdit {
    background-color: #111827;
    border: 1.5px solid #374151;
    border-radius: 6px;
    padding: 6px;
    color: #E5E7EB;
    font-family: "Cascadia Code", "Consolas", "Fira Code", monospace;
    font-size: 12px;
    selection-background-color: #06B6D4;
    selection-color: #FFFFFF;
}

QTextEdit:focus {
    border-color: #06B6D4;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #4B5563;
    border-radius: 3px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #6B7280;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 0;
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #4B5563;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background: #6B7280;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    width: 0;
    background: transparent;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #111827;
    color: #6B7280;
    border-top: 1px solid #1F2937;
    padding: 3px 10px;
    font-size: 11px;
}

/* ========== Label ========== */
QLabel {
    color: #D1D5DB;
}

QLabel#secondaryLabel {
    color: #6B7280;
    font-size: 11px;
}

QLabel#successLabel {
    color: #34D399;
    font-weight: 600;
}

QLabel#errorLabel {
    color: #F87171;
    font-weight: 600;
}

QLabel#headerLabel {
    font-size: 18px;
    font-weight: 800;
    color: #F3F4F6;
    letter-spacing: 0.5px;
}

/* ========== Tooltip ========== */
QToolTip {
    background-color: #374151;
    color: #F3F4F6;
    border: 1px solid #4B5563;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ========== ScrollArea / Stack ========== */
QScrollArea {
    background-color: transparent;
    border: none;
}

QStackedWidget {
    background-color: transparent;
}

/* ========== TextBrowser ========== */
QTextBrowser {
    background-color: #1F2937;
    color: #E5E7EB;
    border: none;
    padding: 10px;
}

/* ========== Slider ========== */
QSlider::groove:horizontal {
    height: 6px;
    background: #374151;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #22D3EE;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #06B6D4;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891B2, stop:1 #06B6D4);
    border-radius: 3px;
}
"""


def get_stylesheet(theme: str = "light") -> str:
    """获取指定主题的样式表"""
    if theme == "dark":
        return DARK_STYLESHEET
    elif theme == "gray":
        return GRAY_STYLESHEET
    return LIGHT_STYLESHEET
