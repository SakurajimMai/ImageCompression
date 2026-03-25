"""
设置页 Tab — avifenc 配置 + 语言/主题切换
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QMessageBox, QFileDialog, QComboBox,
)
from PySide6.QtCore import Qt

from config import Config, CONFIG_FILE
from core.compress import check_avifenc
from ui.widgets.card_group import create_card_group


class SettingsTab(QWidget):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self._load_from_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(2, 2, 2, 2)

        # ── 界面设置 ──
        ug = QVBoxLayout()
        ug.setSpacing(4)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(6)
        lang_row.addWidget(QLabel("界面语言:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("中文", "zh")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.setFixedWidth(120)
        lang_row.addWidget(self.lang_combo)

        lang_row.addWidget(QLabel("界面主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("浅色", "light")
        self.theme_combo.addItem("深色", "dark")
        self.theme_combo.addItem("灰色", "gray")
        self.theme_combo.setFixedWidth(120)
        lang_row.addWidget(self.theme_combo)
        lang_row.addStretch()
        ug.addLayout(lang_row)

        apply_btn = QPushButton("立即应用")
        apply_btn.setObjectName("actionBtn")
        apply_btn.setFixedWidth(120)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_ui_settings)
        ug.addWidget(apply_btn)

        self.restart_hint = QLabel("")
        self.restart_hint.setObjectName("secondaryLabel")
        ug.addWidget(self.restart_hint)

        layout.addLayout(create_card_group("界面设置", ug))

        # ── avifenc ──
        ag = QVBoxLayout()
        ag.setSpacing(4)

        path_row = QHBoxLayout()
        path_row.setSpacing(4)
        path_row.addWidget(QLabel("路径:"))
        self.avifenc_edit = QLineEdit()
        self.avifenc_edit.setPlaceholderText("avifenc（默认使用系统 PATH）")
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(70)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_avifenc)
        path_row.addWidget(self.avifenc_edit, 1)
        path_row.addWidget(browse_btn)
        ag.addLayout(path_row)

        detect_row = QHBoxLayout()
        detect_row.setSpacing(4)
        self.avif_status = QLabel("")
        self.avif_status.setObjectName("secondaryLabel")
        detect_btn = QPushButton("检测")
        detect_btn.setFixedWidth(70)
        detect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        detect_btn.clicked.connect(self._check_avifenc)
        detect_row.addWidget(self.avif_status, 1)
        detect_row.addWidget(detect_btn)
        ag.addLayout(detect_row)
        layout.addLayout(create_card_group("AVIF 编码器", ag))

        # ── 配置管理 ──
        cg = QVBoxLayout()
        cg.setSpacing(4)

        path_info = QLabel(f"配置文件路径: {CONFIG_FILE}")
        path_info.setObjectName("secondaryLabel")
        cg.addWidget(path_info)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        save_btn = QPushButton("保存配置")
        save_btn.setObjectName("actionBtn")
        save_btn.setFixedWidth(100)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_config)
        reset_btn = QPushButton("恢复默认")
        reset_btn.setFixedWidth(100)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_config)
        export_btn = QPushButton("📤 导出配置")
        export_btn.setFixedWidth(110)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_config)
        import_btn = QPushButton("📥 导入配置")
        import_btn.setFixedWidth(110)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self._import_config)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(export_btn)
        btn_row.addWidget(import_btn)
        btn_row.addStretch()
        cg.addLayout(btn_row)
        layout.addLayout(create_card_group("配置管理", cg))

        # ── 关于 ──
        ab = QVBoxLayout()
        ab.setSpacing(4)
        name_label = QLabel("Image Compression  v2.0.0")
        name_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        desc_label = QLabel(
            "批量图片处理、压缩与上传工具\n"
            "支持: CLI + GUI 双模式 | AVIF/WebP/JPEG | 递归/并行/预览"
        )
        desc_label.setObjectName("secondaryLabel")
        ab.addWidget(name_label)
        ab.addWidget(desc_label)
        layout.addLayout(create_card_group("关于", ab))

        layout.addStretch()

    def _browse_avifenc(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 avifenc",
            filter="可执行文件 (*.exe);;所有文件 (*)",
        )
        if path:
            self.avifenc_edit.setText(path)

    def _check_avifenc(self):
        path = self.avifenc_edit.text().strip() or "avifenc"
        available, version = check_avifenc(path)
        if available:
            self.avif_status.setText(f"已检测: {version}")
            self.avif_status.setObjectName("successLabel")
        else:
            self.avif_status.setText("未找到 — 请先安装 libavif")
            self.avif_status.setObjectName("errorLabel")
        self.avif_status.style().unpolish(self.avif_status)
        self.avif_status.style().polish(self.avif_status)

    def _apply_ui_settings(self):
        lang = self.lang_combo.currentData()
        theme = self.theme_combo.currentData()
        old_lang = self.config.language
        self.config.language = lang
        self.config.theme = theme
        self.config.save()

        # 热加载主题（无需重启）
        from ui.theme import get_stylesheet
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            qss = get_stylesheet(theme)
            # 必须在 MainWindow 级别设置（与初始化一致），
            # 否则控件级样式表优先级高于 app 级别，切换不生效
            main_window = None
            for w in app.topLevelWidgets():
                if w.__class__.__name__ == "MainWindow":
                    main_window = w
                    break
            if main_window:
                main_window.setStyleSheet(qss)
            else:
                app.setStyleSheet(qss)
            # 强制所有子组件刷新样式
            for widget in app.allWidgets():
                try:
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                    widget.update()
                except TypeError:
                    pass  # 某些内部控件 (QListView) 的 update() 签名不兼容

        # 语言变更需要重启进程
        if lang != old_lang:
            reply = QMessageBox.question(
                self, "重启应用",
                "语言变更需要重启应用才能生效。\n是否立即重启？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._restart_app()
                return

        self.restart_hint.setText("✓ 主题已实时切换")
        self.restart_hint.setObjectName("successLabel")
        self.restart_hint.style().unpolish(self.restart_hint)
        self.restart_hint.style().polish(self.restart_hint)

    def _restart_app(self):
        """重启应用进程（Windows 兼容）"""
        import sys
        import subprocess
        from PySide6.QtWidgets import QApplication
        # 先启动一个全新的进程
        subprocess.Popen([sys.executable] + sys.argv)
        # 再退出当前进程
        app = QApplication.instance()
        if app:
            app.quit()
        sys.exit(0)

    def _save_config(self):
        self._apply_to_config()
        self.config.save()
        QMessageBox.information(self, "保存成功", "配置已保存")

    def _reset_config(self):
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要恢复所有配置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            new_config = Config()
            self.config.__dict__.update(new_config.__dict__)
            self._load_from_config()
            QMessageBox.information(self, "重置成功", "配置已恢复默认值")

    def _apply_to_config(self):
        self.config.avifenc_path = self.avifenc_edit.text().strip() or "avifenc"
        self.config.language = self.lang_combo.currentData()
        self.config.theme = self.theme_combo.currentData()

    def _export_config(self):
        """导出配置到 JSON 文件"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "image_compression_config.json",
            "JSON 文件 (*.json);;所有文件 (*)",
        )
        if not path:
            return
        try:
            self._apply_to_config()
            self.config.save()
            # 复制配置文件到目标位置
            import shutil
            shutil.copy2(str(CONFIG_FILE), path)
            QMessageBox.information(self, "导出成功", f"配置已导出到：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _import_config(self):
        """从 JSON 文件导入配置"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "",
            "JSON 文件 (*.json);;所有文件 (*)",
        )
        if not path:
            return
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 写入到配置文件
            import shutil
            shutil.copy2(path, str(CONFIG_FILE))
            self.config.load()
            self._load_from_config()
            QMessageBox.information(self, "导入成功",
                "配置已导入，部分设置需重启生效。")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"文件格式错误：{e}")

    def _load_from_config(self):
        self.avifenc_edit.setText(
            self.config.avifenc_path if self.config.avifenc_path != "avifenc" else ""
        )
        # 语言
        lang_index = 0 if self.config.language == "zh" else 1
        self.lang_combo.setCurrentIndex(lang_index)
        # 主题
        theme_map = {"light": 0, "dark": 1, "gray": 2}
        self.theme_combo.setCurrentIndex(theme_map.get(self.config.theme, 0))

        self._check_avifenc()
