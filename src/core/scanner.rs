use lazy_static::lazy_static;
use regex::Regex;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf}; // kept if needed elsewhere; not for exts now

fn image_exts() -> std::collections::HashSet<String> {
    [
        ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif", ".heic", ".heif",
        ".avif",
    ]
    .iter()
    .map(|s| s.to_string())
    .collect()
}
fn video_exts() -> std::collections::HashSet<String> {
    [
        ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".y4m",
    ]
    .iter()
    .map(|s| s.to_string())
    .collect()
}
fn number_re() -> Regex {
    Regex::new(r"\d+|\D+").unwrap()
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct ScanResult {
    #[serde(rename = "baseDir")]
    pub base_dir: String,
    pub images: Vec<String>,
    pub videos: Vec<String>,
    pub others: Vec<String>,
    #[serde(rename = "totalSize")]
    pub total_size: i64,
    pub subdirs: usize,
}

pub fn scan_directory(root: &str, recursive: bool) -> anyhow::Result<ScanResult> {
    let root = Path::new(root).to_string_lossy().replace('\\', "/");
    let root_path = PathBuf::from(&root);
    let mut result = ScanResult {
        base_dir: root.clone(),
        ..Default::default()
    };
    let mut seen_dirs: HashSet<String> = HashSet::new();

    let mut visit = |path: PathBuf, is_dir: bool, size: u64| -> anyhow::Result<()> {
        if is_dir {
            return Ok(());
        }
        result.total_size += size as i64;
        if let Some(parent) = path.parent() {
            let p = parent.to_string_lossy().replace('\\', "/");
            if p != root {
                seen_dirs.insert(p);
            }
        }
        let ext = path
            .extension()
            .and_then(|e| e.to_str())
            .map(|e| format!(".{}", e.to_ascii_lowercase()))
            .unwrap_or_default();
        let pstr = path.to_string_lossy().replace('\\', "/");
        let imgs = image_exts();
        let vids = video_exts();
        if imgs.contains(&ext) {
            result.images.push(pstr);
        } else if vids.contains(&ext) {
            result.videos.push(pstr);
        } else {
            result.others.push(pstr);
        }
        Ok(())
    };

    if recursive {
        for entry in walkdir::WalkDir::new(&root_path)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            let meta = entry.metadata()?;
            visit(
                entry.path().to_path_buf(),
                entry.file_type().is_dir(),
                meta.len(),
            )?;
        }
    } else {
        for e in fs::read_dir(&root_path)? {
            let e = e?;
            let meta = e.metadata()?;
            visit(e.path(), meta.is_dir(), meta.len())?;
        }
    }

    result.subdirs = seen_dirs.len();
    natural_sort(&mut result.images);
    natural_sort(&mut result.videos);
    natural_sort(&mut result.others);
    Ok(result)
}

fn natural_sort(v: &mut [String]) {
    v.sort_by(|a, b| {
        let ba = Path::new(a)
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or(a);
        let bb = Path::new(b)
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or(b);
        natural_less(ba, bb)
    });
}

fn natural_less(a: &str, b: &str) -> std::cmp::Ordering {
    let re = number_re();
    let a_lower = a.to_ascii_lowercase();
    let b_lower = b.to_ascii_lowercase();
    let aa: Vec<&str> = re.find_iter(&a_lower).map(|m| m.as_str()).collect();
    let bb: Vec<&str> = re.find_iter(&b_lower).map(|m| m.as_str()).collect();
    for i in 0..aa.len().min(bb.len()) {
        let ai = aa[i].parse::<i64>();
        let bi = bb[i].parse::<i64>();
        match (ai, bi) {
            (Ok(ai), Ok(bi)) if ai != bi => return ai.cmp(&bi),
            (Ok(_), Ok(_)) => continue,
            _ => {
                if aa[i] != bb[i] {
                    return aa[i].cmp(bb[i]);
                }
            }
        }
    }
    aa.len().cmp(&bb.len())
}

pub fn is_image_like(p: &std::path::Path) -> bool {
    if let Some(ext) = p.extension().and_then(|e| e.to_str()) {
        let e = format!(".{}", ext.to_ascii_lowercase());
        let imgs = image_exts();
        imgs.contains(&e)
    } else {
        false
    }
}

// For tests/CI without walkdir in minimal, but we add dep.
