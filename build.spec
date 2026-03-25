# -*- mode: python ; coding: utf-8 -*-
"""
ImageCompression PyInstaller 构建配置

使用方法:
    pyinstaller build.spec

输出:
    dist/ImageCompression/ — 包含 ImageCompression.exe 和依赖文件
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # PySide6 核心
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # PIL 插件
        'PIL',
        'PIL.Image',
        'PIL.ExifTags',
        'pillow_heif',
        # 上传依赖
        'boto3',
        'botocore',
        'paramiko',
        'socks',
        # 工具
        'click',
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        'psutil',
        # 画质分析（可选）
        'numpy',
        'skimage',
        'skimage.metrics',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型模块
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'notebook',
        'sphinx',
        'pytest',
        'setuptools',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ImageCompression',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 窗口模式，无控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ImageCompression',
)
