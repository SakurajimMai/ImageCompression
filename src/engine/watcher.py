"""
文件夹监控模块 — 自动压缩新增文件
"""
import time
import threading
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from engine.formats.base import CompressParams
from engine.formats.registry import get_handler
from engine.scanner import IMAGE_EXTENSIONS


class CompressionHandler(FileSystemEventHandler):
    """监控文件创建事件并自动压缩"""

    def __init__(
        self,
        output_dir: Path,
        format_name: str = "avif",
        params: Optional[CompressParams] = None,
        on_compressed: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        debounce_seconds: float = 1.0,
    ):
        super().__init__()
        self._output_dir = output_dir
        self._handler = get_handler(format_name)
        self._params = params or CompressParams()
        self._on_compressed = on_compressed
        self._on_error = on_error
        self._debounce = debounce_seconds
        self._pending: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            return

        # 防抖：等待文件写入完成
        with self._lock:
            key = str(path)
            if key in self._pending:
                self._pending[key].cancel()

            timer = threading.Timer(
                self._debounce,
                self._process_file,
                args=[path],
            )
            self._pending[key] = timer
            timer.start()

    def _process_file(self, path: Path):
        """压缩单个文件"""
        with self._lock:
            self._pending.pop(str(path), None)

        if not path.exists():
            return

        target_ext = self._handler.default_extension()
        output_path = self._output_dir / (path.stem + target_ext)

        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            result = self._handler.compress(path, output_path, self._params)

            if self._on_compressed:
                self._on_compressed(result)

        except Exception as e:
            if self._on_error:
                self._on_error(str(path), str(e))


class FolderWatcher:
    """文件夹监控器"""

    def __init__(
        self,
        watch_dir: str | Path,
        output_dir: str | Path,
        format_name: str = "avif",
        params: Optional[CompressParams] = None,
        recursive: bool = False,
        on_compressed: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        self._watch_dir = Path(watch_dir)
        self._output_dir = Path(output_dir)
        self._recursive = recursive
        self._observer = Observer()
        self._handler = CompressionHandler(
            output_dir=self._output_dir,
            format_name=format_name,
            params=params,
            on_compressed=on_compressed,
            on_error=on_error,
        )
        self._running = False

    def start(self):
        """开始监控"""
        if self._running:
            return
        self._observer.schedule(
            self._handler,
            str(self._watch_dir),
            recursive=self._recursive,
        )
        self._observer.start()
        self._running = True

    def stop(self):
        """停止监控"""
        if not self._running:
            return
        self._observer.stop()
        self._observer.join(timeout=5)
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
