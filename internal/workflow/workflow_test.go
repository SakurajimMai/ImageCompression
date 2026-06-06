package workflow

import (
	"testing"

	"imagecompression/internal/compress"
	"imagecompression/internal/prepare"
	"imagecompression/internal/upload"
)

func TestRunPrepareCompressUploadPassesPreparedAndCompressedDirs(t *testing.T) {
	var calls []string
	result, err := RunPrepareCompressUpload(Options{
		PrepareOperations: []prepare.Operation{
			{Source: "D:/raw/a.png", Destination: "D:/prepared/0001.png", Kind: "image"},
		},
		PrepareOverwrite: false,
		CompressOptions: compress.BatchOptions{
			InputDir:  "D:/should-be-replaced",
			OutputDir: "D:/compressed",
			Format:    "avif",
		},
	}, Hooks{
		Prepare: func(ops []prepare.Operation, overwrite bool) (prepare.Result, error) {
			calls = append(calls, "prepare")
			return prepare.Result{TotalFiles: len(ops), OutputDir: "D:/prepared"}, nil
		},
		Compress: func(options compress.BatchOptions) (compress.BatchResult, error) {
			calls = append(calls, "compress:"+options.InputDir)
			return compress.BatchResult{TotalFiles: 1, CompressedFiles: 1, OutputDir: options.OutputDir}, nil
		},
		Upload: func(inputDir string) (upload.Result, error) {
			calls = append(calls, "upload:"+inputDir)
			return upload.Result{TotalFiles: 1, UploadedFiles: 1}, nil
		},
	})
	if err != nil {
		t.Fatal(err)
	}

	wantCalls := []string{"prepare", "compress:D:/prepared", "upload:D:/compressed"}
	for i, want := range wantCalls {
		if calls[i] != want {
			t.Fatalf("call[%d] = %q, want %q; all calls %#v", i, calls[i], want, calls)
		}
	}
	if result.Prepare.TotalFiles != 1 || result.Compress.CompressedFiles != 1 || result.Upload.UploadedFiles != 1 {
		t.Fatalf("unexpected result: %#v", result)
	}
}
