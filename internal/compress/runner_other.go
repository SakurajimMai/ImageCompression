//go:build !windows

package compress

import "os/exec"

func configureHiddenCommand(cmd *exec.Cmd) {}
