package compress

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestReadImageDataURLDetectsMimeAndEncodesBase64(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "tiny.png")
	if err := os.WriteFile(path, []byte{0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x01}, 0o644); err != nil {
		t.Fatal(err)
	}

	dataURL, err := ReadImageDataURL(path)
	if err != nil {
		t.Fatal(err)
	}

	if !strings.HasPrefix(dataURL, "data:image/png;base64,") {
		t.Fatalf("data url = %q", dataURL)
	}
}

func TestReadImageDataURLRejectsNonImage(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "notes.txt")
	if err := os.WriteFile(path, []byte("plain text"), 0o644); err != nil {
		t.Fatal(err)
	}

	if _, err := ReadImageDataURL(path); err == nil {
		t.Fatal("expected error for non-image file")
	}
}
