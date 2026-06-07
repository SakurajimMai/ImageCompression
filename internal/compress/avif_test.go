package compress

import (
	"context"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestBuildAVIFCommandMatchesLegacyParameterShape(t *testing.T) {
	cmd := BuildAVIFCommand("avifenc", "in.png", "out.avif", Params{
		Quality:   55,
		Speed:     6,
		StripExif: true,
		KeepICC:   false,
		StripXMP:  true,
		Extra: map[string]any{
			"min_quality": 20,
			"max_quality": 40,
			"threads":     "all",
			"yuv":         "420",
			"depth":       8,
			"progressive": true,
		},
	})

	want := []string{
		"avifenc",
		"--min", "20",
		"--max", "40",
		"--speed", "6",
		"-j", "all",
		"--yuv", "420",
		"--depth", "8",
		"--progressive",
		"--ignore-exif",
		"--ignore-icc",
		"--ignore-xmp",
		"in.png",
		"out.avif",
	}

	if !reflect.DeepEqual(cmd, want) {
		t.Fatalf("command mismatch\n got: %#v\nwant: %#v", cmd, want)
	}
}

func TestRunAVIFUsesRunnerAndReturnsSizes(t *testing.T) {
	root := t.TempDir()
	input := filepath.Join(root, "input.png")
	output := filepath.Join(root, "out", "output.avif")
	if err := os.WriteFile(input, []byte("input-bytes"), 0o644); err != nil {
		t.Fatal(err)
	}

	var gotCommand []string
	result, err := RunAVIF(context.Background(), "avifenc", input, output, Params{
		Quality: 40,
		Speed:   6,
		Extra:   map[string]any{"threads": "all"},
	}, func(_ context.Context, command []string) ([]byte, error) {
		gotCommand = append([]string{}, command...)
		if err := os.WriteFile(output, []byte("compressed"), 0o644); err != nil {
			return nil, err
		}
		return []byte("ok"), nil
	})
	if err != nil {
		t.Fatal(err)
	}

	if len(gotCommand) == 0 || gotCommand[0] != "avifenc" {
		t.Fatalf("runner did not receive avifenc command: %#v", gotCommand)
	}
	if !result.Success || result.OriginalSize != int64(len("input-bytes")) || result.CompressedSize != int64(len("compressed")) {
		t.Fatalf("unexpected result: %#v", result)
	}
}

func TestResolveAVIFEncPathAcceptsDirectory(t *testing.T) {
	root := t.TempDir()
	exe := filepath.Join(root, "avifenc.exe")
	if err := os.WriteFile(exe, []byte("stub"), 0o755); err != nil {
		t.Fatal(err)
	}

	got, err := ResolveAVIFEncPath(root)
	if err != nil {
		t.Fatal(err)
	}

	if got != exe {
		t.Fatalf("resolved avifenc path = %q, want %q", got, exe)
	}
}

func TestResolveAVIFEncPathKeepsCommandNameForPathLookup(t *testing.T) {
	got, err := ResolveAVIFEncPath("avifenc")
	if err != nil {
		t.Fatal(err)
	}
	if got != "avifenc" {
		t.Fatalf("resolved avifenc path = %q, want avifenc", got)
	}
}

func TestResolveAVIFEncPathRejectsMissingPath(t *testing.T) {
	missing := filepath.Join(t.TempDir(), "missing", "avifenc.exe")

	_, err := ResolveAVIFEncPath(missing)
	if err == nil {
		t.Fatal("expected missing avifenc path error")
	}
}

func TestBuildAVIFCommandUsesLosslessInsteadOfQualityRange(t *testing.T) {
	cmd := BuildAVIFCommand("avifenc", "in.png", "out.avif", Params{
		Lossless: true,
		Speed:    4,
		Extra: map[string]any{
			"threads": "2",
		},
	})

	want := []string{"avifenc", "--lossless", "--speed", "4", "-j", "2", "--yuv", "420", "--depth", "8", "in.png", "out.avif"}
	if !reflect.DeepEqual(cmd, want) {
		t.Fatalf("command mismatch\n got: %#v\nwant: %#v", cmd, want)
	}
}
