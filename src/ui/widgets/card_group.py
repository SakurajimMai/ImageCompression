"""
Helper for modern borderless "Label + Card" UI layout.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

def create_card_group(title_text: str, content_layout: QVBoxLayout, spacing: int = 8) -> QVBoxLayout:
    """
    创建一个类 macOS 风格的选项组布局：
    上方是粗体标题，下方是一个背景独立的纯净卡片。
    返回整合好的外层 QVBoxLayout，直接 addLayout 即可。
    """
    group_layout = QVBoxLayout()
    group_layout.setContentsMargins(0, 4, 0, 12)
    group_layout.setSpacing(6)

    if title_text:
        title = QLabel(title_text)
        title.setObjectName("groupTitle")
        group_layout.addWidget(title)

    # 卡片容器
    card = QWidget()
    card.setObjectName("card")  # 供 QSS 定位
    
    # 为内容 layout 增加内部边距
    content_layout.setContentsMargins(16, 16, 16, 16)
    content_layout.setSpacing(spacing)
    card.setLayout(content_layout)

    group_layout.addWidget(card)
    return group_layout
