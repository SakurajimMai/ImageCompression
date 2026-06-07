package core

import (
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

var imageExtensions = map[string]struct{}{
	".jpg": {}, ".jpeg": {}, ".png": {}, ".webp": {}, ".bmp": {}, ".gif": {},
	".tiff": {}, ".tif": {}, ".heic": {}, ".heif": {}, ".avif": {},
}

var videoExtensions = map[string]struct{}{
	".mp4": {}, ".mov": {}, ".avi": {}, ".mkv": {}, ".wmv": {}, ".flv": {}, ".webm": {}, ".y4m": {},
}

type ScanResult struct {
	BaseDir   string   `json:"baseDir"`
	Images    []string `json:"images"`
	Videos    []string `json:"videos"`
	Others    []string `json:"others"`
	TotalSize int64    `json:"totalSize"`
	Subdirs   int      `json:"subdirs"`
}

func ScanDirectory(root string, recursive bool) (ScanResult, error) {
	root = filepath.Clean(root)
	result := ScanResult{
		BaseDir: root,
		Images:  []string{},
		Videos:  []string{},
		Others:  []string{},
	}
	seenDirs := map[string]struct{}{}

	visit := func(path string, info os.FileInfo, err error) error {
		if err != nil || info == nil || info.IsDir() {
			return nil
		}
		result.TotalSize += info.Size()
		if parent := filepath.Dir(path); filepath.Clean(parent) != root {
			seenDirs[parent] = struct{}{}
		}
		switch strings.ToLower(filepath.Ext(path)) {
		case extensionIn(imageExtensions, filepath.Ext(path)):
			result.Images = append(result.Images, path)
		case extensionIn(videoExtensions, filepath.Ext(path)):
			result.Videos = append(result.Videos, path)
		default:
			result.Others = append(result.Others, path)
		}
		return nil
	}

	if recursive {
		if err := filepath.Walk(root, visit); err != nil {
			return result, err
		}
	} else {
		entries, err := os.ReadDir(root)
		if err != nil {
			return result, err
		}
		for _, entry := range entries {
			info, err := entry.Info()
			if err != nil {
				continue
			}
			if err := visit(filepath.Join(root, entry.Name()), info, nil); err != nil {
				return result, err
			}
		}
	}

	result.Subdirs = len(seenDirs)
	naturalSort(result.Images)
	naturalSort(result.Videos)
	naturalSort(result.Others)
	return result, nil
}

func extensionIn(set map[string]struct{}, ext string) string {
	normalized := strings.ToLower(ext)
	if _, ok := set[normalized]; ok {
		return normalized
	}
	return "\x00"
}

var numberRE = regexp.MustCompile(`\d+|\D+`)

func naturalSort(values []string) {
	sort.Slice(values, func(i, j int) bool {
		return naturalLess(filepath.Base(values[i]), filepath.Base(values[j]))
	})
}

func naturalLess(a, b string) bool {
	aa := numberRE.FindAllString(strings.ToLower(a), -1)
	bb := numberRE.FindAllString(strings.ToLower(b), -1)
	for i := 0; i < len(aa) && i < len(bb); i++ {
		ai, aErr := strconv.Atoi(aa[i])
		bi, bErr := strconv.Atoi(bb[i])
		if aErr == nil && bErr == nil {
			if ai != bi {
				return ai < bi
			}
			continue
		}
		if aa[i] != bb[i] {
			return aa[i] < bb[i]
		}
	}
	return len(aa) < len(bb)
}
