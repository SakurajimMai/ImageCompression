package main

import (
	"path/filepath"
	"testing"

	"imagecompression/internal/config"
)

func TestWithDefaultUploadRemotePathUsesSourceDirectoryName(t *testing.T) {
	folder := "山崎怜 NO.001 华盛顿兔女郎 [45P-187M]"
	inputDir := filepath.Join(t.TempDir(), folder)

	cfg := config.Default().Upload
	cfg.Protocol = "s3"
	cfg.S3.Prefix = ""

	got := withDefaultUploadRemotePath(cfg, inputDir)
	if got.S3.Prefix != folder {
		t.Fatalf("S3 prefix = %q, want %q", got.S3.Prefix, folder)
	}
}

func TestWithDefaultUploadRemotePathTreatsRootRemoteDirAsUnset(t *testing.T) {
	folder := "album"
	inputDir := filepath.Join(t.TempDir(), folder)

	cfg := config.Default().Upload
	cfg.Protocol = "ftp"
	cfg.FTP.RemoteDir = "/"

	got := withDefaultUploadRemotePath(cfg, inputDir)
	if got.FTP.RemoteDir != "/"+folder {
		t.Fatalf("FTP remote_dir = %q, want /%s", got.FTP.RemoteDir, folder)
	}

	cfg.Protocol = "sftp"
	cfg.SFTP.RemoteDir = ""
	got = withDefaultUploadRemotePath(cfg, inputDir)
	if got.SFTP.RemoteDir != "/"+folder {
		t.Fatalf("SFTP remote_dir = %q, want /%s", got.SFTP.RemoteDir, folder)
	}
}

func TestWithDefaultUploadRemotePathKeepsConfiguredPath(t *testing.T) {
	cfg := config.Default().Upload
	cfg.Protocol = "s3"
	cfg.S3.Prefix = "custom/path"
	if got := withDefaultUploadRemotePath(cfg, filepath.Join(t.TempDir(), "album")); got.S3.Prefix != "custom/path" {
		t.Fatalf("configured S3 prefix changed to %q", got.S3.Prefix)
	}

	cfg.Protocol = "ftp"
	cfg.FTP.RemoteDir = "/public/images"
	if got := withDefaultUploadRemotePath(cfg, filepath.Join(t.TempDir(), "album")); got.FTP.RemoteDir != "/public/images" {
		t.Fatalf("configured FTP remote_dir changed to %q", got.FTP.RemoteDir)
	}
}
