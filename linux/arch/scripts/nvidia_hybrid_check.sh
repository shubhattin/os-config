#!/usr/bin/env bash
# Verify hybrid NVIDIA + SDDM guardrails stay in place.
# Usage: ./nvidia_hybrid_check.sh
set -euo pipefail

ok=0
fail=0

pass() { echo "OK  $*"; ok=$((ok + 1)); }
warn() { echo "WARN $*"; }
bad()  { echo "FAIL $*"; fail=$((fail + 1)); }

echo "=== NVIDIA / hybrid SDDM guardrail check ==="

# Packages: current open stack only
if pacman -Q nvidia-open &>/dev/null || pacman -Q nvidia-open-dkms &>/dev/null; then
  pass "nvidia-open (or dkms) installed"
else
  bad "missing nvidia-open / nvidia-open-lts — see linux/arch/nvidia.md"
fi
if pacman -Q nvidia-utils &>/dev/null; then
  pass "nvidia-utils installed"
else
  bad "missing nvidia-utils"
fi
if pacman -Qqs '^nvidia-580xx' 2>/dev/null | rg -q .; then
  bad "legacy nvidia-580xx-* still installed — remove it"
else
  pass "no nvidia-580xx legacy packages"
fi
if pacman -Q dkms &>/dev/null && ! pacman -Q nvidia-open-dkms &>/dev/null; then
  warn "dkms installed but unused (ok to remove: sudo pacman -Rns dkms)"
fi

# Forbidden package name trap
if pacman -Q nvidia &>/dev/null && ! pacman -Q nvidia-open &>/dev/null; then
  bad "package named 'nvidia' present — prefer nvidia-open (see nvidia.md)"
fi

# Modeset
if [[ -f /etc/modprobe.d/nvidia-drm.conf ]] && rg -q 'modeset=1' /etc/modprobe.d/nvidia-drm.conf; then
  pass "nvidia-drm modeset=1"
else
  bad "missing /etc/modprobe.d/nvidia-drm.conf with modeset=1"
fi

# Early modules in mkinitcpio
if rg -q 'nvidia_drm' /etc/mkinitcpio.conf; then
  pass "mkinitcpio MODULES includes nvidia*"
else
  bad "add MODULES=(nvidia nvidia_modeset nvidia_drm) to /etc/mkinitcpio.conf"
fi

# Intel-only Xorg (critical)
xorg=/etc/X11/xorg.conf.d/20-intel-only.conf
if [[ -f $xorg ]] && rg -q 'AutoAddGPU' "$xorg" && rg -q 'IntelScreen' "$xorg"; then
  pass "Intel-only Xorg present ($xorg)"
else
  bad "missing $xorg — WITHOUT THIS SDDM/X CAN BLACK-SCREEN ON HYBRID"
fi

# SDDM astronaut deps
if [[ -f /etc/sddm.conf.d/virtualkbd.conf ]] && rg -q 'qtvirtualkeyboard' /etc/sddm.conf.d/virtualkbd.conf; then
  if pacman -Q qt6-virtualkeyboard &>/dev/null; then
    pass "qt6-virtualkeyboard installed (virtualkbd.conf present)"
  else
    bad "virtualkbd.conf set but qt6-virtualkeyboard NOT installed"
  fi
else
  pass "no virtualkbd InputMethod (or not configured)"
fi

# Runtime (if modules loaded)
if lsmod | rg -q '^nvidia\b'; then
  ver=$(modinfo -F version nvidia 2>/dev/null || true)
  util=$(pacman -Q nvidia-utils 2>/dev/null | awk '{print $2}' | cut -d- -f1)
  if [[ -n $ver && -n $util && $util == $ver* ]]; then
    pass "loaded nvidia module version $ver matches utils"
  else
    warn "nvidia loaded ($ver) vs utils ($util) — reboot if you just switched stacks"
  fi
fi

if systemctl is-active --quiet sddm; then
  if journalctl -u sddm -b --no-pager 2>/dev/null | rg -q 'Message received from greeter: Connect'; then
    pass "SDDM greeter connected this boot"
  else
    warn "SDDM active but no greeter Connect yet — check VT (Ctrl+Alt+F1/F2) and Xorg.0.log"
  fi
fi

echo
echo "Result: $ok ok, $fail fail"
if (( fail > 0 )); then
  echo "See: ~/.config/os-config/linux/arch/nvidia.md"
  exit 1
fi
exit 0
