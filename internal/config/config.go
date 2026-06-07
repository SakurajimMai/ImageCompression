package config

import (
	"encoding/json"
	"net"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

type AvifConfig struct {
	MinQuality   int    `json:"min_quality"`
	MaxQuality   int    `json:"max_quality"`
	Speed        int    `json:"speed"`
	Threads      string `json:"threads"`
	YUV          string `json:"yuv"`
	Depth        int    `json:"depth"`
	AlphaEnabled bool   `json:"alpha_enabled"`
	AlphaMin     int    `json:"alpha_min"`
	AlphaMax     int    `json:"alpha_max"`
	Lossless     bool   `json:"lossless"`
	Progressive  bool   `json:"progressive"`
}

type WebPJpegConfig struct {
	Quality  int  `json:"quality"`
	Lossless bool `json:"lossless"`
}

type S3Config struct {
	Endpoint  string `json:"endpoint"`
	Bucket    string `json:"bucket"`
	AccessKey string `json:"access_key"`
	SecretKey string `json:"secret_key"`
	Region    string `json:"region"`
	Prefix    string `json:"prefix"`
	Domain    string `json:"domain"`
}

type FTPConfig struct {
	Host      string `json:"host"`
	Port      int    `json:"port"`
	Username  string `json:"username"`
	Password  string `json:"password"`
	RemoteDir string `json:"remote_dir"`
	BaseURL   string `json:"base_url"`
}

type SFTPConfig struct {
	Host       string `json:"host"`
	Port       int    `json:"port"`
	Username   string `json:"username"`
	Password   string `json:"password"`
	KeyPath    string `json:"key_path"`
	RemoteDir  string `json:"remote_dir"`
	BaseURL    string `json:"base_url"`
	DomainRoot string `json:"domain_root"`
}

type ProxyConfig struct {
	Enabled  bool   `json:"enabled"`
	URL      string `json:"url"`
	Type     string `json:"type"`
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Username string `json:"username"`
	Password string `json:"password"`
}

type CompressConfig struct {
	Format           string         `json:"format"`
	Avif             AvifConfig     `json:"avif"`
	WebPJpeg         WebPJpegConfig `json:"webp_jpeg"`
	SkipVideo        bool           `json:"skip_videos"`
	ResizeMode       string         `json:"resize_mode"`
	ResizeValue      int            `json:"resize_value"`
	KeepAspectRatio  bool           `json:"keep_aspect_ratio"`
	Workers          int            `json:"workers"`
	ConflictStrategy string         `json:"conflict_strategy"`
}

type UploadConfig struct {
	Protocol string      `json:"protocol"`
	S3       S3Config    `json:"s3"`
	FTP      FTPConfig   `json:"ftp"`
	SFTP     SFTPConfig  `json:"sftp"`
	Proxy    ProxyConfig `json:"proxy"`
}

type PrepareConfig struct {
	RenameImages bool   `json:"rename_images"`
	RenameVideos bool   `json:"rename_videos"`
	StripExif    bool   `json:"strip_exif"`
	OutputMode   string `json:"output_mode"`
}

type Config struct {
	LastInputDir  string         `json:"last_input_dir"`
	LastOutputDir string         `json:"last_output_dir"`
	Prepare       PrepareConfig  `json:"prepare"`
	Compress      CompressConfig `json:"compress"`
	Upload        UploadConfig   `json:"upload"`
	AvifencPath   string         `json:"avifenc_path"`
	Language      string         `json:"language"`
	Theme         string         `json:"theme"`
}

func Default() Config {
	return Config{
		Prepare: PrepareConfig{
			RenameImages: true,
			RenameVideos: true,
			StripExif:    true,
			OutputMode:   "new_directory",
		},
		Compress: CompressConfig{
			Format: "avif",
			Avif: AvifConfig{
				MinQuality: 20,
				MaxQuality: 40,
				Speed:      6,
				Threads:    "all",
				YUV:        "420",
				Depth:      8,
				AlphaMin:   20,
				AlphaMax:   40,
			},
			WebPJpeg:         WebPJpegConfig{Quality: 80},
			SkipVideo:        true,
			ResizeMode:       "none",
			KeepAspectRatio:  true,
			Workers:          1,
			ConflictStrategy: "rename",
		},
		Upload: UploadConfig{
			Protocol: "s3",
			FTP:      FTPConfig{Port: 21, RemoteDir: "/"},
			SFTP:     SFTPConfig{Port: 22, RemoteDir: "/"},
			Proxy: ProxyConfig{
				URL:  "socks5://127.0.0.1:7890",
				Type: "socks5",
				Host: "127.0.0.1",
				Port: 7890,
			},
		},
		AvifencPath: "",
		Language:    "zh",
		Theme:       "light",
	}
}

func DefaultPath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".imagecompression", "config.json"), nil
}

func Load(path string) (Config, error) {
	cfg := Default()
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return cfg, nil
		}
		return cfg, err
	}
	if err := json.Unmarshal(data, &cfg); err != nil {
		return Default(), err
	}
	cfg.Normalize()
	return cfg, nil
}

func Save(path string, cfg Config) error {
	cfg.Normalize()
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	return SaveRaw(path, data)
}

func SaveRaw(path string, data []byte) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func (cfg *Config) Normalize() {
	cfg.AvifencPath = normalizeAVIFEncPath(cfg.AvifencPath)
	cfg.Upload.Proxy.Normalize()
}

func normalizeAVIFEncPath(path string) string {
	trimmed := strings.TrimSpace(path)
	if trimmed == "" {
		return ""
	}
	if strings.EqualFold(trimmed, "avifenc") || strings.EqualFold(trimmed, "avifenc.exe") {
		return ""
	}
	if !filepath.IsAbs(trimmed) && !strings.ContainsAny(trimmed, `/\`) {
		return trimmed
	}
	cleaned := filepath.Clean(trimmed)
	if strings.EqualFold(filepath.Base(cleaned), "avifenc.exe") {
		return filepath.Dir(cleaned)
	}
	return cleaned
}

func (proxy *ProxyConfig) Normalize() {
	if strings.TrimSpace(proxy.Type) == "" {
		proxy.Type = "socks5"
	}
	if proxy.URL == "" {
		return
	}
	if proxy.Host != "" && !proxy.hasDefaultStructuredFields() {
		return
	}

	parsed, err := url.Parse(proxy.URL)
	if err != nil {
		return
	}
	if parsed.Scheme != "" {
		proxy.Type = parsed.Scheme
	}
	if parsed.Hostname() != "" {
		proxy.Host = parsed.Hostname()
	}
	if parsed.Port() != "" {
		if port, err := strconv.Atoi(parsed.Port()); err == nil {
			proxy.Port = port
		}
	}
	if parsed.User != nil {
		proxy.Username = parsed.User.Username()
		if password, ok := parsed.User.Password(); ok {
			proxy.Password = password
		}
	}
}

func (proxy ProxyConfig) hasDefaultStructuredFields() bool {
	return strings.EqualFold(proxy.Type, "socks5") &&
		proxy.Host == "127.0.0.1" &&
		proxy.Port == 7890 &&
		proxy.Username == "" &&
		proxy.Password == ""
}

func (proxy ProxyConfig) EffectiveURL() string {
	if !proxy.Enabled {
		return ""
	}
	if strings.TrimSpace(proxy.Host) == "" {
		return strings.TrimSpace(proxy.URL)
	}

	scheme := strings.ToLower(strings.TrimSpace(proxy.Type))
	if scheme == "" {
		scheme = "socks5"
	}
	host := strings.TrimSpace(proxy.Host)
	if proxy.Port > 0 {
		host = net.JoinHostPort(host, strconv.Itoa(proxy.Port))
	}
	parsed := url.URL{
		Scheme: scheme,
		Host:   host,
	}
	if proxy.Username != "" {
		parsed.User = url.UserPassword(proxy.Username, proxy.Password)
	}
	return parsed.String()
}
