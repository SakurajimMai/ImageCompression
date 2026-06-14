use std::fs::{self, File};
use std::io;
use std::path::Path;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ScanInput {
    #[serde(rename = "BaseDir")]
    pub base_dir: String,
    #[serde(rename = "Images")]
    pub images: Vec<String>,
    #[serde(rename = "Videos")]
    pub videos: Vec<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Options {
    #[serde(rename = "RenameImages")]
    pub rename_images: bool,
    #[serde(rename = "RenameVideos")]
    pub rename_videos: bool,
    #[serde(rename = "Overwrite")]
    pub overwrite: bool,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Operation {
    pub source: String,
    pub destination: String,
    pub kind: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct PrepareResult {
    #[serde(rename = "renamedImages")]
    pub renamed_images: i32,
    #[serde(rename = "renamedVideos")]
    pub renamed_videos: i32,
    #[serde(rename = "totalFiles")]
    pub total_files: i32,
    #[serde(rename = "outputDir")]
    pub output_dir: String,
}

pub type ProgressFunc = Option<Box<dyn Fn(usize, usize, String) + Send + Sync>>;

pub fn plan_operations(
    scan: ScanInput,
    output_dir: &str,
    opts: Options,
) -> anyhow::Result<Vec<Operation>> {
    let base = Path::new(&scan.base_dir)
        .to_string_lossy()
        .replace('\\', "/");
    let mut ops = Vec::new();
    ops.extend(plan_kind(
        &base,
        output_dir,
        &scan.images,
        "image",
        opts.rename_images,
        opts.overwrite,
    )?);
    ops.extend(plan_kind(
        &base,
        output_dir,
        &scan.videos,
        "video",
        opts.rename_videos,
        opts.overwrite,
    )?);
    Ok(ops)
}

fn plan_kind(
    base: &str,
    output_dir: &str,
    files: &[String],
    kind: &str,
    rename: bool,
    overwrite: bool,
) -> anyhow::Result<Vec<Operation>> {
    use std::collections::BTreeMap;
    let mut groups: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for f in files {
        let p = Path::new(f);
        let dir = p
            .parent()
            .map(|d| d.to_string_lossy().replace('\\', "/"))
            .unwrap_or_else(|| ".".to_string());
        groups.entry(dir).or_default().push(f.clone());
    }
    let mut parents: Vec<_> = groups.keys().cloned().collect();
    parents.sort();
    let mut ops = Vec::new();
    for parent in parents {
        let rel = if parent == base {
            ".".to_string()
        } else {
            // compute rel
            let base_p = Path::new(base);
            let par_p = Path::new(&parent);
            match par_p.strip_prefix(base_p) {
                Ok(r) => r.to_string_lossy().replace('\\', "/"),
                _ => parent.clone(),
            }
        };
        let mut fs = groups.get(&parent).unwrap().clone();
        fs.sort();
        for (i, file) in fs.into_iter().enumerate() {
            let name = if rename {
                let ext = Path::new(&file)
                    .extension()
                    .and_then(|e| e.to_str())
                    .unwrap_or("");
                let ext = format!(".{}", ext.to_ascii_lowercase());
                if kind == "video" {
                    format!("video{:03}{}", i + 1, ext)
                } else {
                    format!("{:04}{}", i + 1, ext)
                }
            } else {
                Path::new(&file)
                    .file_name()
                    .unwrap()
                    .to_string_lossy()
                    .to_string()
            };
            let dest_dir = if overwrite {
                parent.clone()
            } else if rel == "." || rel.is_empty() {
                output_dir.to_string()
            } else {
                format!(
                    "{}/{}",
                    output_dir.trim_end_matches('/'),
                    rel.trim_start_matches('/')
                )
            };
            let dest = format!("{}/{}", dest_dir.trim_end_matches('/'), name);
            ops.push(Operation {
                source: file,
                destination: dest.replace('\\', "/"),
                kind: kind.to_string(),
            });
        }
    }
    Ok(ops)
}

pub fn execute_operations(
    ops: Vec<Operation>,
    overwrite: bool,
    progress: ProgressFunc,
) -> anyhow::Result<PrepareResult> {
    let mut res = PrepareResult {
        total_files: ops.len() as i32,
        ..Default::default()
    };
    if let Some(first) = ops.first() {
        if let Some(d) = Path::new(&first.destination).parent() {
            res.output_dir = d.to_string_lossy().to_string();
        }
    }
    for (idx, op) in ops.into_iter().enumerate() {
        if let Some(pf) = &progress {
            pf(
                idx + 1,
                res.total_files as usize,
                format!(
                    "{} -> {}",
                    Path::new(&op.source).file_name().unwrap().to_string_lossy(),
                    Path::new(&op.destination)
                        .file_name()
                        .unwrap()
                        .to_string_lossy()
                ),
            );
        }
        if !overwrite {
            if Path::new(&op.destination).exists() {
                return Err(anyhow::anyhow!(
                    "destination already exists: {}",
                    op.destination
                ));
            }
        }
        if let Some(parent) = Path::new(&op.destination).parent() {
            fs::create_dir_all(parent)?;
        }
        fs::copy(&op.source, &op.destination)?;
        match op.kind.as_str() {
            "image" => res.renamed_images += 1,
            "video" => res.renamed_videos += 1,
            _ => {}
        }
    }
    Ok(res)
}
