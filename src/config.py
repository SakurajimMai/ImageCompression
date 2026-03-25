"""
配置管理模块 — 读写 JSON 配置文件，支持参数持久化
"""
import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict


CONFIG_DIR = Path.home() / ".imagecompression"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AvifConfig:
    min_quality: int = 20
    max_quality: int = 40
    speed: int = 6
    threads: str = "all"


@dataclass
class WebpJpegConfig:
    quality: int = 80


@dataclass
class S3Config:
    endpoint: str = ""
    bucket: str = ""
    access_key: str = ""
    secret_key: str = ""
    region: str = ""
    prefix: str = ""


@dataclass
class FTPConfig:
    host: str = ""
    port: int = 21
    username: str = ""
    password: str = ""
    remote_dir: str = "/"


@dataclass
class SFTPConfig:
    host: str = ""
    port: int = 22
    username: str = ""
    password: str = ""
    key_path: str = ""
    remote_dir: str = "/"


@dataclass
class ProxyConfig:
    enabled: bool = False
    url: str = "socks5://127.0.0.1:7890"


@dataclass
class CompressConfig:
    format: str = "avif"  # avif / webp / jpeg
    avif: AvifConfig = field(default_factory=AvifConfig)
    webp_jpeg: WebpJpegConfig = field(default_factory=WebpJpegConfig)
    skip_videos: bool = True


@dataclass
class UploadConfig:
    protocol: str = "s3"  # s3 / ftp / sftp
    s3: S3Config = field(default_factory=S3Config)
    ftp: FTPConfig = field(default_factory=FTPConfig)
    sftp: SFTPConfig = field(default_factory=SFTPConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)


@dataclass
class PrepareConfig:
    rename_images: bool = True
    rename_videos: bool = True
    strip_exif: bool = True
    output_mode: str = "new_directory"  # new_directory / overwrite


@dataclass
class Config:
    last_input_dir: str = ""
    last_output_dir: str = ""
    prepare: PrepareConfig = field(default_factory=PrepareConfig)
    compress: CompressConfig = field(default_factory=CompressConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)
    avifenc_path: str = "avifenc"  # 默认使用 PATH 中的 avifenc
    language: str = "zh"   # zh / en
    theme: str = "light"   # light / dark

    def save(self):
        """保存配置到 JSON 文件"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = self._to_dict()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        """从 JSON 文件加载配置"""
        if not CONFIG_FILE.exists():
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._from_dict(data)
        except (json.JSONDecodeError, KeyError):
            pass  # 配置文件损坏时使用默认值

    def _to_dict(self) -> dict:
        return asdict(self)

    def _from_dict(self, data: dict):
        """从字典递归更新配置"""
        for key, value in data.items():
            if not hasattr(self, key):
                continue
            attr = getattr(self, key)
            if hasattr(attr, "__dataclass_fields__") and isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if hasattr(attr, sub_key):
                        sub_attr = getattr(attr, sub_key)
                        if hasattr(sub_attr, "__dataclass_fields__") and isinstance(sub_value, dict):
                            for k, v in sub_value.items():
                                if hasattr(sub_attr, k):
                                    setattr(sub_attr, k, v)
                        else:
                            setattr(attr, sub_key, sub_value)
            else:
                setattr(self, key, value)
