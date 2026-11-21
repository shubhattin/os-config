#!/usr/bin/env python3
"""
Autopilot home + software restore for a fresh Arch install (archinstall, Minimal profile).

Run from the pen drive's Backup/ folder, on a TTY, as your normal user:

    bash restore.sh            # bootstraps python if missing, then runs this file
    python3 restore.py --help

Phases
  0  preflight: sudo password (asked ONCE), network, disk space, bootstrap deps
  1  priority files: secrets, configs, browsers, T3 chats, /etc + theme files
  2  in parallel:
       lane FILES : code (01) + personal (02), stow dotfiles, small fixups
       lane SYSTEM: arch_setup.py, desktop (Hyprland/SDDM), every app group from APPS.md
  3  needs both lanes: VS Code extensions, user services, sensors, final touches

State is saved after every step; re-running skips finished steps and retries failed ones.
Logs: ~/.local/state/home-restore/<run>/  (one log per step + errors.log + summary)
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import glob
import hashlib
import importlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ───────────────────────────── machine-specific settings ─────────────────────────────
CPU = "intel"            # arch_setup.py --cpu-type
GPU = "both"             # intel + nvidia (hybrid)
FRAC_SCALE = "1.25"      # SDDM greeter scale
GOOGLE_DNS = True        # arch_setup.py writes Google DNS + chattr +i /etc/resolv.conf
INSTALL_FLUTTER = True   # `fvm install stable` (~1.5 GB download)

BACKUP_DIR = Path(__file__).resolve().parent
BOOTSTRAP_PKGS = ["python-rich", "python-typer", "python-pydantic", "zstd", "tar", "git",
                  "stow", "curl", "base-devel", "sudo"]

# ───────────────────────────── bootstrap: python deps ─────────────────────────────
def _ensure_rich(sudo_pw: str | None) -> None:
    try:
        import rich  # noqa: F401
        return
    except ImportError:
        pass
    print("[bootstrap] python-rich missing → installing it with pacman …")
    pw = sudo_pw or getpass.getpass(f"[sudo] password for {getpass.getuser()}: ")
    r = subprocess.run(["sudo", "-S", "-p", "", "pacman", "-S", "--needed", "--noconfirm", "python-rich"],
                       input=pw + "\n", text=True)
    importlib.invalidate_caches()
    try:
        import rich  # noqa: F401
    except ImportError:
        sys.exit(f"[bootstrap] could not import rich (pacman exit {r.returncode}). "
                 "Install it manually: sudo pacman -S python-rich, then re-run this script.")


# ───────────────────────────── helpers / model ─────────────────────────────
class StepFailed(Exception):
    pass


class StepPartial(Exception):
    """Step finished but some items failed (e.g. a few packages)."""


@dataclass
class Step:
    id: str
    title: str
    phase: int
    lane: str                      # "files" | "system" | "post"
    fn: Callable[["Ctx"], None]
    needs_sudo: bool = False


@dataclass
class Ctx:
    home: Path
    user: str
    run_dir: Path
    dry: bool
    sudo_pw: str | None
    progress: object = None
    task_ids: dict = field(default_factory=dict)
    lane: str = ""
    step: Step | None = None
    log: object = None
    procs: set = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)
    stop: threading.Event = field(default_factory=threading.Event)

    # ---- progress plumbing (per lane task) ----
    def set_total(self, total):
        if self.progress:
            self.progress.update(self.task_ids[self.lane], total=total, completed=0)

    def advance(self, n=1):
        if self.progress:
            self.progress.update(self.task_ids[self.lane], advance=n)

    def set_completed(self, done, total=None):
        if self.progress:
            kw = {"completed": done}
            if total:
                kw["total"] = total
            self.progress.update(self.task_ids[self.lane], **kw)

    def status(self, text: str):
        if self.progress:
            text = text.strip().replace("[", "(").replace("]", ")")
            self.progress.update(self.task_ids[self.lane], status=text[:70])

    def logln(self, text: str):
        if self.log:
            self.log.write(text if text.endswith("\n") else text + "\n")
            self.log.flush()

    # ---- command execution ----
    COUNTER = re.compile(r"\(\s*(\d+)/(\d+)\)")

    def run(self, cmd, sudo=False, shell=False, cwd=None, env=None, check=True, quiet=False) -> int:
        """Run a command, stream output to the step log, parse (n/m) counters for progress."""
        if shell:
            cmd = ["bash", "-o", "pipefail", "-c", cmd]
        if sudo:
            cmd = ["sudo", "-n", *cmd]
        shown = " ".join(cmd) if not shell else cmd[-1]
        self.logln(f"\n$ {shown}")
        if self.dry:
            self.status(f"(dry) {shown[:60]}")
            return 0
        full_env = os.environ.copy()
        full_env.update({"LC_ALL": "C", "PACMAN_COLOR": "never"})
        if env:
            full_env.update(env)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, text=True, bufsize=1, cwd=cwd,
                             env=full_env, errors="replace")
        with self.lock:
            self.procs.add(p)
        try:
            for line in p.stdout:
                self.logln(line.rstrip("\n"))
                if quiet:
                    continue
                m = self.COUNTER.search(line)
                if m:
                    self.set_completed(int(m.group(1)), int(m.group(2)))
                if line.strip():
                    self.status(line)
            rc = p.wait()
        finally:
            with self.lock:
                self.procs.discard(p)
        if check and rc != 0:
            raise StepFailed(f"exit {rc}: {shown[:120]}")
        return rc

    # ---- package helpers ----
    def pkgs(self, names: list[str], aur: bool = False):
        """Install packages; on failure retry one by one so a single bad name can't block the rest."""
        names = [n for n in names if n]
        if not names:
            return
        base = (["paru", "-S", "--needed", "--noconfirm", "--skipreview"] if aur
                else ["pacman", "-S", "--needed", "--noconfirm"])
        try:
            self.run(base + names, sudo=not aur)
            return
        except StepFailed:
            self.logln(f"\n!! group install failed, retrying {len(names)} packages one by one")
        failed = []
        for i, n in enumerate(names, 1):
            self.status(f"retry {i}/{len(names)}: {n}")
            if self.run(base + [n], sudo=not aur, check=False) != 0:
                failed.append(n)
        if failed:
            raise StepPartial("failed packages: " + " ".join(failed))

    def enable(self, *units, user=False, now=True):
        for u in units:
            cmd = ["systemctl"] + (["--user"] if user else []) + ["enable"] + (["--now"] if now else []) + [u]
            self.run(cmd, sudo=not user, check=False)

    # ---- archive extraction (sha256 verified while streaming) ----
    def extract(self, archive: str, dest: Path, sudo=False, extra=None, members=None):
        path = BACKUP_DIR / archive
        if not path.exists():
            raise StepFailed(f"missing archive {path}")
        sums = read_sums()
        size = path.stat().st_size
        self.set_total(size)
        tar = ["tar", "-C", str(dest), "--acls", "--xattrs", "--xattrs-include=*", "-xpf", "-",
               *(extra or []), *(members or [])]
        if sudo:
            tar = ["sudo", "-n", *tar]
        self.logln(f"\n$ zstd -dc {path} | {' '.join(tar)}")
        if self.dry:
            self.set_completed(size)
            return
        h = hashlib.sha256()
        z = subprocess.Popen(["zstd", "-dcq"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=self.log)
        t = subprocess.Popen(tar, stdin=z.stdout, stdout=self.log, stderr=self.log)
        z.stdout.close()
        with self.lock:
            self.procs.update({z, t})
        try:
            with open(path, "rb") as f:
                while chunk := f.read(4 << 20):
                    if self.stop.is_set():
                        raise StepFailed("interrupted")
                    h.update(chunk)
                    try:
                        z.stdin.write(chunk)
                    except BrokenPipeError:
                        break
                    self.advance(len(chunk))
            z.stdin.close()
            zr, tr = z.wait(), t.wait()
        finally:
            with self.lock:
                self.procs.difference_update({z, t})
        if zr != 0 or tr != 0:
            raise StepFailed(f"extract failed (zstd {zr}, tar {tr}); see log")
        want = sums.get(archive)
        if want and h.hexdigest() != want:
            raise StepPartial(f"checksum MISMATCH for {archive} (extracted anyway; check files)")
        self.logln(f"sha256 ok: {h.hexdigest()}" if want else "no checksum on record")


_SUMS: dict | None = None


def read_sums() -> dict:
    global _SUMS
    if _SUMS is None:
        _SUMS = {}
        f = BACKUP_DIR / "SHA256SUMS"
        if f.exists():
            for line in f.read_text().splitlines():
                parts = line.split()
                if len(parts) == 2:
                    _SUMS[parts[1].lstrip("*")] = parts[0]
    return _SUMS


# ───────────────────────────── step implementations ─────────────────────────────
def os_config(ctx: Ctx) -> Path:
    return ctx.home / ".config/os-config/linux/arch"


# ---- phase 1: priority files ----
def f_secrets(ctx):  ctx.extract("03-secrets.tar.zst", ctx.home)
def f_config(ctx):   ctx.extract("06-config.tar.zst", ctx.home)
def f_browsers(ctx): ctx.extract("05-browsers.tar.zst", ctx.home)
def f_t3(ctx):       ctx.extract("04-t3code.tar.zst", ctx.home)
def f_etc(ctx):      ctx.extract("07-system.tar.zst", Path("/"), sudo=True)


def f_desktop_system(ctx):
    # /etc + /usr/share parts keep root ownership; /boot is FAT32 → no owners/permissions there.
    ctx.extract("08-system-desktop.tar.zst", Path("/"), sudo=True,
                extra=["--anchored", "--exclude=boot", "--exclude=etc/default/grub"])
    ctx.extract("08-system-desktop.tar.zst", Path("/"), sudo=True,
                extra=["--no-same-owner", "--no-same-permissions"], members=["boot/grub/themes"])
    # point GRUB at the restored darkmatter theme (arch_setup.py runs grub-mkconfig later)
    ctx.run(r"""set -e
f=/etc/default/grub; [ -f "$f" ] || exit 0
t='/boot/grub/themes/darkmatter/theme.txt'
if grep -q '^GRUB_THEME=' "$f"; then sed -i "s#^GRUB_THEME=.*#GRUB_THEME=\"$t\"#" "$f"
else echo "GRUB_THEME=\"$t\"" >> "$f"; fi
grep -q '^GRUB_GFXMODE=' "$f" || echo 'GRUB_GFXMODE=auto' >> "$f"
fc-cache -f >/dev/null 2>&1 || true""", sudo=True, shell=True)


# ---- phase 2, lane FILES ----
def f_code(ctx):     ctx.extract("01-code.tar.zst", ctx.home)
def f_personal(ctx): ctx.extract("02-personal.tar.zst", ctx.home)


def f_stow(ctx):
    d = ctx.home / ".dotfiles"
    ctx.run(["stow", "--no", "-v", "."], cwd=d)          # dry run first: shows conflicts in the log
    ctx.run(["stow", "-v", "."], cwd=d)


def f_fixups(ctx):
    ctx.run(["git", "-C", str(ctx.home / "yojanAni/lipi/lipilekhika"), "worktree", "prune"], check=False)
    # Zen: use the KDE portal file picker (pref was added after the browser backup)
    pref = 'user_pref("widget.use-xdg-desktop-portal.file-picker", 1);'
    for prof in glob.glob(str(ctx.home / ".zen/*Default (release)*")):
        uj = Path(prof) / "user.js"
        cur = uj.read_text() if uj.exists() else ""
        if pref not in cur and not ctx.dry:
            uj.write_text(cur + ("" if cur.endswith("\n") or not cur else "\n") + pref + "\n")
        ctx.logln(f"zen user.js ok: {uj}")
    ctx.run(["xdg-user-dirs-update"], check=False)


# ---- phase 2, lane SYSTEM ----
def s_arch_setup(ctx):
    script = os_config(ctx) / "scripts/arch_setup.py"
    out = Path("/tmp/arch_app_installer/script")
    before = set(out.glob("*.sh")) if out.exists() else set()
    ctx.run(["python3", str(script), "--cpu-type", CPU, "--gpu-type", GPU, "--frac-scale", FRAC_SCALE,
             "--setup-google-dns" if GOOGLE_DNS else "--no-setup-google-dns",
             "--no-preview-script", "--no-execute-script"])
    if ctx.dry:
        return
    new = sorted(set(out.glob("*.sh")) - before, key=lambda p: p.stat().st_mtime)
    if not new:
        raise StepFailed("arch_setup.py did not produce a script")
    gen = new[-1]
    ctx.logln(f"generated: {gen}")
    shutil.copy(gen, ctx.run_dir / "arch_setup-generated.sh")
    ctx.run(["bash", str(gen)], sudo=True)
    # the generated script never stops on errors → surface pacman errors as a partial result
    errs = [l for l in (ctx.run_dir / f"{ctx.step.id}.log").read_text(errors="replace").splitlines()
            if l.startswith("error:")]
    if errs:
        raise StepPartial(f"{len(errs)} 'error:' lines (e.g. {errs[0][:90]})")


def s_user_shell(ctx):
    ctx.run(["chsh", "-s", "/usr/bin/zsh", ctx.user], sudo=True)
    ctx.run("source /usr/share/nvm/init-nvm.sh && nvm install --lts && nvm alias default 'lts/*'", shell=True)
    ctx.run(["rustup", "default", "stable"])
    ctx.run(["rustup", "toolchain", "install", "nightly", "--profile", "minimal"])
    ctx.run(r"""set -e
URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz"
d=$(mktemp -d); cd "$d"; curl -fsSL "$URL" -o s.tgz; tar -xzf s.tgz
install -Dm755 speedtest "$HOME/.local/bin/speedtest"; rm -rf "$d" """, shell=True, check=False)


def s_desktop(ctx):
    ctx.run(["bash", str(os_config(ctx) / "hyprland/deps_install.sh")])


def apps(repo: list[str] = (), aur: list[str] = (), post: Callable[[Ctx], None] | None = None):
    def fn(ctx: Ctx):
        partial = []
        for names, is_aur in ((list(repo), False), (list(aur), True)):
            try:
                ctx.pkgs(names, aur=is_aur)
            except StepPartial as e:
                partial.append(str(e))
        if post:
            post(ctx)
        if partial:
            raise StepPartial("; ".join(partial))
    return fn


def _post_system(ctx):
    ctx.enable("power-profiles-daemon", "avahi-daemon", "fstrim.timer", "firewalld")
    ctx.run(["pkgfile", "--update"], sudo=True, check=False)


def _post_js(ctx):
    ctx.run("source /usr/share/nvm/init-nvm.sh && npm i -g tsx vite-node oxfmt", shell=True)


def _post_rust(ctx):
    ctx.run(["cargo", "install", "--locked", "flutter_rust_bridge_codegen"], check=False)


def _post_toolchains(ctx):
    if INSTALL_FLUTTER:
        ctx.run(["fvm", "install", "stable"], check=False)


def _post_containers(ctx):
    ctx.enable("docker")
    ctx.run(["usermod", "-aG", "docker,libvirt", ctx.user], sudo=True, check=False)


def _post_cloud(ctx):
    if ctx.dry or Path("/etc/cloudflared/token").exists():
        ctx.enable("cloudflared")
    else:
        raise StepPartial("no /etc/cloudflared/token → cloudflared not enabled")


# ---- phase 3 ----
def p_vscode(ctx):
    inv = BACKUP_DIR / "inventory/vscode-extensions.txt"
    exts = [e.strip() for e in inv.read_text().splitlines() if e.strip()] if inv.exists() else []
    if not exts:
        raise StepPartial("no inventory/vscode-extensions.txt")
    ctx.set_total(len(exts))
    failed = []
    for e in exts:
        ctx.status(e)
        if ctx.run(["code", "--install-extension", e, "--force"], check=False, quiet=True) != 0:
            failed.append(e)
        ctx.advance()
    if failed:
        raise StepPartial("extensions failed: " + " ".join(failed))


def p_services(ctx):
    ctx.run(["systemctl", "--user", "daemon-reload"], check=False)
    if (ctx.home / ".config/systemd/user/cli-proxy-api.service").exists() or ctx.dry:
        ctx.enable("cli-proxy-api", user=True)
    ctx.run(["sensors-detect", "--auto"], sudo=True, check=False, quiet=True)
    ctx.enable("lm_sensors")


def p_final(ctx):
    ctx.run(["fc-cache", "-f"], check=False)
    ctx.run(["update-desktop-database", str(ctx.home / ".local/share/applications")], check=False)
    ctx.run(["sudo", "-n", "grub-mkconfig", "-o", "/boot/grub/grub.cfg"], check=False)


STEPS: list[Step] = [
    # phase 1: priority files (sequential)
    Step("f-secrets",  "Restore secrets (ssh, keyrings, .env)",     1, "files", f_secrets),
    Step("f-config",   "Restore ~/.config & app settings",          1, "files", f_config),
    Step("f-browsers", "Restore browser profiles",                  1, "files", f_browsers),
    Step("f-t3",       "Restore T3 Code + agent chats",             1, "files", f_t3),
    Step("f-etc",      "Restore /etc (cloudflared token)",          1, "files", f_etc, True),
    Step("f-desktop",  "Restore SDDM/GRUB themes + greeter conf",   1, "files", f_desktop_system, True),
    # phase 2, lane FILES
    Step("f-code",     "Restore code (yojanAni, dotfiles, tmp)",    2, "files", f_code),
    Step("f-personal", "Restore personal files",                    2, "files", f_personal),
    Step("f-stow",     "Link dotfiles (stow)",                      2, "files", f_stow),
    Step("f-fixups",   "Small fixups (worktrees, Zen pref)",        2, "files", f_fixups),
    # phase 2, lane SYSTEM  (mirrors APPS.md sections)
    Step("s-arch",     "arch_setup.py: base system, drivers, apps", 2, "system", s_arch_setup, True),
    Step("s-shell",    "zsh, nvm/node LTS, rustup, speedtest",      2, "system", s_user_shell, True),
    Step("s-desktop",  "Hyprland, SDDM, Noctalia, portals, themes", 2, "system", s_desktop, True),
    Step("a-01-system", "APPS §1 system pieces + services",         2, "system", apps(
        ["sof-firmware", "alsa-firmware", "alsa-utils", "power-profiles-daemon", "bash-completion",
         "man-db", "man-pages", "openssh", "plocate", "pkgfile", "xdg-user-dirs", "xdg-utils",
         "ffmpegthumbnailer", "poppler-glib", "libopenraw", "libgsf", "gst-libav", "gst-plugins-bad",
         "gst-plugins-ugly", "gst-plugin-pipewire", "noto-fonts-cjk", "noto-fonts-emoji", "7zip", "unrar",
         "avahi", "nss-mdns", "lm_sensors", "smartmontools", "firewalld"], post=_post_system), True),
    Step("a-02-browsers", "APPS §2 browsers & chat",                2, "system", apps(
        ["firefox", "telegram-desktop", "remmina", "chaotic-aur/google-chrome",
         "chaotic-aur/claude-desktop", "chaotic-aur/vesktop"]), True),
    Step("a-03-editors", "APPS §3 editors & desktop AI apps",       2, "system", apps(
        ["zed", "meld"], ["t3code-bin", "cursor-bin", "antigravity", "wispr-flow-appimage", "hex-bin",
                          "zapfast-bin"]), True),
    Step("a-04-ai", "APPS §4 AI CLIs (claude, codex, gemini…)",     2, "system", apps(
        ["chaotic-aur/claude-code", "openai-codex", "gemini-cli", "opencode", "ollama-cuda"],
        ["cursor-cli", "coderabbit", "cli-proxy-api-bin"]), True),
    Step("a-05-js", "APPS §5 node, pnpm, bun, npm tools",           2, "system", apps(
        ["nvm", "pnpm", "bun"], ["vercel"], post=_post_js), True),
    Step("a-06-python", "APPS §6 python (uv, ruff)",                2, "system", apps(
        ["uv", "ruff", "python-pyqt6"]), True),
    Step("a-07-rust", "APPS §7 rust tools",                         2, "system", apps(
        ["cargo-expand", "cargo-watch", "cargo-ndk", "cargo-zigbuild", "cbindgen", "samply", "sea-orm-cli",
         "wasm-pack", "tree-sitter-cli", "trunk", "binaryen", "rust-analyzer"],
        ["cargo-leptos", "rustfilt"], post=_post_rust), True),
    Step("a-08-toolchains", "APPS §8 clang, zig, dart, go, flutter", 2, "system", apps(
        ["clang", "ninja", "zig", "dart", "fvm", "ghc", "patchelf", "perf", "go", "gopls"],
        post=_post_toolchains), True),
    Step("a-09-containers", "APPS §9 docker, pgvector, swtpm",      2, "system", apps(
        ["docker", "docker-compose", "docker-buildx", "pgvector", "swtpm"], post=_post_containers), True),
    Step("a-10-cloud", "APPS §10 cloud CLIs + cloudflared",         2, "system", apps(
        ["aws-cli-v2", "cloudflared", "rclone", "wget2", "httrack"], ["pscale-cli-bin"],
        post=_post_cloud), True),
    Step("a-11-utils", "APPS §11 CLI utils & terminals",            2, "system", apps(
        ["kitty", "gum", "tldr", "duf", "glances", "iotop", "pv", "fx", "wtype", "chaotic-aur/downgrade"]), True),
    Step("a-12-media", "APPS §12 media, creative, gaming",          2, "system", apps(
        ["krita", "gnome-sound-recorder", "gnuplot", "kio-gdrive", "wine", "lutris", "mangohud",
         "vulkan-intel", "lib32-vulkan-intel"], ["pulsemeeter"]), True),
    Step("a-13-misc", "APPS §13 fonts + Surfshark",                 2, "system", apps(
        [], ["ttf-ms-aptos-core", "surfshark-client"]), True),
    # phase 3
    Step("p-vscode",   "VS Code extensions",                        3, "post", p_vscode),
    Step("p-services", "User services, sensors",                    3, "post", p_services, True),
    Step("p-final",    "Fonts cache, desktop db, GRUB config",      3, "post", p_final, True),
]


# ───────────────────────────── state / logging ─────────────────────────────
STATE_DIR = Path.home() / ".local/state/home-restore"
STATE_FILE = STATE_DIR / "state.json"


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


_state_lock = threading.Lock()


def save_state(state: dict):
    with _state_lock:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2))
        tmp.replace(STATE_FILE)


# ───────────────────────────── sudo handling ─────────────────────────────
def sudo_validate(pw: str) -> bool:
    r = subprocess.run(["sudo", "-S", "-p", "", "-v"], input=pw + "\n", text=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def ask_sudo(console) -> str:
    subprocess.run(["sudo", "-k"])
    for _ in range(3):
        pw = getpass.getpass(f"sudo password for {getpass.getuser()} (asked once, kept in memory only): ")
        if sudo_validate(pw):
            return pw
        console.print("[red]wrong password, try again[/]")
    sys.exit("3 wrong sudo passwords, aborting.")


def sudo_keepalive(pw: str, stop: threading.Event):
    while not stop.wait(45):
        sudo_validate(pw)


# ───────────────────────────── runner ─────────────────────────────
def run_step(ctx_base: Ctx, step: Step, state: dict, results: list, console):
    ctx = Ctx(**{**ctx_base.__dict__, "lane": step.lane, "step": step,
                 "lock": ctx_base.lock, "procs": ctx_base.procs, "stop": ctx_base.stop})
    logp = ctx.run_dir / f"{step.id}.log"
    t0 = time.time()
    status, msg = "ok", ""
    ctx.progress.update(ctx.task_ids[step.lane], description=f"{step.lane:>6} | {step.title}",
                        total=None, completed=0, status="")
    with open(logp, "a", buffering=1) as log:
        ctx.log = log
        log.write(f"### {step.id}: {step.title}  ({dt.datetime.now():%F %T})\n")
        try:
            if step.needs_sudo and ctx.sudo_pw and not ctx.dry:
                sudo_validate(ctx.sudo_pw)
            step.fn(ctx)
        except StepPartial as e:
            status, msg = "partial", str(e)
        except StepFailed as e:
            status, msg = "failed", str(e)
        except Exception as e:  # unexpected python error: keep going with other steps
            status, msg = "failed", f"{type(e).__name__}: {e}"
        log.write(f"### result: {status} {msg}\n")
    took = time.time() - t0
    rec = {"status": status, "msg": msg, "log": str(logp), "seconds": round(took),
           "at": dt.datetime.now().isoformat(timespec="seconds")}
    if not ctx.dry:
        state[step.id] = rec
        save_state(state)
    results.append((step, rec))
    tag = {"ok": "[green][ OK ][/]", "partial": "[yellow][WARN][/]", "failed": "[red][FAIL][/]"}[status]
    console.print(f"{tag} {step.title}  [dim]({took/60:.1f} min)[/]" + (f"\n       [dim]{escape(msg)}[/]" if msg else ""))
    if status != "ok":
        with open(ctx.run_dir / "errors.log", "a") as ef:
            tail = logp.read_text(errors="replace").splitlines()[-40:]
            ef.write(f"\n===== {step.id} [{status}] {step.title}\n{msg}\nlog: {logp}\n--- last lines ---\n")
            ef.write("\n".join(tail) + "\n")
    ctx.progress.advance(ctx.task_ids["overall"])
    return status


def main():
    ap = argparse.ArgumentParser(description="Autopilot restore of home + software on fresh Arch.")
    ap.add_argument("--dry-run", action="store_true", help="show what would run, change nothing")
    ap.add_argument("--list", action="store_true", help="list steps and saved status, then exit")
    ap.add_argument("--only", help="comma-separated step ids to run (ignores saved state)")
    ap.add_argument("--skip", help="comma-separated step ids to skip")
    ap.add_argument("--redo", action="store_true", help="ignore saved state, run everything again")
    ap.add_argument("--home", help="restore into another directory (testing)")
    ap.add_argument("--no-sudo", action="store_true", help="testing: don't ask sudo; skip sudo steps")
    args = ap.parse_args()

    if os.geteuid() == 0:
        sys.exit("Run this as your normal user (not root); it uses sudo itself.")

    _ensure_rich(None)
    from rich.console import Console
    from rich.progress import (BarColumn, Progress, ProgressColumn, SpinnerColumn, TaskProgressColumn,
                               TextColumn, TimeElapsedColumn)
    from rich.table import Table
    from rich.text import Text
    from rich.markup import escape
    globals()["escape"] = escape

    console = Console()
    state = load_state()

    if args.list:
        t = Table("phase", "lane", "id", "title", "status", "when")
        for s in STEPS:
            r = state.get(s.id, {})
            t.add_row(str(s.phase), s.lane, s.id, s.title, r.get("status", "-"), r.get("at", ""))
        console.print(t)
        return

    only = set(args.only.split(",")) if args.only else None
    skip = set(args.skip.split(",")) if args.skip else set()
    todo = []
    for s in STEPS:
        if only is not None:
            if s.id in only:
                todo.append(s)
            continue
        if s.id in skip:
            continue
        if not args.redo and state.get(s.id, {}).get("status") == "ok":
            continue
        if args.no_sudo and s.needs_sudo:
            continue
        todo.append(s)

    home = Path(args.home).resolve() if args.home else Path.home()
    run_dir = STATE_DIR / dt.datetime.now().strftime("run-%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    console.rule("[bold]Arch autopilot restore")
    console.print(f"backup: {BACKUP_DIR}\nhome:   {home}\nlogs:   {run_dir}\n"
                  f"steps:  {len(todo)} to run ({len(STEPS) - len(todo)} done/skipped)"
                  + ("   [yellow]DRY RUN[/]" if args.dry_run else ""))
    if not todo:
        console.print("[green]Nothing to do; everything is already done.[/] (use --redo or --only)")
        return

    # ---- phase 0: preflight ----
    missing = [a for a in ("01-code.tar.zst", "02-personal.tar.zst", "03-secrets.tar.zst",
                           "04-t3code.tar.zst", "05-browsers.tar.zst", "06-config.tar.zst",
                           "07-system.tar.zst", "08-system-desktop.tar.zst") if not (BACKUP_DIR / a).exists()]
    if missing:
        console.print(f"[yellow]missing archives:[/] {', '.join(missing)}")
    if not args.dry_run and not args.home:          # --home = test runs into a scratch dir
        free = shutil.disk_usage(home).free / 2**30
        if free < 30:
            sys.exit(f"Only {free:.0f} GiB free in {home}; need ~30 GiB.")
    sudo_pw = None
    if not args.no_sudo and not args.dry_run and any(s.needs_sudo for s in todo):
        sudo_pw = ask_sudo(console)
    if not args.dry_run:
        net = subprocess.run(["curl", "-sfI", "--max-time", "10", "https://archlinux.org"],
                             stdout=subprocess.DEVNULL).returncode == 0
        if not net and any(s.lane != "files" for s in todo):
            sys.exit("No internet. Connect first (e.g. `nmtui`), then re-run.")
    stop = threading.Event()
    if sudo_pw:
        threading.Thread(target=sudo_keepalive, args=(sudo_pw, stop), daemon=True).start()
        missing_bin = [p for p, b in (("zstd", "zstd"), ("git", "git"), ("stow", "stow"), ("curl", "curl"))
                       if not shutil.which(b)]
        console.print("[bold]bootstrap:[/] pacman -Syu + " + " ".join(BOOTSTRAP_PKGS))
        r = subprocess.run(["sudo", "-n", "pacman", "-Syu", "--needed", "--noconfirm", *BOOTSTRAP_PKGS],
                           stdout=open(run_dir / "00-bootstrap.log", "w"), stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            console.print(f"[yellow]bootstrap pacman exited {r.returncode} (see 00-bootstrap.log)[/]")
            if missing_bin:
                sys.exit(f"Required tools still missing: {missing_bin}. Fix pacman, then re-run.")

    # ---- progress UI ----
    linux_tty = os.environ.get("TERM") == "linux"

    class AsciiBar(ProgressColumn):
        def render(self, task):
            w = 24
            if not task.total:
                pos = int(time.time() * 6) % w
                return Text("[" + " " * pos + "<=>"[: w - pos] + " " * max(0, w - pos - 3) + "]")
            n = int(w * min(1.0, task.completed / task.total))
            return Text("[" + "#" * n + "-" * (w - n) + "]")

    bar = AsciiBar() if linux_tty else BarColumn(bar_width=24)
    progress = Progress(SpinnerColumn("line" if linux_tty else "dots"), TextColumn("{task.description:<46}"),
                        bar, TaskProgressColumn(), TimeElapsedColumn(),
                        TextColumn("[dim]{task.fields[status]}"), console=console, refresh_per_second=4)
    results: list = []
    ctx = Ctx(home=home, user=getpass.getuser(), run_dir=run_dir, dry=args.dry_run,
              sudo_pw=sudo_pw, progress=progress, stop=stop)

    def on_sigint(*_):
        stop.set()
        with ctx.lock:
            for p in list(ctx.procs):
                try:
                    p.terminate()
                except Exception:
                    pass
        console.print("\n[red]Interrupted, state is saved; re-run to continue.[/]")
    signal.signal(signal.SIGINT, on_sigint)

    t_start = time.time()
    with progress:
        ctx.task_ids["overall"] = progress.add_task("[b]OVERALL", total=len(todo), status="")
        for lane in ("files", "system", "post"):
            ctx.task_ids[lane] = progress.add_task(f"{lane:>6} | waiting", total=None, status="")

        def lane_worker(steps):
            for s in steps:
                if stop.is_set():
                    return
                run_step(ctx, s, state, results, progress.console)

        for phase in (1, 2, 3):
            ph = [s for s in todo if s.phase == phase]
            if not ph or stop.is_set():
                continue
            progress.console.rule(f"phase {phase}")
            lanes = {}
            for s in ph:
                lanes.setdefault(s.lane, []).append(s)
            threads = [threading.Thread(target=lane_worker, args=(v,)) for v in lanes.values()]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            for lane in lanes:
                progress.update(ctx.task_ids[lane], description=f"{lane:>6} | done", total=1, completed=1,
                                status="")
    stop.set()

    # ---- summary ----
    took = (time.time() - t_start) / 60
    t = Table("step", "result", "min", "message", title=f"Summary ({took:.0f} min)")
    for s, r in results:
        color = {"ok": "green", "partial": "yellow", "failed": "red"}[r["status"]]
        t.add_row(s.id, f"[{color}]{r['status']}[/]", f"{r['seconds']/60:.1f}", escape(r["msg"][:80]))
    console.print(t)
    (run_dir / "summary.json").write_text(json.dumps(
        [{"id": s.id, **r} for s, r in results], indent=2))
    bad = [r for _, r in results if r["status"] != "ok"]
    if bad:
        console.print(f"[yellow]{len(bad)} step(s) need attention → {run_dir/'errors.log'}[/]\n"
                      "Fix the cause, then just run the script again; finished steps are skipped.")
    else:
        console.print("[green]All steps finished.[/]")
    console.print("\n[b]Next (manual):[/] reboot → log in at the SDDM greeter. See README.md "
                  "'After the script' for the logins/checks list.")


if __name__ == "__main__":
    main()
