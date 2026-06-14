// Theme + icons modeled on pikpaktui
pub fn icon_for_ext(ext: &str) -> &'static str {
    match ext.to_ascii_lowercase().as_str() {
        ".jpg" | ".jpeg" | ".png" | ".webp" | ".avif" | ".heic" => "🖼️",
        ".mp4" | ".mov" | ".mkv" => "🎞️",
        _ => "📄",
    }
}
