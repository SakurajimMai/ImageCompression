"""
性能监控组件 — CPU / 内存 / ETA 实时显示
"""
import time
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import QTimer


class PerfMonitor(QWidget):
    """性能仪表盘 — 显示 CPU / 内存 / 速度 / ETA"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._start_time = 0.0
        self._total = 0
        self._current = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(16)

        self.cpu_label = QLabel("CPU: —")
        self.cpu_label.setObjectName("secondaryLabel")
        self.mem_label = QLabel("内存: —")
        self.mem_label.setObjectName("secondaryLabel")
        self.speed_label = QLabel("速度: —")
        self.speed_label.setObjectName("secondaryLabel")
        self.eta_label = QLabel("剩余: —")
        self.eta_label.setObjectName("secondaryLabel")

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.mem_label)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.eta_label)
        layout.addStretch()

        self.setVisible(False)

    def start(self, total: int):
        """开始监控"""
        self._total = total
        self._current = 0
        self._start_time = time.time()
        self.setVisible(True)
        self._timer.start(1000)
        self._update()

    def update_progress(self, current: int, speed: float = 0):
        """更新进度"""
        self._current = current
        elapsed = time.time() - self._start_time

        # 速度
        if speed > 0:
            self.speed_label.setText(f"速度: {speed:.1f} 张/秒")
        elif elapsed > 0:
            spd = current / elapsed
            self.speed_label.setText(f"速度: {spd:.1f} 张/秒")

        # ETA
        if current > 0 and self._total > 0:
            remaining = self._total - current
            rate = current / elapsed if elapsed > 0 else 0
            if rate > 0:
                eta_seconds = remaining / rate
                self.eta_label.setText(f"剩余: {self._format_eta(eta_seconds)}")
            else:
                self.eta_label.setText("剩余: 计算中...")
        else:
            self.eta_label.setText("剩余: 计算中...")

    def stop(self):
        """停止监控"""
        self._timer.stop()
        elapsed = time.time() - self._start_time
        self.speed_label.setText(f"总耗时: {self._format_eta(elapsed)}")
        self.eta_label.setText("已完成")

    def reset(self):
        """重置"""
        self._timer.stop()
        self.setVisible(False)

    def _update(self):
        """定时刷新 CPU / 内存"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            mem_used_gb = mem.used / (1024 ** 3)
            self.cpu_label.setText(f"CPU: {cpu:.0f}%")
            self.mem_label.setText(f"内存: {mem_used_gb:.1f} GB ({mem.percent:.0f}%)")
        except ImportError:
            self.cpu_label.setText("CPU: N/A")
            self.mem_label.setText("内存: N/A")

    @staticmethod
    def _format_eta(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            m, s = divmod(int(seconds), 60)
            return f"{m}m {s}s"
        else:
            h, remainder = divmod(int(seconds), 3600)
            m, s = divmod(remainder, 60)
            return f"{h}h {m}m"
