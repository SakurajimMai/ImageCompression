package compress

import (
	"encoding/base64"
	"fmt"
	"net/http"
	"os"
)

func ReadImageDataURL(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	contentType := http.DetectContentType(data)
	if len(contentType) < len("image/") || contentType[:len("image/")] != "image/" {
		return "", fmt.Errorf("不是可预览图片: %s", path)
	}
	return "data:" + contentType + ";base64," + base64.StdEncoding.EncodeToString(data), nil
}
