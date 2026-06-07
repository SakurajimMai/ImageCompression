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

// ProgressEvent is emitted once per file as it is being processed. The
// caller is expected to be safe to invoke from a goroutine but Wails
// dispatches the event synchronously on the upload loop.
//
//   - Start=true  : a new upload batch has begun, Total > 0
//   - Done=true   : the batch is finished, Total/Uploaded/Failed are final
//   - Start/Done are mutually exclusive with URL/Error; URL/Error are
//     mutually exclusive with each other and only set while a single file
//     is being processed.
type ProgressEvent struct {
	Current   int    `json:"current"`
	Total     int    `json:"total"`
	Message   string `json:"message"`
	URL       string `json:"url,omitempty"`
	Error     string `json:"error,omitempty"`
	Start     bool   `json:"start,omitempty"`
	Done      bool   `json:"done,omitempty"`
	Uploaded  int    `json:"uploaded"`
	Failed    int    `json:"failed"`
	SourceDir string `json:"sourceDir"`
}

type ProgressFunc func(event ProgressEvent)

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
	if progress != nil {
		progress(ProgressEvent{
			Start:     true,
			Total:     len(files),
			Message:   fmt.Sprintf("准备上传 %d 个文件", len(files)),
			SourceDir: inputDir,
		})
	}
	if err := uploader.Connect(); err != nil {
		if progress != nil {
			progress(ProgressEvent{
				Done:      true,
				Total:     len(files),
				Message:   fmt.Sprintf("连接失败：%s", err),
				Error:     err.Error(),
				SourceDir: inputDir,
			})
		}
		return result, err
	}
	defer uploader.Disconnect()

	for index, file := range files {
		remoteName, err := BuildRemoteName(inputDir, file, options.Recursive)
		if err != nil {
			result.Errors = append(result.Errors, err.Error())
			result.FailedFiles++
			if progress != nil {
				progress(ProgressEvent{
					Current:   index + 1,
					Total:     len(files),
					Message:   fmt.Sprintf("跳过: %s (%s)", file, err),
					Error:     err.Error(),
					Uploaded:  result.UploadedFiles,
					Failed:    result.FailedFiles,
					SourceDir: inputDir,
				})
			}
			continue
		}
		if progress != nil {
			progress(ProgressEvent{
				Current:   index + 1,
				Total:     len(files),
				Message:   fmt.Sprintf("上传中: %s", remoteName),
				Uploaded:  result.UploadedFiles,
				Failed:    result.FailedFiles,
				SourceDir: inputDir,
			})
		}
		url, err := uploader.UploadFile(file, remoteName)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("%s: %s", remoteName, err))
			result.FailedFiles++
			if progress != nil {
				progress(ProgressEvent{
					Current:   index + 1,
					Total:     len(files),
					Message:   fmt.Sprintf("失败: %s", remoteName),
					Error:     err.Error(),
					Uploaded:  result.UploadedFiles,
					Failed:    result.FailedFiles,
					SourceDir: inputDir,
				})
			}
			continue
		}
		result.URLs = append(result.URLs, url)
		result.UploadedFiles++
		if progress != nil {
			progress(ProgressEvent{
				Current:   index + 1,
				Total:     len(files),
				Message:   fmt.Sprintf("已上传: %s", remoteName),
				URL:       url,
				Uploaded:  result.UploadedFiles,
				Failed:    result.FailedFiles,
				SourceDir: inputDir,
			})
		}
	}
	if progress != nil {
		progress(ProgressEvent{
			Done:      true,
			Current:   len(files),
			Total:     len(files),
			Message:   fmt.Sprintf("上传完成：%d 成功 / %d 失败", result.UploadedFiles, result.FailedFiles),
			Uploaded:  result.UploadedFiles,
			Failed:    result.FailedFiles,
			SourceDir: inputDir,
		})
	}
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
