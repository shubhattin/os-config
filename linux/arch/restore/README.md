# Backup & Autopilot Restore (EndeavourOS → Arch, Nov 2026)

This drive has everything needed to rebuild the laptop as it was:
**files** (8 archives) and a **restore script** that also reinstalls all software.

| File | What |
|---|---|
| `restore.sh` / `restore.py` | **the autopilot**: restores files and installs/configures everything |
| `01…08-*.tar.zst` | the backup archives (see table below) |
| `SHA256SUMS`, `manifests/` | checksums and full file lists of every archive |
| `inventory/` | git state per repo, `.env` file list, VS Code extensions, sizes before backup |
| `RESTORE.md` | manual restore commands (if you ever want to do it by hand) |
| `BACKUP-PLAN.md` | how/why the backup was made, what was skipped |
| `scripts/backup.sh` | the script that made these archives |

---

## 1. Install Arch (archinstall)

Partition map (also in the phone screenshot `arch-partition-guide.png`):

| # | Mount | Size | Partition type | Filesystem | Format? |
|---|---|---|---|---|---|
| 1 | `/boot` | 2 GiB | EFI System (flags `boot`, `esp`) | **FAT32** | yes |
| 2 | `/` | 100 GiB | Linux root | **ext4** | yes |
| 3 | `[SWAP]` | 16 GiB | Linux swap | **swap** | yes |
| 4 | `/home` | rest (~359 GiB) | Linux home | **ext4** | yes |

- **FAT32** for `/boot` because UEFI firmware can only read FAT; GRUB and kernels live there.
- **ext4** for `/` and `/home`: what we used before, simple and robust, and offline shrink is easy
  (needed to make room for Windows later). btrfs isn't needed since we don't use snapshots.
- swap = RAM (16 GB), so hibernate works. Also leave archinstall's **zram** on.

archinstall choices: Bootloader **GRUB** · Kernels `linux` + `linux-lts` · Profile **Minimal** ·
Audio **pipewire** · Network **NetworkManager** · enable **multilib** · user **`shubhattin`** with
the **same password as before** (the keyring is encrypted with it) · timezone `Asia/Kolkata` ·
extra packages: `git base-devel zsh stow python python-rich`.

## 2. Run the autopilot

Reboot into the new system, log in **on the TTY** (no desktop yet), then:

```bash
nmtui                                   # connect Wi-Fi if not on Ethernet
sudo mkdir -p /mnt/usb
lsblk -f                                # find the pen drive (exfat, ~115G), e.g. /dev/sda1
sudo mount /dev/sda1 /mnt/usb
cd /mnt/usb/Backup
bash restore.sh                         # asks your sudo password ONCE, then runs on its own
```

Expect roughly **1–2 hours**, mostly downloads and AUR builds. Leave it running; don't log out.
Then **reboot** and log in at the SDDM (Wayland) greeter.

### What it does, in order

```
phase 0  preflight     sudo password (asked once, kept in memory, refreshed every 45 s),
                       internet check, ≥30 GiB free, pacman -Syu + python/zstd/git/stow
phase 1  priority      03 secrets → 06 configs → 05 browsers → 04 T3 chats
         files         → 07 /etc (cloudflared token) → 08 SDDM/GRUB themes + greeter conf
phase 2  ┌ lane FILES  01 code (7 GB) → 02 personal → stow dotfiles → fixups
         │             (worktree prune, Zen portal pref, xdg dirs)
 parallel│
         └ lane SYSTEM arch_setup.py (pacman.conf, chaotic-aur, mirrors, kernels, NVIDIA,
                       GRUB, CLI tools, common apps) → zsh/nvm/rustup → Hyprland desktop
                       (deps_install.sh: SDDM Wayland greeter, Noctalia, KDE portal, keyring)
                       → APPS.md §1…§13 (one step each)
phase 3  after both    VS Code extensions (69) → user services + sensors → font cache, GRUB config
```

Configs and browsers go first, so the software lane can run alongside the large
code/personal copy (pacman doesn't write into `$HOME`). Every archive is **sha256-checked while it
is being extracted** against `SHA256SUMS`.

### Progress, logs, errors

- The screen shows an **OVERALL** bar (steps done / total) plus one bar per lane: bytes for
  archive extraction, `(n/m)` from pacman/paru, extensions done for VS Code. The right column shows
  the current output line. Finished steps print `[ OK ]`, `[WARN]` (partial) or `[FAIL]`.
- Logs: `~/.local/state/home-restore/run-<date>/`
  - `<step-id>.log`: the full output of each step
  - `errors.log`: each failed/partial step with its message and the last 40 log lines
  - `summary.json`, plus `arch_setup-generated.sh` (the exact system script that ran)
- A failing step **doesn't stop the run**. If a package group fails, it retries the
  packages one by one and reports exactly which ones failed (`[WARN] failed packages: …`).
- **Resume:** state is saved after each step in `~/.local/state/home-restore/state.json`.
  Fix the cause and run `bash restore.sh` again; finished steps are skipped.
  Ctrl+C stops cleanly at any time.

### Options

```bash
bash restore.sh --list                 # all steps + saved status
bash restore.sh --dry-run              # show what would run (commands go to the logs)
bash restore.sh --only a-04-ai,p-vscode   # run just these steps
bash restore.sh --skip a-12-media      # skip steps
bash restore.sh --redo                 # ignore saved state
```

Machine-specific settings sit at the top of `restore.py` (`CPU`, `GPU`, `FRAC_SCALE`,
`GOOGLE_DNS`, `INSTALL_FLUTTER`). The master copy lives in
`~/.config/os-config/linux/arch/restore/`. The software steps mirror `os-config/linux/arch/APPS.md`.

If `python` isn't installed, `restore.sh` installs `python` + `python-rich` first (sudo asks once
there too). If `restore.py` finds `rich` missing it installs it and continues by itself; if
that's impossible it tells you to install it and re-run.

## 3. After the script (manual, ~15 min)

1. **Reboot** → SDDM greeter (Wayland/KWin on the Intel GPU). If it's black: Ctrl+Alt+F3, log in,
   `sudo rm /etc/sddm.conf.d/zz-wayland-greeter.conf && sudo systemctl restart sddm` (X11 fallback).
2. Log in to Hyprland. The keyring unlocks automatically (same password), so Brave/Helium/Chrome
   logins come back. Check Zen too.
3. Log in again to the CLIs: `gh auth login`, `claude`, `codex`, `gemini`, `aws configure`/SSO,
   `pscale auth login`, `vercel login`, plus Docker Hub if used.
4. Postgres: `sudo -u postgres psql` → `\password postgres`.
5. `ollama pull <models>` (models weren't backed up).
6. Check `errors.log` and re-run `bash restore.sh` for anything marked FAIL/WARN.
7. Reinstall project dependencies when you open them: `bun install` / `pnpm install`, `cargo build`, `uv sync`,
   `flutter pub get` (node_modules/target/.venv were not backed up on purpose).
8. Optional: `sudo pacman -S chaotic-aur/android-studio`, Edge, Steam.

---

## Archives

| Archive | Contents | Restored to |
|---|---|---|
| `01-code` | `yojanAni` (deps stripped, full `.git`), `.dotfiles`, `~/tmp`, `security-audit-skill` | `~` |
| `02-personal` | Documents, Pictures, Music, Downloads, Videos, Desktop, Bleach, shell histories | `~` |
| `03-secrets` | `.ssh`, `.gnupg`, keyrings (gnome + kwallet), `lipilekhika-signing`, `.npmrc`, `.pypirc`, all `.env` files | `~` |
| `04-t3code` | `.t3` (worktrees, chat DB), T3 app data, `.claude/projects`, `.codex` sessions | `~` |
| `05-browsers` | Zen, Firefox, Brave, Helium, Chrome, Edge, Chromium profiles (no caches) | `~` |
| `06-config` | rest of `~/.config` (VS Code User, systemd user units, os-config, …), Zed data, fonts, `.desktop` files | `~` |
| `07-system` | `/etc/cloudflared/token` (root, 0600) | `/` |
| `08-system-desktop` | SDDM astronaut theme (`black_hole`), its fonts, GRUB `darkmatter`/`starfield` themes, `/etc/sddm.conf*`, Intel-GPU udev rule, old `/etc/default/grub` (reference only, not restored) | `/` |

Not backed up on purpose: caches, `node_modules`/`target`/`.venv`/build output, toolchains/SDKs,
Ollama models, games/Wine prefixes, Cursor/Antigravity settings, `~/C_Drive` (backed up separately).
