use crate::cmd::{print_command_help, B, D, G, R};
use crate::core::compress::{self, BatchOptions, Params, ProgressFunc};
use crate::core::scanner;
use anyhow::Result;
use std::sync::Arc;

pub fn run(args: &[String]) -> Result<()> {
    let mut input = String::new();
    let mut output = String::new();
    let mut format = "avif".to_string();
    let mut quality = 35i32;
    let mut min_quality = 20i32;
    let mut speed = 6i32;
    let mut recursive = true;
    let mut overwrite = false;
    let mut workers = 1i32;
    let mut avifenc = String::new();
    let mut json = false;
    let mut resize_mode = "none".to_string();
    let mut resize_value = 0i32;
    let mut keep_aspect_ratio = true;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--input" => {
                i += 1;
                if i < args.len() {
                    input = args[i].clone();
                }
            }
            "--output" => {
                i += 1;
                if i < args.len() {
                    output = args[i].clone();
                }
            }
            "--format" => {
                i += 1;
                if i < args.len() {
                    format = args[i].clone();
                }
            }
            "--quality" => {
                i += 1;
                if i < args.len() {
                    quality = args[i].parse().unwrap_or(35);
                }
            }
            "--min-quality" => {
                i += 1;
                if i < args.len() {
                    min_quality = args[i].parse().unwrap_or(20);
                }
            }
            "--speed" => {
                i += 1;
                if i < args.len() {
                    speed = args[i].parse().unwrap_or(6);
                }
            }
            "--workers" => {
                i += 1;
                if i < args.len() {
                    workers = args[i].parse().unwrap_or(1);
                }
            }
            "--avifenc" => {
                i += 1;
                if i < args.len() {
                    avifenc = args[i].clone();
                }
            }
            "--resize-mode" => {
                i += 1;
                if i < args.len() {
                    resize_mode = args[i].clone();
                }
            }
            "--resize-value" => {
                i += 1;
                if i < args.len() {
                    resize_value = args[i].parse().unwrap_or(0);
                }
            }
            "--keep-aspect-ratio" => keep_aspect_ratio = true,
            "--no-keep-aspect-ratio" => keep_aspect_ratio = false,
            "--recursive" => recursive = true,
            "--no-recursive" => recursive = false,
            "--overwrite" => overwrite = true,
            "--json" => json = true,
            "-h" | "--help" => return print_command_help("compress"),
            _ => {}
        }
        i += 1;
    }
    if input.is_empty() {
        return Err(anyhow::anyhow!("--input 必填"));
    }
    if output.is_empty() {
        output = format!(
            "{}_compressed",
            input.trim_end_matches(|c| c == '/' || c == '\\')
        );
    }

    let opts = BatchOptions {
        input_dir: input.clone(),
        output_dir: output.clone(),
        format,
        recursive,
        overwrite,
        conflict_strategy: if overwrite {
            "overwrite".to_string()
        } else {
            "rename".to_string()
        },
        avifenc_path: avifenc,
        cwebp_path: "cwebp".to_string(),
        max_workers: workers,
        params: Params {
            quality,
            speed,
            lossless: false,
            resize_mode,
            resize_value,
            keep_aspect_ratio,
            strip_exif: true,
            keep_icc: false,
            strip_xmp: true,
            extra: std::collections::HashMap::from([
                ("min_quality".to_string(), serde_json::json!(min_quality)),
                ("max_quality".to_string(), serde_json::json!(quality)),
                ("threads".to_string(), serde_json::json!("all")),
                ("yuv".to_string(), serde_json::json!("420")),
                ("depth".to_string(), serde_json::json!(8)),
            ]),
        },
    };

    let progress: ProgressFunc = if json {
        Some(Box::new(|ev: compress::ProgressEvent| {
            let _ = serde_json::to_writer(std::io::stdout(), &ev);
            println!();
        }))
    } else {
        Some(Box::new(|ev: compress::ProgressEvent| {
            if ev.start.unwrap_or(false) {
                println!("[compress] 开始 共 {} 个文件", ev.total);
            } else if ev.done.unwrap_or(false) {
                // summary later
            } else if let Some(err) = &ev.error {
                println!(
                    "[compress] {}/{} 失败 {}  err={}",
                    ev.current, ev.total, ev.current_file, err
                );
            } else {
                println!(
                    "[compress] {}/{}  {}  {:.1} 张/秒",
                    ev.current,
                    ev.total,
                    std::path::Path::new(&ev.current_file)
                        .file_name()
                        .unwrap_or_default()
                        .to_string_lossy(),
                    ev.speed
                );
            }
        }))
    };

    let res = compress::compress_directory(Arc::new(()), opts, None, progress)?;

    if json {
        let ratio = if res.original_size > 0 {
            100.0 - (res.compressed_size as f64 / res.original_size as f64 * 100.0)
        } else {
            0.0
        };
        println!(
            r#"{{"event":"done","phase":"compress","outputDir":{:?},"total":{},"compressed":{},"skipped":{},"failed":{},"originalSize":{},"compressedSize":{},"savedPercent":{:.1},"elapsed":{:.1}}}"#,
            res.output_dir,
            res.total_files,
            res.compressed_files,
            res.skipped_files,
            res.failed_files,
            res.original_size,
            res.compressed_size,
            ratio,
            res.elapsed_seconds
        );
    } else {
        let ratio = if res.original_size > 0 {
            100.0 - (res.compressed_size as f64 / res.original_size as f64 * 100.0)
        } else {
            0.0
        };
        println!(
            "\n压缩完成: {} 成功 / {} 跳过 / {} 失败",
            res.compressed_files, res.skipped_files, res.failed_files
        );
        println!(
            "体积: {} -> {} (节省 {:.1}%)",
            format_bytes(res.original_size),
            format_bytes(res.compressed_size),
            ratio
        );
        println!("输出: {}", res.output_dir);
        println!("用时: {:.1} 秒", res.elapsed_seconds);
    }

    if res.failed_files > 0 {
        std::process::exit(1);
    }
    Ok(())
}

fn format_bytes(n: i64) -> String {
    const K: i64 = 1024;
    if n < K {
        return format!("{} B", n);
    }
    if n < K * K {
        return format!("{:.1} KB", n as f64 / K as f64);
    }
    if n < K * K * K {
        return format!("{:.1} MB", n as f64 / (K * K) as f64);
    }
    format!("{:.2} GB", n as f64 / (K * K * K) as f64)
}
