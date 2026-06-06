package upload

import (
	"bufio"
	"context"
	"encoding/base64"
	"fmt"
	"io"
	"mime"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/jlaffaye/ftp"
	"github.com/pkg/sftp"
	"golang.org/x/crypto/ssh"
	"golang.org/x/net/proxy"
)

type S3Config struct {
	Endpoint     string
	Bucket       string
	AccessKey    string
	SecretKey    string
	Region       string
	Prefix       string
	CustomDomain string
	ProxyURL     string
}

type S3Uploader struct {
	cfg    S3Config
	client *s3.Client
}

func NewS3Uploader(cfg S3Config) *S3Uploader {
	return &S3Uploader{cfg: cfg}
}

func (u *S3Uploader) Connect() error {
	region := u.cfg.Region
	if region == "" {
		region = "us-east-1"
	}
	loadOptions := []func(*awsconfig.LoadOptions) error{
		awsconfig.WithRegion(region),
		awsconfig.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(u.cfg.AccessKey, u.cfg.SecretKey, "")),
	}
	httpClient, err := newProxyHTTPClient(u.cfg.ProxyURL)
	if err != nil {
		return err
	}
	if httpClient != nil {
		loadOptions = append(loadOptions, awsconfig.WithHTTPClient(httpClient))
	}

	cfg, err := awsconfig.LoadDefaultConfig(context.Background(), loadOptions...)
	if err != nil {
		return err
	}
	u.client = s3.NewFromConfig(cfg, func(options *s3.Options) {
		if u.cfg.Endpoint != "" {
			options.BaseEndpoint = aws.String(strings.TrimRight(u.cfg.Endpoint, "/"))
			options.UsePathStyle = true
		}
	})
	return nil
}

func (u *S3Uploader) UploadFile(localPath string, remoteName string) (string, error) {
	if u.client == nil {
		return "", fmt.Errorf("S3 未连接")
	}
	file, err := os.Open(localPath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	key := strings.Trim(strings.Trim(u.cfg.Prefix, "/")+"/"+strings.TrimLeft(remoteName, "/"), "/")
	contentType := contentTypeFor(localPath)
	_, err = u.client.PutObject(context.Background(), &s3.PutObjectInput{
		Bucket:      aws.String(u.cfg.Bucket),
		Key:         aws.String(key),
		Body:        file,
		ContentType: aws.String(contentType),
	})
	if err != nil {
		return "", err
	}
	if u.cfg.CustomDomain != "" {
		return BuildPublicURL(u.cfg.CustomDomain, key), nil
	}
	return BuildPublicURL(strings.TrimRight(u.cfg.Endpoint, "/")+"/"+u.cfg.Bucket, key), nil
}

func (u *S3Uploader) Disconnect() error {
	u.client = nil
	return nil
}

type FTPConfig struct {
	Host      string
	Port      int
	Username  string
	Password  string
	RemoteDir string
	BaseURL   string
	ProxyURL  string
}

type FTPUploader struct {
	cfg FTPConfig
	ftp *ftp.ServerConn
}

func NewFTPUploader(cfg FTPConfig) *FTPUploader {
	return &FTPUploader{cfg: cfg}
}

func (u *FTPUploader) Connect() error {
	port := u.cfg.Port
	if port == 0 {
		port = 21
	}
	dialOptions := []ftp.DialOption{ftp.DialWithTimeout(15 * time.Second)}
	dialFunc, err := newProxyDialFunc(u.cfg.ProxyURL, 15*time.Second)
	if err != nil {
		return err
	}
	if dialFunc != nil {
		dialOptions = append(dialOptions, ftp.DialWithDialFunc(dialFunc))
	}
	conn, err := ftp.Dial(fmt.Sprintf("%s:%d", u.cfg.Host, port), dialOptions...)
	if err != nil {
		return err
	}
	if err := conn.Login(u.cfg.Username, u.cfg.Password); err != nil {
		return err
	}
	u.ftp = conn
	if u.cfg.RemoteDir != "" && u.cfg.RemoteDir != "/" {
		if err := conn.MakeDir(u.cfg.RemoteDir); err != nil {
			// 目录已存在时大多数服务器会返回错误，继续尝试切换。
		}
	}
	return nil
}

func (u *FTPUploader) UploadFile(localPath string, remoteName string) (string, error) {
	if u.ftp == nil {
		return "", fmt.Errorf("FTP 未连接")
	}
	if err := u.ensureRemoteParent(remoteName); err != nil {
		return "", err
	}
	file, err := os.Open(localPath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	remotePath := joinRemote(u.cfg.RemoteDir, remoteName)
	if err := u.ftp.Stor(remotePath, file); err != nil {
		return "", err
	}
	if u.cfg.BaseURL != "" {
		return BuildPublicURL(u.cfg.BaseURL, strings.TrimLeft(remotePath, "/")), nil
	}
	return "ftp://" + u.cfg.Host + "/" + strings.TrimLeft(remotePath, "/"), nil
}

func (u *FTPUploader) Disconnect() error {
	if u.ftp != nil {
		err := u.ftp.Quit()
		u.ftp = nil
		return err
	}
	return nil
}

func (u *FTPUploader) ensureRemoteParent(remoteName string) error {
	parent := filepath.ToSlash(filepath.Dir(remoteName))
	if parent == "." || parent == "/" {
		return nil
	}
	current := strings.Trim(u.cfg.RemoteDir, "/")
	for _, part := range strings.Split(parent, "/") {
		if part == "" || part == "." {
			continue
		}
		current = strings.Trim(current+"/"+part, "/")
		_ = u.ftp.MakeDir("/" + current)
	}
	return nil
}

type SFTPConfig struct {
	Host       string
	Port       int
	Username   string
	Password   string
	KeyPath    string
	RemoteDir  string
	BaseURL    string
	DomainRoot string
	ProxyURL   string
}

type SFTPUploader struct {
	cfg    SFTPConfig
	client *sftp.Client
	ssh    *ssh.Client
}

func NewSFTPUploader(cfg SFTPConfig) *SFTPUploader {
	return &SFTPUploader{cfg: cfg}
}

func (u *SFTPUploader) Connect() error {
	auth := []ssh.AuthMethod{}
	if u.cfg.KeyPath != "" {
		key, err := os.ReadFile(u.cfg.KeyPath)
		if err != nil {
			return err
		}
		signer, err := ssh.ParsePrivateKey(key)
		if err != nil {
			return err
		}
		auth = append(auth, ssh.PublicKeys(signer))
	} else {
		auth = append(auth, ssh.Password(u.cfg.Password))
	}
	port := u.cfg.Port
	if port == 0 {
		port = 22
	}
	addr := fmt.Sprintf("%s:%d", u.cfg.Host, port)
	sshConfig := &ssh.ClientConfig{
		User:            u.cfg.Username,
		Auth:            auth,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Timeout:         15 * time.Second,
	}

	dialFunc, err := newProxyDialFunc(u.cfg.ProxyURL, 15*time.Second)
	if err != nil {
		return err
	}
	var sshClient *ssh.Client
	if dialFunc != nil {
		conn, err := dialFunc("tcp", addr)
		if err != nil {
			return err
		}
		clientConn, chans, reqs, err := ssh.NewClientConn(conn, addr, sshConfig)
		if err != nil {
			_ = conn.Close()
			return err
		}
		sshClient = ssh.NewClient(clientConn, chans, reqs)
	} else {
		sshClient, err = ssh.Dial("tcp", addr, sshConfig)
		if err != nil {
			return err
		}
	}
	client, err := sftp.NewClient(sshClient)
	if err != nil {
		sshClient.Close()
		return err
	}
	u.ssh = sshClient
	u.client = client
	return u.mkdirAll(u.cfg.RemoteDir)
}

func (u *SFTPUploader) UploadFile(localPath string, remoteName string) (string, error) {
	if u.client == nil {
		return "", fmt.Errorf("SFTP 未连接")
	}
	remotePath := joinRemote(u.cfg.RemoteDir, remoteName)
	if err := u.mkdirAll(filepath.ToSlash(filepath.Dir(remotePath))); err != nil {
		return "", err
	}
	source, err := os.Open(localPath)
	if err != nil {
		return "", err
	}
	defer source.Close()
	dest, err := u.client.Create(remotePath)
	if err != nil {
		return "", err
	}
	defer dest.Close()
	if _, err := io.Copy(dest, source); err != nil {
		return "", err
	}
	if u.cfg.BaseURL != "" {
		relPath := remotePath
		if u.cfg.DomainRoot != "" && strings.HasPrefix(remotePath, u.cfg.DomainRoot) {
			relPath = strings.TrimPrefix(remotePath, u.cfg.DomainRoot)
		}
		return BuildPublicURL(u.cfg.BaseURL, relPath), nil
	}
	return remotePath, nil
}

func (u *SFTPUploader) Disconnect() error {
	var err error
	if u.client != nil {
		err = u.client.Close()
		u.client = nil
	}
	if u.ssh != nil {
		if closeErr := u.ssh.Close(); err == nil {
			err = closeErr
		}
		u.ssh = nil
	}
	return err
}

func (u *SFTPUploader) mkdirAll(remoteDir string) error {
	remoteDir = strings.Trim(remoteDir, "/")
	if remoteDir == "" {
		return nil
	}
	current := ""
	for _, part := range strings.Split(remoteDir, "/") {
		if part == "" {
			continue
		}
		current += "/" + part
		if err := u.client.Mkdir(current); err != nil {
			// 已存在时继续。
			continue
		}
	}
	return nil
}

func joinRemote(base string, remoteName string) string {
	base = strings.TrimRight(base, "/")
	remoteName = strings.TrimLeft(filepath.ToSlash(remoteName), "/")
	if base == "" {
		return remoteName
	}
	return base + "/" + remoteName
}

func contentTypeFor(path string) string {
	switch strings.ToLower(filepath.Ext(path)) {
	case ".avif":
		return "image/avif"
	case ".webp":
		return "image/webp"
	case ".jpg", ".jpeg":
		return "image/jpeg"
	case ".png":
		return "image/png"
	case ".gif":
		return "image/gif"
	default:
		if detected := mime.TypeByExtension(filepath.Ext(path)); detected != "" {
			return detected
		}
		return "application/octet-stream"
	}
}

func newProxyHTTPClient(proxyURL string) (*http.Client, error) {
	if strings.TrimSpace(proxyURL) == "" {
		return nil, nil
	}
	parsed, err := url.Parse(proxyURL)
	if err != nil {
		return nil, err
	}
	return &http.Client{
		Transport: &http.Transport{
			Proxy: http.ProxyURL(parsed),
		},
		Timeout: 10 * time.Minute,
	}, nil
}

type proxyDialFunc func(network, address string) (net.Conn, error)

func newProxyDialFunc(proxyURL string, timeout time.Duration) (proxyDialFunc, error) {
	if strings.TrimSpace(proxyURL) == "" {
		return nil, nil
	}
	parsed, err := url.Parse(proxyURL)
	if err != nil {
		return nil, err
	}
	switch strings.ToLower(parsed.Scheme) {
	case "socks5", "socks5h":
		proxyDialer, err := proxy.FromURL(parsed, timeoutDialer{timeout: timeout})
		if err != nil {
			return nil, err
		}
		return proxyDialer.Dial, nil
	case "http", "https":
		return func(network, address string) (net.Conn, error) {
			if network == "" {
				network = "tcp"
			}
			dialer := &net.Dialer{Timeout: timeout}
			conn, err := dialer.Dial(network, parsed.Host)
			if err != nil {
				return nil, err
			}
			if err := writeHTTPConnect(conn, parsed, address); err != nil {
				_ = conn.Close()
				return nil, err
			}
			return conn, nil
		}, nil
	default:
		return nil, fmt.Errorf("不支持的上传代理协议: %s", parsed.Scheme)
	}
}

type timeoutDialer struct {
	timeout time.Duration
}

func (d timeoutDialer) Dial(network string, address string) (net.Conn, error) {
	return (&net.Dialer{Timeout: d.timeout}).Dial(network, address)
}

func (d timeoutDialer) DialContext(ctx context.Context, network string, address string) (net.Conn, error) {
	return (&net.Dialer{Timeout: d.timeout}).DialContext(ctx, network, address)
}

func writeHTTPConnect(conn net.Conn, proxyURL *url.URL, target string) error {
	if deadline := time.Now().Add(15 * time.Second); !deadline.IsZero() {
		_ = conn.SetDeadline(deadline)
		defer conn.SetDeadline(time.Time{})
	}
	request := "CONNECT " + target + " HTTP/1.1\r\nHost: " + target + "\r\n"
	if proxyURL.User != nil {
		username := proxyURL.User.Username()
		password, _ := proxyURL.User.Password()
		token := base64.StdEncoding.EncodeToString([]byte(username + ":" + password))
		request += "Proxy-Authorization: Basic " + token + "\r\n"
	}
	request += "\r\n"
	if _, err := io.WriteString(conn, request); err != nil {
		return err
	}
	response, err := http.ReadResponse(bufio.NewReader(conn), &http.Request{Method: http.MethodConnect})
	if err != nil {
		return err
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		return fmt.Errorf("HTTP 代理 CONNECT 失败: %s", response.Status)
	}
	return nil
}
