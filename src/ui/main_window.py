"""
主窗口 — 标签页布局，进度条嵌入每个 tab 底部
"""
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QScrollArea, QComboBox, QStyledItemDelegate,
    QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QAction

from config import Config
from ui.theme import get_stylesheet
from ui.i18n import set_language
from ui.prepare_tab import PrepareTab
from ui.compress_tab import CompressTab
from ui.upload_tab import UploadTab
from ui.settings_tab import SettingsTab
from ui.help_tab import HelpTab
from ui.widgets.progress import ProgressWidget
from ui.widgets.url_output import UrlOutputWidget


def _wrap_in_scroll(widget: QWidget) -> QScrollArea:
    """将 widget 包裹在 QScrollArea 中，使其可滚动"""
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    return scroll


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.config.load()

        self.setWindowTitle("Image Compression")
        self.setMinimumSize(820, 640)
        self.resize(920, 740)
        self.setAcceptDrops(True)

        # 应用语言和主题
        set_language(self.config.language)
        self.setStyleSheet(get_stylesheet(self.config.theme))

        self._setup_ui()
        self._restore_state()
        self._fix_combobox_styles()
        self._setup_tray()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 8, 12, 4)
        root.setSpacing(4)

        # ── 标题行 ──
        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("Image Compression")
        title.setObjectName("headerLabel")
        header.addWidget(title)

        version = QLabel("v2.0")
        version.setObjectName("secondaryLabel")
        header.addWidget(version)
        header.addStretch()

        self.run_all_btn = QPushButton("  ▶  一键执行  ")
        self.run_all_btn.setObjectName("primaryBtn")
        self.run_all_btn.setToolTip("依次执行：准备 → 压缩 → 上传")
        self.run_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_all_btn.clicked.connect(self._run_all)
        header.addWidget(self.run_all_btn)
        root.addLayout(header)

        # ── 共享组件 ──
        self.progress_widget = ProgressWidget()
        self.url_output = UrlOutputWidget()

        # ── 创建各 Tab（嵌入 ScrollArea）──
        self.prepare_tab = PrepareTab(self.config, self.progress_widget)
        self.compress_tab = CompressTab(self.config, self.progress_widget)
        self.upload_tab = UploadTab(self.config, self.progress_widget, self.url_output)
        self.settings_tab = SettingsTab(self.config)
        self.help_tab = HelpTab()

        self.tabs = QTabWidget()
        self.tabs.addTab(_wrap_in_scroll(self.prepare_tab), "📁 准备")
        self.tabs.addTab(_wrap_in_scroll(self.compress_tab), "🗜️ 压缩")
        self.tabs.addTab(_wrap_in_scroll(self.upload_tab), "☁️ 上传")
        self.tabs.addTab(_wrap_in_scroll(self.settings_tab), "⚙️ 设置")
        self.tabs.addTab(_wrap_in_scroll(self.help_tab), "📖 说明")
        root.addWidget(self.tabs, 1)

        # ── 底部状态区 ──
        root.addWidget(self.progress_widget)
        root.addWidget(self.url_output)
        self.progress_widget.setVisible(False)

        self.statusBar().showMessage("就绪")

    def _restore_state(self):
        if self.config.last_input_dir:
            self.prepare_tab.input_edit.setText(self.config.last_input_dir)

    def _fix_combobox_styles(self):
        """强制所有 QComboBox 使用 QSS 样式而非 Windows 原生弹窗"""
        delegate = QStyledItemDelegate(self)
        for combo in self.findChildren(QComboBox):
            combo.setItemDelegate(delegate)
            combo.setMaxVisibleItems(12)

    # ── 一键执行 ──

    def _run_all(self):
        input_dir = self.prepare_tab.input_edit.text().strip()
        if not input_dir:
            QMessageBox.warning(self, "提示", "请先在「准备」页选择输入目录")
            self.tabs.setCurrentIndex(0)
            return

        self.tabs.setCurrentIndex(0)
        self.run_all_btn.setEnabled(False)
        self.statusBar().showMessage("阶段 1/3 · 准备中...")
        self.prepare_tab._run()

        if self.prepare_tab.worker:
            try:
                self.prepare_tab.worker.finished.disconnect(self._on_prepare_done_chain)
            except RuntimeError:
                pass
            try:
                self.prepare_tab.worker.error.disconnect(self._on_chain_error)
            except RuntimeError:
                pass
            self.prepare_tab.worker.finished.connect(self._on_prepare_done_chain)
            self.prepare_tab.worker.error.connect(self._on_chain_error)

    def _on_prepare_done_chain(self, result):
        self.tabs.setCurrentIndex(1)
        self.statusBar().showMessage("阶段 2/3 · 压缩中...")
        prepare_output = self.prepare_tab.get_output_dir() or result.output_dir
        self.compress_tab.set_input_dir(prepare_output)
        QTimer.singleShot(500, self._chain_compress)

    def _chain_compress(self):
        self.compress_tab._run()
        if self.compress_tab.worker:
            try:
                self.compress_tab.worker.finished.disconnect(self._on_compress_done_chain)
            except RuntimeError:
                pass
            try:
                self.compress_tab.worker.error.disconnect(self._on_chain_error)
            except RuntimeError:
                pass
            self.compress_tab.worker.finished.connect(self._on_compress_done_chain)
            self.compress_tab.worker.error.connect(self._on_chain_error)

    def _on_compress_done_chain(self, stats):
        self.tabs.setCurrentIndex(2)
        self.statusBar().showMessage("阶段 3/3 · 上传中...")
        compress_output = self.compress_tab.get_output_dir() or stats.output_dir
        self.upload_tab.set_input_dir(compress_output)
        QTimer.singleShot(500, self._chain_upload)

    def _chain_upload(self):
        self.upload_tab._run()
        if self.upload_tab.worker:
            try:
                self.upload_tab.worker.finished.disconnect(self._on_all_done)
            except RuntimeError:
                pass
            try:
                self.upload_tab.worker.error.disconnect(self._on_chain_error)
            except RuntimeError:
                pass
            self.upload_tab.worker.finished.connect(self._on_all_done)
            self.upload_tab.worker.error.connect(self._on_chain_error)

    def _on_all_done(self, result):
        self.run_all_btn.setEnabled(True)
        self.statusBar().showMessage("全部完成!")

    def _on_chain_error(self, msg):
        self.run_all_btn.setEnabled(True)
        self.statusBar().showMessage("执行中断")
        QMessageBox.critical(self, "执行中断", msg)

    # ── 拖拽 ──

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            import os
            if os.path.isdir(path):
                current_scroll = self.tabs.currentWidget()
                inner = current_scroll.widget() if isinstance(current_scroll, QScrollArea) else current_scroll
                if hasattr(inner, "input_edit"):
                    inner.input_edit.setText(path)
                else:
                    self.prepare_tab.input_edit.setText(path)
                    self.tabs.setCurrentIndex(0)

    def _setup_tray(self):
        """设置系统托盘图标"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Image Compression v2.0")
        # 使用应用默认图标（避免 'No Icon set' 警告）
        app_icon = self.windowIcon()
        if not app_icon.isNull():
            self.tray.setIcon(app_icon)
        else:
            from PySide6.QtWidgets import QApplication
            self.tray.setIcon(QApplication.style().standardIcon(
                QApplication.style().StandardPixmap.SP_ComputerIcon
            ))

        # 托盘菜单
        tray_menu = QMenu()
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self._show_from_tray)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self.tray.setContextMenu(tray_menu)

        # 双击托盘图标显示
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()
        self._really_quit = False

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _quit_app(self):
        self._really_quit = True
        self.config.save()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()

    def closeEvent(self, event):
        input_dir = self.prepare_tab.input_edit.text().strip()
        if input_dir:
            self.config.last_input_dir = input_dir
        self.config.save()

        # 最小化到托盘
        if hasattr(self, 'tray') and self.tray.isVisible() and not getattr(self, '_really_quit', False):
            self.hide()
            self.tray.showMessage(
                "Image Compression",
                "程序已最小化到系统托盘",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
            event.ignore()
        else:
            super().closeEvent(event)
