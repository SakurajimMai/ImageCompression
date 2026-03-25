# Mac/iOS Minimalist UI Overhaul Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Transform the app's UI into a modern, minimalist macOS/iOS style by replacing bordered QGroupBoxes with frameless Cards, removing traditional tabs, and updating QSS for large rounded corners and negative space.

**Architecture:** We will create a `create_card_group` helper in a utils/ui file to replace standard QGroupBox instantiations. We will refactor all tab layouts to use this layout. Finally, we'll rewrite the app's QSS in `theme.py` to match the new visual guidelines.

**Tech Stack:** PySide6, Python, QSS

---

### Task 1: Create Reusable Card UI Helper

**Files:**
- Create: `src/ui/widgets/card_group.py`
- Modify: `src/ui/theme.py`

**Step 1: Write the widget logic**

```python
"""
src/ui/widgets/card_group.py
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

    # 1. 标题
    title = QLabel(title_text)
    title.setStyleSheet("font-weight: 600; font-size: 13px; color: #64748B; padding-left: 4px;")
    group_layout.addWidget(title)

    # 2. 卡片容器
    card = QWidget()
    card.setObjectName("card")  # 供 QSS 定位
    
    # 3. 为内容 layout 增加内部边距
    content_layout.setContentsMargins(16, 16, 16, 16)
    content_layout.setSpacing(spacing)
    card.setLayout(content_layout)

    group_layout.addWidget(card)
    return group_layout
```

**Step 2: Add `#card` selector to QSS**

Update `src/ui/theme.py` Light Theme section to add the `#card` styles:
```css
/* ========== 卡片容器 ========== */
QWidget#card {
    background-color: #FFFFFF;
    border-radius: 12px;
}
```
*(and equivalent deep dark / slate colors for dark and gray themes)*

**Step 3: Commit**

```bash
git add src/ui/widgets/card_group.py src/ui/theme.py
git commit -m "feat(ui): add modern card_group helper and QSS base for mac style"
```

---

### Task 2: Refactor Settings Tab to Card Style

**Files:**
- Modify: `src/ui/settings_tab.py`

**Step 1: Replace QGroupBox with create_card_group**

```python
from ui.widgets.card_group import create_card_group

# Instead of:
# ui_group = QGroupBox("界面设置")
# ug = QVBoxLayout(ui_group)
# ... components ...
# layout.addWidget(ui_group)

# Do this:
ug = QVBoxLayout()
# ... add components to ug ...
layout.addLayout(create_card_group("界面设置", ug))
```

**Step 2: Run & verify the app**

Run: `python src/main.py`
Expected: The app starts, and the Settings tab shows titles with cards underneath instead of bordered group boxes.

**Step 3: Commit**

```bash
git add src/ui/settings_tab.py
git commit -m "refactor(ui): update settings tab to use modern card layout"
```

---

### Task 3: Refactor Prepare, Compress, Upload and Help Tabs

**Files:**
- Modify: `src/ui/prepare_tab.py`
- Modify: `src/ui/compress_tab.py`
- Modify: `src/ui/upload_tab.py`
- Modify: `src/ui/help_tab.py`

**Step 1: Apply the same replacement pattern**

Replace all `QGroupBox` instances with `create_card_group`.

**Step 2: Run test suite to ensure no code broke**

Run: `pytest tests/ -q`
Expected: PASS 65/65

**Step 3: Commit**

```bash
git add src/ui/prepare_tab.py src/ui/compress_tab.py src/ui/upload_tab.py src/ui/help_tab.py
git commit -m "refactor(ui): update all remaining tabs to card layout"
```

---

### Task 4: Complete QSS Overhaul (Typography, Tabs, Inputs)

**Files:**
- Modify: `src/ui/theme.py`

**Step 1: Overhaul Colors and Borders**

Replace the existing QSS colors and borders:
- Remove ALL `1px solid` borders from QTabWidget and QMainWindow.
- Change Tab pane styles to a clean frameless look (Segmented Control style).
- Re-style `QLineEdit` and `QPushButton` with `border-radius: 8px; border: none; padding: 8px;`.
- Set Main Window Background to `#F2F2F7` (Light), `#16161A` (Dark), `#0F172A` (Gray).
- Remove QGroupBox styles completely from QSS since we don't use them anymore.

**Step 2: Start App and Final Verification**

Run: `python src/main.py`
Expected: The UI looks drastically cleaner. Large rounded corners on blocks of settings. Background contrast creates hierarchy, without drawing any lines.

**Step 3: Commit**

```bash
git commit -am "style: complete macOS minimalist QSS overhaul"
```
