# Hyprland Setup

**[Config Files](https://github.com/shubhattin/dotfiles/tree/main/.config)**

## Shell stack

Hyprland is the compositor and Noctalia is the desktop shell. Noctalia replaces
Waybar, Wofi, SwayNC, SwayOSD, Hyprpaper, Hypridle, Hyprlock, cliphist, the
NetworkManager tray applet, Plasma-NM, Plasma Audio, and Bluedevil.

Run the installer as a regular user:

```bash
./deps_install.sh
```

It installs `noctalia-git` through `paru`, retains NetworkManager and BlueZ as
the underlying services, and lets Noctalia manage their UI.

## KDE integration retained intentionally

- `polkit-kde-agent` remains installed and started by Hyprland. It provides the
  password prompts used by Dolphin, KDE Partition Manager, and other privileged
  KDE operations.
- `xdg-desktop-portal-kde` provides the **system file picker** (Dolphin-style
  dialog) for every portal-using app (Electron apps like T3 Code/VS Code,
  Chromium browsers, Zen/Firefox). See [File picker](#file-picker--portals).
- `kwallet` remains installed because KIO, Okular, and other installed KDE
  components require it, but it is **disabled**. GNOME Keyring is the only
  secret store. See [Secrets](#secrets--keyring).

## File picker / portals

Config: `~/.dotfiles/.config/xdg-desktop-portal/hyprland-portals.conf`

| Interface | Backend |
|---|---|
| default | `hyprland;gtk` |
| ScreenCast, RemoteDesktop | hyprland |
| Settings | gtk |
| **FileChooser** | **kde** (the GTK picker overflowed the screen and was unusable) |
| Secret | gnome-keyring |

- `~/.config/hypr/start-portals.sh` (exec at startup) starts hyprland, gtk and
  **kde** backends, then the `xdg-desktop-portal` frontend. Hyprland doesn't
  activate `graphical-session.target`, so they are not auto-started.
- `hyprland.lua` rule `portal-file-picker` floats + centers the dialog (1100×720).
- Zen/Firefox only use the portal picker when
  `widget.use-xdg-desktop-portal.file-picker = 1` (set in the profile's `user.js`).
- Noctalia has no file-picker portal.
- Test: `gdbus call --session --dest org.freedesktop.portal.Desktop --object-path /org/freedesktop/portal/desktop --method org.freedesktop.portal.FileChooser.OpenFile "" "test" "{}"`

## Secrets / keyring

- **GNOME Keyring only.** It owns `org.freedesktop.secrets` and serves the portal
  Secret backend. Its Login collection holds browser/Electron "Safe Storage" keys
  (Brave, Chrome, Chromium, Helium, Claude, T3 Code, VS Code), `gh` tokens,
  Wi-Fi PSKs, Noctalia and Zen keys.
- Unlocked at login by `pam_gnome_keyring` in `/etc/pam.d/sddm` (shipped by
  sddm). **The login password must equal the keyring password**; change both
  together (or use `seahorse` → Login → Change password).
- KWallet: `kwalletrc` → `[Wallet] Enabled=false` (set by `deps_install.sh`);
  `kwallet-pam` is not installed.
- Don't launch Chromium browsers with `--password-store=basic`; that bypasses
  the keyring (passwords only protected by a hard-coded key).
- Reinstall: restore `~/.local/share/keyrings/` from backup **before** first login
  to the desktop, with the same user password.
- `breeze`, `breeze-gtk`, and `breeze-icons` remain installed for Qt/GTK theming
  via qt6ct / Kvantum. They are independent of Plasma-NM and Bluedevil.

## Remove the retired desktop components

After confirming Noctalia is working, remove only the superseded packages:

```bash
sudo pacman -Rns waybar wofi swaync swayosd hyprpaper hypridle hyprlock \
  plasma-nm plasma-pa network-manager-applet bluedevil bluez-obex \
  networkmanager-qt cliphist
```

Do **not** add `kwallet`, `polkit-kde-agent`, `xdg-desktop-portal-kde`,
`breeze`, `breeze-gtk`, `breeze-icons`, `networkmanager`, `bluez`,
`bluez-utils`, or `wl-clipboard` to that command.
`networkmanager-qt` may already disappear as an unused dependency when
`plasma-nm` is removed; naming it explicitly is safe as long as pacman accepts
the transaction.

