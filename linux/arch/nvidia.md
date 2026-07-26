# NVIDIA Drivers (Arch / EndeavourOS)

Notes for hybrid Intel + NVIDIA laptops (e.g. Ideapad with Alder Lake iGPU + RTX 3050) and single-NVIDIA machines. Prefer the [ArchWiki NVIDIA](https://wiki.archlinux.org/title/NVIDIA) and [NVIDIA Optimus](https://wiki.archlinux.org/title/NVIDIA_Optimus) pages when something changes.

## Pick the right packages

On current Arch/EndeavourOS:

| Goal | Packages |
|------|----------|
| **Recommended (Turing+ / RTX 20xx and newer)** | `nvidia-open` **or** `nvidia-open-dkms` + `nvidia-utils` + `nvidia-settings` + `nvidia-prime` |
| DKMS (any kernel / custom kernels) | `nvidia-open-dkms` + matching `linux-headers` / `linux-lts-headers` |
| Prebuilt for `linux` / `linux-lts` only | `nvidia-open` / `nvidia-open-lts` (no DKMS rebuild needed) |
| Optional CUDA | `cuda` `cudnn` `opencl-nvidia` |

**Do not** blindly run `pacman -S nvidia`.

- The closed-source `nvidia` package is effectively gone from official repos in favor of **`nvidia-open`**.
- On systems with **chaotic-aur**, `nvidia` can resolve to **`nvidia-580xx-dkms`** (legacy branch). That is the wrong stack for modern RTX cards and easily mismatches `nvidia-settings` / `libxnvctrl` from the 610.x series.

Keep **kernel module + utils + settings** on the **same major version** (e.g. all 610.x). Mixing `nvidia-580xx-utils` with `nvidia-settings 610.x` is broken.

### Legacy only (usually avoid)

chaotic-aur / AUR legacy branches (`nvidia-580xx-*`, `470xx`, etc.) are for older GPUs that current `nvidia-open` no longer supports. RTX 3050 should use **`nvidia-open*`**, not 580xx.

## Install (hybrid Optimus laptop)

```bash
# headers for the kernels you boot
sudo pacman -S linux-headers linux-lts-headers   # if you use both

# open driver + userspace + PRIME offload helper
sudo pacman -S nvidia-open-dkms nvidia-utils nvidia-settings nvidia-prime

# SDDM greeter — required if InputMethod=qtvirtualkeyboard is set
# (e.g. astronaut theme / /etc/sddm.conf.d/virtualkbd.conf). Missing this can blank the login screen.
sudo pacman -S qt6-virtualkeyboard

# optional
sudo pacman -S opencl-nvidia cuda cudnn
```

Enable DRM KMS (needed for Wayland / modern X):

```bash
sudo bash -c 'echo "options nvidia-drm modeset=1" > /etc/modprobe.d/nvidia-drm.conf'
sudo mkinitcpio -P
sudo reboot
```

> The filename does not matter; older notes used `nvidia-drm-nomodeset.conf` even though the option is `modeset=1`. Prefer a clear name like `nvidia-drm.conf`.

After reboot:

```bash
# should print Y
cat /sys/module/nvidia_drm/parameters/modeset

nvidia-smi
lsmod | grep nvidia
lsmod | grep nouveau          # should be empty
lspci -k | grep -A 3 -i VGA
modinfo -F version nvidia     # must match nvidia-utils version series
```

## Hybrid / PRIME usage

On muxless Optimus laptops the **internal display is driven by Intel**. NVIDIA is for render offload (and sometimes external HDMI on the NVIDIA chip).

- Default apps → Intel (power saving).
- Heavy apps → offload to NVIDIA:

```bash
prime-run glxinfo | grep 'OpenGL renderer'
prime-run glmark2
# or manually:
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glmark2
```

There is a local helper at [`scripts/prime-run`](./scripts/prime-run).

Prefer **PRIME offload** over constantly switching GPU modes. Tools like `optimus-manager` / `envycontrol` can break the display manager if a mode switch leaves X/Wayland without a working output — use carefully, and keep Hybrid + `prime-run` as the default.

### Optimus Manager (X11, optional)

```bash
paru -S optimus-manager-git optimus-manager-qt
sudo systemctl enable optimus-manager
# reboot, then set Hybrid in the Qt app and enable autostart
```

If the greeter fails after a mode switch, drop to a TTY and switch back to Hybrid, or remove the tool and stick with PRIME.

## Intel side (hybrid)

```bash
sudo pacman -S intel-ucode mesa intel-media-driver libva-mesa-driver
```

List GPUs: `lspci -vnn | grep -E 'VGA|3D'`

## SDDM / greeter (common breakage after NVIDIA install)

SDDM may look “dead” while `systemctl status sddm` is still active. Typical pattern: **Xorg on VT2**, greeter crashed, you are debugging on **tty3**.

```bash
systemctl status sddm
journalctl -u sddm -b --no-pager
# greeter / Qt errors often under the sddm user session
journalctl -b --no-pager | grep -i 'sddm-greeter\|xcb\|virtualkeyboard'
```

Switch to the graphical VT: `Ctrl+Alt+F2` (or `chvt 2`).

### Checklist when the login screen is blank

1. **`qt6-virtualkeyboard`** — install it (see Install section). Required when `/etc/sddm.conf.d/` sets `InputMethod=qtvirtualkeyboard`.
2. **Theme** — temporarily force a simple theme (e.g. `breeze`) instead of heavy QML themes like astronaut.
3. **Driver version mismatch** — remove chaotic `nvidia-580xx-*` if you meant to install current open drivers (see cleanup below).
4. **Xorg hybrid error** — look for `(EE) modeset(G0): Failed to create pixmap` in `/var/log/Xorg.0.log`. Usually means NVIDIA was initialized incorrectly with modesetting; fix the driver stack + keep `nvidia-drm modeset=1`, then reboot.
5. **Missing cursor** — `Could not setup default cursor` often rides along with a broken greeter/GL setup; fix greeter deps and drivers first.

### Cleanup wrong 580xx / mismatched install

```bash
sudo pacman -Rns nvidia-580xx-dkms nvidia-580xx-utils
# if settings/libxnvctrl are 610.x orphans or mismatched, reinstall with the open stack:
sudo pacman -S nvidia-open-dkms nvidia-utils nvidia-settings nvidia-prime qt6-virtualkeyboard
sudo mkinitcpio -P
sudo reboot
```

Confirm versions match:

```bash
pacman -Q | grep -E 'nvidia|libxnvctrl'
```

## Verify / benchmark

```bash
sudo pacman -S mesa-utils glmark2 mission-center   # or: paru -S resources
glmark2                 # primary (usually Intel on hybrid)
glmark2-wayland
prime-run glmark2       # NVIDIA offload — watch Mission Center
```

## Wayland notes (Hyprland / Plasma)

- `nvidia-drm modeset=1` is required.
- Prefer current `nvidia-open` + `nvidia-utils`; keep `egl-wayland` (pulled by utils).
- External monitors on some Optimus laptops only work when the panel is wired to a given GPU — check hardware if a port stays black.

## References

- [ArchWiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [ArchWiki: NVIDIA Optimus](https://wiki.archlinux.org/title/NVIDIA_Optimus)
- [ArchWiki: SDDM](https://wiki.archlinux.org/title/SDDM)
- Local overview still in [DE.md](./DE.md) (points here for install details)
