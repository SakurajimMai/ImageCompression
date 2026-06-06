package compress

import (
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"strings"

	xdraw "golang.org/x/image/draw"
)

func prepareEncoderInput(inputPath string, outputPath string, params Params) (string, func(), error) {
	if !shouldResize(params) {
		return inputPath, func() {}, nil
	}

	source, err := os.Open(inputPath)
	if err != nil {
		return "", nil, err
	}
	defer source.Close()

	img, _, err := image.Decode(source)
	if err != nil {
		return "", nil, fmt.Errorf("缩放失败: %w", err)
	}
	resized, err := resizeImage(img, params)
	if err != nil {
		return "", nil, err
	}

	if err := os.MkdirAll(filepath.Dir(outputPath), 0o755); err != nil {
		return "", nil, err
	}
	temp, err := os.CreateTemp(filepath.Dir(outputPath), "_resized-*.png")
	if err != nil {
		return "", nil, err
	}
	tempPath := temp.Name()
	if err := png.Encode(temp, resized); err != nil {
		_ = temp.Close()
		_ = os.Remove(tempPath)
		return "", nil, err
	}
	if err := temp.Close(); err != nil {
		_ = os.Remove(tempPath)
		return "", nil, err
	}
	return tempPath, func() { _ = os.Remove(tempPath) }, nil
}

func shouldResize(params Params) bool {
	mode := strings.ToLower(strings.TrimSpace(params.ResizeMode))
	return mode != "" && mode != "none" && params.ResizeValue > 0
}

func resizeImage(img image.Image, params Params) (image.Image, error) {
	mode := strings.ToLower(strings.TrimSpace(params.ResizeMode))
	value := params.ResizeValue
	if mode == "" || mode == "none" || value <= 0 {
		return img, nil
	}

	bounds := img.Bounds()
	width := bounds.Dx()
	height := bounds.Dy()
	if width <= 0 || height <= 0 {
		return nil, fmt.Errorf("缩放失败: 图片尺寸无效")
	}

	targetWidth := width
	targetHeight := height
	keepRatio := params.KeepAspectRatio
	if !keepRatio && mode == "width" {
		targetWidth = value
	} else if !keepRatio && mode == "height" {
		targetHeight = value
	} else {
		keepRatio = true
	}

	switch mode {
	case "width":
		targetWidth = value
		if keepRatio {
			targetHeight = maxInt(1, int(float64(height)*(float64(value)/float64(width))))
		}
	case "height":
		targetHeight = value
		if keepRatio {
			targetWidth = maxInt(1, int(float64(width)*(float64(value)/float64(height))))
		}
	case "percent":
		targetWidth = maxInt(1, int(float64(width)*float64(value)/100))
		targetHeight = maxInt(1, int(float64(height)*float64(value)/100))
	case "long_edge":
		longEdge := maxInt(width, height)
		if longEdge <= value {
			return img, nil
		}
		scale := float64(value) / float64(longEdge)
		targetWidth = maxInt(1, int(float64(width)*scale))
		targetHeight = maxInt(1, int(float64(height)*scale))
	case "short_edge":
		shortEdge := minIntValue(width, height)
		if shortEdge <= value {
			return img, nil
		}
		scale := float64(value) / float64(shortEdge)
		targetWidth = maxInt(1, int(float64(width)*scale))
		targetHeight = maxInt(1, int(float64(height)*scale))
	case "fit":
		scale := minFloat(float64(value)/float64(width), float64(value)/float64(height))
		if scale >= 1 {
			return img, nil
		}
		targetWidth = maxInt(1, int(float64(width)*scale))
		targetHeight = maxInt(1, int(float64(height)*scale))
	case "fill":
		scale := maxFloatValue(float64(value)/float64(width), float64(value)/float64(height))
		scaledWidth := maxInt(1, int(float64(width)*scale))
		scaledHeight := maxInt(1, int(float64(height)*scale))
		scaled := scaleImage(img, scaledWidth, scaledHeight)
		left := maxInt(0, (scaledWidth-value)/2)
		top := maxInt(0, (scaledHeight-value)/2)
		return cropImage(scaled, image.Rect(left, top, left+value, top+value)), nil
	case "exact":
		targetWidth = value
		targetHeight = value
	default:
		return img, nil
	}

	return scaleImage(img, maxInt(1, targetWidth), maxInt(1, targetHeight)), nil
}

func scaleImage(img image.Image, width int, height int) *image.RGBA {
	dst := image.NewRGBA(image.Rect(0, 0, width, height))
	xdraw.CatmullRom.Scale(dst, dst.Bounds(), img, img.Bounds(), xdraw.Over, nil)
	return dst
}

func cropImage(img image.Image, rect image.Rectangle) image.Image {
	dst := image.NewRGBA(image.Rect(0, 0, rect.Dx(), rect.Dy()))
	xdraw.Draw(dst, dst.Bounds(), img, rect.Min, xdraw.Src)
	return dst
}

func minIntValue(a int, b int) int {
	if a < b {
		return a
	}
	return b
}

func maxInt(a int, b int) int {
	if a > b {
		return a
	}
	return b
}

func minFloat(a float64, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func maxFloatValue(a float64, b float64) float64 {
	if a > b {
		return a
	}
	return b
}
