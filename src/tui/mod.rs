//! pikpaktui 风格的 TUI 实现。
//! 采用 Miller 3 列布局 (Parent / Current / Preview & Status)。
//! 支持目录浏览、异步 scan/prepare/compress、设置 overlay (可编辑关键参数并保存)、帮助 sheet。
//! 按 pikpaktui 模式：彩色提示、spinner、mpsc 后台任务、键盘驱动 (j/k, Enter, ,, h, q 等)。

use std::path::PathBuf;
use std::sync::mpsc::{self, Receiver, Sender};
use std::time::{Duration, Instant};
use std::{env, fs, thread};

use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, List, ListItem, ListState, Paragraph};
use ratatui::Terminal;

use crate::config;
use crate::core::{compress, prepare, scanner};

const SPINNER: &[&str] = &["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

#[derive(Clone)]
enum OpResult {
    ScanDone(scanner::ScanResult),
    PrepareDone(prepare::PrepareResult),
    CompressDone(compress::BatchResult),
    Log(String),
    Error(String),
}

#[derive(PartialEq, Clone)]
enum InputMode {
    Normal,
    Settings {
        selected: usize,
        draft: config::Config,
    },
    ConfirmQuit,
    HelpSheet,
}

pub struct App {
    current_dir: PathBuf,
    entries: Vec<(PathBuf, bool)>, // (path, is_dir)
    selected: usize,
    list_state: ListState,
    scan_result: Option<scanner::ScanResult>,
    last_status: String,
    input: InputMode,
    tx: Sender<OpResult>,
    rx: Receiver<OpResult>,
    spinner_idx: usize,
    last_spinner: Instant,
    config: config::Config,
}

pub fn run() -> Result<()> {
    enable_raw_mode()?;
    let mut stdout = std::io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let (tx, rx) = mpsc::channel();
    let mut app = App {
        current_dir: env::current_dir()?,
        entries: vec![],
        selected: 0,
        list_state: ListState::default(),
        scan_result: None,
        last_status: "欢迎使用 ImageCompression TUI (pikpaktui 风格) | r=扫描 | p=准备 | c=压缩 | ,=设置 | h=帮助 | q=退出".to_string(),
        input: InputMode::Normal,
        tx,
        rx,
        spinner_idx: 0,
        last_spinner: Instant::now(),
        config: config::load(None).unwrap_or_else(|_| config::default_config()),
    };
    app.refresh_entries();

    let res = app.run_loop(&mut terminal);

    disable_raw_mode()?;
    execute!(std::io::stdout(), LeaveAlternateScreen, DisableMouseCapture)?;
    if let Err(e) = res {
        eprintln!("TUI error: {e}");
    }
    Ok(())
}

impl App {
    fn refresh_entries(&mut self) {
        self.entries.clear();
        if let Ok(rd) = fs::read_dir(&self.current_dir) {
            for e in rd.filter_map(|e| e.ok()) {
                let p = e.path();
                let is_dir = p.is_dir();
                if is_dir || crate::core::scanner::is_image_like(&p) {
                    self.entries.push((p, is_dir));
                }
            }
        }
        self.entries.sort_by_key(|(p, d)| {
            (
                !*d,
                p.file_name()
                    .map(|n| n.to_string_lossy().to_string())
                    .unwrap_or_default(),
            )
        });
        self.list_state.select(Some(
            self.selected.min(self.entries.len().saturating_sub(1)),
        ));
    }

    fn run_loop(
        &mut self,
        terminal: &mut Terminal<CrosstermBackend<std::io::Stdout>>,
    ) -> Result<()> {
        loop {
            if self.last_spinner.elapsed() > Duration::from_millis(80) {
                self.spinner_idx = (self.spinner_idx + 1) % SPINNER.len();
                self.last_spinner = Instant::now();
            }
            self.poll_results();

            terminal.draw(|f| self.draw(f))?;

            if event::poll(Duration::from_millis(50))? {
                if let Event::Key(key) = event::read()? {
                    if key.kind != KeyEventKind::Press {
                        continue;
                    }
                    if self.handle_key(key.code)? {
                        break;
                    }
                }
            }
        }
        Ok(())
    }

    fn poll_results(&mut self) {
        while let Ok(res) = self.rx.try_recv() {
            match res {
                OpResult::ScanDone(r) => {
                    self.scan_result = Some(r.clone());
                    self.last_status = format!(
                        "扫描完成：图片 {} / 视频 {} / 其他 {}",
                        r.images.len(),
                        r.videos.len(),
                        r.others.len()
                    );
                }
                OpResult::PrepareDone(r) => {
                    self.last_status =
                        format!("准备完成：{} 个文件 -> {}", r.total_files, r.output_dir);
                    // 自动更新当前目录到 prepared
                    if let Ok(p) = std::path::Path::new(&r.output_dir).canonicalize() {
                        self.current_dir = p;
                        self.refresh_entries();
                    }
                }
                OpResult::CompressDone(r) => {
                    self.last_status = format!(
                        "压缩完成：成功 {}/{} ，节省约 {:.1}%",
                        r.compressed_files,
                        r.total_files,
                        if r.original_size > 0 {
                            100.0 - (r.compressed_size as f64 / r.original_size as f64 * 100.0)
                        } else {
                            0.0
                        }
                    );
                }
                OpResult::Log(s) => self.last_status = s,
                OpResult::Error(s) => self.last_status = format!("错误: {}", s),
            }
        }
    }

    fn draw(&mut self, f: &mut ratatui::Frame) {
        let size = f.size();
        let chunks = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([
                Constraint::Percentage(22),
                Constraint::Percentage(42),
                Constraint::Percentage(36),
            ])
            .split(size);

        // === Left: Parent column (Miller style, dim) ===
        let parent_path = self
            .current_dir
            .parent()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|| "/".to_string());
        let left_content = vec![
            Line::from(Span::styled(
                "↑ Parent",
                Style::default().fg(Color::DarkGray),
            )),
            Line::from(parent_path),
            Line::from(""),
            Line::from(Span::styled(
                "(Backspace 返回)",
                Style::default().fg(Color::DarkGray),
            )),
        ];
        let left = Paragraph::new(left_content).block(
            Block::default()
                .title("Parent")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::DarkGray)),
        );
        f.render_widget(left, chunks[0]);

        // === Center: Current dir list ===
        let title = format!(
            "{}  ({} 项)  | r:扫描",
            self.current_dir.display(),
            self.entries.len()
        );
        let items: Vec<ListItem> = self
            .entries
            .iter()
            .enumerate()
            .map(|(i, (p, is_dir))| {
                let name = p
                    .file_name()
                    .map(|n| n.to_string_lossy().to_string())
                    .unwrap_or_default();
                let prefix = if *is_dir { "📁 " } else { "🖼️ " };
                let style = if i == self.selected {
                    Style::default()
                        .fg(Color::Yellow)
                        .add_modifier(Modifier::BOLD)
                } else {
                    Style::default()
                };
                ListItem::new(Line::from(Span::styled(
                    format!("{}{}", prefix, name),
                    style,
                )))
            })
            .collect();

        let list = List::new(items)
            .block(Block::default().title(title).borders(Borders::ALL))
            .highlight_style(Style::default().bg(Color::Rgb(40, 40, 60)));
        f.render_stateful_widget(list, chunks[1], &mut self.list_state);

        // === Right: Preview / Status / Info ===
        let mut right_lines = vec![Line::from(Span::styled(
            "Preview & Status",
            Style::default().fg(Color::Cyan),
        ))];
        if let Some(scan) = &self.scan_result {
            right_lines.push(Line::from(format!(
                "📷 图片: {}   🎞 视频: {}",
                scan.images.len(),
                scan.videos.len()
            )));
            right_lines.push(Line::from(format!("体积: {} bytes", scan.total_size)));
        }
        right_lines.push(Line::from(""));
        right_lines.push(Line::from(self.last_status.as_str()));
        right_lines.push(Line::from(""));
        right_lines.push(Line::from(Span::styled(
            "快捷键指南:",
            Style::default().add_modifier(Modifier::BOLD),
        )));
        right_lines.push(Line::from(
            "j/k ↑↓ 导航 | Enter 进入目录 | r 扫描 | p 准备 | c 压缩",
        ));
        right_lines.push(Line::from(", 设置 | h 帮助 | q 退出"));

        if let Some((p, _)) = self.entries.get(self.selected) {
            if !p.is_dir() {
                right_lines.push(Line::from(""));
                right_lines.push(Line::from(format!(
                    "选中: {}",
                    p.file_name()
                        .map(|n| n.to_string_lossy())
                        .unwrap_or_default()
                )));
            }
        }

        let right =
            Paragraph::new(right_lines).block(Block::default().title("Info").borders(Borders::ALL));
        f.render_widget(right, chunks[2]);

        // === Overlays ===
        match &self.input {
            InputMode::Settings { selected, draft } => {
                let area = centered_rect(55, 55, size);
                f.render_widget(Clear, area);
                let mut lines = vec![
                    Line::from(Span::styled(
                        "⚙ 设置 (pikpaktui 风格) - s 保存, Esc 取消, j/k 选择",
                        Style::default().fg(Color::Green),
                    )),
                    Line::from(""),
                ];
                // 显示可编辑项 (简化示例，实际可扩展为更多字段)
                let items = [
                    format!("格式: {}", draft.compress.format),
                    format!("AVIF 质量上限: {}", draft.compress.avif.max_quality),
                    format!(
                        "avifenc 路径: {}",
                        if draft.avifenc_path.is_empty() {
                            "(PATH)"
                        } else {
                            &draft.avifenc_path
                        }
                    ),
                    format!("准备重命名图片: {}", draft.prepare.rename_images),
                    format!("递归: (在 CLI/TUI 操作时控制)"),
                ];
                for (i, item) in items.iter().enumerate() {
                    let style = if i == *selected {
                        Style::default()
                            .fg(Color::Yellow)
                            .add_modifier(Modifier::BOLD)
                    } else {
                        Style::default()
                    };
                    lines.push(Line::from(Span::styled(
                        format!("{} {}", if i == *selected { ">" } else { " " }, item),
                        style,
                    )));
                }
                lines.push(Line::from(""));
                lines.push(Line::from("提示: Space 切换部分选项，Enter 确认当前，s 保存到 ~/.imagecompression/config.json"));
                let overlay = Paragraph::new(lines).block(
                    Block::default()
                        .title("Settings")
                        .borders(Borders::ALL)
                        .border_style(Style::default().fg(Color::Blue)),
                );
                f.render_widget(overlay, area);
            }
            InputMode::ConfirmQuit => {
                let area = centered_rect(40, 20, size);
                f.render_widget(Clear, area);
                let overlay = Paragraph::new("确认退出? (y/Enter 退出, 其他键取消)")
                    .block(Block::default().title("Quit").borders(Borders::ALL));
                f.render_widget(overlay, area);
            }
            InputMode::HelpSheet => {
                let area = centered_rect(65, 60, size);
                f.render_widget(Clear, area);
                let help_text = vec![
                    Line::from(Span::styled(
                        "帮助 - pikpaktui 风格 ImageCompression TUI",
                        Style::default()
                            .fg(Color::Green)
                            .add_modifier(Modifier::BOLD),
                    )),
                    Line::from(""),
                    Line::from("导航: j/k 或 ↑↓  |  Enter: 进入目录或选择  |  Backspace: 返回上级"),
                    Line::from("r: 扫描当前目录 (统计图片/视频)"),
                    Line::from("p: 执行准备 (重命名 + 复制到 _prepared)"),
                    Line::from("c: 执行压缩 (使用当前配置参数，jpeg 演示)"),
                    Line::from(", : 打开设置 (编辑质量、格式、路径等并保存)"),
                    Line::from("h : 显示/隐藏此帮助"),
                    Line::from("q : 退出 (带确认)"),
                    Line::from(""),
                    Line::from(
                        "CLI 模式: imagecompression scan --input <dir> --json 等 (与原 Go 兼容)",
                    ),
                    Line::from("配置文件: ~/.imagecompression/config.json (完全兼容)"),
                    Line::from(""),
                    Line::from(Span::styled(
                        "按任意键关闭帮助",
                        Style::default().fg(Color::DarkGray),
                    )),
                ];
                let overlay = Paragraph::new(help_text)
                    .block(Block::default().title("Help").borders(Borders::ALL));
                f.render_widget(overlay, area);
            }
            _ => {}
        }
    }

    fn handle_key(&mut self, code: KeyCode) -> Result<bool> {
        match &mut self.input {
            InputMode::Normal => {
                match code {
                    KeyCode::Char('q') => {
                        self.input = InputMode::ConfirmQuit;
                    }
                    KeyCode::Char('h') => {
                        self.input = InputMode::HelpSheet;
                    }
                    KeyCode::Char('r') => {
                        let tx = self.tx.clone();
                        let dir = self.current_dir.clone();
                        thread::spawn(move || {
                            match scanner::scan_directory(dir.to_str().unwrap_or("."), true) {
                                Ok(r) => {
                                    let _ = tx.send(OpResult::ScanDone(r));
                                }
                                Err(e) => {
                                    let _ = tx.send(OpResult::Error(e.to_string()));
                                }
                            }
                        });
                        self.last_status = "正在扫描...".to_string();
                    }
                    KeyCode::Char('p') => {
                        if let Some(scan) = &self.scan_result {
                            let tx = self.tx.clone();
                            let s = prepare::ScanInput {
                                base_dir: scan.base_dir.clone(),
                                images: scan.images.clone(),
                                videos: scan.videos.clone(),
                            };
                            let out = format!("{}_prepared", scan.base_dir);
                            let cfg = self.config.clone(); // clone for thread
                            thread::spawn(move || {
                                let overwrite = cfg.prepare.output_mode == "overwrite";
                                match prepare::plan_operations(
                                    s,
                                    &out,
                                    prepare::Options {
                                        rename_images: cfg.prepare.rename_images,
                                        rename_videos: cfg.prepare.rename_videos,
                                        overwrite,
                                    },
                                ) {
                                    Ok(plan) => {
                                        if let Ok(res) =
                                            prepare::execute_operations(plan, overwrite, None)
                                        {
                                            let _ = tx.send(OpResult::PrepareDone(res));
                                        }
                                    }
                                    Err(e) => {
                                        let _ = tx.send(OpResult::Error(e.to_string()));
                                    }
                                }
                            });
                        } else {
                            self.last_status = "请先按 r 扫描目录".to_string();
                        }
                    }
                    KeyCode::Char('c') => {
                        let tx = self.tx.clone();
                        let input = if let Some(s) = &self.scan_result {
                            s.base_dir.clone()
                        } else {
                            self.current_dir.to_string_lossy().to_string()
                        };
                        // 使用当前 config 构造真实参数
                        let cfg = self.config.clone();
                        thread::spawn(move || {
                            let avif = &cfg.compress.avif;
                            let mut params = compress::Params {
                                quality: cfg.compress.webp_jpeg.quality,
                                speed: avif.speed,
                                lossless: avif.lossless,
                                resize_mode: cfg.compress.resize_mode.clone(),
                                resize_value: cfg.compress.resize_value,
                                keep_aspect_ratio: cfg.compress.keep_aspect_ratio,
                                strip_exif: cfg.prepare.strip_exif,
                                keep_icc: false,
                                strip_xmp: true,
                                extra: std::collections::HashMap::from([
                                    ("min_quality".into(), serde_json::json!(avif.min_quality)),
                                    ("max_quality".into(), serde_json::json!(avif.max_quality)),
                                    ("threads".into(), serde_json::json!(avif.threads)),
                                    ("yuv".into(), serde_json::json!(avif.yuv)),
                                    ("depth".into(), serde_json::json!(avif.depth)),
                                ]),
                            };
                            let opts = compress::BatchOptions {
                                input_dir: input.clone(),
                                output_dir: format!("{}_compressed", input),
                                format: cfg.compress.format.clone(),
                                recursive: true,
                                overwrite: false,
                                conflict_strategy: cfg.compress.conflict_strategy.clone(),
                                avifenc_path: cfg.avifenc_path.clone(),
                                cwebp_path: "cwebp".to_string(),
                                max_workers: cfg.compress.workers,
                                params,
                            };
                            match compress::compress_directory(
                                std::sync::Arc::new(()),
                                opts,
                                None,
                                None,
                            ) {
                                Ok(res) => {
                                    let _ = tx.send(OpResult::CompressDone(res));
                                }
                                Err(e) => {
                                    let _ = tx.send(OpResult::Error(e.to_string()));
                                }
                            }
                        });
                        self.last_status = "正在压缩... (后台)".to_string();
                    }
                    KeyCode::Char(',') => {
                        self.input = InputMode::Settings {
                            selected: 0,
                            draft: self.config.clone(),
                        };
                    }
                    KeyCode::Down | KeyCode::Char('j') => {
                        if self.selected + 1 < self.entries.len() {
                            self.selected += 1;
                            self.list_state.select(Some(self.selected));
                        }
                    }
                    KeyCode::Up | KeyCode::Char('k') => {
                        if self.selected > 0 {
                            self.selected -= 1;
                            self.list_state.select(Some(self.selected));
                        }
                    }
                    KeyCode::Enter => {
                        if let Some((p, is_dir)) = self.entries.get(self.selected) {
                            if *is_dir {
                                self.current_dir = p.clone();
                                self.selected = 0;
                                self.refresh_entries();
                            } else {
                                self.last_status =
                                    format!("选中文件: {} (可用于压缩)", p.display());
                            }
                        }
                    }
                    KeyCode::Backspace => {
                        if let Some(parent) = self.current_dir.parent() {
                            self.current_dir = parent.to_path_buf();
                            self.selected = 0;
                            self.refresh_entries();
                        }
                    }
                    _ => {}
                }
            }
            InputMode::Settings { selected, draft } => {
                match code {
                    KeyCode::Esc => {
                        self.input = InputMode::Normal;
                    }
                    KeyCode::Char('s') | KeyCode::Enter => {
                        if let Ok(()) = config::save(None, draft.clone()) {
                            self.config = draft.clone();
                            self.last_status =
                                "设置已保存到 ~/.imagecompression/config.json".to_string();
                        }
                        self.input = InputMode::Normal;
                    }
                    KeyCode::Down | KeyCode::Char('j') => {
                        *selected = (*selected + 1).min(4);
                    }
                    KeyCode::Up | KeyCode::Char('k') => {
                        if *selected > 0 {
                            *selected -= 1;
                        }
                    }
                    KeyCode::Char(' ') | KeyCode::Enter => {
                        // 简单切换示例
                        match *selected {
                            0 => {
                                // 切换格式
                                draft.compress.format = match draft.compress.format.as_str() {
                                    "avif" => "webp".to_string(),
                                    "webp" => "jpeg".to_string(),
                                    _ => "avif".to_string(),
                                };
                            }
                            1 => {
                                draft.compress.avif.max_quality =
                                    (draft.compress.avif.max_quality + 5).min(63);
                            }
                            2 => {
                                // avifenc_path 简单清空/示例
                                if draft.avifenc_path.is_empty() {
                                    draft.avifenc_path = "build/bin/windows-artifacts".to_string();
                                } else {
                                    draft.avifenc_path.clear();
                                }
                            }
                            3 => {
                                draft.prepare.rename_images = !draft.prepare.rename_images;
                            }
                            _ => {}
                        }
                        self.last_status = "设置已修改 (按 s 保存)".to_string();
                    }
                    _ => {}
                }
            }
            InputMode::ConfirmQuit => match code {
                KeyCode::Char('y') | KeyCode::Enter => return Ok(true),
                _ => {
                    self.input = InputMode::Normal;
                }
            },
            InputMode::HelpSheet => {
                // 任意键关闭帮助
                self.input = InputMode::Normal;
            }
        }
        Ok(false)
    }
}

fn centered_rect(percent_x: u16, percent_y: u16, r: Rect) -> Rect {
    let popup_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - percent_y) / 2),
            Constraint::Percentage(percent_y),
            Constraint::Percentage((100 - percent_y) / 2),
        ])
        .split(r);
    Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - percent_x) / 2),
            Constraint::Percentage(percent_x),
            Constraint::Percentage((100 - percent_x) / 2),
        ])
        .split(popup_layout[1])[1]
}
