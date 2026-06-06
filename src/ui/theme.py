"""
应用主题 — 现代高端主题系统

设计理念：
- 浅色主题：极简灰白底色 + HSL 柔和卡片 + 浮动胶囊标签页 + 蓝紫渐变强调色
- 深色主题：暗夜微光背景 + 碳黑悬浮卡片 + 靛蓝渐变强调色
- 灰色主题：中性钢灰底色 + 青蓝微发光强调色
"""

# ================================================================
#  浅色主题 — 现代简约 + 柔和阴影 + 蓝紫渐变
# ================================================================
LIGHT_STYLESHEET = """
/* ========== 全局字体与基底 ========== */
* {
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", "Helvetica Neue", sans-serif;
    font-size: 13px;
    outline: none;
}

QMainWindow {
    background-color: #F4F4F7;
    color: #18181B;
}

QWidget {
    color: #27272A;
}

/* ========== 浮动胶囊标签页 ========== */
QTabWidget::pane {
    border: none;
    background-color: transparent;
    padding: 0px;
    margin-top: 12px;
}

QTabBar {
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background-color: transparent;
    color: #71717A;
    padding: 8px 22px;
    margin-right: 6px;
    margin-bottom: 2px;
    border: 1px solid transparent;
    border-radius: 18px; /* 胶囊形状 */
    font-weight: 500;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #6366F1;
    border: 1px solid #E4E4E7;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #E4E4E7;
    color: #18181B;
}

/* ========== 卡片视图 ========== */
QWidget#card {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 12px;
}

QLabel#groupTitle {
    font-weight: 700;
    font-size: 12px;
    color: #71717A;
    padding-left: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ========== 分组框 — 卡片化 ========== */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 10px;
    margin-top: 10px;
    padding: 12px 14px 14px 14px;
    padding-top: 28px;
    font-weight: 600;
    font-size: 12px;
    color: #3F3F46;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    left: 10px;
    background-color: #EEF2FF;
    border-radius: 6px;
    color: #4F46E5;
    font-weight: 700;
    font-size: 11px;
}

/* ========== 输入控件 ========== */
QLineEdit, QComboBox, QSpinBox {
    background-color: #F4F4F5;
    border: 1px solid #E4E4E7;
    border-radius: 10px;
    padding: 8px 12px;
    color: #18181B;
    min-height: 24px;
    selection-background-color: #C7D2FE;
    selection-color: #4338CA;
}

QLineEdit:focus, QComboBox:focus, QComboBox:on, QSpinBox:focus {
    border-color: #818CF8;
    background-color: #FFFFFF;
}

QLineEdit::placeholder {
    color: #A1A1AA;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    background-color: #F4F4F5;
    color: #A1A1AA;
    border-color: #E4E4E7;
}

/* 下拉框弹窗微调 */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 8px;
    selection-background-color: #EEF2FF;
    selection-color: #4F46E5;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 6px;
    min-height: 26px;
    color: #27272A;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #F4F4F5;
    color: #18181B;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #FFFFFF;
    color: #4F46E5;
    border: 1px solid #E4E4E7;
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 600;
    min-height: 24px;
    letter-spacing: 0.2px;
}

QPushButton:hover {
    background-color: #EEF2FF;
    border-color: #C7D2FE;
    color: #4338CA;
}

QPushButton:pressed {
    background-color: #E0E7FF;
    border-color: #A5B4FC;
}

QPushButton:disabled {
    background-color: #F4F4F5;
    color: #D1D1D6;
    border-color: #E4E4E7;
}

/* 主操作按钮 — 蓝紫渐变 */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 24px;
    font-size: 13px;
    border-radius: 10px;
    letter-spacing: 0.5px;
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
    background: #E4E4E7;
    color: #A1A1AA;
}

/* 页内主执行按钮 */
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 22px;
    border-radius: 8px;
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
    background: #E4E4E7;
    color: #A1A1AA;
}

/* ========== 复选框 / 单选框 ========== */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #3F3F46;
    min-height: 22px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #D1D1D6;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #6366F1;
    border-color: #6366F1;
}

QCheckBox::indicator:hover {
    border-color: #818CF8;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #D1D1D6;
    background-color: #FFFFFF;
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

/* ========== 文本与滚动条 ========== */
QTextEdit, QTextBrowser {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 10px;
    padding: 8px;
    color: #18181B;
    font-family: "Cascadia Code", "Consolas", "Fira Code", monospace;
    font-size: 12px;
    selection-background-color: #C7D2FE;
    selection-color: #4338CA;
}

QTextEdit:focus {
    border-color: #818CF8;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #E4E4E7;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #CBD5E1;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #E4E4E7;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #CBD5E1;
}

QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
    border: none;
    width: 0px;
    height: 0px;
}

/* ========== 状态栏与提示 ========== */
QStatusBar {
    background-color: #FFFFFF;
    color: #71717A;
    border-top: 1px solid #E4E4E7;
    padding: 4px 12px;
    font-size: 11px;
}

QLabel {
    color: #27272A;
}

QLabel#secondaryLabel {
    color: #71717A;
    font-size: 11px;
}

QLabel#successLabel {
    color: #16A34A;
    font-weight: 700;
}

QLabel#errorLabel {
    color: #DC2626;
    font-weight: 700;
}

QLabel#headerLabel {
    font-size: 20px;
    font-weight: 800;
    color: #18181B;
    letter-spacing: -0.2px;
}

QToolTip {
    background-color: #18181B;
    color: #FAFAFA;
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #E4E4E7;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 18px;
    height: 18px;
    margin: -6px 0;
    background: #6366F1;
    border-radius: 9px;
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
/* ========== 全局字体与基底 ========== */
* {
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-size: 13px;
    outline: none;
}

QMainWindow {
    background-color: #09090B;
    color: #F4F4F5;
}

QWidget {
    color: #E4E4E7;
}

/* ========== 选项卡胶囊 ========== */
QTabWidget::pane {
    border: none;
    background-color: transparent;
    padding: 0px;
    margin-top: 12px;
}

QTabBar {
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background-color: transparent;
    color: #A1A1AA;
    padding: 8px 22px;
    margin-right: 6px;
    margin-bottom: 2px;
    border: 1px solid transparent;
    border-radius: 18px;
    font-weight: 500;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #27272A;
    color: #FAFAFA;
    border: 1px solid #3F3F46;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #18181B;
    color: #FFFFFF;
}

/* ========== 卡片视图 ========== */
QWidget#card {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 12px;
}

QLabel#groupTitle {
    font-weight: 700;
    font-size: 12px;
    color: #A1A1AA;
    padding-left: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ========== 分组框 ========== */
QGroupBox {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 10px;
    margin-top: 10px;
    padding: 12px 14px 14px 14px;
    padding-top: 28px;
    font-weight: 600;
    font-size: 12px;
    color: #E4E4E7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    left: 10px;
    background-color: #312E81;
    border-radius: 6px;
    color: #C7D2FE;
    font-weight: 700;
    font-size: 11px;
}

/* ========== 输入控件 ========== */
QLineEdit, QComboBox, QSpinBox {
    background-color: #09090B;
    border: 1px solid #27272A;
    border-radius: 10px;
    padding: 8px 12px;
    color: #FAFAFA;
    min-height: 24px;
    selection-background-color: #312E81;
    selection-color: #E0E7FF;
}

QLineEdit:focus, QComboBox:focus, QComboBox:on, QSpinBox:focus {
    border-color: #818CF8;
    background-color: #18181B;
}

QLineEdit::placeholder {
    color: #52525B;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    background-color: #09090B;
    color: #52525B;
    border-color: #27272A;
}

/* 下拉框列表 */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
    selection-background-color: #312E81;
    selection-color: #C7D2FE;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 6px;
    min-height: 26px;
    color: #E4E4E7;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #27272A;
    color: #FFFFFF;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #18181B;
    color: #818CF8;
    border: 1px solid #27272A;
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 600;
    min-height: 24px;
    letter-spacing: 0.2px;
}

QPushButton:hover {
    background-color: #1E1B4B;
    border-color: #4338CA;
    color: #C7D2FE;
}

QPushButton:pressed {
    background-color: #312E81;
    border-color: #4F46E5;
}

QPushButton:disabled {
    background-color: #09090B;
    color: #3F3F46;
    border-color: #27272A;
}

/* 一键执行 */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 24px;
    font-size: 13px;
    border-radius: 10px;
    letter-spacing: 0.5px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #818CF8, stop:1 #A78BFA);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4F46E5, stop:1 #7C3AED);
}

QPushButton#primaryBtn:disabled {
    background: #27272A;
    color: #52525B;
}

/* 动作按钮 */
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1, stop:1 #8B5CF6);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 22px;
    border-radius: 8px;
}

QPushButton#actionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #818CF8, stop:1 #A78BFA);
}

QPushButton#actionBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4F46E5, stop:1 #7C3AED);
}

QPushButton#actionBtn:disabled {
    background: #27272A;
    color: #52525B;
}

/* ========== 复选框 / 单选框 ========== */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #D4D4D8;
    min-height: 22px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #52525B;
    background-color: #09090B;
}

QCheckBox::indicator:checked {
    background-color: #818CF8;
    border-color: #818CF8;
}

QCheckBox::indicator:hover {
    border-color: #A5B4FC;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #52525B;
    background-color: #09090B;
}

QRadioButton::indicator:checked {
    background-color: #818CF8;
    border-color: #818CF8;
}

QRadioButton::indicator:hover {
    border-color: #A5B4FC;
}

/* ========== 进度条 ========== */
QProgressBar {
    background-color: #18181B;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
    font-size: 1px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #818CF8, stop:0.5 #8B5CF6, stop:1 #C084FC);
    border-radius: 6px;
}

/* ========== 文本与滚动条 ========== */
QTextEdit, QTextBrowser {
    background-color: #09090B;
    border: 1px solid #27272A;
    border-radius: 10px;
    padding: 8px;
    color: #FAFAFA;
    font-family: "Cascadia Code", "Consolas", "Fira Code", monospace;
    font-size: 12px;
    selection-background-color: #312E81;
    selection-color: #E0E7FF;
}

QTextEdit:focus {
    border-color: #818CF8;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #27272A;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #3F3F46;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #27272A;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #3F3F46;
}

QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
    border: none;
    width: 0px;
    height: 0px;
}

/* ========== 状态栏与标签 ========== */
QStatusBar {
    background-color: #18181B;
    color: #71717A;
    border-top: 1px solid #27272A;
    padding: 4px 12px;
    font-size: 11px;
}

QLabel {
    color: #E4E4E7;
}

QLabel#secondaryLabel {
    color: #71717A;
    font-size: 11px;
}

QLabel#successLabel {
    color: #34D399;
    font-weight: 700;
}

QLabel#errorLabel {
    color: #F87171;
    font-weight: 700;
}

QLabel#headerLabel {
    font-size: 20px;
    font-weight: 800;
    color: #FAFAFA;
    letter-spacing: -0.2px;
}

QToolTip {
    background-color: #27272A;
    color: #FFFFFF;
    border: 1px solid #3F3F46;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #27272A;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 18px;
    height: 18px;
    margin: -6px 0;
    background: #818CF8;
    border-radius: 9px;
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
/* ========== 全局字体与基底 ========== */
* {
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-size: 13px;
    outline: none;
}

QMainWindow {
    background-color: #0F172A;
    color: #E2E8F0;
}

QWidget {
    color: #CBD5E1;
}

/* ========== 选项卡胶囊 ========== */
QTabWidget::pane {
    border: none;
    background-color: transparent;
    padding: 0px;
    margin-top: 12px;
}

QTabBar {
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background-color: transparent;
    color: #64748B;
    padding: 8px 22px;
    margin-right: 6px;
    margin-bottom: 2px;
    border: 1px solid transparent;
    border-radius: 18px;
    font-weight: 500;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #1E293B;
    color: #22D3EE;
    border: 1px solid #334155;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #1E293B;
    color: #F1F5F9;
}

/* ========== 卡片视图 ========== */
QWidget#card {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
}

QLabel#groupTitle {
    font-weight: 700;
    font-size: 12px;
    color: #94A3B8;
    padding-left: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ========== 分组框 ========== */
QGroupBox {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    margin-top: 10px;
    padding: 12px 14px 14px 14px;
    padding-top: 28px;
    font-weight: 600;
    font-size: 12px;
    color: #E2E8F0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    left: 10px;
    background-color: #164E63;
    border-radius: 6px;
    color: #67E8F9;
    font-weight: 700;
    font-size: 11px;
}

/* ========== 输入控件 ========== */
QLineEdit, QComboBox, QSpinBox {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px 12px;
    color: #F8FAFC;
    min-height: 24px;
    selection-background-color: #164E63;
    selection-color: #67E8F9;
}

QLineEdit:focus, QComboBox:focus, QComboBox:on, QSpinBox:focus {
    border-color: #06B6D4;
    background-color: #1E293B;
}

QLineEdit::placeholder {
    color: #475569;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    background-color: #0F172A;
    color: #475569;
    border-color: #334155;
}

/* 下拉列表 */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: #164E63;
    selection-color: #67E8F9;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 6px;
    min-height: 26px;
    color: #E2E8F0;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #334155;
    color: #FFFFFF;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #1E293B;
    color: #38BDF8;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 600;
    min-height: 24px;
    letter-spacing: 0.2px;
}

QPushButton:hover {
    background-color: #0C4A6E;
    border-color: #0284C7;
    color: #E0F2FE;
}

QPushButton:pressed {
    background-color: #075985;
    border-color: #0369A1;
}

QPushButton:disabled {
    background-color: #0F172A;
    color: #475569;
    border-color: #334155;
}

/* 一键执行 */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891B2, stop:1 #06B6D4);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 24px;
    font-size: 13px;
    border-radius: 10px;
    letter-spacing: 0.5px;
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
    background: #334155;
    color: #64748B;
}

/* 动作按钮 */
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0891B2, stop:1 #06B6D4);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 22px;
    border-radius: 8px;
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
    background: #334155;
    color: #64748B;
}

/* ========== 复选框 / 单选框 ========== */
QCheckBox, QRadioButton {
    spacing: 8px;
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
    background-color: #06B6D4;
    border-color: #06B6D4;
}

QCheckBox::indicator:hover {
    border-color: #22D3EE;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #475569;
    background-color: #0F172A;
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
        stop:0 #0891B2, stop:0.5 #06B6D4, stop:1 #22D3EE);
    border-radius: 6px;
}

/* ========== 文本与滚动条 ========== */
QTextEdit, QTextBrowser {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px;
    color: #E2E8F0;
    font-family: "Cascadia Code", "Consolas", "Fira Code", monospace;
    font-size: 12px;
    selection-background-color: #164E63;
    selection-color: #67E8F9;
}

QTextEdit:focus {
    border-color: #06B6D4;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #475569;
}

QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
    border: none;
    width: 0px;
    height: 0px;
}

/* ========== 状态栏与标签 ========== */
QStatusBar {
    background-color: #1E293B;
    color: #64748B;
    border-top: 1px solid #334155;
    padding: 4px 12px;
    font-size: 11px;
}

QLabel {
    color: #E2E8F0;
}

QLabel#secondaryLabel {
    color: #64748B;
    font-size: 11px;
}

QLabel#successLabel {
    color: #34D399;
    font-weight: 700;
}

QLabel#errorLabel {
    color: #F87171;
    font-weight: 700;
}

QLabel#headerLabel {
    font-size: 20px;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.2px;
}

QToolTip {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #334155;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 18px;
    height: 18px;
    margin: -6px 0;
    background: #06B6D4;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #0891B2;
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
