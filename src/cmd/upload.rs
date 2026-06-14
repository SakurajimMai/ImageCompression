use crate::cmd::{print_command_help, B, D, G, R};
use crate::config;
use crate::core::upload::build_uploader;
use crate::core::upload::{self as up, Options as UpOptions, ProgressFunc};
use anyhow::Result;

pub fn run(args: &[String]) -> Result<()> {
    let mut input = String::new();
    let mut cfg_path = String::new();
    let mut recursive = true;
    let mut json = false;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--input" => {
                i += 1;
                input = args.get(i).cloned().unwrap_or_default();
            }
            "--config" => {
                i += 1;
                cfg_path = args.get(i).cloned().unwrap_or_default();
            }
            "--recursive" => recursive = true,
            "--no-recursive" => recursive = false,
            "--json" => json = true,
            "-h" | "--help" => return print_command_help("upload"),
            _ => {}
        }
        i += 1;
    }
    if input.is_empty() {
        return Err(anyhow::anyhow!("--input 必填"));
    }

    let cfg = if cfg_path.is_empty() {
        config::load(None)?
    } else {
        config::load(Some(&cfg_path))?
    };
    let eff = crate::core::upload::effective_config(cfg.upload.clone(), &input);
    let mut uploader = build_uploader(eff);

    let progress: ProgressFunc = if json {
        Some(Box::new(|e| {
            let _ = serde_json::to_writer(std::io::stdout(), &e);
            println!();
        }))
    } else {
        Some(Box::new(|e| {
            if e.start.unwrap_or(false) {
                println!("[upload] 开始 共 {} 个文件", e.total);
            } else if e.done.unwrap_or(false) { /* summary */
            } else if let Some(err) = &e.error {
                println!(
                    "[upload] {}/{} 失败 {}  err={}",
                    e.current, e.total, e.message, err
                );
            } else if let Some(u) = &e.url {
                println!(
                    "[upload] {}/{} OK {} -> {}",
                    e.current, e.total, e.message, u
                );
            } else {
                println!("[upload] {}/{} .. {}", e.current, e.total, e.message);
            }
        }))
    };

    let res = up::upload_directory(&mut *uploader, &input, UpOptions { recursive }, progress)?;

    if json {
        println!(
            r#"{{"event":"done","phase":"upload","total":{},"uploaded":{},"failed":{},"urls":{},"errors":{}}}"#,
            res.total_files,
            res.uploaded_files,
            res.failed_files,
            serde_json::to_string(&res.urls)?,
            serde_json::to_string(&res.errors)?
        );
    } else {
        println!(
            "\n上传完成: {} 成功 / {} 失败",
            res.uploaded_files, res.failed_files
        );
        for u in &res.urls {
            println!("  {}", u);
        }
        for e in &res.errors {
            println!("  ! {}", e);
        }
    }
    if res.failed_files > 0 {
        std::process::exit(1);
    }
    Ok(())
}
