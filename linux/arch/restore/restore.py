#!/usr/bin/env python3
"""
Autopilot home + software restore for a fresh EndeavourOS install (Hyprland edition).

Run from the pen drive's Backup/ folder, in a terminal, as your normal user:

    bash restore.sh            # bootstraps python if missing, then runs this file
    python3 restore.py --help

Phases
  0  preflight: sudo password (asked ONCE), network, disk space, bootstrap deps
  1  priority files: secrets, configs, browsers, T3 chats, /etc + theme files
  2  in parallel:
       lane FILES : code (01) + personal (02), stow dotfiles, small fixups
       lane SYSTEM: arch_setup.py, desktop extras (Noctalia/portals/themes), apps from APPS.md
  3  needs both lanes: VS Code extensions, user services, sensors, final touches

State is saved after every step; re-running skips finished steps and retries failed ones.
Logs: ~/.local/state/home-restore/<run>/  (one log per step + live.log + errors.log + summary)
Watch everything live from another terminal:
    tail -f ~/.local/state/home-restore/latest/live.log
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
FRAC_SCALE = "1.25"      # X11 SDDM greeter scale (/etc/sddm.conf.d/hidpi.conf)
GOOGLE_DNS = True        # arch_setup.py writes IPv4 DNS (1.1.1.1, 8.8.4.4) + chattr +i /etc/resolv.conf
INSTALL_FLUTTER = True   # `fvm install stable` (~1.5 GB download)

BACKUP_DIR = Path(__file__).resolve().parent
BOOTSTRAP_PKGS = ["python-rich", "python-typer", "python-pydantic", "zstd", "tar", "git",
                  "stow", "curl", "base-devel", "sudo", "reflector", "nvm", "rustup",
                  "fontconfig", "desktop-file-utils", "xdg-user-dirs"]

# Safety net only: used when /etc/pacman.d/mirrorlist is completely empty (a failed
# `reflector > mirrorlist` truncates it). On a normal EndeavourOS install this never triggers.
MIRROR_FALLBACK = """# Fallback mirrors written by restore.py; reflector can refine this later.
Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch
Server = https://mirror.rackspace.com/archlinux/$repo/os/$arch
Server = https://mirrors.kernel.org/archlinux/$repo/os/$arch
"""

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


# ───────────────────────────── live log (observability) ─────────────────────────────
# Every line any step writes also goes to <run>/live.log as "HH:MM:SS [step-id] line", so
# one `tail -f ~/.local/state/home-restore/latest/live.log` shows everything that happens.
# With --verbose the same lines are also echoed under the progress bars.
class Live:
    f = None
    verbose = False
    console = None
    lock = threading.Lock()

    @classmethod
    def write(cls, tag: str, text: str, echo: bool = False, style: str = "dim"):
        lines = text.rstrip("\n").split("\n") if text.strip() else []
        if not lines:
            return
        ts = dt.datetime.now().strftime("%H:%M:%S")
        with cls.lock:
            if cls.f:
                for ln in lines:
                    cls.f.write(f"{ts} [{tag}] {ln}\n")
                cls.f.flush()
        if (echo or cls.verbose) and cls.console:
            from rich.text import Text
            for ln in lines:
                cls.console.print(Text(f"{ts} [{tag}] {ln}"[:400], style=style))


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
        Live.write(self.step.id if self.step else "main", text)

    def note(self, text: str):
        """Important progress message: always shown on screen + written to the logs."""
        if self.log:
            self.log.write(f">> {text}\n")
            self.log.flush()
        Live.write(self.step.id if self.step else "main", f">> {text}", echo=True, style="cyan")

    def warn(self, text: str):
        if self.log:
            self.log.write(f"!! {text}\n")
            self.log.flush()
        Live.write(self.step.id if self.step else "main", f"!! {text}", echo=True, style="yellow")

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
        self.status(f"$ {shown}")
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, text=True, bufsize=1, cwd=cwd,
                                 env=full_env, errors="replace")
        except OSError as e:
            raise StepFailed(f"cannot run '{shown[:100]}': {e}")
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
        if rc != 0:
            self.logln(f"!! exit {rc}: {shown[:200]}")
        if check and rc != 0:
            raise StepFailed(f"exit {rc}: {shown[:120]}")
        return rc

    # ---- package helpers ----
    def ensure_db(self):
        """Sync pacman DBs once per process (fixes 'could not find database')."""
        if self.dry:
            return
        sync_databases(self.log)

    def ensure_paru(self):
        if self.dry:
            return
        if shutil.which("paru"):
            return
        if not install_paru(self.log):
            raise StepFailed("paru is not installed and could not be installed "
                             "(see 00-bootstrap.log / this step's log)")

    @staticmethod
    def installed(name: str) -> bool:
        return subprocess.run(["pacman", "-Q", name], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0

    def pkgs(self, names: list[str], aur: bool = False):
        """Install packages; on failure retry one by one so a single bad name can't block the rest.

        A repo package that is missing from core/extra/chaotic-aur is retried through paru,
        so AUR-only names don't turn into a failed step.
        """
        names = list(dict.fromkeys(n for n in names if n))
        if not names:
            return
        self.ensure_db()
        if aur:
            self.ensure_paru()
        base = (["paru", "-S", "--needed", "--noconfirm", "--skipreview"] if aur
                else ["pacman", "-S", "--needed", "--noconfirm"])
        # A transaction can abort because one mirror stalled. Retry the whole group once:
        # packages that already downloaded stay in the cache, so this is much faster than
        # falling straight back to one-by-one installs.
        for attempt in (1, 2):
            try:
                self.run(base + names, sudo=not aur)
                return
            except StepFailed:
                if attempt == 1:
                    self.logln(f"\n!! group install failed (attempt 1/2); retrying the same "
                               f"{len(names)} packages (cached downloads are reused)")
        self.warn(f"group install failed twice; retrying {len(names)} packages one by one")
        failed = []
        for i, n in enumerate(names, 1):
            bare = n.split("/")[-1]
            if self.installed(bare):
                continue
            self.status(f"retry {i}/{len(names)}: {n}")
            if self.run(base + [n], sudo=not aur, check=False) != 0:
                failed.append(n)
                self.warn(f"package failed: {n}")
        # A name missing from the repos may live in the AUR.
        if failed and not aur:
            try:
                self.ensure_paru()
            except StepFailed:
                pass
            else:
                still = []
                for n in failed:
                    bare = n.split("/")[-1]
                    self.status(f"AUR fallback: {bare}")
                    if self.run(["paru", "-S", "--needed", "--noconfirm", "--skipreview", bare],
                                check=False) != 0:
                        still.append(n)
                failed = still
        if failed:
            raise StepPartial("failed packages: " + " ".join(failed))

    def enable(self, *units, user=False, now=True):
        for u in units:
            cmd = ["systemctl"] + (["--user"] if user else []) + ["enable"] + (["--now"] if now else []) + [u]
            self.run(cmd, sudo=not user, check=False)

    # ---- archive extraction (sha256 verified while streaming) ----
    def extract(self, archive: str, dest: Path, sudo=False, extra=None, members=None, acl=True,
                exclude_file: Path | None = None):
        path = BACKUP_DIR / archive
        if not path.exists():
            raise StepFailed(f"missing archive {path}")
        sums = read_sums()
        size = path.stat().st_size
        self.set_total(size)
        tar = ["tar", "-C", str(dest), "--keep-directory-symlink"]
        if acl:
            tar += ["--acls", "--xattrs", "--xattrs-include=*"]
        tar += ["-xpf", "-", *(extra or [])]
        if exclude_file:
            tar += ["--no-wildcards", f"--exclude-from={exclude_file}"]
        tar += [*(members or [])]
        if sudo:
            tar = ["sudo", "-n", *tar]
        self.logln(f"\n$ zstd -dc {path} | {' '.join(tar)}")
        self.status(f"extracting {archive} ({size / 2**30:.1f} GiB) → {dest}")
        if self.dry:
            self.set_completed(size)
            return
        h = hashlib.sha256()
        t0 = time.time()
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
            try:
                z.stdin.close()
            except BrokenPipeError:
                pass
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
        self.logln(f"extracted {archive}: {size / 2**30:.2f} GiB in {time.time() - t0:.0f}s")


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


# ─────────────────────── pacman bootstrap: mirrors, DBs, paru ───────────────────────
# On a fresh archinstall, /etc/pacman.conf can already contain [multilib] and
# [chaotic-aur] while their *.db files do not exist. Every `pacman -S` then aborts
# with "failed to prepare transaction (could not find database)", which is what made
# the previous run install almost nothing. Sync the DBs first, then install paru.
_PACMAN_LOCK = threading.RLock()
_DB_READY = False
_PARU_READY = False
_PACMAN_TUNED = False


def _logline(log, text: str) -> None:
    if log:
        log.write(text if text.endswith("\n") else text + "\n")
        log.flush()
    Live.write("pacman-setup", text)


def _run_bootstrap(cmd, log=None, cwd=None, input_text=None) -> int:
    """Small subprocess helper used before the rich Progress UI exists."""
    _logline(log, "\n$ " + " ".join(cmd))
    try:
        p = subprocess.Popen(cmd, text=True, errors="replace", cwd=cwd,
                             stdin=subprocess.DEVNULL if input_text is None else subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if input_text is not None:
            p.stdin.write(input_text)
            p.stdin.close()
        for line in p.stdout:
            _logline(log, line.rstrip("\n"))
        rc = p.wait()
        if rc != 0:
            _logline(log, f"!! exit {rc}: {' '.join(cmd)[:200]}")
        return rc
    except OSError as e:
        _logline(log, f"!! {e}")
        return 127


def _has_servers(path: Path) -> bool:
    try:
        return any(line.strip().startswith("Server") for line in path.read_text().splitlines())
    except OSError:
        return False


def _pacman_running() -> bool:
    for name in ("pacman", "paru"):
        try:
            if subprocess.run(["pgrep", "-x", name], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0:
                return True
        except OSError:
            pass
    return False


def clear_stale_lock(log=None) -> bool:
    """Remove /var/lib/pacman/db.lck left behind by an interrupted run.

    pacman refuses every transaction while this file exists. Only remove it when no
    pacman/paru process is alive, so a concurrent install is never corrupted.
    """
    lock = Path("/var/lib/pacman/db.lck")
    if not lock.exists():
        return True
    if _pacman_running():
        _logline(log, "pacman is running; leaving /var/lib/pacman/db.lck in place")
        return False
    _logline(log, "!! stale /var/lib/pacman/db.lck (no pacman running) → removing it")
    return _run_bootstrap(["sudo", "-n", "rm", "-f", str(lock)], log) == 0


def tune_pacman_conf(log=None) -> bool:
    """Raise ParallelDownloads so big package sets download in parallel."""
    script = (
        "f=/etc/pacman.conf; "
        "if grep -qE '^[#[:space:]]*ParallelDownloads[[:space:]]*=' \"$f\"; then "
        "  sed -i -E 's|^[#[:space:]]*ParallelDownloads[[:space:]]*=.*|ParallelDownloads = 20|' \"$f\"; "
        "else sed -i '/^\\[options\\]/a ParallelDownloads = 20' \"$f\"; fi; "
        "grep -nE '^ParallelDownloads' \"$f\""
    )
    return _run_bootstrap(["sudo", "-n", "bash", "-c", script], log) == 0


def ensure_mirrorlist(log=None) -> bool:
    """Guarantee /etc/pacman.d/mirrorlist has at least one Server line."""
    p = Path("/etc/pacman.d/mirrorlist")
    if _has_servers(p):
        return True
    text = None
    for cand in (Path("/etc/pacman.d/mirrorlist.pacnew"), Path("/etc/pacman.d/mirrorlist.orig")):
        if _has_servers(cand):
            text = cand.read_text()
            break
    if text is None:
        text = MIRROR_FALLBACK
    _logline(log, f"!! {p} is empty/missing → writing fallback mirrors")
    _run_bootstrap(["sudo", "-n", "tee", str(p)], log, input_text=text)
    return _has_servers(p)


def ensure_chaotic(log=None) -> bool:
    """Install chaotic-aur keyring/mirrorlist when the repo is configured but unusable."""
    try:
        if "[chaotic-aur]" not in Path("/etc/pacman.conf").read_text():
            return True                      # arch_setup.py adds it later
    except OSError:
        return False
    ml = Path("/etc/pacman.d/chaotic-mirrorlist")
    keyring_ok = subprocess.run(["pacman", "-Q", "chaotic-keyring"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if keyring_ok and _has_servers(ml):
        return True
    _logline(log, "!! chaotic-aur keyring/mirrorlist missing → installing them")
    _run_bootstrap(["sudo", "-n", "pacman-key", "--recv-key", "3056513887B78AEB",
                    "--keyserver", "keyserver.ubuntu.com"], log)
    _run_bootstrap(["sudo", "-n", "pacman-key", "--lsign-key", "3056513887B78AEB"], log)
    _run_bootstrap(["sudo", "-n", "pacman", "--noconfirm", "-U",
                    "https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst",
                    "https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst"], log)
    return _has_servers(ml)


def sync_databases(log=None) -> bool:
    """Force-sync every repo DB. Safe to call repeatedly; does real work once."""
    global _DB_READY, _PACMAN_TUNED
    with _PACMAN_LOCK:
        clear_stale_lock(log)
        if not _PACMAN_TUNED:
            tune_pacman_conf(log)
            _PACMAN_TUNED = True
        if _DB_READY:
            return True
        ensure_mirrorlist(log)
        ensure_chaotic(log)
        for extra in ([], ["--disable-download-timeout"]):
            if _run_bootstrap(["sudo", "-n", "pacman", "-Syy", "--noconfirm", *extra], log) == 0:
                _DB_READY = True
                _logline(log, "pacman databases synced")
                return True
        _logline(log, "!! pacman -Syy failed; package installs may still fail")
        return False


def install_paru(log=None) -> bool:
    """Install paru from chaotic-aur; fall back to building paru-bin from the AUR."""
    global _PARU_READY
    with _PACMAN_LOCK:
        if shutil.which("paru"):
            _PARU_READY = True
            return True
        sync_databases(log)
        _logline(log, "installing paru (AUR helper)")
        if _run_bootstrap(["sudo", "-n", "pacman", "-S", "--needed", "--noconfirm", "paru"], log) == 0 \
                and shutil.which("paru"):
            _PARU_READY = True
            return True
        # Fallback: build the prebuilt paru-bin package from the AUR (no Rust compile).
        for repo in ("paru-bin", "paru"):
            build = Path("/tmp/restore-paru-build")
            shutil.rmtree(build, ignore_errors=True)
            _logline(log, f"paru not in a repo → building {repo} from the AUR")
            if _run_bootstrap(["git", "clone", "--depth", "1",
                               f"https://aur.archlinux.org/{repo}.git", str(build)], log) != 0:
                continue
            if _run_bootstrap(["makepkg", "-si", "--noconfirm", "--needed"], log, cwd=build) == 0 \
                    and shutil.which("paru"):
                _PARU_READY = True
                return True
        _logline(log, "!! could not install paru")
        return False


def bootstrap_pacman(log=None, say=print) -> bool:
    """Phase-0 on EndeavourOS: DB sync → system upgrade + base tools → paru.

    EndeavourOS already ships working mirrorlists (Arch + endeavouros), chaotic-aur is
    set up and paru is installed, so nothing here rewrites mirrors or pacman.conf.
    """
    say("  · checking mirrorlist / chaotic-aur / pacman lock")
    ensure_mirrorlist(log)
    ensure_chaotic(log)
    clear_stale_lock(log)
    say("  · syncing pacman databases (pacman -Syy)")
    sync_databases(log)
    say(f"  · system upgrade + {len(BOOTSTRAP_PKGS)} base tools (pacman -Syu) — can take a few minutes")
    _logline(log, "installing bootstrap packages: " + " ".join(BOOTSTRAP_PKGS))
    if _run_bootstrap(["sudo", "-n", "pacman", "-Syu", "--needed", "--noconfirm", *BOOTSTRAP_PKGS], log) != 0:
        say("  · [warn] -Syu failed; retrying the base tools without the upgrade")
        _run_bootstrap(["sudo", "-n", "pacman", "-S", "--needed", "--noconfirm", *BOOTSTRAP_PKGS], log)
    say("  · checking paru")
    return install_paru(log)


# ───────────────────────────── step implementations ─────────────────────────────
def os_config(ctx: Ctx) -> Path:
    return ctx.home / ".config/os-config/linux/arch"


# ---- phase 1: priority files ----
def keep_git_clones(ctx, repos: list[str]) -> Path | None:
    """Build a tar exclude list so existing git clones are NOT overwritten by the backup.

    ~/.dotfiles and ~/.config/os-config were cloned fresh (and fixed for EndeavourOS) before
    this restore. The archives hold the older copies. For each clone that already exists we
    exclude its .git dir and every tracked file, so the clone stays authoritative and the
    backup only adds what git doesn't track (my_env.sh, themes, caches, …).
    """
    lines = []
    for rel in repos:
        repo = ctx.home / rel
        if not (repo / ".git").exists():
            ctx.logln(f"{rel}: no existing clone → restoring it fully from the backup")
            continue
        r = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True)
        tracked = [f for f in r.stdout.decode(errors="replace").split("\0") if f]
        lines.append(f"{rel}/.git")
        lines += [f"{rel}/{f}" for f in tracked]
        head = subprocess.run(["git", "-C", str(repo), "log", "--oneline", "-1"],
                              capture_output=True, text=True).stdout.strip()
        ctx.logln(f"{rel}: existing clone kept (HEAD {head}); skipping .git + {len(tracked)} tracked files")
    if not lines:
        return None
    f = ctx.run_dir / f"{ctx.step.id}-keep-clones.exclude"
    f.write_text("\n".join(lines) + "\n")
    return f


def f_secrets(ctx):  ctx.extract("03-secrets.tar.zst", ctx.home)
def f_config(ctx):
    ctx.extract("06-config.tar.zst", ctx.home,
                exclude_file=keep_git_clones(ctx, [".config/os-config"]))
def f_browsers(ctx): ctx.extract("05-browsers.tar.zst", ctx.home)
def f_t3(ctx):       ctx.extract("04-t3code.tar.zst", ctx.home)
def f_etc(ctx):      ctx.extract("07-system.tar.zst", Path("/"), sudo=True)


WAYLAND_GREETER_FILES = ["/etc/sddm.conf.d/zz-wayland-greeter.conf", "/etc/udev/rules.d/61-intel-igpu.rules"]


def f_desktop_system(ctx):
    # /etc + /usr/share parts keep root ownership. The SDDM greeter stays on X11, so the
    # KWin/Wayland greeter drop-in and its Intel-GPU udev rule (from the Arch attempt) are
    # NOT restored. hidpi.conf (QT_SCREEN_SCALE_FACTORS=1.25) is, which scales the X11 greeter.
    ctx.extract("08-system-desktop.tar.zst", Path("/"), sudo=True,
                extra=["--anchored", "--exclude=boot", "--exclude=etc/default/grub",
                       *[f"--exclude={p.lstrip('/')}" for p in WAYLAND_GREETER_FILES]])
    ctx.extract("08-system-desktop.tar.zst", Path("/"), sudo=True,
                extra=["--no-same-owner", "--no-same-permissions"], members=["boot/grub/themes"],
                acl=False)
    # GRUB: plain default (black/text) menu, no theme. The theme files stay in /boot/grub/themes.
    ctx.run(r"""set -e
f=/etc/default/grub; [ -f "$f" ] || exit 0
sed -i -E 's|^(GRUB_THEME|GRUB_BACKGROUND)=|#\1=|' "$f"
fc-cache -f >/dev/null 2>&1 || true""", sudo=True, shell=True)
    # X11 greeter: drop any Wayland greeter leftovers, make sure the 1.25 scale is set.
    ctx.run(f"""set -e
rm -fv {' '.join(WAYLAND_GREETER_FILES)}
mkdir -p /etc/sddm.conf.d
f=/etc/sddm.conf.d/hidpi.conf
if ! grep -qs 'QT_SCREEN_SCALE_FACTORS={FRAC_SCALE}' "$f"; then
  printf '[General]\nGreeterEnvironment=QT_SCREEN_SCALE_FACTORS={FRAC_SCALE}\n' > "$f"
fi
echo "--- SDDM drop-ins now:"; for c in /etc/sddm.conf /etc/sddm.conf.d/*.conf; do echo "## $c"; cat "$c" 2>/dev/null || true; done
udevadm control --reload || true""", sudo=True, shell=True)


# ---- phase 2, lane FILES ----
def f_code(ctx):
    ctx.extract("01-code.tar.zst", ctx.home, exclude_file=keep_git_clones(ctx, [".dotfiles"]))
def f_personal(ctx): ctx.extract("02-personal.tar.zst", ctx.home)


def f_stow(ctx):
    d = ctx.home / ".dotfiles"
    ctx.run(["stow", "--no", "-v", "-R", "."], cwd=d)     # dry run first: shows conflicts in the log
    ctx.run(["stow", "-v", "-R", "."], cwd=d)             # --restow makes re-runs idempotent


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
    if shutil.which("xdg-user-dirs-update"):
        ctx.run(["xdg-user-dirs-update"], check=False)
    else:
        ctx.logln("xdg-user-dirs-update not installed yet; skipping (a-01 installs it)")


# ---- phase 2, lane SYSTEM ----
def s_arch_setup(ctx):
    # Make sure pacman works before the generated script runs (no-ops on a healthy system).
    if not ctx.dry:
        ensure_mirrorlist(ctx.log)
        ensure_chaotic(ctx.log)
        sync_databases(ctx.log)
        ctx.ensure_paru()

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

    # Patch the generated script in two places so it cannot destroy the pacman setup again.
    text = gen.read_text()
    old_reflector = ("reflector --verbose -c IN -c SG --protocol https --sort age --latest 20 "
                     "--download-timeout 5 > /etc/pacman.d/mirrorlist")
    new_reflector = ("if command -v reflector >/dev/null 2>&1; then "
                     "reflector --verbose -c IN -c SG --protocol https --sort rate --latest 20 "
                     "--download-timeout 10 > /etc/pacman.d/mirrorlist.restore-new 2>/dev/null "
                     "&& [ -s /etc/pacman.d/mirrorlist.restore-new ] "
                     "&& mv /etc/pacman.d/mirrorlist.restore-new /etc/pacman.d/mirrorlist; fi")
    # Keep the EndeavourOS /etc/pacman.conf (it already has [endeavouros], [multilib] and
    # [chaotic-aur]); don't swap in the dotfiles copy, which pins linux/nvidia via IgnorePkg.
    old_curl = ("curl https://raw.githubusercontent.com/shubhattin/dotfiles/refs/heads/main/"
                "others/pacman.conf -o /etc/pacman.conf")
    new_curl = ("echo 'restore: keeping the EndeavourOS /etc/pacman.conf (not replaced)'\n"
                "pacman -Syy --noconfirm")
    for name, old, new in (("reflector", old_reflector, new_reflector), ("pacman.conf", old_curl, new_curl)):
        if old in text:
            text = text.replace(old, new)
            ctx.logln(f"patch applied: {name}")
        else:
            ctx.logln(f"!! patch NOT applied ({name}): line not found in generated script")
            ctx.warn(f"arch_setup patch '{name}' not applied — check {ctx.step.id}.log")

    shutil.copy(gen, ctx.run_dir / "arch_setup-generated.original.sh")
    patched = ctx.run_dir / "arch_setup-generated.sh"
    patched.write_text(text)
    ctx.logln(f"running patched script: {patched}")
    ctx.note(f"running generated setup script ({sum(1 for l in text.splitlines() if l.startswith('pacman '))} pacman calls)")
    rc = ctx.run(["bash", str(patched)], sudo=True, check=False)
    # The script swaps in the upstream pacman.conf; make sure ParallelDownloads survives it.
    tune_pacman_conf(ctx.log)

    # the generated script never stops on errors → surface pacman errors as a partial result
    errs = [l for l in (ctx.run_dir / f"{ctx.step.id}.log").read_text(errors="replace").splitlines()
            if l.startswith("error:")]
    if errs:
        raise StepPartial(f"{len(errs)} 'error:' lines (e.g. {errs[0][:90]})")
    if rc != 0:
        raise StepPartial(f"generated script exited {rc} (non-fatal; see log)")


def s_user_shell(ctx):
    ctx.run(["chsh", "-s", "/usr/bin/zsh", ctx.user], sudo=True)
    nvm_init = Path("/usr/share/nvm/init-nvm.sh")
    if nvm_init.exists():
        ctx.run(f"source {nvm_init} && nvm install --lts && nvm alias default 'lts/*'",
                shell=True, check=False)
    else:
        ctx.logln("nvm not installed yet; skipping node LTS here (a-05 installs nvm)")
    if shutil.which("rustup"):
        ctx.run(["rustup", "default", "stable"], check=False)
        ctx.run(["rustup", "toolchain", "install", "nightly", "--profile", "minimal"], check=False)
    else:
        ctx.logln("rustup not installed yet; skipping (arch_setup.py installs it)")
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
    if shutil.which("pkgfile"):
        ctx.run(["pkgfile", "--update"], sudo=True, check=False)


def _post_js(ctx):
    init = Path("/usr/share/nvm/init-nvm.sh")
    if init.exists():
        ctx.run(f"source {init} && nvm install --lts && npm i -g tsx vite-node oxfmt",
                shell=True, check=False)
    else:
        ctx.logln("nvm unavailable; skipping npm globals (re-run a-05 after fixing nvm)")


def _post_rust(ctx):
    if shutil.which("cargo"):
        ctx.run(["cargo", "install", "--locked", "flutter_rust_bridge_codegen"], check=False)
    else:
        ctx.logln("cargo unavailable; skipping flutter_rust_bridge_codegen")


def _post_toolchains(ctx):
    if INSTALL_FLUTTER and shutil.which("fvm"):
        ctx.run(["fvm", "install", "stable"], check=False)
    elif INSTALL_FLUTTER:
        ctx.logln("fvm unavailable; skipping `fvm install stable`")


def _post_containers(ctx):
    ctx.enable("docker")
    groups = [g for g in ("docker", "libvirt")
              if subprocess.run(["getent", "group", g], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL).returncode == 0]
    if groups:
        ctx.run(["usermod", "-aG", ",".join(groups), ctx.user], sudo=True, check=False)
    else:
        ctx.logln("docker/libvirt groups do not exist yet; skipping usermod")


def _post_cloud(ctx):
    if ctx.dry or Path("/etc/cloudflared/token").exists():
        ctx.enable("cloudflared")
    else:
        raise StepPartial("no /etc/cloudflared/token → cloudflared not enabled")


# ---- phase 3 ----
def p_vscode(ctx):
    if not shutil.which("code") and not ctx.dry:
        ctx.logln("`code` not found; installing visual-studio-code-bin")
        try:
            ctx.pkgs(["visual-studio-code-bin"])
        except StepPartial as e:
            ctx.logln(str(e))
    if not shutil.which("code"):
        if ctx.dry:
            return
        raise StepPartial("VS Code (`code`) is not installed; extensions skipped")
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
    if shutil.which("sensors-detect"):
        ctx.run(["sensors-detect", "--auto"], sudo=True, check=False, quiet=True)
    else:
        ctx.logln("sensors-detect missing; skipping hardware sensor probing")
    ctx.enable("lm_sensors")


def p_final(ctx):
    if shutil.which("fc-cache"):
        ctx.run(["fc-cache", "-f"], check=False)
    else:
        ctx.logln("fc-cache missing; skipping font cache rebuild")
    if shutil.which("update-desktop-database"):
        ctx.run(["update-desktop-database", str(ctx.home / ".local/share/applications")], check=False)
    else:
        ctx.logln("update-desktop-database missing; skipping desktop DB refresh")
    if shutil.which("grub-mkconfig"):
        ctx.run(["sudo", "-n", "grub-mkconfig", "-o", "/boot/grub/grub.cfg"], check=False)
    else:
        ctx.logln("grub-mkconfig missing; skipping GRUB config rebuild")


STEPS: list[Step] = [
    # phase 1: priority files (sequential)
    Step("f-secrets",  "Restore secrets (ssh, keyrings, .env)",     1, "files", f_secrets),
    Step("f-config",   "Restore ~/.config & app settings",          1, "files", f_config),
    Step("f-browsers", "Restore browser profiles",                  1, "files", f_browsers),
    Step("f-t3",       "Restore T3 Code + agent chats",             1, "files", f_t3),
    Step("f-etc",      "Restore /etc (cloudflared token)",          1, "files", f_etc, True),
    Step("f-desktop",  "Restore SDDM/GRUB themes, X11 greeter 1.25", 1, "files", f_desktop_system, True),
    # phase 2, lane FILES
    Step("f-code",     "Restore code (yojanAni, dotfiles, tmp)",    2, "files", f_code),
    Step("f-personal", "Restore personal files",                    2, "files", f_personal),
    Step("f-stow",     "Link dotfiles (stow)",                      2, "files", f_stow),
    Step("f-fixups",   "Small fixups (worktrees, Zen pref)",        2, "files", f_fixups),
    # phase 2, lane SYSTEM  (mirrors APPS.md sections)
    Step("s-arch",     "arch_setup.py: base system, drivers, apps", 2, "system", s_arch_setup, True),
    Step("s-shell",    "zsh, nvm/node LTS, rustup, speedtest",      2, "system", s_user_shell, True),
    Step("s-desktop",  "Noctalia, portals, keyring, themes",        2, "system", s_desktop, True),
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


RESUME_SCRIPT = r"""#!/usr/bin/env bash
# One-shot: resume the pending restore once we are logged into Hyprland.
set -u
MARK="$HOME/.config/autostart/restore-resume.desktop"
[[ -f "$MARK" ]] || exit 0
rm -f "$MARK"

# Locate the Backup folder (exfat pen drive). It normally lives at /mnt/Backup.
backup=""
if [[ -f /mnt/Backup/restore.sh ]]; then
  backup=/mnt/Backup
else
  for m in $(findmnt -rn -o TARGET 2>/dev/null); do
    [[ -f "$m/Backup/restore.sh" ]] && { backup="$m/Backup"; break; }
  done
fi
if [[ -z "$backup" ]]; then
  echo "restore: couldn't find the Backup folder; mount the pen drive at /mnt/Backup" >&2
  exit 0
fi

# Run the rest of the restore inside an existing terminal so the sudo password prompt
# is visible and the user can type it once.
for t in konsole ghostty alacritty kitty xfce4-terminal gnome-terminal; do
  case "$t" in
    konsole)        cmd=("konsole" -e bash -c 'cd "$1" && exec bash restore.sh' _ "$backup");;
    ghostty)        cmd=("ghostty" -e bash -c 'cd "$1" && exec bash restore.sh' "$backup");;
    alacritty)      cmd=("alacritty" -e bash -c 'cd "$1" && exec bash restore.sh' "$backup");;
    kitty)          cmd=("kitty" --hold bash -c 'cd "$1" && exec bash restore.sh' "$backup");;
    xfce4-terminal) cmd=("xfce4-terminal" -e bash -c 'cd "$1" && exec bash restore.sh' "$backup");;
    gnome-terminal) cmd=("gnome-terminal" -e bash -c 'cd "$1" && exec bash restore.sh' "$backup");;
  esac
  if command -v "$t" >/dev/null 2>&1; then
    ( exec "${cmd[@]}" ) >/dev/null 2>&1 && exit 0
  fi
done
echo "restore: no terminal found to resume; run in one: bash $backup/restore.sh" >&2
"""

def write_handoff(console) -> None:
    """Install the one-shot autostart entry + resume script for a later Hyprland login."""
    bin_dir = Path.home() / ".local/bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    res = bin_dir / "restore-resume"
    res.write_text(RESUME_SCRIPT)
    res.chmod(0o755)
    ad = Path.home() / ".config/autostart"
    ad.mkdir(parents=True, exist_ok=True)
    (ad / "restore-resume.desktop").write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Resume restore\n"
        f"Exec={res}\n"
        "NoDisplay=true\n"
        "X-GNOME-Autostart-enabled=true\n")
    console.print("[green]Handoff set:[/] when you log into Hyprland, a terminal will open "
                  "running the remaining restore (type your sudo password once). "
                  "Follow its progress via the step logs in "
                  f"[dim]{Path.home() / '.local/state/home-restore'}[/].")


# ───────────────────────────── runner ─────────────────────────────
def run_step(ctx_base: Ctx, step: Step, state: dict, results: list, console):
    ctx = Ctx(**{**ctx_base.__dict__, "lane": step.lane, "step": step,
                 "lock": ctx_base.lock, "procs": ctx_base.procs, "stop": ctx_base.stop})
    logp = ctx.run_dir / f"{step.id}.log"
    t0 = time.time()
    status, msg = "ok", ""
    # reset() also restarts the lane's elapsed timer, so it shows how long THIS step has run
    ctx.progress.reset(ctx.task_ids[step.lane], total=None, completed=0,
                       description=f"{step.lane:>6} | {step.title}", status="starting …")
    console.print(f"[cyan][ >> ][/] {escape(step.title)}  [dim]({step.id}, log: {logp})[/]")
    Live.write(step.id, f"===== START {step.title}  (log: {logp})")
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
            import traceback
            status, msg = "failed", f"{type(e).__name__}: {e}"
            log.write(traceback.format_exc())
        log.write(f"### result: {status} {msg}\n")
    Live.write(step.id, f"===== END {status.upper()} {msg}")
    took = time.time() - t0
    rec = {"status": status, "msg": msg, "log": str(logp), "seconds": round(took),
           "at": dt.datetime.now().isoformat(timespec="seconds")}
    if not ctx.dry and ctx.home == Path.home():     # --home test runs don't touch the real state
        state[step.id] = rec
        save_state(state)
    results.append((step, rec))
    tag = {"ok": "[green][ OK ][/]", "partial": "[yellow][WARN][/]", "failed": "[red][FAIL][/]"}[status]
    console.print(f"{tag} {step.title}  [dim]({took/60:.1f} min)[/]" + (f"\n       [dim]{escape(msg)}[/]" if msg else ""))
    if status != "ok":
        tail = logp.read_text(errors="replace").splitlines()[-40:]
        # show the last few meaningful lines right away, so nobody has to open the log to see why
        shown = [l for l in tail if l.strip() and not l.startswith("### result")][-8:]
        for l in shown:
            console.print(Text(f"       | {l}"[:220], style="dim"))
        console.print(f"       [dim]full log: {logp}[/]")
        with open(ctx.run_dir / "errors.log", "a") as ef:
            ef.write(f"\n===== {step.id} [{status}] {step.title}\n{msg}\nlog: {logp}\n--- last lines ---\n")
            ef.write("\n".join(tail) + "\n")
    ctx.progress.advance(ctx.task_ids["overall"])
    return status


def main():
    ap = argparse.ArgumentParser(description="Autopilot restore of home + software on fresh EndeavourOS.")
    ap.add_argument("--dry-run", action="store_true", help="show what would run, change nothing")
    ap.add_argument("--list", action="store_true", help="list steps and saved status, then exit")
    ap.add_argument("--only", help="comma-separated step ids to run (ignores saved state)")
    ap.add_argument("--skip", help="comma-separated step ids to skip")
    ap.add_argument("--redo", action="store_true", help="ignore saved state, run everything again")
    ap.add_argument("--stop-after", help="stop after this step finishes; the rest resumes later")
    ap.add_argument("--home", help="restore into another directory (testing)")
    ap.add_argument("--no-sudo", action="store_true", help="testing: don't ask sudo; skip sudo steps")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="also print every output line of every step on screen (always in live.log)")
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
    globals()["Text"] = Text

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
    stop_after = args.stop_after
    if stop_after:
        all_ids = [s.id for s in STEPS]
        if stop_after not in all_ids:
            sys.exit(f"Unknown step id {stop_after!r}; run --list to see valid ids")
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
    if stop_after:
        lim = [s.id for s in STEPS].index(stop_after)
        todo = [s for s in todo if [x.id for x in STEPS].index(s.id) <= lim]

    home = Path(args.home).resolve() if args.home else Path.home()
    run_dir = STATE_DIR / dt.datetime.now().strftime("run-%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    latest = STATE_DIR / "latest"
    try:
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        latest.symlink_to(run_dir.name)
    except OSError:
        pass
    Live.f = open(run_dir / "live.log", "a", buffering=1)
    Live.console = console
    Live.verbose = args.verbose

    console.rule("[bold]EndeavourOS autopilot restore")
    console.print(f"backup: {BACKUP_DIR}\nhome:   {home}\nlogs:   {run_dir}\n"
                  f"steps:  {len(todo)} to run ({len(STEPS) - len(todo)} done/skipped)"
                  + ("   [yellow]DRY RUN[/]" if args.dry_run else ""))
    console.print(f"[bold]watch live[/] (another terminal):  [cyan]tail -f {latest}/live.log[/]\n"
                  f"[bold]step status[/]:                    [cyan]bash {BACKUP_DIR}/restore.sh --list[/]")
    for ph in (1, 2, 3):
        ids = [s.id for s in todo if s.phase == ph]
        if ids:
            console.print(f"[dim]  phase {ph}: {' '.join(ids)}[/]")
    Live.write("main", f"run started: {len(todo)} steps: {' '.join(s.id for s in todo)}")
    if not todo:
        if stop_after:
            write_handoff(console)
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
    # Restoring ~/.config, browser profiles and T3/Claude data while those apps run would
    # get overwritten again (or corrupt their databases) when they exit.
    if not args.dry_run and not args.home and {"f-config", "f-browsers", "f-t3"} & {s.id for s in todo}:
        apps_re = ("zen|zen-bin|firefox|brave|helium|chrome|google-chrome|msedge|chromium|"
                   "code|zed|zeditor|t3code|claude-desktop|vesktop")
        while True:
            r = subprocess.run(["pgrep", "-x", "-l", apps_re], capture_output=True, text=True)
            running = sorted({l.split()[1] for l in r.stdout.splitlines() if len(l.split()) > 1})
            if not running:
                break
            console.print(f"[yellow]These apps are running and their data is about to be restored:[/] "
                          f"{', '.join(running)}\nClose them (Claude desktop too), then press Enter. "
                          "Type [b]go[/] to continue anyway.")
            if input("> ").strip().lower() == "go":
                Live.write("main", f"continuing with apps still running: {running}")
                break
    if not args.dry_run:
        net = subprocess.run(["curl", "-sfI", "--max-time", "10", "https://archlinux.org"],
                             stdout=subprocess.DEVNULL).returncode == 0
        if not net and any(s.lane != "files" for s in todo):
            sys.exit("No internet. Connect first (e.g. `nmtui`), then re-run.")
    stop = threading.Event()
    if sudo_pw:
        threading.Thread(target=sudo_keepalive, args=(sudo_pw, stop), daemon=True).start()
        console.print(f"[bold]bootstrap:[/] pacman DB sync, system upgrade, base tools, paru  "
                      f"[dim](log: {run_dir / '00-bootstrap.log'})[/]")
        t_b = time.time()
        with open(run_dir / "00-bootstrap.log", "w") as blog:
            paru_ok = bootstrap_pacman(
                blog, say=lambda m: (console.print(f"[dim]{escape(m)}[/]"), Live.write("bootstrap", m)))
        console.print(f"[dim]  · bootstrap done in {(time.time() - t_b) / 60:.1f} min[/]")
        missing_bin = [b for b in ("zstd", "git", "stow", "curl") if not shutil.which(b)]
        if missing_bin:
            console.print(f"[yellow]bootstrap: still missing {', '.join(missing_bin)} "
                          f"(see 00-bootstrap.log)[/]")
        if not paru_ok:
            console.print("[yellow]bootstrap: paru unavailable — AUR steps will report failures "
                          "(see 00-bootstrap.log)[/]")

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
    if stop_after:
        write_handoff(console)
        console.print(f"\n[b]Stopped after {stop_after}.[/] Remaining steps stay pending "
                      "(phase-3 steps + apps). After logging into Hyprland the resume "
                      "terminal picks them up automatically.")
        return
    console.print("\n[b]Next (manual):[/] reboot → log in at the SDDM greeter (X11, 1.25 scale). "
                  "See README.md 'After the script' for the logins/checks list.")


if __name__ == "__main__":
    main()
