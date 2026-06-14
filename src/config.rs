use std::net;
use std::path::PathBuf;
use std::str::FromStr;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct AvifConfig {
    #[serde(rename = "min_quality")]
    pub min_quality: i32,
    #[serde(rename = "max_quality")]
    pub max_quality: i32,
    pub speed: i32,
    pub threads: String,
    pub yuv: String,
    pub depth: i32,
    #[serde(rename = "alpha_enabled")]
    pub alpha_enabled: bool,
    #[serde(rename = "alpha_min")]
    pub alpha_min: i32,
    #[serde(rename = "alpha_max")]
    pub alpha_max: i32,
    pub lossless: bool,
    pub progressive: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct WebPJpegConfig {
    pub quality: i32,
    pub lossless: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct S3Config {
    pub endpoint: String,
    pub bucket: String,
    #[serde(rename = "access_key")]
    pub access_key: String,
    #[serde(rename = "secret_key")]
    pub secret_key: String,
    pub region: String,
    pub prefix: String,
    pub domain: String,
    #[serde(rename = "proxy_url", default)]
    pub proxy_url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct FTPConfig {
    pub host: String,
    pub port: i32,
    pub username: String,
    pub password: String,
    #[serde(rename = "remote_dir")]
    pub remote_dir: String,
    #[serde(rename = "base_url")]
    pub base_url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct SFTPConfig {
    pub host: String,
    pub port: i32,
    pub username: String,
    pub password: String,
    #[serde(rename = "key_path")]
    pub key_path: String,
    #[serde(rename = "remote_dir")]
    pub remote_dir: String,
    #[serde(rename = "base_url")]
    pub base_url: String,
    #[serde(rename = "domain_root")]
    pub domain_root: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct ProxyConfig {
    pub enabled: bool,
    pub url: String,
    #[serde(rename = "type")]
    pub r#type: String,
    pub host: String,
    pub port: i32,
    pub username: String,
    pub password: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct CompressConfig {
    pub format: String,
    pub avif: AvifConfig,
    #[serde(rename = "webp_jpeg")]
    pub webp_jpeg: WebPJpegConfig,
    #[serde(rename = "skip_videos")]
    pub skip_videos: bool,
    #[serde(rename = "resize_mode")]
    pub resize_mode: String,
    #[serde(rename = "resize_value")]
    pub resize_value: i32,
    #[serde(rename = "keep_aspect_ratio")]
    pub keep_aspect_ratio: bool,
    pub workers: i32,
    #[serde(rename = "conflict_strategy")]
    pub conflict_strategy: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct UploadConfig {
    pub protocol: String,
    pub s3: S3Config,
    pub ftp: FTPConfig,
    pub sftp: SFTPConfig,
    pub proxy: ProxyConfig,
    #[serde(rename = "custom_path")]
    pub custom_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct PrepareConfig {
    #[serde(rename = "rename_images")]
    pub rename_images: bool,
    #[serde(rename = "rename_videos")]
    pub rename_videos: bool,
    #[serde(rename = "strip_exif")]
    pub strip_exif: bool,
    #[serde(rename = "output_mode")]
    pub output_mode: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(default)]
pub struct Config {
    #[serde(rename = "last_input_dir")]
    pub last_input_dir: String,
    #[serde(rename = "last_output_dir")]
    pub last_output_dir: String,
    pub prepare: PrepareConfig,
    pub compress: CompressConfig,
    pub upload: UploadConfig,
    #[serde(rename = "avifenc_path")]
    pub avifenc_path: String,
    pub language: String,
    pub theme: String,
    // TUI extensions (stored under same json for simplicity; ignored by old Go if present)
    #[serde(rename = "tui", skip_serializing_if = "Option::is_none")]
    pub tui: Option<serde_json::Value>,
}

impl Config {
    pub fn normalize(&mut self) {
        self.avifenc_path = normalize_avifenc_path(&self.avifenc_path);
        self.upload.proxy.normalize();
    }
}

pub fn default_config() -> Config {
    Config {
        prepare: PrepareConfig {
            rename_images: true,
            rename_videos: true,
            strip_exif: true,
            output_mode: "new_directory".to_string(),
        },
        compress: CompressConfig {
            format: "avif".to_string(),
            avif: AvifConfig {
                min_quality: 20,
                max_quality: 40,
                speed: 6,
                threads: "all".to_string(),
                yuv: "420".to_string(),
                depth: 8,
                alpha_min: 20,
                alpha_max: 40,
                ..Default::default()
            },
            webp_jpeg: WebPJpegConfig {
                quality: 80,
                lossless: false,
            },
            skip_videos: true,
            resize_mode: "none".to_string(),
            resize_value: 0,
            keep_aspect_ratio: true,
            workers: 1,
            conflict_strategy: "rename".to_string(),
        },
        upload: UploadConfig {
            protocol: "s3".to_string(),
            ftp: FTPConfig {
                port: 21,
                remote_dir: "/".to_string(),
                ..Default::default()
            },
            sftp: SFTPConfig {
                port: 22,
                remote_dir: "/".to_string(),
                ..Default::default()
            },
            proxy: ProxyConfig {
                url: "socks5://127.0.0.1:7890".to_string(),
                r#type: "socks5".to_string(),
                host: "127.0.0.1".to_string(),
                port: 7890,
                ..Default::default()
            },
            ..Default::default()
        },
        avifenc_path: String::new(),
        language: "zh".to_string(),
        theme: "light".to_string(),
        ..Default::default()
    }
}

pub fn default_path() -> anyhow::Result<PathBuf> {
    let home = dirs::home_dir().ok_or_else(|| anyhow::anyhow!("cannot determine home dir"))?;
    Ok(home.join(".imagecompression").join("config.json"))
}

pub fn load(path: Option<&str>) -> anyhow::Result<Config> {
    let p = if let Some(s) = path {
        PathBuf::from(s)
    } else {
        default_path()?
    };
    let mut cfg = default_config();
    if let Ok(data) = std::fs::read(&p) {
        match serde_json::from_slice::<Config>(&data) {
            Ok(loaded) => cfg = loaded,
            Err(_) => return Ok(default_config()),
        }
    }
    cfg.normalize();
    Ok(cfg)
}

pub fn save(path: Option<&str>, mut cfg: Config) -> anyhow::Result<()> {
    cfg.normalize();
    let p = if let Some(s) = path {
        PathBuf::from(s)
    } else {
        default_path()?
    };
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let data = serde_json::to_vec_pretty(&cfg)?;
    std::fs::write(p, data)?;
    Ok(())
}

fn normalize_avifenc_path(p: &str) -> String {
    let t = p.trim();
    if t.is_empty() {
        return String::new();
    }
    let tl = t.to_ascii_lowercase();
    if tl == "avifenc" || tl == "avifenc.exe" {
        return String::new();
    }
    if !std::path::Path::new(t).is_absolute() && !t.contains('/') && !t.contains('\\') {
        return t.to_string();
    }
    let c = std::path::Path::new(t).to_string_lossy().replace('\\', "/");
    if c.to_ascii_lowercase().ends_with("avifenc.exe") {
        if let Some(dir) = std::path::Path::new(&c).parent() {
            return dir.to_string_lossy().to_string();
        }
    }
    c
}

impl ProxyConfig {
    pub fn normalize(&mut self) {
        if self.r#type.trim().is_empty() {
            self.r#type = "socks5".to_string();
        }
        if self.url.is_empty() {
            return;
        }
        if !self.host.is_empty() && !self.has_default_structured_fields() {
            return;
        }
        if let Ok(parsed) = url::Url::parse(&self.url) {
            if !parsed.scheme().is_empty() {
                self.r#type = parsed.scheme().to_string();
            }
            if let Some(h) = parsed.host_str() {
                self.host = h.to_string();
            }
            if let Some(port) = parsed.port() {
                self.port = port as i32;
            }
            let u = parsed.username();
            if !u.is_empty() {
                self.username = u.to_string();
            }
            if let Some(p) = parsed.password() {
                self.password = p.to_string();
            }
        }
    }

    fn has_default_structured_fields(&self) -> bool {
        self.r#type.eq_ignore_ascii_case("socks5")
            && self.host == "127.0.0.1"
            && self.port == 7890
            && self.username.is_empty()
            && self.password.is_empty()
    }

    pub fn effective_url(&self) -> String {
        if !self.enabled {
            return String::new();
        }
        if self.host.trim().is_empty() {
            return self.url.trim().to_string();
        }
        let scheme = if self.r#type.trim().is_empty() {
            "socks5"
        } else {
            &self.r#type
        };
        let host = if self.port > 0 {
            format!("{}:{}", self.host.trim(), self.port)
        } else {
            self.host.trim().to_string()
        };
        let mut u = url::Url::parse(&format!("{}://{}", scheme, host))
            .unwrap_or_else(|_| url::Url::parse("socks5://127.0.0.1:0").unwrap());
        if !self.username.is_empty() {
            let _ = u.set_username(&self.username);
            let _ = u.set_password(Some(&self.password));
        }
        u.to_string()
    }
}

// For tests and compat we expose a from_url style normalizer (used in Go proxy normalize)
pub fn parse_proxy_from_url(raw: &str) -> Option<(String, String, i32, String, String)> {
    if raw.trim().is_empty() {
        return None;
    }
    if let Ok(p) = url::Url::parse(raw) {
        let scheme = p.scheme().to_string();
        let host = p.host_str().unwrap_or("").to_string();
        let port = p.port().unwrap_or(0) as i32;
        let user = p.username().to_string();
        let pass = p.password().unwrap_or("").to_string();
        return Some((scheme, host, port, user, pass));
    }
    None
}

// 给 CLI all 使用的便捷函数
pub fn effective_for_upload(upload: UploadConfig, source: &str) -> UploadConfig {
    crate::core::upload::effective_config(upload, source)
}
