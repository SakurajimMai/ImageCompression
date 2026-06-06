package compress

import "testing"

func TestBuildPreviewItemsKeepsSuccessfulResultsAndSavings(t *testing.T) {
	items := BuildPreviewItems(BatchResult{
		Results: []Result{
			{
				Success:        true,
				InputPath:      "D:/in/a.png",
				OutputPath:     "D:/out/a.avif",
				OriginalSize:   1000,
				CompressedSize: 250,
			},
			{
				Success:    false,
				InputPath:  "D:/in/b.png",
				OutputPath: "D:/out/b.avif",
				Error:      "failed",
			},
			{
				Success:        true,
				InputPath:      "D:/in/c.png",
				OutputPath:     "D:/out/c.avif",
				OriginalSize:   0,
				CompressedSize: 10,
			},
		},
	}, 4)

	if len(items) != 2 {
		t.Fatalf("items = %d, want 2", len(items))
	}
	if items[0].InputPath != "D:/in/a.png" || items[0].OutputPath != "D:/out/a.avif" {
		t.Fatalf("first item mismatch: %#v", items[0])
	}
	if items[0].SavedPercent != 75 {
		t.Fatalf("saved percent = %.1f, want 75", items[0].SavedPercent)
	}
	if items[1].SavedPercent != 0 {
		t.Fatalf("zero original saved percent = %.1f, want 0", items[1].SavedPercent)
	}
}

func TestBuildPreviewItemsHonorsLimit(t *testing.T) {
	items := BuildPreviewItems(BatchResult{
		Results: []Result{
			{Success: true, InputPath: "1.png", OutputPath: "1.avif", OriginalSize: 10, CompressedSize: 5},
			{Success: true, InputPath: "2.png", OutputPath: "2.avif", OriginalSize: 10, CompressedSize: 5},
			{Success: true, InputPath: "3.png", OutputPath: "3.avif", OriginalSize: 10, CompressedSize: 5},
		},
	}, 2)

	if len(items) != 2 {
		t.Fatalf("items = %d, want 2", len(items))
	}
	if items[1].InputPath != "2.png" {
		t.Fatalf("second item = %#v", items[1])
	}
}
