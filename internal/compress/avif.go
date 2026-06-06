package compress

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type Params struct {
	Quality         int
	Speed           int
	Lossless        bool
	ResizeMode      string
	ResizeValue     int
	KeepAspectRatio bool
	StripExif       bool
	KeepICC         bool
	StripXMP        bool
	Extra           map[string]any
}

type Result struct {
	Success        bool    `json:"success"`
	InputPath      string  `json:"inputPath"`
	OutputPath     string  `json:"outputPath"`
	OriginalSize   int64   `json:"originalSize"`
	CompressedSize int64   `json:"compressedSize"`
	ElapsedSeconds float64 `json:"elapsedSeconds"`
	Error          string  `json:"error,omitempty"`
}

type Runner func(ctx context.Context, command []string) ([]byte, error)

func RunAVIF(ctx context.Context, avifencPath string, inputPath string, outputPath string, params Params, runner Runner) (Result, error) {
	start := time.Now()
	inputInfo, err := os.Stat(inputPath)
	if err != nil {
		return Result{Success: false, InputPath: inputPath, OutputPath: outputPath, Error: err.Error()}, err
	}
	if avifencPath == "" {
		avifencPath = "avifenc"
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

	command := BuildAVIFCommand(avifencPath, effectiveInput, outputPath, params)
	output, err := runner(ctx, command)
	result := Result{
		Success:        err == nil,
		InputPath:      inputPath,
		OutputPath:     outputPath,
		OriginalSize:   inputInfo.Size(),
		ElapsedSeconds: time.Since(start).Seconds(),
	}
	if err != nil {
		result.Error = strings.TrimSpace(string(output))
		if result.Error == "" {
			result.Error = err.Error()
		}
		return result, err
	}
	outputInfo, err := os.Stat(outputPath)
	if err != nil {
		result.Success = false
		result.Error = err.Error()
		return result, err
	}
	result.CompressedSize = outputInfo.Size()
	return result, nil
}

func defaultRunner(ctx context.Context, command []string) ([]byte, error) {
	cmd := exec.CommandContext(ctx, command[0], command[1:]...)
	return cmd.CombinedOutput()
}

func BuildAVIFCommand(avifencPath string, inputPath string, outputPath string, params Params) []string {
	cmd := []string{avifencPath}
	if params.Lossless {
		cmd = append(cmd, "--lossless")
	} else {
		minQ := extraInt(params.Extra, "min_quality", max(0, params.Quality-10))
		maxQ := extraInt(params.Extra, "max_quality", min(63, params.Quality))
		cmd = append(cmd, "--min", strconv.Itoa(minQ), "--max", strconv.Itoa(maxQ))
	}

	speed := params.Speed
	if speed == 0 {
		speed = 6
	}
	cmd = append(cmd, "--speed", strconv.Itoa(speed))
	cmd = append(cmd, "-j", extraString(params.Extra, "threads", "all"))
	cmd = append(cmd, "--yuv", extraString(params.Extra, "yuv", "420"))
	cmd = append(cmd, "--depth", strconv.Itoa(extraInt(params.Extra, "depth", 8)))

	if alphaMin, ok := optionalInt(params.Extra, "alpha_min"); ok {
		if alphaMax, ok := optionalInt(params.Extra, "alpha_max"); ok {
			cmd = append(cmd, "--alpha-min", strconv.Itoa(alphaMin), "--alpha-max", strconv.Itoa(alphaMax))
		}
	}
	if extraBool(params.Extra, "progressive", false) {
		cmd = append(cmd, "--progressive")
	}
	if gainMap, ok := optionalInt(params.Extra, "gain_map_quality"); ok {
		cmd = append(cmd, "--gain-map-quality", strconv.Itoa(gainMap))
	}
	if params.StripExif {
		cmd = append(cmd, "--ignore-exif")
		if !params.KeepICC {
			cmd = append(cmd, "--ignore-icc")
		}
	}
	if params.StripXMP {
		cmd = append(cmd, "--ignore-xmp")
	}
	return append(cmd, inputPath, outputPath)
}

func extraString(extra map[string]any, key string, fallback string) string {
	if extra == nil {
		return fallback
	}
	if value, ok := extra[key]; ok {
		return fmt.Sprint(value)
	}
	return fallback
}

func extraInt(extra map[string]any, key string, fallback int) int {
	if value, ok := optionalInt(extra, key); ok {
		return value
	}
	return fallback
}

func optionalInt(extra map[string]any, key string) (int, bool) {
	if extra == nil {
		return 0, false
	}
	switch value := extra[key].(type) {
	case int:
		return value, true
	case int64:
		return int(value), true
	case float64:
		return int(value), true
	case string:
		parsed, err := strconv.Atoi(value)
		return parsed, err == nil
	default:
		return 0, false
	}
}

func extraBool(extra map[string]any, key string, fallback bool) bool {
	if extra == nil {
		return fallback
	}
	if value, ok := extra[key].(bool); ok {
		return value
	}
	return fallback
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
