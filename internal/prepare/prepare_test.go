package prepare

import (
	"os"
	"path/filepath"
	"testing"
)

func TestPlanOperationsRenamesPerDirectoryAndKeepsStructure(t *testing.T) {
	base := filepath.Clean("D:/input")
	scan := ScanInput{
		BaseDir: base,
		Images: []string{
			filepath.Join(base, "z.png"),
			filepath.Join(base, "sub", "a.jpg"),
			filepath.Join(base, "sub", "b.jpg"),
		},
		Videos: []string{
			filepath.Join(base, "sub", "clip.mp4"),
		},
	}

	ops, err := PlanOperations(scan, "D:/out", Options{
		RenameImages: true,
		RenameVideos: true,
		Overwrite:    false,
	})
	if err != nil {
		t.Fatal(err)
	}

	want := []string{
		filepath.Clean("D:/out/0001.png"),
		filepath.Clean("D:/out/sub/0001.jpg"),
		filepath.Clean("D:/out/sub/0002.jpg"),
		filepath.Clean("D:/out/sub/video001.mp4"),
	}
	if len(ops) != len(want) {
		t.Fatalf("len(ops) = %d, want %d", len(ops), len(want))
	}
	for i := range ops {
		if filepath.Clean(ops[i].Destination) != want[i] {
			t.Fatalf("op[%d].Destination = %q, want %q", i, ops[i].Destination, want[i])
		}
	}
}

func TestExecuteOperationsCopiesFilesAndReportsCounts(t *testing.T) {
	root := t.TempDir()
	sourceImage := filepath.Join(root, "raw", "a.png")
	sourceVideo := filepath.Join(root, "raw", "clip.mp4")
	if err := os.MkdirAll(filepath.Dir(sourceImage), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(sourceImage, []byte("image"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(sourceVideo, []byte("video"), 0o644); err != nil {
		t.Fatal(err)
	}

	ops := []Operation{
		{Source: sourceImage, Destination: filepath.Join(root, "out", "0001.png"), Kind: "image"},
		{Source: sourceVideo, Destination: filepath.Join(root, "out", "video001.mp4"), Kind: "video"},
	}
	result, err := ExecuteOperations(ops, false, nil)
	if err != nil {
		t.Fatal(err)
	}

	if result.RenamedImages != 1 || result.RenamedVideos != 1 || result.TotalFiles != 2 {
		t.Fatalf("unexpected result: %#v", result)
	}
	if got, err := os.ReadFile(filepath.Join(root, "out", "0001.png")); err != nil || string(got) != "image" {
		t.Fatalf("image copy mismatch: %q, %v", string(got), err)
	}
	if got, err := os.ReadFile(filepath.Join(root, "out", "video001.mp4")); err != nil || string(got) != "video" {
		t.Fatalf("video copy mismatch: %q, %v", string(got), err)
	}
}

func TestExecuteOperationsRefusesOverwriteWhenDisabled(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "a.png")
	dest := filepath.Join(root, "out.png")
	if err := os.WriteFile(source, []byte("new"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(dest, []byte("old"), 0o644); err != nil {
		t.Fatal(err)
	}

	_, err := ExecuteOperations([]Operation{{Source: source, Destination: dest, Kind: "image"}}, false, nil)
	if err == nil {
		t.Fatal("expected conflict error")
	}
}
