"""
进度条组件
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout
from PySide6.QtCore import Qt


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(14)
        layout.addWidget(self.progress_bar)

        info = QHBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("secondaryLabel")
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("secondaryLabel")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        info.addWidget(self.status_label)
        info.addWidget(self.stats_label)
        layout.addLayout(info)

    def update_progress(self, current: int, total: int, message: str = ""):
        self.setVisible(True)
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            percent = int(current / total * 100)
            self.progress_bar.setFormat(f"{current}/{total}  ({percent}%)")
        self.status_label.setText(message)

    def set_stats(self, text: str):
        self.stats_label.setText(text)

    def reset(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")
        self.status_label.setText("就绪")
        self.status_label.setObjectName("secondaryLabel")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.stats_label.setText("")
        self.setVisible(False)

    def set_complete(self, message: str = "完成"):
        self.setVisible(True)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText(message)
        self.status_label.setObjectName("successLabel")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def set_speed(self, files_per_sec: float):
        """显示实时处理速度"""
        if files_per_sec > 0:
            current_stats = self.stats_label.text()
            speed_text = f"速度: {files_per_sec:.1f} 张/秒"
            self.stats_label.setText(speed_text)
