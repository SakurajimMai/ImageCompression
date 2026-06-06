package compress

type PreviewItem struct {
	InputPath      string  `json:"inputPath"`
	OutputPath     string  `json:"outputPath"`
	OriginalSize   int64   `json:"originalSize"`
	CompressedSize int64   `json:"compressedSize"`
	SavedPercent   float64 `json:"savedPercent"`
}

func BuildPreviewItems(result BatchResult, limit int) []PreviewItem {
	if limit <= 0 {
		limit = len(result.Results)
	}
	items := make([]PreviewItem, 0, minInt(limit, len(result.Results)))
	for _, item := range result.Results {
		if !item.Success {
			continue
		}
		preview := PreviewItem{
			InputPath:      item.InputPath,
			OutputPath:     item.OutputPath,
			OriginalSize:   item.OriginalSize,
			CompressedSize: item.CompressedSize,
			SavedPercent:   savedPercent(item.OriginalSize, item.CompressedSize),
		}
		items = append(items, preview)
		if len(items) >= limit {
			break
		}
	}
	return items
}

func savedPercent(originalSize int64, compressedSize int64) float64 {
	if originalSize <= 0 {
		return 0
	}
	return maxFloat(0, 100-(float64(compressedSize)/float64(originalSize))*100)
}

func minInt(a int, b int) int {
	if a < b {
		return a
	}
	return b
}

func maxFloat(a float64, b float64) float64 {
	if a > b {
		return a
	}
	return b
}
