package workflow

import (
	"fmt"

	"imagecompression/internal/compress"
	"imagecompression/internal/prepare"
	"imagecompression/internal/upload"
)

type Options struct {
	PrepareOperations []prepare.Operation
	PrepareOverwrite  bool
	CompressOptions   compress.BatchOptions
}

type Result struct {
	Prepare  prepare.Result       `json:"prepare"`
	Compress compress.BatchResult `json:"compress"`
	Upload   upload.Result        `json:"upload"`
}

type Hooks struct {
	Prepare  func([]prepare.Operation, bool) (prepare.Result, error)
	Compress func(compress.BatchOptions) (compress.BatchResult, error)
	Upload   func(string) (upload.Result, error)
}

func RunPrepareCompressUpload(options Options, hooks Hooks) (Result, error) {
	if hooks.Prepare == nil || hooks.Compress == nil || hooks.Upload == nil {
		return Result{}, fmt.Errorf("workflow hooks 未配置完整")
	}

	prepareResult, err := hooks.Prepare(options.PrepareOperations, options.PrepareOverwrite)
	if err != nil {
		return Result{}, err
	}

	compressOptions := options.CompressOptions
	compressOptions.InputDir = prepareResult.OutputDir
	compressResult, err := hooks.Compress(compressOptions)
	if err != nil {
		return Result{Prepare: prepareResult}, err
	}

	uploadResult, err := hooks.Upload(compressResult.OutputDir)
	if err != nil {
		return Result{Prepare: prepareResult, Compress: compressResult}, err
	}

	return Result{
		Prepare:  prepareResult,
		Compress: compressResult,
		Upload:   uploadResult,
	}, nil
}
