package compress

import (
	"context"
	"fmt"
	"image"
	"image/draw"
	_ "image/gif"
	"image/jpeg"
	_ "image/png"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	_ "golang.org/x/image/bmp"
	_ "golang.org/x/image/tiff"
	_ "golang.org/x/image/webp"
)

var batchImageExtensions = map[string]struct{}{
	".jpg": {}, ".jpeg": {}, ".png": {}, ".webp": {}, ".bmp": {}, ".gif": {},
	".tiff": {}, ".tif": {}, ".heic": {}, ".heif": {}, ".avif": {},
}

type BatchOptions struct {
	InputDir         string
	OutputDir        string
	Format           string
	Recursive        bool
	Overwrite        bool
	ConflictStrategy string
	AVIFEncPath      string
	CWebPPath        string
	MaxWorkers       int
	Params           Params
}

type BatchResult struct {
	TotalFiles      int      `json:"totalFiles"`
	CompressedFiles int      `json:"compressedFiles"`
	SkippedFiles    int      `json:"skippedFiles"`
	FailedFiles     int      `json:"failedFiles"`
	OutputDir       string   `json:"outputDir"`
	OriginalSize    int64    `json:"originalSize"`
	CompressedSize  int64    `json:"compressedSize"`
	ElapsedSeconds  float64  `json:"elapsedSeconds"`
	Results         []Result `json:"results"`
	Errors          []string `json:"errors"`
}

type ProgressFunc func(current int, total int, message string)

func CompressDirectory(ctx context.Context, options BatchOptions, runner Runner, progress ProgressFunc) (BatchResult, error) {
	start := time.Now()
	options = normalizeBatchOptions(options)
	files, err := collectImageFiles(options.InputDir, options.Recursive)
	if err != nil {
		return BatchResult{}, err
	}
	result := BatchResult{TotalFiles: len(files), OutputDir: options.OutputDir}

	processOneFile := func(index int, inputPath string) Result {
		outputPath, err := BuildOutputPath(options.InputDir, options.OutputDir, inputPath, options.Format, options.Recursive)
		if err != nil {
			return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, Error: err.Error()}
		}
		outputPath = resolveConflict(outputPath, options.ConflictStrategy)
		if options.ConflictStrategy == "skip" {
			if info, err := os.Stat(outputPath); err == nil && !info.IsDir() {
				inputInfo, _ := os.Stat(inputPath)
				return Result{
					Success:        true,
					InputPath:      inputPath,
					OutputPath:     outputPath,
					OriginalSize:   sizeOf(inputInfo),
					CompressedSize: info.Size(),
					Error:          "skipped",
				}
			}
		}
		if progress != nil {
			progress(index+1, len(files), fmt.Sprintf("压缩: %s", filepath.Base(inputPath)))
		}
		item, err := compressOne(ctx, inputPath, outputPath, options, runner)
		if err != nil && item.Error == "" {
			item.Error = err.Error()
		}
		return item
	}

	addResult := func(inputPath string, item Result) {
		result.Results = append(result.Results, item)
		result.OriginalSize += item.OriginalSize
		result.CompressedSize += item.CompressedSize
		if item.Error == "skipped" {
			result.SkippedFiles++
			return
		}
		if !item.Success {
			result.Errors = append(result.Errors, fmt.Sprintf("%s: %s", inputPath, item.Error))
			return
		}
		result.CompressedFiles++
	}

	if options.MaxWorkers <= 1 || options.Format == "avif" {
		for index, inputPath := range files {
			addResult(inputPath, processOneFile(index, inputPath))
		}
	} else {
		var mutex sync.Mutex
		work := make(chan int)
		var wg sync.WaitGroup
		for worker := 0; worker < options.MaxWorkers; worker++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for index := range work {
					inputPath := files[index]
					item := processOneFile(index, inputPath)
					mutex.Lock()
					addResult(inputPath, item)
					mutex.Unlock()
				}
			}()
		}
		for index := range files {
			work <- index
		}
		close(work)
		wg.Wait()
	}

	result.FailedFiles = len(result.Errors)
	result.ElapsedSeconds = time.Since(start).Seconds()
	return result, nil
}

func BuildOutputPath(inputDir string, outputDir string, inputPath string, format string, recursive bool) (string, error) {
	ext := targetExtension(format)
	if ext == "" {
		return "", fmt.Errorf("不支持的压缩格式: %s", format)
	}
	baseDir := outputDir
	if baseDir == "" {
		baseDir = inputDir
	}
	if recursive {
		rel, err := filepath.Rel(filepath.Clean(inputDir), filepath.Clean(inputPath))
		if err != nil {
			return "", err
		}
		return filepath.Join(baseDir, filepath.Dir(rel), trimExtension(filepath.Base(rel))+ext), nil
	}
	return filepath.Join(baseDir, trimExtension(filepath.Base(inputPath))+ext), nil
}

func RunWebP(ctx context.Context, cwebpPath string, inputPath string, outputPath string, params Params, runner Runner) (Result, error) {
	start := time.Now()
	inputInfo, err := os.Stat(inputPath)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, Error: err.Error()}, err
	}
	if cwebpPath == "" {
		cwebpPath = "cwebp"
	}
	if runner == nil {
		runner = defaultRunner
	}
	if err := os.MkdirAll(filepath.Dir(outputPath), 0o755); err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}

	effectiveInput, cleanup, err := prepareEncoderInput(inputPath, outputPath, params)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}
	defer cleanup()

	command := BuildWebPCommand(cwebpPath, effectiveInput, outputPath, params.Quality, params.Lossless)
	output, err := runner(ctx, command)
	item := Result{
		Success:        err == nil,
		InputPath:      inputPath,
		OutputPath:     outputPath,
		OriginalSize:   inputInfo.Size(),
		ElapsedSeconds: time.Since(start).Seconds(),
	}
	if err != nil {
		item.Error = strings.TrimSpace(string(output))
		if item.Error == "" {
			item.Error = err.Error()
		}
		return item, err
	}
	outputInfo, err := os.Stat(outputPath)
	if err != nil {
		item.Success = false
		item.Error = err.Error()
		return item, err
	}
	item.CompressedSize = outputInfo.Size()
	return item, nil
}

func BuildWebPCommand(cwebpPath string, inputPath string, outputPath string, quality int, lossless bool) []string {
	if cwebpPath == "" {
		cwebpPath = "cwebp"
	}
	cmd := []string{cwebpPath}
	if lossless {
		cmd = append(cmd, "-lossless")
	} else {
		if quality == 0 {
			quality = 80
		}
		cmd = append(cmd, "-q", fmt.Sprint(quality))
	}
	cmd = append(cmd, "-metadata", "none", inputPath, "-o", outputPath)
	return cmd
}

func RunJPEG(ctx context.Context, inputPath string, outputPath string, params Params) (Result, error) {
	start := time.Now()
	inputInfo, err := os.Stat(inputPath)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, Error: err.Error()}, err
	}
	if err := os.MkdirAll(filepath.Dir(outputPath), 0o755); err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}
	quality := params.Quality
	if quality <= 0 {
		quality = 80
	}
	if quality > 100 {
		quality = 100
	}

	effectiveInput, cleanup, err := prepareEncoderInput(inputPath, outputPath, params)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}
	defer cleanup()

	source, err := os.Open(effectiveInput)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}
	defer source.Close()

	img, _, err := image.Decode(source)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}
	select {
	case <-ctx.Done():
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: ctx.Err().Error()}, ctx.Err()
	default:
	}

	file, err := os.Create(outputPath)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}
	defer file.Close()

	rgba := image.NewRGBA(img.Bounds())
	draw.Draw(rgba, rgba.Bounds(), image.White, image.Point{}, draw.Src)
	draw.Draw(rgba, rgba.Bounds(), img, img.Bounds().Min, draw.Over)
	if err := jpeg.Encode(file, rgba, &jpeg.Options{Quality: quality}); err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}
	outputInfo, err := os.Stat(outputPath)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, OriginalSize: inputInfo.Size(), Error: err.Error()}, err
	}
	return Result{
		Success:        true,
		InputPath:      inputPath,
		OutputPath:     outputPath,
		OriginalSize:   inputInfo.Size(),
		CompressedSize: outputInfo.Size(),
		ElapsedSeconds: time.Since(start).Seconds(),
	}, nil
}

func compressOne(ctx context.Context, inputPath string, outputPath string, options BatchOptions, runner Runner) (Result, error) {
	switch options.Format {
	case "jpeg":
		return RunJPEG(ctx, inputPath, outputPath, options.Params)
	case "webp":
		return RunWebP(ctx, options.CWebPPath, inputPath, outputPath, options.Params, runner)
	default:
		return RunAVIF(ctx, options.AVIFEncPath, inputPath, outputPath, options.Params, runner)
	}
}

func normalizeBatchOptions(options BatchOptions) BatchOptions {
	options.InputDir = filepath.Clean(options.InputDir)
	if options.OutputDir == "" || options.Overwrite {
		options.OutputDir = options.InputDir
	} else {
		options.OutputDir = filepath.Clean(options.OutputDir)
	}
	options.Format = strings.ToLower(strings.TrimSpace(options.Format))
	if options.Format == "jpg" {
		options.Format = "jpeg"
	}
	if options.Format == "" {
		options.Format = "avif"
	}
	if options.ConflictStrategy == "" {
		options.ConflictStrategy = "overwrite"
	}
	if options.MaxWorkers <= 0 {
		options.MaxWorkers = 1
	}
	return options
}

func collectImageFiles(root string, recursive bool) ([]string, error) {
	var files []string
	visit := func(path string, info os.FileInfo, err error) error {
		if err != nil || info == nil || info.IsDir() {
			return nil
		}
		if _, ok := batchImageExtensions[strings.ToLower(filepath.Ext(path))]; ok {
			files = append(files, path)
		}
		return nil
	}
	if recursive {
		if err := filepath.Walk(root, visit); err != nil {
			return nil, err
		}
	} else {
		entries, err := os.ReadDir(root)
		if err != nil {
			return nil, err
		}
		for _, entry := range entries {
			info, err := entry.Info()
			if err != nil {
				continue
			}
			if err := visit(filepath.Join(root, entry.Name()), info, nil); err != nil {
				return nil, err
			}
		}
	}
	return files, nil
}

func targetExtension(format string) string {
	switch strings.ToLower(format) {
	case "avif":
		return ".avif"
	case "webp":
		return ".webp"
	case "jpeg", "jpg":
		return ".jpg"
	default:
		return ""
	}
}

func trimExtension(name string) string {
	return strings.TrimSuffix(name, filepath.Ext(name))
}

func resolveConflict(outputPath string, strategy string) string {
	if strategy != "rename" {
		return outputPath
	}
	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		return outputPath
	}
	ext := filepath.Ext(outputPath)
	stem := strings.TrimSuffix(outputPath, ext)
	for index := 1; ; index++ {
		candidate := fmt.Sprintf("%s_%d%s", stem, index, ext)
		if _, err := os.Stat(candidate); os.IsNotExist(err) {
			return candidate
		}
	}
}

func sizeOf(info os.FileInfo) int64 {
	if info == nil {
		return 0
	}
	return info.Size()
}
