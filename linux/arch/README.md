## Config/Setup Guide for Arch / EndeavourOS

- **[Command Line Tools](./CLI.md)**
- **[Desktop Environment](./DE.md)**
- **[NVIDIA / Hybrid GPU](./nvidia.md)**
- **[Hyprland + Noctalia desktop](./hyprland/README.md)** (current desktop; installer: `hyprland/deps_install.sh`)
- **[Extra Apps & Tools](./APPS.md)**: everything else installed on the machine, with install commands and order

Fresh install order: EndeavourOS installer (Hyprland) → `scripts/arch_setup.py` → `hyprland/deps_install.sh` → [APPS.md](./APPS.md) → `stow .` in `~/.dotfiles`.

**Autopilot:** [`restore/restore.py`](./restore/) runs all of the above *and* restores the home backup, with progress, logs and resume. See [restore/README.md](./restore/README.md). A copy ships on the backup pen drive.

### _[Custom Arch Setup Script](./scripts/arch_setup.py)_

```bash
curl -H "Cache-Control: no-cache" -H "Pragma: no-cache" https://raw.githubusercontent.com/shubhattin/os-config/refs/heads/main/linux/arch/scripts/arch_setup.py -o /tmp/arch_setup.py && python3 /tmp/arch_setup.py
```
