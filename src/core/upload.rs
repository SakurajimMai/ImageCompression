//! Upload 模块 - 完整 port 原 Go 逻辑。
//! Uploader trait + EffectiveConfig + S3/FTP/SFTP + 代理 (socks5 + HTTP CONNECT 精确 port)。

use std::fs;
use std::io::{self, BufRead, BufReader, Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::path::Path;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};

use crate::config::{self, UploadConfig};

use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};

type HmacSha256 = Hmac<Sha256>;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Options {
    pub recursive: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct UploadResult {
    #[serde(rename = "totalFiles")]
    pub total_files: i32,
    #[serde(rename = "uploadedFiles")]
    pub uploaded_files: i32,
    #[serde(rename = "failedFiles")]
    pub failed_files: i32,
    pub urls: Vec<String>,
    pub errors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ProgressEvent {
    pub current: i32,
    pub total: i32,
    pub message: String,
    pub url: Option<String>,
    pub error: Option<String>,
    pub start: Option<bool>,
    pub done: Option<bool>,
    pub uploaded: i32,
    pub failed: i32,
    #[serde(rename = "sourceDir")]
    pub source_dir: String,
}

pub type ProgressFunc = Option<Box<dyn Fn(ProgressEvent) + Send + Sync>>;

pub trait Uploader: Send + Sync {
    fn connect(&mut self) -> Result<()>;
    fn upload_file(&mut self, local_path: &str, remote_name: &str) -> Result<String>;
    fn disconnect(&mut self);
}

pub fn build_remote_name(input_dir: &str, file: &str, recursive: bool) -> Result<String> {
    let p = Path::new(file);
    if recursive {
        let rel = p.strip_prefix(input_dir).unwrap_or(p);
        Ok(rel.to_string_lossy().replace('\\', "/"))
    } else {
        Ok(p.file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_default())
    }
}

pub fn collect_files(dir: &str, recursive: bool) -> Result<Vec<String>> {
    let mut out = Vec::new();
    let root = Path::new(dir);
    if recursive {
        for e in walkdir::WalkDir::new(root) {
            let e = e?;
            if e.file_type().is_file() {
                out.push(e.path().to_string_lossy().to_string());
            }
        }
    } else {
        for e in fs::read_dir(root)? {
            let e = e?;
            let p = e.path();
            if p.is_file() {
                out.push(p.to_string_lossy().to_string());
            }
        }
    }
    out.sort();
    Ok(out)
}

// EffectiveConfig 精确 port
pub fn effective_config(mut cfg: UploadConfig, source_dir: &str) -> UploadConfig {
    let custom = cfg.custom_path.trim().trim_matches('/').to_string();
    if !custom.is_empty() {
        return apply_subpath(cfg, &custom);
    }
    let name = Path::new(source_dir)
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("")
        .to_string();
    if name.is_empty() || name == "." || name == "/" {
        return cfg;
    }
    let proto = cfg.protocol.to_ascii_lowercase();
    match proto.as_str() {
        "ftp" => {
            if cfg.ftp.remote_dir.trim_matches('/').is_empty() {
                cfg.ftp.remote_dir = format!("/{}", name);
            }
        }
        "sftp" => {
            if cfg.sftp.remote_dir.trim_matches('/').is_empty() {
                cfg.sftp.remote_dir = format!("/{}", name);
            }
        }
        _ => {
            if cfg.s3.prefix.trim_matches('/').is_empty() {
                cfg.s3.prefix = name;
            }
        }
    }
    cfg
}

fn apply_subpath(mut cfg: UploadConfig, sub: &str) -> UploadConfig {
    let proto = cfg.protocol.to_ascii_lowercase();
    match proto.as_str() {
        "ftp" => {
            let base = cfg.ftp.remote_dir.trim_end_matches('/');
            cfg.ftp.remote_dir = if base.is_empty() || base == "/" {
                format!("/{}", sub)
            } else {
                format!("{}/{}", base, sub)
            };
        }
        "sftp" => {
            let base = cfg.sftp.remote_dir.trim_end_matches('/');
            cfg.sftp.remote_dir = if base.is_empty() || base == "/" {
                format!("/{}", sub)
            } else {
                format!("{}/{}", base, sub)
            };
        }
        _ => {
            let base = cfg.s3.prefix.trim_end_matches('/');
            cfg.s3.prefix = if base.is_empty() {
                sub.to_string()
            } else {
                format!("{}/{}", base, sub)
            };
        }
    }
    cfg
}

pub fn upload_directory(
    uploader: &mut dyn Uploader,
    input_dir: &str,
    options: Options,
    progress: ProgressFunc,
) -> Result<UploadResult> {
    let files = collect_files(input_dir, options.recursive)?;
    let mut res = UploadResult {
        total_files: files.len() as i32,
        ..Default::default()
    };

    if let Some(p) = &progress {
        p(ProgressEvent {
            start: Some(true),
            total: res.total_files,
            message: format!("准备上传 {} 个文件", res.total_files),
            source_dir: input_dir.to_string(),
            ..Default::default()
        });
    }

    if let Err(e) = uploader.connect() {
        if let Some(p) = &progress {
            p(ProgressEvent {
                done: Some(true),
                total: res.total_files,
                error: Some(e.to_string()),
                source_dir: input_dir.to_string(),
                ..Default::default()
            });
        }
        return Err(e);
    }

    for (i, f) in files.iter().enumerate() {
        let remote = build_remote_name(input_dir, f, options.recursive)?;
        let msg = Path::new(f)
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();

        if let Some(p) = &progress {
            p(ProgressEvent {
                current: (i + 1) as i32,
                total: res.total_files,
                message: msg.clone(),
                source_dir: input_dir.to_string(),
                ..Default::default()
            });
        }

        match uploader.upload_file(f, &remote) {
            Ok(url) => {
                res.urls.push(url.clone());
                res.uploaded_files += 1;
                if let Some(p) = &progress {
                    p(ProgressEvent {
                        current: (i + 1) as i32,
                        total: res.total_files,
                        message: msg,
                        url: Some(url),
                        source_dir: input_dir.to_string(),
                        ..Default::default()
                    });
                }
            }
            Err(e) => {
                res.failed_files += 1;
                res.errors.push(format!("{}: {}", f, e));
                if let Some(p) = &progress {
                    p(ProgressEvent {
                        current: (i + 1) as i32,
                        total: res.total_files,
                        message: msg,
                        error: Some(e.to_string()),
                        source_dir: input_dir.to_string(),
                        ..Default::default()
                    });
                }
            }
        }
    }

    uploader.disconnect();

    if let Some(p) = &progress {
        p(ProgressEvent {
            done: Some(true),
            total: res.total_files,
            uploaded: res.uploaded_files,
            failed: res.failed_files,
            source_dir: input_dir.to_string(),
            ..Default::default()
        });
    }

    Ok(res)
}

// ============ 协议实现 (简化但功能完整版) ============

pub struct S3Uploader {
    cfg: config::S3Config, // 注意：使用 config 里的结构 (需确保字段公开)
    client: Option<reqwest::blocking::Client>,
}

impl S3Uploader {
    pub fn new(cfg: config::S3Config) -> Self {
        Self { cfg, client: None }
    }

    pub fn canonical_uri_for_key(&self, key: &str) -> String {
        canonical_uri_for_s3_put(&self.cfg.endpoint, &self.cfg.bucket, key)
    }

    /// 拼出最终 PUT 目标 URL。空 endpoint 时回退到 AWS 官方域名。
    fn put_url(&self, key: &str) -> String {
        if self.cfg.endpoint.is_empty() {
            format!("https://{}.s3.amazonaws.com/{}", self.cfg.bucket, key)
        } else {
            format!(
                "{}/{}/{}",
                self.cfg.endpoint.trim_end_matches('/'),
                self.cfg.bucket,
                key
            )
        }
    }

    /// 提取 host 给 SigV4 签名用。endpoint 为空时按 AWS 默认虚拟主机处理。
    fn host_header(&self) -> String {
        if self.cfg.endpoint.is_empty() {
            format!("{}.s3.amazonaws.com", self.cfg.bucket)
        } else {
            // 兼容 "https://host[:port][/...]" 与 "host[:port]" 两种写法
            let raw = self.cfg.endpoint.trim();
            let without_scheme = if let Some(idx) = raw.find("://") {
                &raw[idx + 3..]
            } else {
                raw
            };
            without_scheme
                .split('/')
                .next()
                .unwrap_or("")
                .trim()
                .to_string()
        }
    }
}

impl Uploader for S3Uploader {
    fn connect(&mut self) -> Result<()> {
        let mut builder = reqwest::blocking::Client::builder().timeout(Duration::from_secs(120));
        if let Some(proxy_url) = effective_proxy(&self.cfg.proxy_url) {
            if !proxy_url.is_empty() {
                builder = builder.proxy(reqwest::Proxy::all(&proxy_url)?);
            }
        }
        self.client = Some(builder.build()?);
        Ok(())
    }

    fn upload_file(&mut self, local: &str, remote_name: &str) -> Result<String> {
        let c = self
            .client
            .as_ref()
            .ok_or_else(|| anyhow!("not connected"))?;
        let data = fs::read(local)?;
        let key = format!(
            "{}/{}",
            self.cfg.prefix.trim_matches('/'),
            remote_name.trim_start_matches('/')
        )
        .trim_matches('/')
        .to_string();

        let url = self.put_url(&key);
        let host = self.host_header();
        let region = if self.cfg.region.is_empty() {
            "us-east-1".to_string()
        } else {
            self.cfg.region.clone()
        };

        // 计算 SigV4 签名
        let signed = sign_s3_put(
            "PUT",
            &url,
            &self.cfg.endpoint,
            &self.cfg.bucket,
            &key,
            &host,
            &self.cfg.access_key,
            &self.cfg.secret_key,
            &region,
            &data,
        )?;

        let mut req = c.put(url.as_str()).body(data);
        for (name, value) in &signed.headers {
            req = req.header(name.as_str(), value.as_str());
        }

        let resp = req.send()?;
        if !resp.status().is_success() {
            let status = resp.status();
            let body = resp.text().unwrap_or_default();
            return Err(anyhow!("S3 PUT 失败 {}: {}", status, body));
        }

        if !self.cfg.domain.is_empty() {
            Ok(format!("{}/{}", self.cfg.domain.trim_end_matches('/'), key))
        } else {
            Ok(url)
        }
    }

    fn disconnect(&mut self) {}
}

// ---------- AWS SigV4 (PUT) ----------

struct SignedRequest {
    /// 注入到 reqwest 的所有 header(包含 host/content-type/x-amz-content-sha256/x-amz-date/Authorization)
    headers: Vec<(String, String)>,
}

fn now_iso_basic() -> (String, String) {
    // 返回 (amz_date: YYYYMMDDTHHMMSSZ, date_stamp: YYYYMMDD)
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0);
    let mut t = secs;
    let sec = (t % 60) as u32;
    t /= 60;
    let min = (t % 60) as u32;
    t /= 60;
    let hour = (t % 24) as u32;
    t /= 24;
    // 1970-01-01 起的"自纪元天数"再换算成 y/m/d,简化版够用
    let mut days = t;
    let mut year: i64 = 1970;
    loop {
        let leap = is_leap(year);
        let yd = if leap { 366 } else { 365 };
        if days < yd {
            break;
        }
        days -= yd;
        year += 1;
    }
    let leap = is_leap(year);
    let mdays = if leap {
        [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    } else {
        [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    };
    let mut month = 0usize;
    for (i, dm) in mdays.iter().enumerate() {
        if days < *dm {
            month = i;
            break;
        }
        days -= *dm;
    }
    let day = days + 1;
    let amz_date = format!(
        "{:04}{:02}{:02}T{:02}{:02}{:02}Z",
        year,
        month + 1,
        day,
        hour,
        min,
        sec
    );
    let date_stamp = format!("{:04}{:02}{:02}", year, month + 1, day);
    (amz_date, date_stamp)
}

fn is_leap(y: i64) -> bool {
    (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0)
}

fn hmac_sha256(key: &[u8], data: &[u8]) -> Vec<u8> {
    let mut mac = HmacSha256::new_from_slice(key).expect("HMAC accepts any key length");
    mac.update(data);
    mac.finalize().into_bytes().to_vec()
}

fn sha256_hex(data: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(data);
    hex::encode(h.finalize())
}

pub fn canonical_uri_for_s3_put(endpoint: &str, bucket: &str, key: &str) -> String {
    let encoded_key = uri_encode_path(key.trim_start_matches('/'), false);
    if endpoint.trim().is_empty() {
        if encoded_key.is_empty() {
            "/".to_string()
        } else {
            format!("/{}", encoded_key)
        }
    } else {
        let encoded_bucket = uri_encode_path(bucket.trim_matches('/'), false);
        match (encoded_bucket.is_empty(), encoded_key.is_empty()) {
            (true, true) => "/".to_string(),
            (true, false) => format!("/{}", encoded_key),
            (false, true) => format!("/{}", encoded_bucket),
            (false, false) => format!("/{}/{}", encoded_bucket, encoded_key),
        }
    }
}

/// 严格按 AWS SigV4 spec 计算 PUT 签名并返回所有需要附加的 header。
/// `url` 必须是完整 URL(`https://host/bucket/key`),`key` 是对象 key。
fn sign_s3_put(
    method: &str,
    url: &str,
    endpoint: &str,
    bucket: &str,
    key: &str,
    host: &str,
    access_key: &str,
    secret_key: &str,
    region: &str,
    body: &[u8],
) -> Result<SignedRequest> {
    if access_key.is_empty() || secret_key.is_empty() {
        return Err(anyhow!("S3 上传缺少 access_key / secret_key"));
    }
    let (amz_date, date_stamp) = now_iso_basic();
    let payload_hash = sha256_hex(body);

    // 1. canonical request
    let canonical_uri = canonical_uri_for_s3_put(endpoint, bucket, key);
    let canonical_query = ""; // PUT 不带 query
    let signed_headers_list = ["content-type", "host", "x-amz-content-sha256", "x-amz-date"];
    let mut canonical_headers = String::new();
    canonical_headers.push_str("content-type:application/octet-stream\n");
    canonical_headers.push_str(&format!("host:{}\n", host));
    canonical_headers.push_str(&format!("x-amz-content-sha256:{}\n", payload_hash));
    canonical_headers.push_str(&format!("x-amz-date:{}\n", amz_date));
    let signed_headers = signed_headers_list.join(";");
    let canonical_request = format!(
        "{}\n{}\n{}\n{}\n{}\n{}",
        method, canonical_uri, canonical_query, canonical_headers, signed_headers, payload_hash
    );
    let hashed_canonical = sha256_hex(canonical_request.as_bytes());

    // 2. string to sign
    let credential_scope = format!("{}/{}/s3/aws4_request", date_stamp, region);
    let string_to_sign = format!(
        "AWS4-HMAC-SHA256\n{}\n{}\n{}",
        amz_date, credential_scope, hashed_canonical
    );

    // 3. signing key
    let k_date = hmac_sha256(
        format!("AWS4{}", secret_key).as_bytes(),
        date_stamp.as_bytes(),
    );
    let k_region = hmac_sha256(&k_date, region.as_bytes());
    let k_service = hmac_sha256(&k_region, b"s3");
    let k_signing = hmac_sha256(&k_service, b"aws4_request");
    let signature = hex::encode(hmac_sha256(&k_signing, string_to_sign.as_bytes()));

    // 4. Authorization header
    let auth = format!(
        "AWS4-HMAC-SHA256 Credential={}/{}, SignedHeaders={}, Signature={}",
        access_key, credential_scope, signed_headers, signature
    );

    let headers = vec![
        (
            "content-type".to_string(),
            "application/octet-stream".to_string(),
        ),
        ("host".to_string(), host.to_string()),
        ("x-amz-content-sha256".to_string(), payload_hash),
        ("x-amz-date".to_string(), amz_date),
        ("Authorization".to_string(), auth),
    ];

    // 避免编译期未用警告(url 用来给调用方排错时定位目标)
    let _ = url;
    Ok(SignedRequest { headers })
}

/// 极简版 S3 path 编码(只做必要字符转义,够覆盖常规目录+文件名)
fn uri_encode_path(s: &str, encode_slash: bool) -> String {
    let mut out = String::with_capacity(s.len());
    for b in s.bytes() {
        let c = b as char;
        let unreserved = c.is_ascii_alphanumeric() || matches!(c, '-' | '_' | '.' | '~');
        if unreserved {
            out.push(c);
        } else if c == '/' && !encode_slash {
            out.push('/');
        } else {
            out.push_str(&format!("%{:02X}", b));
        }
    }
    out
}

// FTP 简化 (使用 suppaftp)
pub struct FtpUploader {
    cfg: config::FTPConfig,
    proxy_url: String,
    client: Option<suppaftp::FtpStream>,
}

impl FtpUploader {
    pub fn new(cfg: config::FTPConfig, proxy_url: String) -> Self {
        Self {
            cfg,
            proxy_url,
            client: None,
        }
    }

    pub fn proxy_url(&self) -> Option<&str> {
        if self.proxy_url.is_empty() {
            None
        } else {
            Some(&self.proxy_url)
        }
    }
}

impl Uploader for FtpUploader {
    fn connect(&mut self) -> Result<()> {
        let addr = format!("{}:{}", self.cfg.host, self.cfg.port);
        let mut stream = if let Some(proxy_url) = self.proxy_url() {
            let dialer = new_proxy_dialer(proxy_url)?;
            let control = dialer(&addr)?;
            suppaftp::FtpStream::connect_with_stream(control)?.passive_stream_builder(
                move |passive_addr| {
                    let target = passive_addr.to_string();
                    dialer(&target).map_err(|e| {
                        suppaftp::FtpError::ConnectionError(std::io::Error::new(
                            std::io::ErrorKind::Other,
                            e.to_string(),
                        ))
                    })
                },
            )
        } else {
            suppaftp::FtpStream::connect(addr)?
        };
        stream.login(&self.cfg.username, &self.cfg.password)?;
        if !self.cfg.remote_dir.is_empty() {
            let _ = stream.mkdir(&self.cfg.remote_dir);
            let _ = stream.cwd(&self.cfg.remote_dir);
        }
        self.client = Some(stream);
        Ok(())
    }

    fn upload_file(&mut self, local: &str, remote_name: &str) -> Result<String> {
        let c = self
            .client
            .as_mut()
            .ok_or_else(|| anyhow!("not connected"))?;
        let data = fs::read(local)?;
        c.put_file(remote_name, &mut std::io::Cursor::new(data))?;
        Ok(format!(
            "{}/{}",
            self.cfg.base_url.trim_end_matches('/'),
            remote_name.trim_start_matches('/')
        ))
    }

    fn disconnect(&mut self) {
        if let Some(mut c) = self.client.take() {
            let _ = c.quit();
        }
    }
}

// SFTP 简化 (ssh2) — 仅在 feature = "sftp" 时编译
#[cfg(feature = "sftp")]
pub struct SftpUploader {
    cfg: config::SFTPConfig,
    proxy_url: String,
    session: Option<ssh2::Session>,
}

#[cfg(feature = "sftp")]
impl SftpUploader {
    pub fn new(cfg: config::SFTPConfig, proxy_url: String) -> Self {
        Self {
            cfg,
            proxy_url,
            session: None,
        }
    }
}

#[cfg(feature = "sftp")]
impl Uploader for SftpUploader {
    fn connect(&mut self) -> Result<()> {
        let addr = format!("{}:{}", self.cfg.host, self.cfg.port);
        let tcp = if let Some(proxy_url) = effective_proxy(&self.proxy_url) {
            let dialer = new_proxy_dialer(&proxy_url)?;
            dialer(&addr)?
        } else {
            TcpStream::connect_timeout(
                &addr.to_socket_addrs()?.next().unwrap(),
                Duration::from_secs(15),
            )?
        };
        let mut sess = ssh2::Session::new()?;
        sess.set_tcp_stream(tcp);
        sess.handshake()?;
        if !self.cfg.key_path.is_empty() {
            sess.userauth_pubkey_file(
                &self.cfg.username,
                None,
                Path::new(&self.cfg.key_path),
                None,
            )?;
        } else {
            sess.userauth_password(&self.cfg.username, &self.cfg.password)?;
        }
        self.session = Some(sess);
        Ok(())
    }

    fn upload_file(&mut self, local: &str, remote_name: &str) -> Result<String> {
        let sess = self
            .session
            .as_ref()
            .ok_or_else(|| anyhow!("not connected"))?;
        let sftp = sess.sftp()?;
        let mut remote_file = sftp.create(Path::new(remote_name))?;
        let mut f = fs::File::open(local)?;
        io::copy(&mut f, &mut remote_file)?;
        let url = if !self.cfg.base_url.is_empty() {
            format!(
                "{}/{}",
                self.cfg.base_url.trim_end_matches('/'),
                remote_name.trim_start_matches('/')
            )
        } else {
            remote_name.to_string()
        };
        Ok(url)
    }

    fn disconnect(&mut self) {
        self.session = None;
    }
}

fn effective_proxy(p: &str) -> Option<String> {
    if p.trim().is_empty() {
        None
    } else {
        Some(p.to_string())
    }
}

// 构建 uploader (从 config)
pub fn build_uploader(cfg: UploadConfig) -> Box<dyn Uploader> {
    let proxy = cfg.proxy.effective_url();
    match cfg.protocol.to_ascii_lowercase().as_str() {
        "ftp" => {
            let c = cfg.ftp.clone();
            // proxy 注入略 (suppaftp 代理支持有限)
            Box::new(FtpUploader::new(c, proxy))
        }
        "sftp" => {
            #[cfg(feature = "sftp")]
            {
                Box::new(SftpUploader::new(cfg.sftp.clone(), proxy))
            }
            #[cfg(not(feature = "sftp"))]
            {
                let _ = proxy;
                Box::new(UnsupportedUploader {
                    name: "sftp",
                    reason:
                        "该二进制未启用 sftp feature。请用 `cargo build --features sftp` 重新编译",
                })
            }
        }
        _ => {
            let mut s = cfg.s3.clone();
            s.proxy_url = proxy;
            Box::new(S3Uploader::new(s))
        }
    }
}

/// 占位 uploader:对未实现的协议返回明确错误,而不是直接 panic。
pub struct UnsupportedUploader {
    name: &'static str,
    reason: &'static str,
}

impl Uploader for UnsupportedUploader {
    fn connect(&mut self) -> Result<()> {
        Err(anyhow!("{} 上传未启用:{}", self.name, self.reason))
    }
    fn upload_file(&mut self, _local: &str, _remote: &str) -> Result<String> {
        Err(anyhow!("{} 上传未启用:{}", self.name, self.reason))
    }
    fn disconnect(&mut self) {}
}

// 简单 proxy 支持辅助 (CONNECT 实现可在此扩展)
pub fn new_proxy_dialer(proxy_url: &str) -> Result<impl Fn(&str) -> Result<TcpStream>> {
    let proxy = parse_proxy_url(proxy_url)?;
    Ok(move |target: &str| {
        if proxy.scheme.starts_with("socks5") {
            let target = parse_host_port(target)?;
            let target = socks::TargetAddr::Domain(target.0, target.1);
            let stream = if let Some((username, password)) = &proxy.auth {
                socks::Socks5Stream::connect_with_password(&proxy.addr, target, username, password)?
            } else {
                socks::Socks5Stream::connect(&proxy.addr, target)?
            };
            Ok(stream.into_inner())
        } else {
            let mut stream = TcpStream::connect(&proxy.addr)?;
            let req = format!("CONNECT {} HTTP/1.1\r\nHost: {}\r\n\r\n", target, target);
            stream.write_all(req.as_bytes())?;
            let mut reader = BufReader::new(&mut stream);
            let mut status = String::new();
            reader.read_line(&mut status)?;
            if !status.contains("200") {
                return Err(anyhow!("CONNECT failed: {}", status));
            }
            Ok(stream)
        }
    })
}

#[derive(Clone)]
struct ProxyEndpoint {
    scheme: String,
    addr: String,
    auth: Option<(String, String)>,
}

fn parse_proxy_url(raw: &str) -> Result<ProxyEndpoint> {
    let parsed = url::Url::parse(raw)?;
    let host = parsed
        .host_str()
        .ok_or_else(|| anyhow!("proxy url missing host"))?;
    let port = parsed
        .port_or_known_default()
        .ok_or_else(|| anyhow!("proxy url missing port"))?;
    let auth = if parsed.username().is_empty() {
        None
    } else {
        Some((
            parsed.username().to_string(),
            parsed.password().unwrap_or("").to_string(),
        ))
    };
    Ok(ProxyEndpoint {
        scheme: parsed.scheme().to_ascii_lowercase(),
        addr: format!("{}:{}", host, port),
        auth,
    })
}

fn parse_host_port(target: &str) -> Result<(String, u16)> {
    let parsed = url::Url::parse(&format!("tcp://{}", target))?;
    let host = parsed
        .host_str()
        .ok_or_else(|| anyhow!("target missing host"))?
        .to_string();
    let port = parsed
        .port()
        .ok_or_else(|| anyhow!("target missing port"))?;
    Ok((host, port))
}
