"""
上传页 Tab — S3 / FTP / SFTP 上传，支持 HTTP / SOCKS5 代理
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QGroupBox, QComboBox,
    QCheckBox, QStackedWidget, QSpinBox, QMessageBox,
)
from PySide6.QtCore import QThread, Signal, Qt

from core.upload import (
    S3Uploader, FTPUploader, SFTPUploader,
    upload_directory, UploadResult,
)
from ui.widgets.card_group import create_card_group


class UploadWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, uploader, input_dir, recursive=False):
        super().__init__()
        self.uploader = uploader
        self.input_dir = input_dir
        self.recursive = recursive

    def run(self):
        try:
            result = upload_directory(
                self.uploader,
                self.input_dir,
                recursive=self.recursive,
                progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class UploadTab(QWidget):
    def __init__(self, config, progress_widget, url_output_widget, parent=None):
        super().__init__(parent)
        self.config = config
        self.progress_widget = progress_widget
        self.url_output = url_output_widget
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(2, 2, 2, 2)

        # ── 上传目录 ──
        ig = QHBoxLayout()
        ig.setSpacing(4)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("选择要上传的目录...")
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(70)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_input)
        ig.addWidget(self.input_edit, 1)
        ig.addWidget(browse_btn)
        self.chk_recursive_upload = QCheckBox("递归子目录")
        self.chk_recursive_upload.setToolTip("上传时保留子目录结构")
        ig.addWidget(self.chk_recursive_upload)
        layout.addLayout(create_card_group("上传目录", ig))

        # ── 连接配置 ──
        conn_group = QGroupBox("连接配置")
        cg = QVBoxLayout()
        cg.setSpacing(4)

        proto_row = QHBoxLayout()
        proto_row.addWidget(QLabel("协议:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["S3", "FTP", "SFTP"])
        self.protocol_combo.setFixedWidth(120)
        self.protocol_combo.currentIndexChanged.connect(self._on_protocol_changed)
        proto_row.addWidget(self.protocol_combo)
        proto_row.addStretch()
        cg.addLayout(proto_row)

        self.config_stack = QStackedWidget()

        # S3
        s3_w = QWidget()
        s3_l = QVBoxLayout(s3_w)
        s3_l.setContentsMargins(0, 0, 0, 0)
        s3_l.setSpacing(3)
        self.s3_endpoint = QLineEdit()
        self.s3_endpoint.setPlaceholderText("Endpoint (如 https://s3.amazonaws.com)")
        self.s3_bucket = QLineEdit()
        self.s3_bucket.setPlaceholderText("Bucket 名称")
        s3_keys = QHBoxLayout()
        s3_keys.setSpacing(4)
        self.s3_access_key = QLineEdit()
        self.s3_access_key.setPlaceholderText("Access Key")
        self.s3_secret_key = QLineEdit()
        self.s3_secret_key.setPlaceholderText("Secret Key")
        self.s3_secret_key.setEchoMode(QLineEdit.EchoMode.Password)
        s3_keys.addWidget(self.s3_access_key, 1)
        s3_keys.addWidget(self.s3_secret_key, 1)
        self.s3_prefix = QLineEdit()
        self.s3_prefix.setPlaceholderText("远程路径前缀 (如 /2026/03/)")
        self.s3_domain = QLineEdit()
        self.s3_domain.setPlaceholderText("自定义域名 (如 https://cdn.example.com)〔可选〕")
        s3_l.addWidget(self.s3_endpoint)
        s3_l.addWidget(self.s3_bucket)
        s3_l.addLayout(s3_keys)
        s3_l.addWidget(self.s3_prefix)
        s3_l.addWidget(self.s3_domain)
        self.config_stack.addWidget(s3_w)

        # FTP
        ftp_w = QWidget()
        ftp_l = QVBoxLayout(ftp_w)
        ftp_l.setContentsMargins(0, 0, 0, 0)
        ftp_l.setSpacing(3)
        ftp_host_row = QHBoxLayout()
        ftp_host_row.setSpacing(4)
        self.ftp_host = QLineEdit()
        self.ftp_host.setPlaceholderText("主机地址")
        self.ftp_port = QSpinBox()
        self.ftp_port.setRange(1, 65535)
        self.ftp_port.setValue(21)
        ftp_host_row.addWidget(self.ftp_host, 3)
        ftp_host_row.addWidget(QLabel(":"))
        ftp_host_row.addWidget(self.ftp_port, 1)
        ftp_l.addLayout(ftp_host_row)
        ftp_cred = QHBoxLayout()
        ftp_cred.setSpacing(4)
        self.ftp_user = QLineEdit()
        self.ftp_user.setPlaceholderText("用户名")
        self.ftp_pass = QLineEdit()
        self.ftp_pass.setPlaceholderText("密码")
        self.ftp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        ftp_cred.addWidget(self.ftp_user, 1)
        ftp_cred.addWidget(self.ftp_pass, 1)
        ftp_l.addLayout(ftp_cred)
        self.ftp_dir = QLineEdit()
        self.ftp_dir.setPlaceholderText("远程目录 (如 /uploads/)")
        self.ftp_base_url = QLineEdit()
        self.ftp_base_url.setPlaceholderText("访问基址 (如 https://cdn.example.com)")
        ftp_l.addWidget(self.ftp_dir)
        ftp_l.addWidget(self.ftp_base_url)
        self.config_stack.addWidget(ftp_w)

        # SFTP
        sftp_w = QWidget()
        sftp_l = QVBoxLayout(sftp_w)
        sftp_l.setContentsMargins(0, 0, 0, 0)
        sftp_l.setSpacing(3)
        sftp_host_row = QHBoxLayout()
        sftp_host_row.setSpacing(4)
        self.sftp_host = QLineEdit()
        self.sftp_host.setPlaceholderText("主机地址")
        self.sftp_port = QSpinBox()
        self.sftp_port.setRange(1, 65535)
        self.sftp_port.setValue(22)
        sftp_host_row.addWidget(self.sftp_host, 3)
        sftp_host_row.addWidget(QLabel(":"))
        sftp_host_row.addWidget(self.sftp_port, 1)
        sftp_l.addLayout(sftp_host_row)
        sftp_cred = QHBoxLayout()
        sftp_cred.setSpacing(4)
        self.sftp_user = QLineEdit()
        self.sftp_user.setPlaceholderText("用户名")
        self.sftp_pass = QLineEdit()
        self.sftp_pass.setPlaceholderText("密码")
        self.sftp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        sftp_cred.addWidget(self.sftp_user, 1)
        sftp_cred.addWidget(self.sftp_pass, 1)
        sftp_l.addLayout(sftp_cred)
        self.sftp_key = QLineEdit()
        self.sftp_key.setPlaceholderText("私钥文件路径（可选）")
        self.sftp_dir = QLineEdit()
        self.sftp_dir.setPlaceholderText("远程目录 (如 /var/www/uploads/xxxx)")
        self.sftp_base_url = QLineEdit()
        self.sftp_base_url.setPlaceholderText("访问域名 (如 https://cdn.example.com)")
        self.sftp_domain_root = QLineEdit()
        self.sftp_domain_root.setPlaceholderText("域名根目录 (如 /var/www)")
        sftp_l.addWidget(self.sftp_key)
        sftp_l.addWidget(self.sftp_dir)
        sftp_l.addWidget(self.sftp_base_url)
        sftp_l.addWidget(self.sftp_domain_root)
        self.config_stack.addWidget(sftp_w)

        cg.addWidget(self.config_stack)
        layout.addLayout(create_card_group("连接配置", cg))

        # ── 代理配置 ──
        pg = QVBoxLayout()
        pg.setSpacing(4)

        proxy_top = QHBoxLayout()
        proxy_top.setSpacing(6)
        self.chk_proxy = QCheckBox("启用代理")
        self.chk_proxy.toggled.connect(self._on_proxy_toggled)
        proxy_top.addWidget(self.chk_proxy)
        proxy_top.addWidget(QLabel("类型:"))
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["HTTP", "SOCKS5"])
        self.proxy_type_combo.setFixedWidth(100)
        self.proxy_type_combo.setEnabled(False)
        proxy_top.addWidget(self.proxy_type_combo)
        proxy_top.addStretch()
        pg.addLayout(proxy_top)

        proxy_addr = QHBoxLayout()
        proxy_addr.setSpacing(4)
        self.proxy_host = QLineEdit()
        self.proxy_host.setPlaceholderText("代理地址 (如 127.0.0.1)")
        self.proxy_host.setEnabled(False)
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(7890)
        self.proxy_port.setEnabled(False)
        proxy_addr.addWidget(self.proxy_host, 3)
        proxy_addr.addWidget(QLabel(":"))
        proxy_addr.addWidget(self.proxy_port, 1)
        pg.addLayout(proxy_addr)

        proxy_auth = QHBoxLayout()
        proxy_auth.setSpacing(4)
        self.proxy_user = QLineEdit()
        self.proxy_user.setPlaceholderText("用户名（可选）")
        self.proxy_user.setEnabled(False)
        self.proxy_pass = QLineEdit()
        self.proxy_pass.setPlaceholderText("密码（可选）")
        self.proxy_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.proxy_pass.setEnabled(False)
        proxy_auth.addWidget(self.proxy_user, 1)
        proxy_auth.addWidget(self.proxy_pass, 1)
        pg.addLayout(proxy_auth)
        layout.addLayout(create_card_group("代理设置", pg))

        # ── 操作按钮 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.run_btn = QPushButton("开始上传")
        self.run_btn.setObjectName("actionBtn")
        self.run_btn.setFixedWidth(120)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run)
        btn_row.addWidget(self.run_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择上传目录")
        if path:
            self.input_edit.setText(path)

    def _on_protocol_changed(self, index):
        self.config_stack.setCurrentIndex(index)

    def _on_proxy_toggled(self, checked):
        self.proxy_type_combo.setEnabled(checked)
        self.proxy_host.setEnabled(checked)
        self.proxy_port.setEnabled(checked)
        self.proxy_user.setEnabled(checked)
        self.proxy_pass.setEnabled(checked)

    def _get_proxy_url(self) -> str | None:
        if not self.chk_proxy.isChecked():
            return None
        ptype = self.proxy_type_combo.currentText().lower()
        host = self.proxy_host.text().strip() or "127.0.0.1"
        port = self.proxy_port.value()
        user = self.proxy_user.text().strip()
        passwd = self.proxy_pass.text()
        scheme = "socks5" if ptype == "socks5" else "http"
        if user:
            from urllib.parse import quote
            user_enc = quote(user, safe="")
            pass_enc = quote(passwd, safe="") if passwd else ""
            return f"{scheme}://{user_enc}:{pass_enc}@{host}:{port}"
        return f"{scheme}://{host}:{port}"

    def _create_uploader(self):
        protocol = self.protocol_combo.currentText()
        proxy_url = self._get_proxy_url()

        if protocol == "S3":
            return S3Uploader(
                endpoint=self.s3_endpoint.text().strip(),
                bucket=self.s3_bucket.text().strip(),
                access_key=self.s3_access_key.text().strip(),
                secret_key=self.s3_secret_key.text().strip(),
                prefix=self.s3_prefix.text().strip(),
                proxy_url=proxy_url,
                custom_domain=self.s3_domain.text().strip(),
            )
        elif protocol == "FTP":
            return FTPUploader(
                host=self.ftp_host.text().strip(),
                port=self.ftp_port.value(),
                username=self.ftp_user.text().strip(),
                password=self.ftp_pass.text().strip(),
                remote_dir=self.ftp_dir.text().strip() or "/",
                base_url=self.ftp_base_url.text().strip(),
            )
        else:
            return SFTPUploader(
                host=self.sftp_host.text().strip(),
                port=self.sftp_port.value(),
                username=self.sftp_user.text().strip(),
                password=self.sftp_pass.text().strip(),
                key_path=self.sftp_key.text().strip(),
                remote_dir=self.sftp_dir.text().strip() or "/",
                base_url=self.sftp_base_url.text().strip(),
                domain_root=self.sftp_domain_root.text().strip(),
            )

    def _run(self):
        if self.worker and self.worker.isRunning():
            return  # 防双击
        input_dir = self.input_edit.text().strip()
        if not input_dir:
            QMessageBox.warning(self, "提示", "请先选择上传目录")
            return

        try:
            uploader = self._create_uploader()
        except Exception as e:
            QMessageBox.critical(self, "配置错误", str(e))
            return

        self.run_btn.setEnabled(False)
        self.progress_widget.reset()
        self.url_output.clear()

        self.worker = UploadWorker(
            uploader, input_dir,
            recursive=self.chk_recursive_upload.isChecked(),
        )
        self.worker.progress.connect(self.progress_widget.update_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, result: UploadResult):
        self.run_btn.setEnabled(True)
        self.progress_widget.set_complete(
            f"完成: {result.uploaded_files}/{result.total_files} 已上传"
        )
        self.url_output.set_urls(result.urls)
        if result.errors:
            QMessageBox.warning(self, "部分上传失败",
                f"{result.failed_files} 个文件上传失败:\n" +
                "\n".join(result.errors[:10]))

    def _on_error(self, msg):
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "上传失败", msg)

    def set_input_dir(self, path: str):
        self.input_edit.setText(path)
