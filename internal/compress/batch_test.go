package compress

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestBuildOutputPathPreservesRelativeDirectory(t *testing.T) {
	inputDir := filepath.Clean("D:/photos")
	inputPath := filepath.Join(inputDir, "sub", "0001.png")
	got, err := BuildOutputPath(inputDir, "D:/out", inputPath, "avif", true)
	if err != nil {
		t.Fatal(err)
	}
	want := filepath.Clean("D:/out/sub/0001.avif")
	if got != want {
		t.Fatalf("output path = %q, want %q", got, want)
	}
}

func TestBuildWebPCommandUsesCWebPShape(t *testing.T) {
	cmd := BuildWebPCommand("cwebp", "in.png", "out.webp", 82, false)
	want := []string{"cwebp", "-q", "82", "-metadata", "none", "in.png", "-o", "out.webp"}
	if !reflect.DeepEqual(cmd, want) {
		t.Fatalf("command mismatch\n got: %#v\nwant: %#v", cmd, want)
	}
}

func TestCompressDirectoryRunsAllImages(t *testing.T) {
	root := t.TempDir()
	outputDir := filepath.Join(root, "out")
	writePNG(t, filepath.Join(root, "a.png"))
	writePNG(t, filepath.Join(root, "sub", "b.png"))

	result, err := CompressDirectory(context.Background(), BatchOptions{
		InputDir:    root,
		OutputDir:   outputDir,
		Format:      "avif",
		Recursive:   true,
		AVIFEncPath: "avifenc",
		Params: Params{
			Quality: 40,
			Speed:   6,
			Extra:   map[string]any{"threads": "all"},
		},
	}, func(_ context.Context, command []string) ([]byte, error) {
		outputPath := command[len(command)-1]
		if err := os.MkdirAll(filepath.Dir(outputPath), 0o755); err != nil {
			return nil, err
		}
		return []byte("ok"), os.WriteFile(outputPath, []byte("compressed"), 0o644)
	}, nil)
	if err != nil {
		t.Fatal(err)
	}

	if result.TotalFiles != 2 || result.CompressedFiles != 2 || result.FailedFiles != 0 {
		t.Fatalf("unexpected batch result: %#v", result)
	}
	if _, err := os.Stat(filepath.Join(outputDir, "a.avif")); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(outputDir, "sub", "b.avif")); err != nil {
		t.Fatal(err)
	}
}

func TestCompressDirectoryReturnsEmptySlicesForNoMatches(t *testing.T) {
	root := t.TempDir()
	if err := os.WriteFile(filepath.Join(root, "notes.txt"), []byte("notes"), 0o644); err != nil {
		t.Fatal(err)
	}

	result, err := CompressDirectory(context.Background(), BatchOptions{
		InputDir:  root,
		OutputDir: filepath.Join(root, "out"),
		Format:    "avif",
	}, nil, nil)
	if err != nil {
		t.Fatal(err)
	}

	if result.Results == nil {
		t.Fatal("Results is nil, want empty slice")
	}
	if result.Errors == nil {
		t.Fatal("Errors is nil, want empty slice")
	}
	data, err := json.Marshal(result)
	if err != nil {
		t.Fatal(err)
	}
	payload := string(data)
	if strings.Contains(payload, `"results":null`) || strings.Contains(payload, `"errors":null`) {
		t.Fatalf("batch JSON contains null slices: %s", payload)
	}
}

func TestCompressDirectoryUsesMaxWorkersForWebPAndJPEG(t *testing.T) {
	root := t.TempDir()
	outputDir := filepath.Join(root, "out")
	writePNG(t, filepath.Join(root, "a.png"))
	writePNG(t, filepath.Join(root, "b.png"))

	var inFlight int32
	var maxSeen int32
	result, err := CompressDirectory(context.Background(), BatchOptions{
		InputDir:   root,
		OutputDir:  outputDir,
		Format:     "webp",
		Recursive:  false,
		CWebPPath:  "cwebp",
		MaxWorkers: 2,
		Params:     Params{Quality: 80},
	}, func(_ context.Context, command []string) ([]byte, error) {
		current := atomic.AddInt32(&inFlight, 1)
		for {
			seen := atomic.LoadInt32(&maxSeen)
			if current <= seen || atomic.CompareAndSwapInt32(&maxSeen, seen, current) {
				break
			}
		}
		time.Sleep(30 * time.Millisecond)
		atomic.AddInt32(&inFlight, -1)
		outputPath := command[len(command)-1]
		if err := os.WriteFile(outputPath, []byte("compressed"), 0o644); err != nil {
			return nil, err
		}
		return []byte("ok"), nil
	}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if result.CompressedFiles != 2 {
		t.Fatalf("compressed files = %d, want 2", result.CompressedFiles)
	}
	if atomic.LoadInt32(&maxSeen) < 2 {
		t.Fatalf("max concurrent workers = %d, want at least 2", maxSeen)
	}
}

func TestRunJPEGEncodesPNGInput(t *testing.T) {
	root := t.TempDir()
	input := filepath.Join(root, "in.png")
	output := filepath.Join(root, "out", "in.jpg")
	writePNG(t, input)

	result, err := RunJPEG(context.Background(), input, output, Params{Quality: 75})
	if err != nil {
		t.Fatal(err)
	}
	if !result.Success || result.CompressedSize == 0 {
		t.Fatalf("unexpected result: %#v", result)
	}
	data, err := os.ReadFile(output)
	if err != nil {
		t.Fatal(err)
	}
	if len(data) < 2 || data[0] != 0xff || data[1] != 0xd8 {
		t.Fatalf("output is not a JPEG file")
	}
}

func TestRunJPEGEncodesBMPInput(t *testing.T) {
	root := t.TempDir()
	input := filepath.Join(root, "in.bmp")
	output := filepath.Join(root, "out", "in.jpg")
	if err := os.WriteFile(input, []byte{
		0x42, 0x4d, 0x3a, 0x00, 0x00, 0x00, 0x00, 0x00,
		0x00, 0x00, 0x36, 0x00, 0x00, 0x00, 0x28, 0x00,
		0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00,
		0x00, 0x00, 0x01, 0x00, 0x18, 0x00, 0x00, 0x00,
		0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x13, 0x0b,
		0x00, 0x00, 0x13, 0x0b, 0x00, 0x00, 0x00, 0x00,
		0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
		0xff, 0x00,
	}, 0o644); err != nil {
		t.Fatal(err)
	}

	result, err := RunJPEG(context.Background(), input, output, Params{Quality: 75})
	if err != nil {
		t.Fatal(err)
	}
	if !result.Success || result.CompressedSize == 0 {
		t.Fatalf("unexpected result: %#v", result)
	}
}

func TestRunJPEGEncodesWebPInput(t *testing.T) {
	root := t.TempDir()
	input := filepath.Join(root, "in.webp")
	output := filepath.Join(root, "out", "in.jpg")
	data, err := base64.StdEncoding.DecodeString("UklGRrIBAABXRUJQVlA4TKUBAAAvSsAYAA8w//M///MfeJAkbXvaSG7m8Q3GfYSBJekwQztm/IcZlgwnmWImn2BK7aFmBtnVir6q//8VOkFE/xm4baTIu8c48ArEo6+B3zFKYln3pqClSCKX0begFTAXFOLXHSyF8cCNcZEG4OywuA4KVVfJCiArU7GAgJI8+lJP/OKMT/fBAjevg1cYB7YVkFuWga2lyPi5I0HFy5YTpWIHg0RZpkniRVW9odHAKOwosWuOGdxIyn2OvaCDvhg/we6TwadPBPbqBV58MsLmMJ8yZnOWk8SRz4N+QoyPL+MnamzMvcE1rHNEr91F9GKZPVUcS9w7PhhH36suB9qPeYb/oLk6cuTiJ0wOK3m5h1cKjW6EVZCYMK7dxcKCBdgP9HkKr9gkAO2P8GKZGWVdIAatQa+1IDpt6qyorVwdy01xdW8Jkfk6xjEXmVQQ+HQdFr6OKhIN34dXWq0+0qr6EJSCeeVLH9+gvGTLyqM65PQ44ihzlTXxQKjKbAvshXgir7Lil9w4L2bvMycmjQcqXaMCO6BlY28i+FOLzbfI1vEqxAhotocAAA==")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(input, data, 0o644); err != nil {
		t.Fatal(err)
	}

	result, err := RunJPEG(context.Background(), input, output, Params{Quality: 75})
	if err != nil {
		t.Fatal(err)
	}
	if !result.Success || result.CompressedSize == 0 {
		t.Fatalf("unexpected result: %#v", result)
	}
}

func TestRunJPEGAppliesPercentResize(t *testing.T) {
	root := t.TempDir()
	input := filepath.Join(root, "in.png")
	output := filepath.Join(root, "out", "in.jpg")
	writeSizedPNG(t, input, 8, 4)

	result, err := RunJPEG(context.Background(), input, output, Params{
		Quality:         75,
		ResizeMode:      "percent",
		ResizeValue:     50,
		KeepAspectRatio: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !result.Success {
		t.Fatalf("unexpected result: %#v", result)
	}

	file, err := os.Open(output)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	img, _, err := image.Decode(file)
	if err != nil {
		t.Fatal(err)
	}
	if got := img.Bounds().Size(); got.X != 4 || got.Y != 2 {
		t.Fatalf("jpeg size = %dx%d, want 4x2", got.X, got.Y)
	}
}

func TestRunWebPUsesResizedTemporaryInput(t *testing.T) {
	root := t.TempDir()
	input := filepath.Join(root, "in.png")
	output := filepath.Join(root, "out", "in.webp")
	writeSizedPNG(t, input, 8, 4)

	result, err := RunWebP(context.Background(), "cwebp", input, output, Params{
		Quality:         80,
		ResizeMode:      "width",
		ResizeValue:     4,
		KeepAspectRatio: true,
	}, func(_ context.Context, command []string) ([]byte, error) {
		effectiveInput := command[len(command)-3]
		if effectiveInput == input {
			t.Fatalf("webp command used original input, want resized temp input")
		}
		assertImageSize(t, effectiveInput, 4, 2)
		if err := os.WriteFile(output, []byte("compressed"), 0o644); err != nil {
			return nil, err
		}
		return []byte("ok"), nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if !result.Success {
		t.Fatalf("unexpected result: %#v", result)
	}
}

func writePNG(t *testing.T, path string) {
	t.Helper()
	writeSizedPNG(t, path, 3, 3)
}

func writeSizedPNG(t *testing.T, path string, width int, height int) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	img := image.NewRGBA(image.Rect(0, 0, width, height))
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			img.Set(x, y, color.RGBA{R: 220, G: 120, B: 80, A: 255})
		}
	}
	file, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	if err := png.Encode(file, img); err != nil {
		t.Fatal(err)
	}
}

func assertImageSize(t *testing.T, path string, width int, height int) {
	t.Helper()
	file, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	img, _, err := image.Decode(file)
	if err != nil {
		t.Fatal(err)
	}
	if got := img.Bounds().Size(); got.X != width || got.Y != height {
		t.Fatalf("%s size = %dx%d, want %dx%d", path, got.X, got.Y, width, height)
	}
}
