"""
URL 输出组件 — 显示上传后的 URL 列表，支持一键复制
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt, QTimer


class UrlOutputWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        header = QHBoxLayout()
        title = QLabel("URL 输出")
        title.setStyleSheet("font-weight: 600; font-size: 12px;")
        self.count_label = QLabel("")
        self.count_label.setObjectName("secondaryLabel")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(title)
        header.addWidget(self.count_label)
        layout.addLayout(header)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("上传完成后 URL 将显示在这里...")
        self.text_edit.setMaximumHeight(100)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.copy_btn = QPushButton("全部复制")
        self.copy_btn.setFixedWidth(80)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_all)
        self.copy_btn.setEnabled(False)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedWidth(60)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.clear_btn)
        layout.addLayout(btn_row)

    def set_urls(self, urls: list[str]):
        self.text_edit.setPlainText("\n".join(urls))
        self.count_label.setText(f"{len(urls)} 条")
        self.copy_btn.setEnabled(bool(urls))

    def add_url(self, url: str):
        self.text_edit.append(url)
        count = len(self.text_edit.toPlainText().strip().split("\n"))
        self.count_label.setText(f"{count} 条")
        self.copy_btn.setEnabled(True)

    def clear(self):
        self.text_edit.clear()
        self.count_label.setText("")
        self.copy_btn.setEnabled(False)

    def _copy_all(self):
        text = self.text_edit.toPlainText().strip()
        if text:
            QGuiApplication.clipboard().setText(text)
            self.copy_btn.setText("已复制!")
            QTimer.singleShot(2000, lambda: self.copy_btn.setText("全部复制"))
