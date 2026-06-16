use assert_cmd::Command;
use image::{GenericImageView, ImageBuffer, Rgb};
use tempfile::tempdir;

#[test]
fn compress_cli_applies_resize_options() {
    let dir = tempdir().unwrap();
    let input_dir = dir.path().join("input");
    let output_dir = dir.path().join("output");
    std::fs::create_dir(&input_dir).unwrap();

    let source = input_dir.join("source.png");
    let img = ImageBuffer::from_pixel(80, 40, Rgb([200u8, 40, 20]));
    img.save(&source).unwrap();

    Command::cargo_bin("ImageCompression")
        .unwrap()
        .args([
            "compress",
            "--input",
            input_dir.to_str().unwrap(),
            "--output",
            output_dir.to_str().unwrap(),
            "--format",
            "jpeg",
            "--quality",
            "85",
            "--resize-mode",
            "long_edge",
            "--resize-value",
            "20",
            "--json",
        ])
        .assert()
        .success();

    let output = output_dir.join("source.jpg");
    let compressed = image::open(output).unwrap();
    assert_eq!(compressed.dimensions(), (20, 10));
}
