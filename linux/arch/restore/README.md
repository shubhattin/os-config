# Backup & Autopilot Restore (EndeavourOS, Nov 2026)

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

## 1. Install EndeavourOS

EndeavourOS installer, **Hyprland** edition, GRUB, user **`shubhattin`** with the **same password
as before** (the keyring is encrypted with it). The installer already brings Hyprland, SDDM (X11
greeter), Xorg, NetworkManager, pipewire, paru/yay, dolphin, ghostty and alacritty, so the restore
doesn't reinstall them (`--needed` makes any overlap a no-op).

Before running: `git clone` + `stow` of `~/.dotfiles` and `~/.config/os-config` is fine (already done
on this machine). The restore **keeps those clones** and only adds the untracked files from the backup.

## 2. Run the autopilot

Open a terminal in Hyprland. **Close the browsers, VS Code, Zed, T3 Code and Claude desktop first**:
their data is restored (the script checks and waits if any are still running).

```bash
cd /run/media/$USER/1C8B-7665/Backup
bash restore.sh                         # asks your sudo password ONCE, then runs on its own
```

Watch everything live from a second terminal (every line of every step, timestamped, tagged by step):

```bash
tail -f ~/.local/state/home-restore/latest/live.log
```

Or have the same output on the main screen under the progress bars: `bash restore.sh --verbose`.

Expect roughly **1–2 hours**, mostly downloads and AUR builds. Leave it running; don't log out.

### What it does, in order

```
phase 0  preflight     sudo password (asked once, kept in memory, refreshed every 45 s),
                       running-apps check, internet check, ≥30 GiB free,
                       pacman -Syy, pacman -Syu + base tools (python-rich, stow, nvm, rustup …), paru
phase 1  priority      03 secrets → 06 configs (os-config clone kept) → 05 browsers → 04 T3 chats
         files         → 07 /etc (cloudflared token) → 08 SDDM/GRUB themes + X11 greeter 1.25 scale
phase 2  ┌ lane FILES  01 code (7 GB, .dotfiles clone kept) → 02 personal → stow dotfiles → fixups
 parallel│
         └ lane SYSTEM arch_setup.py (kernels incl. LTS, NVIDIA, GRUB, CLI tools, common apps;
                       keeps the EndeavourOS pacman.conf) → zsh/nvm/rustup → deps_install.sh
                       (Noctalia, KDE portal, keyring, themes) → APPS.md §1…§13 (one step each)
phase 3  after both    VS Code extensions (69) → user services + sensors → font cache, GRUB config
```

**SDDM greeter: X11** (as before). `/etc/sddm.conf.d/hidpi.conf` sets `QT_SCREEN_SCALE_FACTORS=1.25`.
The KWin/Wayland greeter from the Arch attempt (`zz-wayland-greeter.conf`, `61-intel-igpu.rules`)
is not restored, and is deleted if present.

Every archive is **sha256-checked while it is being extracted** against `SHA256SUMS`.

### Progress, logs, errors

- Screen: an **OVERALL** bar plus one bar per lane (bytes for archives, `(n/m)` from pacman/paru,
  extensions for VS Code); the right column shows the command or output line running right now, and
  each lane's timer shows how long the current step has been running.
  Each step prints `[ >> ]` when it starts (with its log path), then `[ OK ]`, `[WARN]` or `[FAIL]`.
  On WARN/FAIL the last 8 log lines are printed right there.
- Logs: `~/.local/state/home-restore/latest/` (→ `run-<date>/`)
  - `live.log`: everything from every step, timestamped
  - `<step-id>.log`: the full output of one step
  - `00-bootstrap.log`, `errors.log` (each failed/partial step + last 40 lines), `summary.json`,
    `arch_setup-generated.sh` (the patched script that ran)
- A failing step **doesn't stop the run**. Package groups are retried, then one by one, then
  through `paru`; only truly unavailable ones are reported (`[WARN] failed packages: …`).
- **Resume:** state is saved after each step. Fix the cause and run `bash restore.sh` again;
  finished steps are skipped. Ctrl+C stops cleanly at any time.

### Options

```bash
bash restore.sh --list                 # all steps + saved status
bash restore.sh --dry-run              # show what would run (commands go to the logs)
bash restore.sh --verbose              # print every output line on screen too
bash restore.sh --only a-04-ai,p-vscode   # run just these steps
bash restore.sh --skip a-12-media      # skip steps
bash restore.sh --redo                 # ignore saved state
```

Machine-specific settings sit at the top of `restore.py` (`CPU`, `GPU`, `FRAC_SCALE`,
`GOOGLE_DNS`, `INSTALL_FLUTTER`). The master copy lives in
`~/.config/os-config/linux/arch/restore/`. The software steps mirror `os-config/linux/arch/APPS.md`.

The Arch-install version of these files is kept as `*.arch-version.bak*`.

## 3. After the script (manual, ~15 min)

1. **Reboot** → SDDM greeter (X11, 1.25 scale).
2. Log in to Hyprland. The keyring unlocks automatically (same password), so Brave/Helium/Chrome
   logins come back. Check Zen too.
3. Log in again to the CLIs: `gh auth login`, `claude`, `codex`, `gemini`, `aws configure`/SSO,
   `pscale auth login`, `vercel login`, plus Docker Hub if used.
4. Postgres: `sudo -u postgres psql` → `\password postgres`.
5. `ollama pull <models>` (models weren't backed up).
6. Check `errors.log` and re-run `bash restore.sh` for anything marked FAIL/WARN.
7. Reinstall project dependencies when you open them: `bun install` / `pnpm install`, `cargo build`, `uv sync`,
   `flutter pub get` (node_modules/target/.venv were not backed up on purpose).

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
| `08-system-desktop` | SDDM astronaut theme (`black_hole`), its fonts, GRUB `darkmatter`/`starfield` themes, `/etc/sddm.conf*` (the Wayland-greeter drop-in and Intel-GPU udev rule in it are skipped), old `/etc/default/grub` (reference only, not restored) | `/` |

Not backed up on purpose: caches, `node_modules`/`target`/`.venv`/build output, toolchains/SDKs,
Ollama models, games/Wine prefixes, Cursor/Antigravity settings, `~/C_Drive` (backed up separately).
