//go:build windows

package compress

import (
	"os/exec"
	"testing"
)

func TestConfigureHiddenCommandHidesWindowsConsole(t *testing.T) {
	cmd := exec.Command("cmd", "/c", "exit")

	configureHiddenCommand(cmd)

	if cmd.SysProcAttr == nil {
		t.Fatal("SysProcAttr was not configured")
	}
	if !cmd.SysProcAttr.HideWindow {
		t.Fatal("HideWindow was not enabled")
	}
	if cmd.SysProcAttr.CreationFlags&createNoWindow == 0 {
		t.Fatalf("CreationFlags = %#x, want CREATE_NO_WINDOW", cmd.SysProcAttr.CreationFlags)
	}
}
