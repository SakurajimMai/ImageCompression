use crate::cmd::{B, D, G, R};
use crate::core::{prepare, scanner};
use anyhow::Result;

pub fn run(args: &[String]) -> Result<()> {
    let mut input = String::new();
    let mut output = String::new();
    let mut no_rename = false;
    let mut overwrite = false;
    let mut recursive = true;
    let mut json = false;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--input" => {
                i += 1;
                input = args.get(i).cloned().unwrap_or_default();
            }
            "--output" => {
                i += 1;
                output = args.get(i).cloned().unwrap_or_default();
            }
            "--no-rename" => no_rename = true,
            "--overwrite" => overwrite = true,
            "--recursive" => recursive = true,
            "--no-recursive" => recursive = false,
            "--json" => json = true,
            "-h" | "--help" => return crate::cmd::print_command_help("prepare"),
            _ => {}
        }
        i += 1;
    }
    if input.is_empty() {
        anyhow::bail!("--input required");
    }
    if output.is_empty() {
        output = format!(
            "{}_prepared",
            input.trim_end_matches(|c| c == '/' || c == '\\')
        );
    }
    let scan = scanner::scan_directory(&input, recursive)?;
    let plan = prepare::plan_operations(
        prepare::ScanInput {
            base_dir: scan.base_dir,
            images: scan.images,
            videos: scan.videos,
        },
        &output,
        prepare::Options {
            rename_images: !no_rename,
            rename_videos: !no_rename,
            overwrite,
        },
    )?;
    if json {
        println!(
            r#"{{"event":"start","phase":"prepare","total":{}}}"#,
            plan.len()
        );
    } else {
        println!("计划 {} 个文件,输出到 {}", plan.len(), output);
    }
    let prog = if json {
        None
    } else {
        Some(
            Box::new(|c: usize, t: usize, m: String| println!("[prepare] {}/{}  {}", c, t, m))
                as Box<dyn Fn(usize, usize, String) + Send + Sync>,
        )
    };
    let res = prepare::execute_operations(plan, overwrite, prog)?;
    if json {
        println!(
            r#"{{"event":"done","phase":"prepare","outputDir":{:?},"totalFiles":{}}}"#,
            res.output_dir, res.total_files
        );
    } else {
        println!("完成: {} 个文件 -> {}", res.total_files, res.output_dir);
    }
    Ok(())
}
