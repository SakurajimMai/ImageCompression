"""
上传模块 — 支持 S3 / FTP / SFTP 多协议上传
"""
import os
import ftplib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass

from core.prepare import IMAGE_EXTENSIONS


@dataclass
class UploadResult:
    """上传结果"""
    total_files: int
    uploaded_files: int
    failed_files: int
    urls: list[str]
    errors: list[str]


class BaseUploader(ABC):
    """上传器基类"""

    @abstractmethod
    def connect(self):
        """建立连接"""
        ...

    @abstractmethod
    def upload_file(self, local_path: Path, remote_name: str) -> str:
        """上传单个文件，返回访问 URL"""
        ...

    @abstractmethod
    def disconnect(self):
        """断开连接"""
        ...


class S3Uploader(BaseUploader):
    """S3 兼容存储上传器"""

    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str = "",
        prefix: str = "",
        proxy_url: Optional[str] = None,
        custom_domain: str = "",
    ):
        self.endpoint = endpoint.rstrip("/")
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region or "us-east-1"
        self.prefix = prefix.strip("/")
        self.proxy_url = proxy_url
        self.custom_domain = custom_domain.rstrip("/") if custom_domain else ""
        self.client = None

    def connect(self):
        import boto3
        from botocore.config import Config as BotoConfig

        config_kwargs = {}
        if self.proxy_url:
            config_kwargs["proxies"] = {"https": self.proxy_url, "http": self.proxy_url}

        boto_config = BotoConfig(**config_kwargs) if config_kwargs else None

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=boto_config,
        )

    def upload_file(self, local_path: Path, remote_name: str) -> str:
        if not self.client:
            raise RuntimeError("未连接到 S3")

        key = f"{self.prefix}/{remote_name}" if self.prefix else remote_name
        # 去除开头的 /
        key = key.lstrip("/")

        content_type = self._guess_content_type(local_path)
        self.client.upload_file(
            str(local_path),
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

        # 构造访问 URL
        if self.custom_domain:
            url = f"{self.custom_domain}/{key}"
        else:
            url = f"{self.endpoint}/{self.bucket}/{key}"
        return url

    def disconnect(self):
        self.client = None

    @staticmethod
    def _guess_content_type(path: Path) -> str:
        ext = path.suffix.lower()
        type_map = {
            ".avif": "image/avif",
            ".webp": "image/webp",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
        }
        return type_map.get(ext, "application/octet-stream")


class FTPUploader(BaseUploader):
    """FTP 上传器"""

    def __init__(
        self,
        host: str,
        port: int = 21,
        username: str = "",
        password: str = "",
        remote_dir: str = "/",
        base_url: str = "",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_dir = remote_dir.rstrip("/")
        self.base_url = base_url.rstrip("/")
        self.ftp: Optional[ftplib.FTP] = None

    def connect(self):
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.host, self.port)
        if self.username:
            self.ftp.login(self.username, self.password)
        # 尝试切换到远程目录
        try:
            self.ftp.cwd(self.remote_dir)
        except ftplib.error_perm:
            self.ftp.mkd(self.remote_dir)
            self.ftp.cwd(self.remote_dir)

    def upload_file(self, local_path: Path, remote_name: str) -> str:
        if not self.ftp:
            raise RuntimeError("未连接到 FTP")

        with open(local_path, "rb") as f:
            self.ftp.storbinary(f"STOR {remote_name}", f)

        if self.base_url:
            return f"{self.base_url}/{self.remote_dir.strip('/')}/{remote_name}"
        return f"ftp://{self.host}/{self.remote_dir.strip('/')}/{remote_name}"

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                self.ftp.close()
            self.ftp = None


class SFTPUploader(BaseUploader):
    """SFTP 上传器"""

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: str = "",
        key_path: str = "",
        remote_dir: str = "/",
        base_url: str = "",
        domain_root: str = "",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self.remote_dir = remote_dir.rstrip("/")
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.domain_root = domain_root.rstrip("/") if domain_root else ""
        self.transport = None
        self.sftp = None

    def connect(self):
        import paramiko

        self.transport = paramiko.Transport((self.host, self.port))

        if self.key_path and os.path.exists(self.key_path):
            key = paramiko.RSAKey.from_private_key_file(self.key_path)
            self.transport.connect(username=self.username, pkey=key)
        else:
            self.transport.connect(username=self.username, password=self.password)

        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

        # 递归创建远程目录
        self._mkdir_p(self.remote_dir)

    def _mkdir_p(self, remote_dir: str):
        """递归创建远程目录（类似 mkdir -p）"""
        if not remote_dir or remote_dir == "/":
            return
        # 从根目录逐级创建
        parts = remote_dir.split("/")
        current = ""
        for part in parts:
            if not part:
                continue
            current += f"/{part}"
            try:
                self.sftp.stat(current)
            except FileNotFoundError:
                self.sftp.mkdir(current)

    def upload_file(self, local_path: Path, remote_name: str) -> str:
        if not self.sftp:
            raise RuntimeError("未连接到 SFTP")

        remote_path = f"{self.remote_dir}/{remote_name}"

        # 如果 remote_name 包含子目录（如 subdir/file.avif），自动创建
        if "/" in remote_name:
            parent_dir = f"{self.remote_dir}/{'/'.join(remote_name.split('/')[:-1])}"
            self._mkdir_p(parent_dir)

        self.sftp.put(str(local_path), remote_path)

        # 生成 URL：base_url + (remote_dir 相对于 domain_root 的路径) + filename
        if self.base_url:
            if self.domain_root and self.remote_dir.startswith(self.domain_root):
                rel_path = self.remote_dir[len(self.domain_root):]
            else:
                rel_path = self.remote_dir
            return f"{self.base_url}{rel_path}/{remote_name}"
        return remote_path

    def disconnect(self):
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.transport:
            self.transport.close()
            self.transport = None


def upload_directory(
    uploader: BaseUploader,
    input_dir: str | Path,
    recursive: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> UploadResult:
    """
    批量上传目录中的文件

    Args:
        uploader: 上传器实例
        input_dir: 输入目录
        recursive: 是否递归上传子目录
        progress_callback: 进度回调 (current, total, message)
    """
    input_path = Path(input_dir)

    if recursive:
        files = sorted([f for f in input_path.rglob("*") if f.is_file()])
    else:
        files = sorted([f for f in input_path.iterdir() if f.is_file()])

    total = len(files)
    urls = []
    errors = []
    uploaded = 0

    uploader.connect()

    try:
        for i, file_path in enumerate(files):
            # 计算相对路径（保留子目录结构）
            if recursive:
                remote_name = file_path.relative_to(input_path).as_posix()
            else:
                remote_name = file_path.name

            if progress_callback:
                progress_callback(i + 1, total, f"上传: {remote_name}")

            try:
                url = uploader.upload_file(file_path, remote_name)
                urls.append(url)
                uploaded += 1
            except Exception as e:
                errors.append(f"{remote_name}: {str(e)}")
    finally:
        uploader.disconnect()

    return UploadResult(
        total_files=total,
        uploaded_files=uploaded,
        failed_files=len(errors),
        urls=urls,
        errors=errors,
    )
