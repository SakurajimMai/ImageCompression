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

func TestWithDefaultUploadRemotePathUsesCustomPathForS3(t *testing.T) {
	inputDir := filepath.Join(t.TempDir(), "山崎怜 NO.001 华盛顿兔女郎 [45P-187M]")

	cfg := config.Default().Upload
	cfg.Protocol = "s3"
	cfg.S3.Prefix = ""
	cfg.CustomPath = "山崎怜/华盛顿兔女郎"

	got := withDefaultUploadRemotePath(cfg, inputDir)
	if got.S3.Prefix != "山崎怜/华盛顿兔女郎" {
		t.Fatalf("S3 prefix = %q, want %q", got.S3.Prefix, "山崎怜/华盛顿兔女郎")
	}
}

func TestWithDefaultUploadRemotePathCustomPathAppendsToBaseForS3(t *testing.T) {
	cfg := config.Default().Upload
	cfg.Protocol = "s3"
	cfg.S3.Prefix = "images"
	cfg.CustomPath = "album/spring"

	got := withDefaultUploadRemotePath(cfg, filepath.Join(t.TempDir(), "raw"))
	if got.S3.Prefix != "images/album/spring" {
		t.Fatalf("S3 prefix = %q, want images/album/spring", got.S3.Prefix)
	}
}

func TestWithDefaultUploadRemotePathCustomPathForFTPAndSFTP(t *testing.T) {
	cfg := config.Default().Upload
	cfg.Protocol = "ftp"
	cfg.FTP.RemoteDir = ""
	cfg.CustomPath = "山崎怜/华盛顿兔女郎"

	got := withDefaultUploadRemotePath(cfg, filepath.Join(t.TempDir(), "raw"))
	if got.FTP.RemoteDir != "/山崎怜/华盛顿兔女郎" {
		t.Fatalf("FTP remote_dir = %q, want /山崎怜/华盛顿兔女郎", got.FTP.RemoteDir)
	}

	cfg.Protocol = "sftp"
	cfg.SFTP.RemoteDir = "/var/www"
	got = withDefaultUploadRemotePath(cfg, filepath.Join(t.TempDir(), "raw"))
	if got.SFTP.RemoteDir != "/var/www/山崎怜/华盛顿兔女郎" {
		t.Fatalf("SFTP remote_dir = %q, want /var/www/山崎怜/华盛顿兔女郎", got.SFTP.RemoteDir)
	}
}

func TestWithDefaultUploadRemotePathCustomPathTrimsSurroundingSlashes(t *testing.T) {
	cfg := config.Default().Upload
	cfg.Protocol = "s3"
	cfg.S3.Prefix = ""
	cfg.CustomPath = "  /山崎怜/华盛顿兔女郎/  "

	got := withDefaultUploadRemotePath(cfg, filepath.Join(t.TempDir(), "raw"))
	if got.S3.Prefix != "山崎怜/华盛顿兔女郎" {
		t.Fatalf("S3 prefix = %q, want %q", got.S3.Prefix, "山崎怜/华盛顿兔女郎")
	}
}
