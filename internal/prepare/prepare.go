package prepare

import (
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type ScanInput struct {
	BaseDir string
	Images  []string
	Videos  []string
}

type Options struct {
	RenameImages bool
	RenameVideos bool
	Overwrite    bool
}

type Operation struct {
	Source      string `json:"source"`
	Destination string `json:"destination"`
	Kind        string `json:"kind"`
}

type Result struct {
	RenamedImages int    `json:"renamedImages"`
	RenamedVideos int    `json:"renamedVideos"`
	TotalFiles    int    `json:"totalFiles"`
	OutputDir     string `json:"outputDir"`
}

type ProgressFunc func(current int, total int, message string)

func PlanOperations(scan ScanInput, outputDir string, options Options) ([]Operation, error) {
	base := filepath.Clean(scan.BaseDir)
	var ops []Operation

	imageOps, err := planKind(base, outputDir, scan.Images, "image", options.RenameImages, options.Overwrite)
	if err != nil {
		return nil, err
	}
	videoOps, err := planKind(base, outputDir, scan.Videos, "video", options.RenameVideos, options.Overwrite)
	if err != nil {
		return nil, err
	}

	ops = append(ops, imageOps...)
	ops = append(ops, videoOps...)
	return ops, nil
}

func ExecuteOperations(ops []Operation, overwrite bool, progress ProgressFunc) (Result, error) {
	result := Result{TotalFiles: len(ops)}
	if len(ops) > 0 {
		result.OutputDir = filepath.Dir(ops[0].Destination)
	}

	for index, op := range ops {
		if progress != nil {
			progress(index+1, len(ops), fmt.Sprintf("%s -> %s", filepath.Base(op.Source), filepath.Base(op.Destination)))
		}
		if !overwrite {
			if _, err := os.Stat(op.Destination); err == nil {
				return result, fmt.Errorf("destination already exists: %s", op.Destination)
			} else if !errors.Is(err, os.ErrNotExist) {
				return result, err
			}
		}
		if err := copyFile(op.Source, op.Destination); err != nil {
			return result, err
		}
		switch op.Kind {
		case "image":
			result.RenamedImages++
		case "video":
			result.RenamedVideos++
		}
	}
	return result, nil
}

func copyFile(source string, destination string) error {
	input, err := os.Open(source)
	if err != nil {
		return err
	}
	defer input.Close()

	if err := os.MkdirAll(filepath.Dir(destination), 0o755); err != nil {
		return err
	}
	output, err := os.Create(destination)
	if err != nil {
		return err
	}
	defer output.Close()

	if _, err := io.Copy(output, input); err != nil {
		return err
	}
	return output.Close()
}

func planKind(base, outputDir string, files []string, kind string, rename bool, overwrite bool) ([]Operation, error) {
	groups := map[string][]string{}
	for _, file := range files {
		groups[filepath.Dir(file)] = append(groups[filepath.Dir(file)], file)
	}

	parents := make([]string, 0, len(groups))
	for parent := range groups {
		parents = append(parents, parent)
		sort.Strings(groups[parent])
	}
	sort.Strings(parents)

	var ops []Operation
	for _, parent := range parents {
		rel := "."
		if filepath.Clean(parent) != base {
			nextRel, err := filepath.Rel(base, parent)
			if err != nil {
				return nil, err
			}
			rel = nextRel
		}
		for i, file := range groups[parent] {
			name := filepath.Base(file)
			if rename {
				ext := strings.ToLower(filepath.Ext(file))
				if kind == "video" {
					name = fmt.Sprintf("video%03d%s", i+1, ext)
				} else {
					name = fmt.Sprintf("%04d%s", i+1, ext)
				}
			}
			destDir := parent
			if !overwrite {
				destDir = outputDir
				if rel != "." {
					destDir = filepath.Join(outputDir, rel)
				}
			}
			ops = append(ops, Operation{
				Source:      file,
				Destination: filepath.Join(destDir, name),
				Kind:        kind,
			})
		}
	}
	return ops, nil
}
