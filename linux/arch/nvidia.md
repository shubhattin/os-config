# NVIDIA Drivers (Arch / EndeavourOS)

For Turing+ GPUs (RTX 20xx and newer), including hybrid Intel + NVIDIA laptops.
Prefer [ArchWiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA) / [NVIDIA Optimus](https://wiki.archlinux.org/title/NVIDIA_Optimus) if package names change.

## Packages (use only these)

| Role | Package |
|------|---------|
| Kernel module (`linux`) | `nvidia-open` |
| Kernel module (`linux-lts`) | `nvidia-open-lts` |
| Userspace | `nvidia-utils` |
| Settings UI | `nvidia-settings` |
| PRIME offload helper | `nvidia-prime` |
| SDDM astronaut / virtual keyboard | `qt6-virtualkeyboard` |
| Optional | `opencl-nvidia` `cuda` `cudnn` |

Do **not** install:

- `nvidia` / `nvidia-lts` / `nvidia-dkms` — obsolete; with chaotic-aur, `nvidia` can pull a **legacy** branch
- `nvidia-*-dkms` — not needed with stock `linux` + `linux-lts`
- Any `nvidia-580xx-*` / other legacy xx branches
- Mixing versions across module / utils / settings

## Install (do all steps — hybrid needs the Xorg file)

> **Do not remove** these after install: `20-intel-only.conf`, `nvidia-drm.conf` modeset, mkinitcpio `MODULES=(nvidia…)`, `qt6-virtualkeyboard` (if astronaut/virtualkbd). Removing any of them can bring back a black SDDM.

```bash
# 1) packages
sudo pacman -S nvidia-open nvidia-open-lts nvidia-utils nvidia-settings nvidia-prime qt6-virtualkeyboard
# optional: sudo pacman -S opencl-nvidia cuda cudnn
# Intel side (hybrid): sudo pacman -S intel-ucode mesa intel-media-driver libva-mesa-driver

# 2) DRM KMS
sudo bash -c 'echo "options nvidia-drm modeset=1" > /etc/modprobe.d/nvidia-drm.conf'

# 3) Early-load NVIDIA in initramfs (avoids SDDM/X racing a late NVIDIA hotplug)
# If MODULES=() is empty:
sudo sed -i 's/^MODULES=()/MODULES=(nvidia nvidia_modeset nvidia_drm)/' /etc/mkinitcpio.conf
# If MODULES already has other entries, add: nvidia nvidia_modeset nvidia_drm into that list.

# 3b) Also load at systemd modules-load (belt and suspenders)
sudo tee /etc/modules-load.d/nvidia.conf >/dev/null <<'EOF'
nvidia
nvidia_modeset
nvidia_drm
EOF

# 3c) Start SDDM only after modules-load
sudo mkdir -p /etc/systemd/system/sddm.service.d
sudo tee /etc/systemd/system/sddm.service.d/10-after-modules.conf >/dev/null <<'EOF'
[Unit]
After=systemd-modules-load.service
Wants=systemd-modules-load.service
EOF
sudo systemctl daemon-reload

# 4) REQUIRED on hybrid Optimus laptops — Intel-only X (see next section)
#    BusID from: lspci -nn | grep -E 'VGA|3D'   (e.g. 00:02.0 → PCI:0:2:0)
sudo tee /etc/X11/xorg.conf.d/20-intel-only.conf >/dev/null <<'EOF'
# DO NOT REMOVE — required on Intel+NVIDIA Optimus (see nvidia.md)
Section "ServerLayout"
    Identifier "Layout0"
    Screen 0 "IntelScreen"
EndSection

Section "Device"
    Identifier "IntelGraphics"
    Driver "modesetting"
    BusID "PCI:0:2:0"
EndSection

Section "Screen"
    Identifier "IntelScreen"
    Device "IntelGraphics"
EndSection

Section "ServerFlags"
    Option "AutoAddGPU" "false"
EndSection
EOF

# 5) rebuild initramfs and reboot
sudo mkinitcpio -P
sudo reboot
```

If you only boot one kernel, install just that module package (`nvidia-open` **or** `nvidia-open-lts`), not both.

Desktop-only NVIDIA (no Intel iGPU) can skip step 4. **This Ideapad / all Optimus hybrids must not skip it.**

### Regression check

After changes or driver updates:

```bash
~/.config/os-config/linux/arch/scripts/nvidia_hybrid_check.sh
```

All checks should print `OK`. Fix any `FAIL` before reboot.

## Why the Intel-only Xorg file is required (hybrid)

On Optimus, Intel drives the panel; NVIDIA often has no internal connector. If X modesets NVIDIA as a second GPU:

`modeset(G0): Failed to create pixmap` → `Fatal server error: failed to create screen resources` → SDDM black / greeter hang.

Intel-only X keeps displays on Intel. NVIDIA stays available for **PRIME offload** via `/dev/dri/renderD*`.

Confirm BusID matches your machine (`lspci` → `PCI:<bus>:<dev>:<func>` with decimal numbers).

## After reboot — verify

```bash
cat /sys/module/nvidia_drm/parameters/modeset   # Y
lsinitcpio /boot/initramfs-linux.img | grep nvidia
nvidia-smi                                    # same series as nvidia-utils
pacman -Q | grep -E 'nvidia|libxnvctrl'       # no 580xx / dkms
test -f /etc/X11/xorg.conf.d/20-intel-only.conf && echo 'intel-only xorg: ok'
lsmod | grep nouveau                          # empty
prime-run glxinfo | grep 'OpenGL renderer'
```

## Hybrid / PRIME

```bash
prime-run <app>
# or: __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia <app>
```

Helper: [`scripts/prime-run`](./scripts/prime-run). Prefer PRIME over `optimus-manager` / `envycontrol`.

## SDDM (astronaut theme)

Checklist if login looks “dead” but you can open a TTY:

1. `qt6-virtualkeyboard` installed when `InputMethod=qtvirtualkeyboard` is set (`/etc/sddm.conf.d/virtualkbd.conf`).
2. `/etc/X11/xorg.conf.d/20-intel-only.conf` present on hybrid (step 4 above).
3. NVIDIA early in initramfs (`MODULES=…` + `mkinitcpio -P`).
4. You are on the **greeter VT**, not the debug TTY — try **Ctrl+Alt+F1** or **F2**.

```bash
systemctl status sddm
journalctl -u sddm -b --no-pager
# healthy: Message received from greeter: Connect
# broken X: Failed to create pixmap / failed to create screen resources in /var/log/Xorg.0.log
```

## Benchmark

```bash
sudo pacman -S mesa-utils glmark2
glmark2
prime-run glmark2
```

## References

- [ArchWiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [ArchWiki: NVIDIA Optimus](https://wiki.archlinux.org/title/NVIDIA_Optimus)
- [ArchWiki: SDDM](https://wiki.archlinux.org/title/SDDM)
- [DE.md](./DE.md)
