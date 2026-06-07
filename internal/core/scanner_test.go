package core

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
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

func TestScanDirectoryReturnsEmptySlicesForMissingCategories(t *testing.T) {
	root := t.TempDir()
	mustWrite(t, filepath.Join(root, "0001.jpg"), "img")

	result, err := ScanDirectory(root, false)
	if err != nil {
		t.Fatal(err)
	}

	if result.Videos == nil {
		t.Fatal("Videos is nil, want empty slice")
	}
	if result.Others == nil {
		t.Fatal("Others is nil, want empty slice")
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatal(err)
	}
	payload := string(data)
	if strings.Contains(payload, `"videos":null`) || strings.Contains(payload, `"others":null`) {
		t.Fatalf("scan JSON contains null slices: %s", payload)
	}
}

func TestScanDirectoryHandlesUnicodeAndBracketedPaths(t *testing.T) {
	parent := t.TempDir()
	root := filepath.Join(parent, "山崎怜 NO.001 华盛顿兔女郎 [45P-187M]")
	mustWrite(t, filepath.Join(root, "0001.jpg"), "img")
	mustWrite(t, filepath.Join(root, "0002.jpg"), "img")

	result, err := ScanDirectory(root, true)
	if err != nil {
		t.Fatal(err)
	}

	if len(result.Images) != 2 {
		t.Fatalf("Images = %d, want 2", len(result.Images))
	}
	if len(result.Videos) != 0 || len(result.Others) != 0 {
		t.Fatalf("unexpected non-image categories: videos=%#v others=%#v", result.Videos, result.Others)
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
