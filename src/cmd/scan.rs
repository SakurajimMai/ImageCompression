use crate::cmd::{B, D, G, R};
use crate::core::scanner;
use anyhow::Result;

pub fn run(args: &[String]) -> Result<()> {
    let mut input = String::new();
    let mut recursive = true;
    let mut json = false;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--input" => {
                i += 1;
                if i < args.len() {
                    input = args[i].clone();
                }
            }
            "--recursive" => recursive = true,
            "--no-recursive" => recursive = false,
            "--json" => json = true,
            "-h" | "--help" => return crate::cmd::print_command_help("scan"),
            _ => {}
        }
        i += 1;
    }
    if input.is_empty() {
        anyhow::bail!("--input required\n\nRun `imagecompression scan --help`");
    }
    let res = scanner::scan_directory(&input, recursive)?;
    if json {
        println!("{}", serde_json::to_string_pretty(&res)?);
    } else {
        println!("{B}目录:{R} {}", res.base_dir);
        println!("图片: {}", res.images.len());
        println!("视频: {}", res.videos.len());
        println!("其他: {}", res.others.len());
        println!("子目录: {}", res.subdirs);
        println!("总体积: {} bytes", res.total_size);
    }
    Ok(())
}
