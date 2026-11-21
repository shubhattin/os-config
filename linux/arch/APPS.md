# Extra Apps & Tools Reference (Arch)

Everything installed on the EndeavourOS machine (Nov 2026) that the other guides don't
already install. Copy the blocks you want after the base setup.

> Automated: [`restore/restore.py`](./restore/restore.py) runs §1–§13 as steps `a-01…a-13`.
> **Keep both in sync** when adding/removing apps.

**Install order on a fresh EndeavourOS:**

1. EndeavourOS installer: Hyprland edition, GRUB (ships pipewire, NetworkManager, SDDM, paru/yay)
2. [`scripts/arch_setup.py`](./scripts/arch_setup.py): pacman.conf + chaotic-aur, mirrors, kernels, drivers, CLI basics, common apps
3. [`hyprland/deps_install.sh`](./hyprland/deps_install.sh): Hyprland, SDDM, Noctalia, portals, keyring, themes
4. **This file**: everything else
5. `cd ~/.dotfiles && stow .`, then restore the pen-drive backup (`Backup/RESTORE.md`)

**Source preference:** official repo (`core`/`extra`/`multilib`) → `chaotic-aur` (prebuilt AUR) →
AUR via `paru` → vendor installer → language package managers (npm/bun/cargo/pip) only when
nothing above exists. `paru` already prefers chaotic-aur when a package is in both.

---

## 1. System pieces the base install doesn't add

Laptop audio firmware, power profiles (used by Noctalia), thumbnails for Dolphin, media codecs, fonts.

```bash
sudo pacman -S --needed \
  sof-firmware alsa-firmware alsa-utils power-profiles-daemon \
  bash-completion man-db man-pages openssh plocate pkgfile xdg-user-dirs xdg-utils \
  ffmpegthumbnailer poppler-glib libopenraw libgsf \
  gst-libav gst-plugins-bad gst-plugins-ugly gst-plugin-pipewire \
  noto-fonts-cjk noto-fonts-emoji 7zip unrar \
  avahi nss-mdns lm_sensors smartmontools firewalld
sudo systemctl enable --now power-profiles-daemon avahi-daemon fstrim.timer firewalld
sudo pkgfile --update
xdg-user-dirs-update
# os-prober: only if Windows comes back (then set GRUB_DISABLE_OS_PROBER=false)
```

firewalld zones in use today: `public` (wlan0, services `ssh` + `dhcpv6-client`),
plus `docker` and `libvirt` zones that those packages create themselves.

## 2. Browsers & communication

Brave, Zen, Helium, Zoom are already in `arch_setup.py`.

```bash
sudo pacman -S --needed firefox telegram-desktop remmina
sudo pacman -S --needed chaotic-aur/google-chrome chaotic-aur/claude-desktop chaotic-aur/vesktop
# Edge: paru -S microsoft-edge-stable-bin
```

## 3. Editors, IDEs & desktop AI apps

VS Code is in `arch_setup.py`; Zed configs live in dotfiles.

```bash
sudo pacman -S --needed zed meld
paru -S --needed t3code-bin cursor-bin antigravity wispr-flow-appimage hex-bin zapfast-bin
# optional: sudo pacman -S chaotic-aur/android-studio   (configs survive in ~/.config/Google)
```

VS Code extensions: `xargs -n1 code --install-extension < Backup/inventory/vscode-extensions.txt`

## 4. AI coding CLIs: pacman first

| Tool | Install | Notes |
|---|---|---|
| Claude Code | `sudo pacman -S chaotic-aur/claude-code` | Update it with `pacman -Syu`, not its built-in updater (which can't write to `/usr`). The old native install (`~/.local/bin/claude`) isn't needed. |
| Codex | `sudo pacman -S openai-codex` | official `extra`; replaces the bun-global `@openai/codex` |
| Gemini CLI | `sudo pacman -S gemini-cli` | official `extra`; replaces the npm-global `@google/gemini-cli` |
| opencode | `sudo pacman -S opencode` | official `extra`; replaces the npm/bun-global `opencode-ai` |
| Cursor agent | `paru -S cursor-cli` | AUR; replaces the self-installer in `~/.local/share/cursor-agent` |
| CodeRabbit | `paru -S coderabbit` | AUR; replaces the self-installer in `~/.local/bin/coderabbit` |
| CLIProxyAPI | `paru -S cli-proxy-api-bin` then `systemctl --user enable --now cli-proxy-api` | the user unit is restored from backup (`06-config`) |
| Ollama | `sudo pacman -S ollama-cuda` | **use `-cuda`** for the RTX 3050 (today's plain `ollama` is CPU-only). Models: `ollama pull …` |

Logins (`claude`, `codex`, `gemini`, `gh auth login`, …) have to be done again after a reinstall.

## 5. JavaScript / Node

```bash
sudo pacman -S --needed nvm pnpm bun
source /usr/share/nvm/init-nvm.sh && nvm install --lts     # today: v24
npm i -g tsx vite-node oxfmt                              # small dev tools, no pacman package
paru -S vercel                                            # or: bun add -g vercel
```

- **pnpm** from `extra` is a standalone binary (depends only on glibc/sqlite). It needs
  **neither npm nor nvm**, and it uses whichever `node` is on `PATH` (the nvm one) to run scripts.
- **bun** from `extra` replaces the AUR `bun-bin`.
- Avoid installing CLIs with `npm -g`/`bun add -g` when §4 has a pacman package; those globals
  disappear when you switch nvm Node versions.

## 6. Python

```bash
sudo pacman -S --needed uv ruff python-pyqt6
```

`uv` is the CLI (arch_setup.py's `python-uv` is only the Python-module wrapper; keep both).
`ruff` from `extra` replaces `uv tool install ruff`.
Old `pip --user` leftovers (fastapi, uvicorn, dotenv, watchfiles, wpull, hyprconf2lua) belong in
project venvs (`uv add …`). Reinstall `hyprconf2lua` only if still needed: `uv tool install hyprconf2lua`.

## 7. Rust

```bash
rustup default stable && rustup toolchain install nightly
# 1.93 / 1.94 are pinned by projects' rust-toolchain.toml and auto-install on first build
sudo pacman -S --needed cargo-expand cargo-watch cargo-ndk cargo-zigbuild cbindgen samply \
  sea-orm-cli wasm-pack tree-sitter-cli trunk binaryen rust-analyzer
paru -S --needed cargo-leptos rustfilt
cargo install flutter_rust_bridge_codegen     # not packaged anywhere
```

## 8. Other toolchains

```bash
sudo pacman -S --needed clang ninja zig dart fvm ghc patchelf perf go gopls
fvm install stable          # Flutter SDK via fvm (projects pin versions in .fvmrc)
# Android SDK/NDK: install through Android Studio (§3) → ~/Android/Sdk
```

## 9. Containers, databases, VMs

```bash
sudo pacman -S --needed docker docker-compose docker-buildx pgvector swtpm
sudo systemctl enable --now docker
sudo usermod -aG docker,libvirt "$USER"     # libvirt itself is in arch_setup.py; re-login after
```

`postgresql` + `libvirtd` are set up by `arch_setup.py`. `pgvector` adds the vector extension.
`swtpm` gives virt-manager VMs a TPM (Windows 11).

## 10. Cloud & network CLIs

```bash
sudo pacman -S --needed aws-cli-v2 cloudflared rclone wget2 httrack
paru -S --needed pscale-cli-bin
```

**cloudflared tunnel service.** It runs with `--token-file /etc/cloudflared/token`. That file is
**outside /home and not in the backup**. Copy it now with `sudo cp /etc/cloudflared/token <pen drive>`,
or get a new token from the Cloudflare dashboard (Zero Trust → Networks → Tunnels → the tunnel →
Configure). Then:

```bash
sudo install -Dm600 token /etc/cloudflared/token
sudo systemctl enable --now cloudflared
```

rclone remotes are in `~/.config/rclone` (restored from backup). `aws`/`pscale` need logging in again.

## 11. CLI utilities & terminals

```bash
sudo pacman -S --needed kitty gum tldr duf glances iotop pv fx wtype
sudo pacman -S --needed chaotic-aur/downgrade     # roll a package back (was in EOS repo)
```

`ghostty` + `alacritty` are installed by `deps_install.sh` (Hyprland binds use them).

## 12. Media, creative, gaming

```bash
sudo pacman -S --needed krita gnome-sound-recorder gnuplot kio-gdrive
paru -S --needed pulsemeeter
# gaming (needs [multilib]):
sudo pacman -S --needed wine lutris mangohud vulkan-intel lib32-vulkan-intel
```

## 13. Fonts

```bash
paru -S --needed ttf-ms-aptos-core
```

## 14. Services & groups (checklist)

| Unit | Enabled by |
|---|---|
| `NetworkManager`, `bluetooth` | archinstall / arch_setup.py |
| `sddm` | deps_install.sh |
| `postgresql`, `libvirtd` (+ sockets) | arch_setup.py |
| `docker` | §9 |
| `cloudflared` | §10 (needs the token) |
| `firewalld`, `avahi-daemon`, `power-profiles-daemon`, `fstrim.timer` | §1 |
| `lm_sensors` | run `sudo sensors-detect` once, then `sudo systemctl enable lm_sensors` |
| user: `cli-proxy-api` | §4 |
| user: pipewire / wireplumber / `gnome-keyring-daemon.socket` | enabled automatically by their packages |

Groups: `wheel` (archinstall), `docker`, `libvirt`.

## 15. Not carried over

- **EndeavourOS-only:** `eos-*`, `endeavouros-*`, `dracut`/`eos-dracut` (Arch uses mkinitcpio),
  `eos-rankmirrors` (use reflector-simple / rate-mirrors, see [CLI.md](./CLI.md)).
- **Leftovers, don't reinstall:** `weston` (old Wayland-greeter test), `iwd` and `netctl`
  (NetworkManager handles Wi-Fi), `xterm`.
- **Base packages** (`base`, filesystems' progs, firmware, `efibootmgr`, …) come with archinstall.
- **Self-updating tools in `~/.local/bin`** (`muse`, `agy`, old `claude`/`cursor-agent`/`coderabbit`
  binaries): `~/.local/bin` isn't backed up. Use the pacman/AUR versions above, or re-run their installers.
