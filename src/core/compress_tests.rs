use super::compress::{compress_directory, BatchOptions, Params};
use std::sync::Arc;

fn minimal_options(input_dir: String, recursive: bool) -> BatchOptions {
    BatchOptions {
        input_dir,
        output_dir: String::new(),
        format: "jpeg".to_string(),
        recursive,
        overwrite: false,
        conflict_strategy: "rename".to_string(),
        avifenc_path: String::new(),
        cwebp_path: String::new(),
        max_workers: 1,
        params: Params {
            quality: 80,
            speed: 6,
            lossless: false,
            resize_mode: "none".to_string(),
            resize_value: 0,
            keep_aspect_ratio: true,
            strip_exif: true,
            keep_icc: false,
            strip_xmp: true,
            extra: Default::default(),
        },
    }
}

#[test]
fn compress_directory_returns_error_for_missing_non_recursive_input() {
    let dir = tempfile::tempdir().unwrap();
    let missing = dir.path().join("missing");
    let opts = minimal_options(missing.to_string_lossy().to_string(), false);

    let err = compress_directory(Arc::new(()), opts, None, None).unwrap_err();

    assert!(
        err.to_string().contains("missing"),
        "unexpected error: {err:#}"
    );
}

#[test]
fn compress_directory_returns_error_for_missing_recursive_input() {
    let dir = tempfile::tempdir().unwrap();
    let missing = dir.path().join("missing");
    let opts = minimal_options(missing.to_string_lossy().to_string(), true);

    let err = compress_directory(Arc::new(()), opts, None, None).unwrap_err();

    assert!(
        err.to_string().contains("missing"),
        "unexpected error: {err:#}"
    );
}
