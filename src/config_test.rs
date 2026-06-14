#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::*;

    #[test]
    fn test_default_and_normalize() {
        let mut c = default_config();
        assert_eq!(c.compress.avif.min_quality, 20);
        c.avifenc_path = "avifenc.exe".to_string();
        c.normalize();
        assert_eq!(c.avifenc_path, "");
    }

    #[test]
    fn test_proxy_legacy_and_effective() {
        let mut p = ProxyConfig {
            enabled: true,
            url: "socks5://user:pass@127.0.0.1:7890".to_string(),
            ..Default::default()
        };
        p.normalize();
        assert_eq!(p.host, "127.0.0.1");
        assert_eq!(p.username, "user");
        let eff = p.effective_url();
        assert!(eff.contains("user:pass"));
    }
}
