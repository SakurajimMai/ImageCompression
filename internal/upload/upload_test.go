package upload

import (
	"bufio"
	"encoding/base64"
	"encoding/json"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestBuildRemoteNamePreservesRelativePathWhenRecursive(t *testing.T) {
	base := filepath.Clean("D:/out")
	file := filepath.Join(base, "sub", "0001.avif")

	got, err := BuildRemoteName(base, file, true)
	if err != nil {
		t.Fatal(err)
	}
	if got != "sub/0001.avif" {
		t.Fatalf("remote name = %q, want sub/0001.avif", got)
	}
}

func TestBuildPublicURLJoinsBaseAndRemoteName(t *testing.T) {
	got := BuildPublicURL("https://cdn.example.com/uploads/", "/2026/0001.avif")
	if got != "https://cdn.example.com/uploads/2026/0001.avif" {
		t.Fatalf("url = %q", got)
	}
}

func TestUploadDirectoryUsesUploaderAndCollectsURLs(t *testing.T) {
	root := t.TempDir()
	fileA := writeTestFile(t, filepath.Join(root, "a.avif"))
	fileB := writeTestFile(t, filepath.Join(root, "sub", "b.webp"))

	uploader := &recordingUploader{}
	result, err := UploadFiles(uploader, root, []string{fileA, fileB}, Options{
		Recursive: true,
	})
	if err != nil {
		t.Fatal(err)
	}

	if result.TotalFiles != 2 || result.UploadedFiles != 2 || len(result.URLs) != 2 {
		t.Fatalf("unexpected result: %#v", result)
	}
	wantNames := []string{"a.avif", "sub/b.webp"}
	for i, want := range wantNames {
		if uploader.names[i] != want {
			t.Fatalf("remote[%d] = %q, want %q", i, uploader.names[i], want)
		}
	}
}

func TestUploadFilesReturnsEmptySlicesForNoFiles(t *testing.T) {
	result, err := UploadFiles(&recordingUploader{}, t.TempDir(), nil, Options{})
	if err != nil {
		t.Fatal(err)
	}

	if result.URLs == nil {
		t.Fatal("URLs is nil, want empty slice")
	}
	if result.Errors == nil {
		t.Fatal("Errors is nil, want empty slice")
	}
	data, err := json.Marshal(result)
	if err != nil {
		t.Fatal(err)
	}
	payload := string(data)
	if strings.Contains(payload, `"urls":null`) || strings.Contains(payload, `"errors":null`) {
		t.Fatalf("upload JSON contains null slices: %s", payload)
	}
}

func TestNewProxyHTTPClientUsesConfiguredProxy(t *testing.T) {
	client, err := newProxyHTTPClient("socks5://127.0.0.1:7890")
	if err != nil {
		t.Fatal(err)
	}
	if client == nil {
		t.Fatal("client is nil")
	}

	transport, ok := client.Transport.(*http.Transport)
	if !ok {
		t.Fatalf("transport type = %T, want *http.Transport", client.Transport)
	}
	request, err := http.NewRequest(http.MethodPut, "https://s3.example.com/bucket/key", nil)
	if err != nil {
		t.Fatal(err)
	}
	proxyURL, err := transport.Proxy(request)
	if err != nil {
		t.Fatal(err)
	}
	if proxyURL.String() != "socks5://127.0.0.1:7890" {
		t.Fatalf("proxy = %q", proxyURL.String())
	}
}

func TestNewProxyHTTPClientReturnsNilWhenProxyIsEmpty(t *testing.T) {
	client, err := newProxyHTTPClient("")
	if err != nil {
		t.Fatal(err)
	}
	if client != nil {
		t.Fatalf("client = %#v, want nil", client)
	}
}

func TestNewProxyDialFuncUsesHTTPConnectProxyWithCredentials(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()

	requests := make(chan string, 1)
	go func() {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		defer conn.Close()
		reader := bufio.NewReader(conn)
		var builder strings.Builder
		for {
			line, err := reader.ReadString('\n')
			if err != nil {
				return
			}
			builder.WriteString(line)
			if line == "\r\n" {
				break
			}
		}
		requests <- builder.String()
		_, _ = conn.Write([]byte("HTTP/1.1 200 Connection Established\r\n\r\n"))
		time.Sleep(20 * time.Millisecond)
	}()

	dialFunc, err := newProxyDialFunc("http://alice:secret@"+listener.Addr().String(), time.Second)
	if err != nil {
		t.Fatal(err)
	}
	conn, err := dialFunc("tcp", "upload.example.com:22")
	if err != nil {
		t.Fatal(err)
	}
	_ = conn.Close()

	got := <-requests
	if !strings.Contains(got, "CONNECT upload.example.com:22 HTTP/1.1") {
		t.Fatalf("CONNECT request missing target:\n%s", got)
	}
	wantAuth := "Proxy-Authorization: Basic " + base64.StdEncoding.EncodeToString([]byte("alice:secret"))
	if !strings.Contains(got, wantAuth) {
		t.Fatalf("CONNECT request missing auth header %q:\n%s", wantAuth, got)
	}
}

func TestNewProxyDialFuncReturnsNilWhenProxyIsEmpty(t *testing.T) {
	dialFunc, err := newProxyDialFunc("", time.Second)
	if err != nil {
		t.Fatal(err)
	}
	if dialFunc != nil {
		t.Fatalf("dialFunc = %#v, want nil", dialFunc)
	}
}

type recordingUploader struct {
	names []string
}

func (r *recordingUploader) Connect() error {
	return nil
}

func (r *recordingUploader) UploadFile(localPath string, remoteName string) (string, error) {
	r.names = append(r.names, remoteName)
	return "https://cdn.example.com/" + remoteName, nil
}

func (r *recordingUploader) Disconnect() error {
	return nil
}

func writeTestFile(t *testing.T, path string) string {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}
