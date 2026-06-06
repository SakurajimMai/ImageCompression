package core

import (
	"os"
	"path/filepath"
	"testing"
)

func TestScanDirectoryClassifiesAndNaturallySortsFiles(t *testing.T) {
	root := t.TempDir()
	mustWrite(t, filepath.Join(root, "10.png"), "img")
	mustWrite(t, filepath.Join(root, "2.jpg"), "img")
	mustWrite(t, filepath.Join(root, "clip.mp4"), "video")
	mustWrite(t, filepath.Join(root, "notes.txt"), "other")

	result, err := ScanDirectory(root, false)
	if err != nil {
		t.Fatal(err)
	}

	if len(result.Images) != 2 || filepath.Base(result.Images[0]) != "2.jpg" || filepath.Base(result.Images[1]) != "10.png" {
		t.Fatalf("images not naturally sorted: %#v", result.Images)
	}
	if len(result.Videos) != 1 || filepath.Base(result.Videos[0]) != "clip.mp4" {
		t.Fatalf("videos not classified: %#v", result.Videos)
	}
	if len(result.Others) != 1 || filepath.Base(result.Others[0]) != "notes.txt" {
		t.Fatalf("others not classified: %#v", result.Others)
	}
}

func TestScanDirectoryCountsRecursiveSubdirectories(t *testing.T) {
	root := t.TempDir()
	mustWrite(t, filepath.Join(root, "a", "1.png"), "img")
	mustWrite(t, filepath.Join(root, "a", "b", "2.png"), "img")

	result, err := ScanDirectory(root, true)
	if err != nil {
		t.Fatal(err)
	}

	if len(result.Images) != 2 {
		t.Fatalf("Images = %d, want 2", len(result.Images))
	}
	if result.Subdirs != 2 {
		t.Fatalf("Subdirs = %d, want 2", result.Subdirs)
	}
}

func mustWrite(t *testing.T, path string, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}
