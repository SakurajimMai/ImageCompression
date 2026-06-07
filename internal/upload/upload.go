package upload

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type Uploader interface {
	Connect() error
	UploadFile(localPath string, remoteName string) (string, error)
	Disconnect() error
}

type Options struct {
	Recursive bool
}

type Result struct {
	TotalFiles    int      `json:"totalFiles"`
	UploadedFiles int      `json:"uploadedFiles"`
	FailedFiles   int      `json:"failedFiles"`
	URLs          []string `json:"urls"`
	Errors        []string `json:"errors"`
}

type ProgressFunc func(current int, total int, message string)

func UploadDirectory(uploader Uploader, inputDir string, options Options, progress ProgressFunc) (Result, error) {
	files, err := collectFiles(inputDir, options.Recursive)
	if err != nil {
		return Result{}, err
	}
	return uploadFiles(uploader, inputDir, files, options, progress)
}

func UploadFiles(uploader Uploader, inputDir string, files []string, options Options) (Result, error) {
	return uploadFiles(uploader, inputDir, files, options, nil)
}

func uploadFiles(uploader Uploader, inputDir string, files []string, options Options, progress ProgressFunc) (Result, error) {
	result := Result{
		TotalFiles: len(files),
		URLs:       []string{},
		Errors:     []string{},
	}
	if err := uploader.Connect(); err != nil {
		return result, err
	}
	defer uploader.Disconnect()

	for index, file := range files {
		remoteName, err := BuildRemoteName(inputDir, file, options.Recursive)
		if err != nil {
			result.Errors = append(result.Errors, err.Error())
			continue
		}
		if progress != nil {
			progress(index+1, len(files), fmt.Sprintf("上传: %s", remoteName))
		}
		url, err := uploader.UploadFile(file, remoteName)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("%s: %s", remoteName, err))
			continue
		}
		result.URLs = append(result.URLs, url)
		result.UploadedFiles++
	}
	result.FailedFiles = len(result.Errors)
	return result, nil
}

func BuildRemoteName(inputDir string, localPath string, recursive bool) (string, error) {
	if !recursive {
		return filepath.Base(localPath), nil
	}
	rel, err := filepath.Rel(filepath.Clean(inputDir), filepath.Clean(localPath))
	if err != nil {
		return "", err
	}
	return filepath.ToSlash(rel), nil
}

func BuildPublicURL(baseURL string, remoteName string) string {
	if baseURL == "" {
		return remoteName
	}
	return strings.TrimRight(baseURL, "/") + "/" + strings.TrimLeft(filepath.ToSlash(remoteName), "/")
}

func collectFiles(inputDir string, recursive bool) ([]string, error) {
	var files []string
	if recursive {
		err := filepath.Walk(inputDir, func(path string, info os.FileInfo, err error) error {
			if err != nil || info == nil || info.IsDir() {
				return nil
			}
			files = append(files, path)
			return nil
		})
		if err != nil {
			return nil, err
		}
	} else {
		entries, err := os.ReadDir(inputDir)
		if err != nil {
			return nil, err
		}
		for _, entry := range entries {
			if entry.Type().IsRegular() {
				files = append(files, filepath.Join(inputDir, entry.Name()))
			}
		}
	}
	sort.Strings(files)
	return files, nil
}
