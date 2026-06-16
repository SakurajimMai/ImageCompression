use crate::cmd::{print_command_help, B, D, G, R};
use crate::config;
use crate::core::{compress, prepare, scanner, upload as up};
use anyhow::Result;

pub fn run(args: &[String]) -> Result<()> {
    let mut input = String::new();
    let mut prepared_out = String::new();
    let mut compressed_out = String::new();
    let mut format = "avif".to_string();
    let mut quality = 35i32;
    let mut recursive = true;
    let mut overwrite = false;
    let mut do_upload = false;
    let mut cfg_path = String::new();
    let mut json = false;
    let mut resize_mode = "none".to_string();
    let mut resize_value = 0i32;
    let mut keep_aspect_ratio = true;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--input" => {
                i += 1;
                input = args.get(i).cloned().unwrap_or_default();
            }
            "--prepared-output" => {
                i += 1;
                prepared_out = args.get(i).cloned().unwrap_or_default();
            }
            "--compressed-output" => {
                i += 1;
                compressed_out = args.get(i).cloned().unwrap_or_default();
            }
            "--format" => {
                i += 1;
                format = args.get(i).cloned().unwrap_or_default();
            }
            "--quality" => {
                i += 1;
                quality = args
                    .get(i)
                    .cloned()
                    .unwrap_or_default()
                    .parse()
                    .unwrap_or(35);
            }
            "--resize-mode" => {
                i += 1;
                resize_mode = args.get(i).cloned().unwrap_or_else(|| "none".to_string());
            }
            "--resize-value" => {
                i += 1;
                resize_value = args
                    .get(i)
                    .cloned()
                    .unwrap_or_default()
                    .parse()
                    .unwrap_or(0);
            }
            "--keep-aspect-ratio" => keep_aspect_ratio = true,
            "--no-keep-aspect-ratio" => keep_aspect_ratio = false,
            "--upload" => do_upload = true,
            "--config" => {
                i += 1;
                cfg_path = args.get(i).cloned().unwrap_or_default();
            }
            "--json" => json = true,
            "-h" | "--help" => return print_command_help("all"),
            _ => {}
        }
        i += 1;
    }
    if input.is_empty() {
        return Err(anyhow::anyhow!("--input 必填"));
    }
    if prepared_out.is_empty() {
        prepared_out = format!("{}_prepared", input);
    }
    if compressed_out.is_empty() {
        compressed_out = format!("{}_compressed", prepared_out);
    }

    // 1. scan + prepare
    let scan = scanner::scan_directory(&input, recursive)?;
    if !json {
        println!("[1/3] 准备阶段,共 {} 张图片...", scan.images.len());
    }
    let plan = prepare::plan_operations(
        prepare::ScanInput {
            base_dir: scan.base_dir,
            images: scan.images,
            videos: scan.videos,
        },
        &prepared_out,
        prepare::Options {
            rename_images: true,
            rename_videos: true,
            overwrite,
        },
    )?;
    let prep_res = prepare::execute_operations(plan, overwrite, None)?;

    if !json {
        println!("准备完成 -> {}", prep_res.output_dir);
        println!("[2/3] 压缩阶段 -> {}", compressed_out);
    }

    // 2. compress
    let comp_opts = compress::BatchOptions {
        input_dir: prep_res.output_dir.clone(),
        output_dir: compressed_out.clone(),
        format,
        recursive,
        overwrite: false,
        conflict_strategy: "rename".to_string(),
        avifenc_path: "".to_string(),
        cwebp_path: "cwebp".to_string(),
        max_workers: 1,
        params: compress::Params {
            quality,
            speed: 6,
            resize_mode,
            resize_value,
            keep_aspect_ratio,
            ..Default::default()
        },
    };
    let comp_res = compress::compress_directory(std::sync::Arc::new(()), comp_opts, None, None)?;

    if !json {
        println!(
            "压缩完成: {} 成功 / {} 失败",
            comp_res.compressed_files, comp_res.failed_files
        );
    }

    if !do_upload {
        if comp_res.failed_files > 0 {
            std::process::exit(1);
        }
        return Ok(());
    }

    if !json {
        println!("[3/3] 上传阶段 -> {}", comp_res.output_dir);
    }

    let cfg = if cfg_path.is_empty() {
        config::load(None)?
    } else {
        config::load(Some(&cfg_path))?
    };
    let eff = crate::core::upload::effective_config(cfg.upload, &comp_res.output_dir);
    let mut upl = crate::core::upload::build_uploader(eff);
    let up_res = up::upload_directory(
        &mut *upl,
        &comp_res.output_dir,
        up::Options { recursive },
        None,
    )?;

    if !json {
        println!(
            "上传完成: {} 成功 / {} 失败",
            up_res.uploaded_files, up_res.failed_files
        );
    }
    if up_res.failed_files > 0 {
        std::process::exit(1);
    }
    Ok(())
}
