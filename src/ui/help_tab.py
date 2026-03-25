"""
说明页 Tab — CLI 用法与功能说明（精美排版）
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextBrowser,
)


HELP_HTML = """
<style>
    body {
        font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
        font-size: 13px;
        line-height: 1.7;
        color: #334155;
        margin: 0;
        padding: 16px 20px;
    }

    /* 大标题 */
    .hero {
        text-align: center;
        padding: 20px 0 14px;
        border-bottom: 2px solid #EEF2FF;
        margin-bottom: 18px;
    }
    .hero h1 {
        font-size: 22px;
        font-weight: 800;
        color: #1E293B;
        margin: 0 0 4px;
        letter-spacing: 1px;
    }
    .hero p {
        color: #64748B;
        font-size: 13px;
        margin: 0;
    }
    .hero .badge {
        display: inline-block;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        color: #fff;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 10px;
        margin: 0 3px;
        letter-spacing: 0.5px;
    }

    /* 章节标题 */
    h2 {
        font-size: 16px;
        font-weight: 700;
        color: #1E293B;
        margin: 22px 0 8px;
        padding-bottom: 6px;
        border-bottom: 2px solid #E2E8F0;
    }
    h2 .icon { margin-right: 6px; }

    h3 {
        font-size: 13px;
        font-weight: 600;
        color: #475569;
        margin: 14px 0 4px;
    }

    /* 代码块 */
    pre {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #818CF8;
        color: #334155;
        padding: 10px 14px;
        border-radius: 6px;
        font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
        font-size: 12px;
        line-height: 1.6;
        margin: 6px 0 10px;
        overflow-x: auto;
    }

    /* 行内代码 */
    code {
        background: #EEF2FF;
        color: #4F46E5;
        padding: 1px 6px;
        border-radius: 4px;
        font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
        font-size: 12px;
        font-weight: 500;
    }

    /* 表格 */
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 8px 0 14px;
        border-radius: 8px;
        overflow: hidden;
    }
    th {
        background: #F1F5F9;
        color: #334155;
        font-weight: 700;
        font-size: 12px;
        padding: 8px 12px;
        text-align: left;
        border-bottom: 2px solid #E2E8F0;
    }
    td {
        padding: 7px 12px;
        border-bottom: 1px solid #F1F5F9;
        font-size: 12px;
        color: #475569;
    }
    tr:hover td { background: #F8FAFC; }

    /* 提示框 */
    .card {
        border-radius: 8px;
        padding: 10px 14px;
        margin: 10px 0;
        font-size: 12px;
        line-height: 1.6;
    }
    .card-info {
        background: #EEF2FF;
        border: 1px solid #C7D2FE;
        color: #3730A3;
    }
    .card-warn {
        background: #FFFBEB;
        border: 1px solid #FCD34D;
        color: #92400E;
    }
    .card-success {
        background: #ECFDF5;
        border: 1px solid #6EE7B7;
        color: #065F46;
    }

    /* 标签 */
    .tag {
        display: inline-block;
        background: #F1F5F9;
        color: #475569;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        margin: 2px 3px;
        border: 1px solid #E2E8F0;
    }
    .tag-primary {
        background: #EEF2FF;
        color: #4F46E5;
        border-color: #C7D2FE;
    }

    /* 分隔线 */
    hr {
        border: none;
        height: 1px;
        background: #E2E8F0;
        margin: 18px 0;
    }

    /* 列表 */
    ul { padding-left: 20px; margin: 4px 0; }
    li { margin: 3px 0; color: #475569; }
    li b { color: #334155; }
</style>

<!-- ═══════════════ 正文 ═══════════════ -->

<div class="hero">
    <h1>Image Compression</h1>
    <p>
        <span class="badge">GUI</span>
        <span class="badge">CLI</span>
        <span class="badge">AVIF</span>
        <span class="badge">WebP</span>
        <span class="badge">JPEG</span>
    </p>
    <p style="margin-top:6px;">高性能批量图片压缩工具 · 支持 GUI 界面 + CLI 命令行双模式</p>
</div>

<h2><span class="icon">⌨️</span>CLI 命令行模式</h2>

<h3>基本压缩</h3>
<pre>python cli.py compress ./photos -f avif -q 55 -o ./output</pre>

<h3>使用预设模板</h3>
<pre>python cli.py compress ./photos --preset web
python cli.py compress ./photos --preset hdr
python cli.py compress ./photos --preset lossless</pre>

<h3>递归目录 + 并行处理</h3>
<pre>python cli.py compress ./photos -f webp --recursive -j 4</pre>

<h3>无损 + HDR 模式</h3>
<pre>python cli.py compress ./photos --lossless --depth 10 --yuv 444</pre>

<h3>缩放 + 元数据控制</h3>
<pre>python cli.py compress ./photos --resize w800 --strip-exif --keep-icc</pre>

<h3>stdin 管道输入</h3>
<pre>echo "C:/photos" | python cli.py compress --stdin -f avif</pre>

<h3>图片信息 / 目录扫描</h3>
<pre>python cli.py info photo.jpg
python cli.py scan ./photos -r
python cli.py presets</pre>

<hr>

<h2><span class="icon">🎯</span>预设模板</h2>

<table>
    <tr>
        <th>预设</th><th>用途</th><th>质量</th><th>YUV</th><th>位深</th>
    </tr>
    <tr>
        <td><code>web</code></td><td>网页展示，平衡质量与体积</td><td>55</td><td>420</td><td>8</td>
    </tr>
    <tr>
        <td><code>mobile</code></td><td>移动端优化</td><td>60</td><td>420</td><td>8</td>
    </tr>
    <tr>
        <td><code>lossless</code></td><td>完全无损</td><td>100</td><td>444</td><td>10</td>
    </tr>
    <tr>
        <td><code>max_compress</code></td><td>极致压缩，最小体积</td><td>30</td><td>420</td><td>8</td>
    </tr>
    <tr>
        <td><code>hdr</code></td><td>HDR / Gain Map 模式</td><td>65</td><td>444</td><td>10</td>
    </tr>
</table>

<hr>

<h2><span class="icon">⚙️</span>AVIF 参数说明</h2>

<table>
    <tr><th>参数</th><th>范围</th><th>说明</th></tr>
    <tr><td><code>--quality</code></td><td>0 – 100</td><td>压缩质量，越高画质越好</td></tr>
    <tr><td><code>--speed</code></td><td>0 – 10</td><td>编码速度  0 = 最慢最好  10 = 最快</td></tr>
    <tr><td><code>--yuv</code></td><td>420 / 422 / 444</td><td>色度采样  444 = 最高视觉质量</td></tr>
    <tr><td><code>--depth</code></td><td>8 / 10 / 12</td><td>位深度  10+ 适合 HDR 内容</td></tr>
    <tr><td><code>--lossless</code></td><td>flag</td><td>开启无损压缩</td></tr>
    <tr><td><code>--progressive</code></td><td>flag</td><td>渐进式输出（需 libavif 1.1+）</td></tr>
    <tr><td><code>--resize</code></td><td>w800 / h600 / 50%</td><td>按宽度 / 高度 / 比例缩放</td></tr>
    <tr><td><code>--strip-exif</code></td><td>flag</td><td>清除 EXIF 元数据</td></tr>
    <tr><td><code>--keep-icc</code></td><td>flag</td><td>保留 ICC 色彩配置文件</td></tr>
</table>

<hr>

<h2><span class="icon">📂</span>支持格式</h2>

<p><b>输入：</b>
    <span class="tag">JPG</span>
    <span class="tag">PNG</span>
    <span class="tag">WebP</span>
    <span class="tag">HEIC</span>
    <span class="tag">TIFF</span>
    <span class="tag">BMP</span>
    <span class="tag">GIF</span>
    <span class="tag">AVIF</span>
    <span class="tag">Y4M</span>
</p>

<p><b>输出：</b>
    <span class="tag tag-primary">AVIF</span>
    <span class="tag tag-primary">WebP</span>
    <span class="tag tag-primary">JPEG</span>
</p>

<hr>

<h2><span class="icon">🖥️</span>GUI 界面功能</h2>

<ul>
    <li><b>📁 准备</b> — 扫描目录 · 重命名文件 · 清除 EXIF · 递归子目录</li>
    <li><b>🗜️ 压缩</b> — AVIF/WebP/JPEG · 完整参数 · 缩放 · 并行 · 预览对比</li>
    <li><b>☁️ 上传</b> — S3 / FTP / SFTP · 自定义域名 · 代理</li>
    <li><b>⚙️ 设置</b> — 语言切换 · 深浅主题 · avifenc 路径</li>
</ul>

<hr>

<div class="card card-info">
    💡 <b>提示：</b> 使用 <code>--preset web</code> 可一键获得适合网页的最优参数组合，无需手动调参。
</div>

<div class="card card-warn">
    ⚠️ <b>注意：</b> AVIF 压缩需要系统安装 <code>avifenc</code>。
    Windows: <code>scoop install libavif</code> ·
    macOS: <code>brew install libavif</code> ·
    Linux: <code>apt install libavif-bin</code>
</div>

<div class="card card-success">
    ✅ <b>版本：</b> Image Compression v2.0 — 支持 HDR/Gain Map · 渐进式 AVIF · 并行处理 · Watch Folder
</div>
"""


class HelpTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        browser = QTextBrowser()
        browser.setHtml(HELP_HTML)
        browser.setOpenExternalLinks(True)
        layout.addWidget(browser)
