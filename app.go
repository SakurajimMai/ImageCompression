package main

import (
	"context"
	"os/exec"
	"time"

	"imagecompression/internal/compress"
	"imagecompression/internal/config"
	"imagecompression/internal/core"
	"imagecompression/internal/prepare"
	"imagecompression/internal/upload"
	"imagecompression/internal/workflow"
)

type App struct {
	ctx context.Context
}

func NewApp() *App {
	return &App{}
}

func (a *App) Startup(ctx context.Context) {
	a.ctx = ctx
}

func (a *App) LoadConfig() (config.Config, error) {
	path, err := config.DefaultPath()
	if err != nil {
		return config.Default(), err
	}
	return config.Load(path)
}

func (a *App) SaveConfig(cfg config.Config) error {
	path, err := config.DefaultPath()
	if err != nil {
		return err
	}
	return config.Save(path, cfg)
}

func (a *App) ScanDirectory(path string, recursive bool) (core.ScanResult, error) {
	return core.ScanDirectory(path, recursive)
}

func (a *App) PlanPrepare(scan prepare.ScanInput, outputDir string, options prepare.Options) ([]prepare.Operation, error) {
	return prepare.PlanOperations(scan, outputDir, options)
}

func (a *App) ExecutePrepare(operations []prepare.Operation, overwrite bool) (prepare.Result, error) {
	return prepare.ExecuteOperations(operations, overwrite, nil)
}

func (a *App) PreviewAVIFCommand(inputPath string, outputPath string, params compress.Params, avifencPath string) []string {
	resolved, err := compress.ResolveAVIFEncPath(avifencPath)
	if err == nil {
		avifencPath = resolved
	} else if avifencPath == "" {
		avifencPath = "avifenc"
	}
	return compress.BuildAVIFCommand(avifencPath, inputPath, outputPath, params)
}

func (a *App) CompressAVIF(inputPath string, outputPath string, params compress.Params, avifencPath string) (compress.Result, error) {
	ctx, cancel := context.WithTimeout(a.ctx, 10*time.Minute)
	defer cancel()
	return compress.RunAVIF(ctx, avifencPath, inputPath, outputPath, params, nil)
}

func (a *App) CompressDirectory(options compress.BatchOptions) (compress.BatchResult, error) {
	ctx, cancel := context.WithTimeout(a.ctx, 30*time.Minute)
	defer cancel()
	return compress.CompressDirectory(ctx, options, nil, nil)
}

func (a *App) BuildPreviewItems(result compress.BatchResult, limit int) []compress.PreviewItem {
	return compress.BuildPreviewItems(result, limit)
}

func (a *App) ReadImageDataURL(path string) (string, error) {
	return compress.ReadImageDataURL(path)
}

type RunAllOptions struct {
	PrepareOperations []prepare.Operation   `json:"prepareOperations"`
	PrepareOverwrite  bool                  `json:"prepareOverwrite"`
	CompressOptions   compress.BatchOptions `json:"compressOptions"`
	UploadConfig      config.UploadConfig   `json:"uploadConfig"`
	UploadRecursive   bool                  `json:"uploadRecursive"`
}

func (a *App) RunPrepareCompressUpload(options RunAllOptions) (workflow.Result, error) {
	ctx, cancel := context.WithTimeout(a.ctx, 45*time.Minute)
	defer cancel()
	return workflow.RunPrepareCompressUpload(workflow.Options{
		PrepareOperations: options.PrepareOperations,
		PrepareOverwrite:  options.PrepareOverwrite,
		CompressOptions:   options.CompressOptions,
	}, workflow.Hooks{
		Prepare: func(ops []prepare.Operation, overwrite bool) (prepare.Result, error) {
			return prepare.ExecuteOperations(ops, overwrite, nil)
		},
		Compress: func(batchOptions compress.BatchOptions) (compress.BatchResult, error) {
			return compress.CompressDirectory(ctx, batchOptions, nil, nil)
		},
		Upload: func(inputDir string) (upload.Result, error) {
			return upload.UploadDirectory(buildUploader(options.UploadConfig), inputDir, upload.Options{Recursive: options.UploadRecursive}, nil)
		},
	})
}

func (a *App) UploadDirectory(inputDir string, recursive bool, cfg config.UploadConfig) (upload.Result, error) {
	uploader := buildUploader(cfg)
	return upload.UploadDirectory(uploader, inputDir, upload.Options{Recursive: recursive}, nil)
}

func (a *App) CheckAVIFEnc(avifencPath string) (string, error) {
	resolved, err := compress.ResolveAVIFEncPath(avifencPath)
	if err != nil {
		return "", err
	}
	out, err := exec.Command(resolved, "--version").CombinedOutput()
	return string(out), err
}

func buildUploader(cfg config.UploadConfig) upload.Uploader {
	proxy := proxyURL(cfg)
	switch cfg.Protocol {
	case "ftp":
		return upload.NewFTPUploader(upload.FTPConfig{
			Host:      cfg.FTP.Host,
			Port:      cfg.FTP.Port,
			Username:  cfg.FTP.Username,
			Password:  cfg.FTP.Password,
			RemoteDir: cfg.FTP.RemoteDir,
			BaseURL:   cfg.FTP.BaseURL,
			ProxyURL:  proxy,
		})
	case "sftp":
		return upload.NewSFTPUploader(upload.SFTPConfig{
			Host:       cfg.SFTP.Host,
			Port:       cfg.SFTP.Port,
			Username:   cfg.SFTP.Username,
			Password:   cfg.SFTP.Password,
			KeyPath:    cfg.SFTP.KeyPath,
			RemoteDir:  cfg.SFTP.RemoteDir,
			BaseURL:    cfg.SFTP.BaseURL,
			DomainRoot: cfg.SFTP.DomainRoot,
			ProxyURL:   proxy,
		})
	default:
		return upload.NewS3Uploader(upload.S3Config{
			Endpoint:     cfg.S3.Endpoint,
			Bucket:       cfg.S3.Bucket,
			AccessKey:    cfg.S3.AccessKey,
			SecretKey:    cfg.S3.SecretKey,
			Region:       cfg.S3.Region,
			Prefix:       cfg.S3.Prefix,
			CustomDomain: cfg.S3.Domain,
			ProxyURL:     proxy,
		})
	}
}

func proxyURL(cfg config.UploadConfig) string {
	return cfg.Proxy.EffectiveURL()
}
