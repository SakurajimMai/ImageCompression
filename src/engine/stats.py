"""
批量统计数据模型
"""
from dataclasses import dataclass, field
from engine.formats.base import CompressResult


@dataclass
class BatchStats:
    """批量压缩统计"""
    total_files: int = 0
    compressed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    original_size: int = 0
    compressed_size: int = 0
    total_elapsed: float = 0.0
    output_dir: str = ""

    # 每张图的详细结果
    results: list[CompressResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def saved_ratio(self) -> float:
        if self.original_size == 0:
            return 0
        return 1 - (self.compressed_size / self.original_size)

    @property
    def saved_percent(self) -> float:
        return self.saved_ratio * 100

    @property
    def original_size_mb(self) -> float:
        return self.original_size / (1024 * 1024)

    @property
    def compressed_size_mb(self) -> float:
        return self.compressed_size / (1024 * 1024)

    @property
    def speed_files_per_sec(self) -> float:
        if self.total_elapsed <= 0:
            return 0
        return self.compressed_files / self.total_elapsed

    def add_result(self, result: CompressResult):
        """添加单个压缩结果"""
        self.results.append(result)
        self.total_files += 1
        self.original_size += result.original_size

        if result.success:
            self.compressed_files += 1
            self.compressed_size += result.compressed_size
        else:
            self.failed_files += 1
            if result.error:
                self.errors.append(f"{result.input_path}: {result.error}")

        self.total_elapsed += result.elapsed_seconds
