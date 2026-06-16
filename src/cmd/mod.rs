pub mod all;
pub mod compress;
pub mod prepare;
pub mod scan;
pub mod upload;

use anyhow::Result;

pub const G: &str = "\x1b[32m";
pub const D: &str = "\x1b[2m";
pub const B: &str = "\x1b[1m";
pub const R: &str = "\x1b[0m";

pub const COMMAND_GROUPS: &[(&str, &[&str])] = &[
    ("Core", &["scan", "prepare", "compress", "upload", "all"]),
    ("Utility", &["version", "help"]),
];

pub fn wants_help(args: &[String]) -> bool {
    args.iter().any(|a| a == "-h" || a == "--help")
}

pub fn print_command_help(cmd: &str) -> Result<()> {
    let (usage, desc, body) = command_help_text(cmd);
    println!("{B}imagecompression {G}{cmd}{R} {D}─{R} {desc}");
    println!();
    println!("{B}USAGE:{R}  {G}imagecompression{R} {usage}");
    println!();
    print!("{}", body);
    Ok(())
}

pub fn command_help_text(cmd: &str) -> (&'static str, &'static str, String) {
    match cmd {
        "scan" => (
            "scan --input <dir> [--recursive]",
            "Scan directory for images/videos",
            format!(
                "{B}OPTIONS:{R}\n  {G}--input DIR{R}      {D}Directory to scan (required){R}\n  {G}--recursive{R}     {D}Recurse subdirs (default true){R}\n\n{B}EXAMPLES:{R}\n  imagecompression scan --input ./photos\n",
                G = G, D = D, B = B, R = R
            ),
        ),
        "prepare" => (
            "prepare --input <dir> [--output <dir>] [--no-rename] [--overwrite]",
            "Rename + copy images/videos to target dir",
            format!(
                "{B}OPTIONS:{R}\n  {G}--input DIR{R}     {D}Source (required){R}\n  {G}--output DIR{R}    {D}Target (defaults <input>_prepared){R}\n  {G}--no-rename{R}   {D}Keep original names{R}\n  {G}--overwrite{R}   {D}Allow overwrite / in-place{R}\n\n{B}EXAMPLES:{R}\n  imagecompression prepare --input ./raw --output ./prepared\n",
                G = G, D = D, B = B, R = R
            ),
        ),
        "compress" => (
            "compress --input <dir> [--format avif|webp|jpeg] [--quality N] [--resize-mode MODE --resize-value N] ...",
            "Batch compress images",
            format!(
                "{B}OPTIONS:{R}\n  {G}--input DIR{R}                {D}Source directory (required){R}\n  {G}--output DIR{R}               {D}Target directory (defaults <input>_compressed){R}\n  {G}--format avif|webp|jpeg{R}    {D}Output format{R}\n  {G}--quality N{R}                {D}JPEG/WebP quality or AVIF max quality{R}\n  {G}--resize-mode MODE{R}         {D}none,width,height,percent,long_edge,short_edge,fit,fill,exact{R}\n  {G}--resize-value N{R}           {D}Pixel value or percent, depending on mode{R}\n  {G}--no-keep-aspect-ratio{R}     {D}Only affects width/height modes{R}\n\n{B}EXAMPLES:{R}\n  imagecompression compress --input ./photos --format avif --resize-mode long_edge --resize-value 1920\n",
                G = G, D = D, B = B, R = R
            ),
        ),
        "upload" => ("upload --input <dir> [--config <path>]", "Upload to S3/FTP/SFTP", "Reads ~/.imagecompression/config.json\n".to_string()),
        "all" => (
            "all --input <dir> [--upload] [--resize-mode MODE --resize-value N]",
            "prepare → compress → (upload)",
            "One-shot workflow. Resize options are forwarded to the compress stage.\n".to_string(),
        ),
        _ => ("<command>", "Unknown", "Run imagecompression --help\n".to_string()),
    }
}

pub fn help_run() -> Result<()> {
    println!("{B}imagecompression{R} — image prep, compress (AVIF/WebP/JPEG), upload (S3/FTP/SFTP) TUI+CLI (pikpaktui style)");
    println!();
    println!("{B}USAGE:{R}  imagecompression            {D}# launch TUI (Miller columns, keyboard driven){R}");
    println!("         imagecompression [options] <command> [args]");
    println!();
    println!("{B}COMMANDS:{R}");
    for (grp, cmds) in COMMAND_GROUPS {
        println!("  {B}{}{R}", grp);
        for c in *cmds {
            let (_, d, _) = command_help_text(c);
            println!("    {G}{}{R}  {D}{}{R}", c, d);
        }
    }
    println!();
    println!(
        "Press , in TUI for settings, h for help, q to quit. Use --json for agent-friendly output."
    );
    Ok(())
}
