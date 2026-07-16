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
- `xdg-desktop-portal-kde` remains installed for KDE file-dialog and desktop
  integration.
- `kwallet` remains installed because KIO, Okular, and other installed KDE
  components require it. GNOME Keyring remains the general secret service.

## Remove the retired desktop components

After confirming Noctalia is working, remove only the superseded packages:

```bash
sudo pacman -Rns waybar wofi swaync swayosd hyprpaper hypridle hyprlock \
  plasma-nm plasma-pa network-manager-applet bluedevil bluez-obex \
  networkmanager-qt cliphist
```

Do **not** add `kwallet`, `polkit-kde-agent`, `xdg-desktop-portal-kde`,
`networkmanager`, `bluez`, `bluez-utils`, or `wl-clipboard` to that command.
`networkmanager-qt` may already disappear as an unused dependency when
`plasma-nm` is removed; naming it explicitly is safe as long as pacman accepts
the transaction.

