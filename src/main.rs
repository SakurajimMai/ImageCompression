mod cmd;
mod config;
mod core;
mod theme;
mod tui;

use anyhow::Result;
use std::env;
use std::process::exit;

fn main() {
    if let Err(e) = entry() {
        eprintln!("Error: {e:#}");
        exit(1);
    }
}

fn entry() -> Result<()> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() {
        // Launch TUI like pikpaktui (no args = interactive TUI)
        return tui::run();
    }
    if args.len() >= 2
        && cmd::wants_help(&args[1..])
        && !matches!(
            args[0].as_str(),
            "--help" | "-h" | "help" | "--version" | "-V"
        )
    {
        return cmd::print_command_help(&args[0]);
    }
    match args[0].as_str() {
        "--version" | "-V" | "version" => {
            println!("imagecompression {}", env!("CARGO_PKG_VERSION"));
            Ok(())
        }
        "--help" | "-h" | "help" => cmd::help_run(),
        "scan" => cmd::scan::run(&args[1..]),
        "prepare" => cmd::prepare::run(&args[1..]),
        "compress" => cmd::compress::run(&args[1..]),
        "upload" => cmd::upload::run(&args[1..]),
        "all" => cmd::all::run(&args[1..]),
        other => Err(anyhow::anyhow!(
            "unknown command: {other}\nRun `imagecompression --help` for usage."
        )),
    }
}
