use super::upload::{canonical_uri_for_s3_put, collect_files, FtpUploader, S3Uploader};
use crate::config::{FTPConfig, ProxyConfig, S3Config, UploadConfig};

#[test]
fn collect_files_returns_error_for_missing_non_recursive_input() {
    let dir = tempfile::tempdir().unwrap();
    let missing = dir.path().join("missing");

    let err = collect_files(missing.to_str().unwrap(), false).unwrap_err();

    assert!(
        err.to_string().contains("missing"),
        "unexpected error: {err:#}"
    );
}

#[test]
fn collect_files_returns_error_for_missing_recursive_input() {
    let dir = tempfile::tempdir().unwrap();
    let missing = dir.path().join("missing");

    let err = collect_files(missing.to_str().unwrap(), true).unwrap_err();

    assert!(
        err.to_string().contains("missing"),
        "unexpected error: {err:#}"
    );
}

#[test]
fn custom_s3_endpoint_canonical_uri_includes_bucket() {
    let uri = canonical_uri_for_s3_put(
        "https://example.r2.cloudflarestorage.com",
        "bucket-name",
        "prefix/image 01.avif",
    );

    assert_eq!(uri, "/bucket-name/prefix/image%2001.avif");
}

#[test]
fn aws_s3_endpoint_canonical_uri_keeps_virtual_host_style_key_only() {
    let uri = canonical_uri_for_s3_put("", "bucket-name", "prefix/image 01.avif");

    assert_eq!(uri, "/prefix/image%2001.avif");
}

#[test]
fn ftp_uploader_retains_effective_proxy() {
    let mut cfg = UploadConfig {
        protocol: "ftp".to_string(),
        ftp: FTPConfig {
            host: "ftp.example.test".to_string(),
            port: 21,
            username: "user".to_string(),
            password: "pass".to_string(),
            remote_dir: "/".to_string(),
            base_url: "https://cdn.example.test".to_string(),
        },
        proxy: ProxyConfig {
            enabled: true,
            r#type: "socks5".to_string(),
            host: "127.0.0.1".to_string(),
            port: 7890,
            ..Default::default()
        },
        ..Default::default()
    };
    cfg.proxy.normalize();

    let uploader = FtpUploader::new(cfg.ftp, cfg.proxy.effective_url());

    assert_eq!(uploader.proxy_url(), Some("socks5://127.0.0.1:7890/"));
}

#[test]
fn s3_uploader_uses_custom_endpoint_path_style_canonical_uri() {
    let uploader = S3Uploader::new(S3Config {
        endpoint: "https://example.r2.cloudflarestorage.com".to_string(),
        bucket: "bucket-name".to_string(),
        prefix: "prefix".to_string(),
        access_key: "access".to_string(),
        secret_key: "secret".to_string(),
        region: "auto".to_string(),
        ..Default::default()
    });

    assert_eq!(
        uploader.canonical_uri_for_key("prefix/image.avif"),
        "/bucket-name/prefix/image.avif"
    );
}
