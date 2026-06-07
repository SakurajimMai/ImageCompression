package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestDefaultConfigMatchesLegacyDefaults(t *testing.T) {
	cfg := Default()

	if cfg.Compress.Format != "avif" {
		t.Fatalf("Compress.Format = %q, want avif", cfg.Compress.Format)
	}
	if cfg.Compress.Avif.MinQuality != 20 || cfg.Compress.Avif.MaxQuality != 40 {
		t.Fatalf("AVIF quality = %d..%d, want 20..40", cfg.Compress.Avif.MinQuality, cfg.Compress.Avif.MaxQuality)
	}
	if cfg.Compress.Avif.Speed != 6 || cfg.Compress.Avif.Threads != "all" {
		t.Fatalf("AVIF speed/threads = %d/%q, want 6/all", cfg.Compress.Avif.Speed, cfg.Compress.Avif.Threads)
	}
	if cfg.Compress.Avif.YUV != "420" || cfg.Compress.Avif.Depth != 8 {
		t.Fatalf("AVIF yuv/depth = %q/%d, want 420/8", cfg.Compress.Avif.YUV, cfg.Compress.Avif.Depth)
	}
	if cfg.Compress.Avif.AlphaMin != 20 || cfg.Compress.Avif.AlphaMax != 40 {
		t.Fatalf("AVIF alpha quality = %d..%d, want 20..40", cfg.Compress.Avif.AlphaMin, cfg.Compress.Avif.AlphaMax)
	}
	if cfg.Compress.ResizeMode != "none" || cfg.Compress.ResizeValue != 0 || !cfg.Compress.KeepAspectRatio {
		t.Fatalf("resize defaults not compatible with legacy UI: %#v", cfg.Compress)
	}
	if cfg.Compress.Workers != 1 {
		t.Fatalf("Compress.Workers = %d, want 1", cfg.Compress.Workers)
	}
	if !cfg.Prepare.RenameImages || !cfg.Prepare.RenameVideos || !cfg.Prepare.StripExif {
		t.Fatalf("prepare defaults should rename images/videos and strip exif")
	}
	if cfg.Upload.Protocol != "s3" || cfg.Upload.FTP.Port != 21 || cfg.Upload.SFTP.Port != 22 {
		t.Fatalf("upload defaults not compatible with legacy config: %#v", cfg.Upload)
	}
}

func TestLoadMergesPartialLegacyConfig(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.json")
	data := []byte(`{
		"last_input_dir": "D:/photos",
		"compress": {
			"format": "webp",
			"avif": {"max_quality": 52}
		},
		"upload": {
			"sftp": {"host": "example.com"}
		}
	}`)
	if err := SaveRaw(path, data); err != nil {
		t.Fatal(err)
	}

	cfg, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}

	if cfg.LastInputDir != "D:/photos" || cfg.Compress.Format != "webp" {
		t.Fatalf("top-level fields were not loaded: %#v", cfg)
	}
	if cfg.Compress.Avif.MinQuality != 20 || cfg.Compress.Avif.MaxQuality != 52 {
		t.Fatalf("partial nested config should merge with defaults: %#v", cfg.Compress.Avif)
	}
	if cfg.Upload.SFTP.Host != "example.com" || cfg.Upload.SFTP.Port != 22 {
		t.Fatalf("partial SFTP config should keep default port: %#v", cfg.Upload.SFTP)
	}
	if cfg.Compress.Avif.YUV != "420" || cfg.Compress.ResizeMode != "none" {
		t.Fatalf("partial legacy config should keep advanced compress defaults: %#v", cfg.Compress)
	}
}

func TestProxyConfigBuildsAuthenticatedURL(t *testing.T) {
	proxy := ProxyConfig{
		Enabled:  true,
		Type:     "http",
		Host:     "proxy.example.com",
		Port:     8080,
		Username: "alice",
		Password: "p@ss word",
	}

	got := proxy.EffectiveURL()
	want := "http://alice:p%40ss%20word@proxy.example.com:8080"
	if got != want {
		t.Fatalf("proxy URL = %q, want %q", got, want)
	}
}

func TestProxyConfigKeepsLegacyURLWhenStructuredFieldsAreMissing(t *testing.T) {
	proxy := ProxyConfig{
		Enabled: true,
		URL:     "socks5://127.0.0.1:7890",
	}

	got := proxy.EffectiveURL()
	if got != "socks5://127.0.0.1:7890" {
		t.Fatalf("proxy URL = %q", got)
	}
}

func TestLoadNormalizesLegacyProxyURLForSettingsForm(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.json")
	data := []byte(`{
		"upload": {
			"proxy": {
				"enabled": true,
				"url": "socks5://bob:secret@127.0.0.1:7891"
			}
		}
	}`)
	if err := SaveRaw(path, data); err != nil {
		t.Fatal(err)
	}

	cfg, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}

	if cfg.Upload.Proxy.Type != "socks5" ||
		cfg.Upload.Proxy.Host != "127.0.0.1" ||
		cfg.Upload.Proxy.Port != 7891 ||
		cfg.Upload.Proxy.Username != "bob" ||
		cfg.Upload.Proxy.Password != "secret" {
		t.Fatalf("legacy proxy URL was not normalized: %#v", cfg.Upload.Proxy)
	}
}

func TestNormalizeAVIFEncFilePathToDirectory(t *testing.T) {
	dir := t.TempDir()
	avifencFile := filepath.Join(dir, "windows-artifacts", "avifenc.exe")
	cfg := Default()
	cfg.AvifencPath = avifencFile

	cfg.Normalize()

	want := filepath.Dir(avifencFile)
	if cfg.AvifencPath != want {
		t.Fatalf("avifenc_path = %q, want %q", cfg.AvifencPath, want)
	}
}

func TestNormalizeLegacyAVIFEncCommandToEmptyDirectorySetting(t *testing.T) {
	cfg := Default()
	cfg.AvifencPath = "avifenc"

	cfg.Normalize()

	if cfg.AvifencPath != "" {
		t.Fatalf("avifenc_path = %q, want empty PATH fallback", cfg.AvifencPath)
	}
}

func TestSavePersistsNormalizedAVIFEncDirectory(t *testing.T) {
	dir := t.TempDir()
	avifencFile := filepath.Join(dir, "windows-artifacts", "avifenc.exe")
	path := filepath.Join(dir, "config.json")
	cfg := Default()
	cfg.AvifencPath = avifencFile

	if err := Save(path, cfg); err != nil {
		t.Fatal(err)
	}

	var stored Config
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(data, &stored); err != nil {
		t.Fatal(err)
	}

	want := filepath.Dir(avifencFile)
	if stored.AvifencPath != want {
		t.Fatalf("stored avifenc_path = %q, want %q", stored.AvifencPath, want)
	}
}
