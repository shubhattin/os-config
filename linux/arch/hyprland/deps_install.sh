#!/usr/bin/env bash
set -euo pipefail

# Packages for the Hyprland + Noctalia desktop.
# Run as a normal user with sudo access: paru must not be run as root.

# Basic tools
sudo pacman -S --needed --noconfirm vi vim bat git ddcutil

# paru comes from chaotic-aur on plain Arch (arch_setup.py enables chaotic-aur first).
if ! command -v paru >/dev/null 2>&1; then
  sudo pacman -S --needed --noconfirm chaotic-aur/paru
fi

# Compositor + login manager. archinstall "Minimal" profile installs neither.
# The SDDM greeter runs on X11 (see ../DE.md "SDDM greeter"), so it needs xorg-server.
sudo pacman -S --needed --noconfirm hyprland sddm xorg-server qt6-wayland layer-shell-qt
sudo systemctl enable sddm

# Shell, notifications, wallpaper, idle/lock screen, launcher, clipboard, OSD,
# network and Bluetooth UI are all provided by Noctalia.
paru -S --needed --noconfirm noctalia-git

# Hyprland utilities that remain in use.
sudo pacman -S --needed --noconfirm hyprshot dolphin archlinux-xdg-menu playerctl ghostty alacritty  # used by hyprland.lua binds

# Keep this KDE polkit agent: it supplies authentication dialogs for Dolphin,
# KDE Partition Manager, and other privileged KDE application actions.
sudo pacman -S --needed --noconfirm polkit polkit-kde-agent
sudo systemctl enable --now polkit
update-desktop-database

# Fonts
sudo pacman -S --needed --noconfirm ttf-font-awesome ttf-meslo-nerd

# Noctalia manages NetworkManager and BlueZ directly; do not install Plasma-NM,
# Bluedevil, the NetworkManager tray applet, or Plasma's audio applet.
sudo pacman -S --needed --noconfirm networkmanager bluez bluez-utils
sudo systemctl enable --now NetworkManager bluetooth.service

# GNOME Keyring is the ONLY secret store (org.freedesktop.secrets + the portal
# Secret backend). It holds browser/Electron "Safe Storage" keys, gh tokens,
# Wi-Fi PSKs, Noctalia, etc. SDDM's PAM (pam_gnome_keyring) unlocks it at login,
# so keep the login password identical to the keyring password.
# KWallet stays installed (kio, okular, kaccounts depend on it) but is DISABLED so
# KDE apps never create/prompt for a second wallet. Do not install kwallet-pam.
sudo pacman -S --needed --noconfirm gnome-keyring libsecret seahorse
kwriteconfig6 --file kwalletrc --group Wallet --key Enabled false

# Breeze and GTk Themes
sudo pacman -S --needed --noconfirm breeze breeze-gtk kde-cli-tools chaotic-aur/qt6ct-kde breeze-icons
sudo pacman -S --needed --noconfirm kvantum ttf-hack
# NOTE: plain `qt6ct` conflicts with `qt6ct-kde` (installed above) — don't add it here.
sudo pacman -S --needed --noconfirm qt5ct adwaita-icon-theme gnome-themes-extra gtk3 gtk4
# Portals: hyprland (screencast), gtk (settings/fallback), kde (FILE PICKER).
# Routing lives in ~/.dotfiles/.config/xdg-desktop-portal/hyprland-portals.conf
# (FileChooser=kde, Secret=gnome-keyring); ~/.config/hypr/start-portals.sh starts
# all backends; hyprland.lua floats the picker (rule "portal-file-picker").
# Noctalia has no file-picker portal of its own.
sudo pacman -S --needed --noconfirm xdg-desktop-portal xdg-desktop-portal-gtk xdg-desktop-portal-hyprland xdg-desktop-portal-kde

# Fonts
sudo pacman -S --needed --noconfirm \
  ttf-cascadia-code-nerd \
  ttf-fira-code \
  ttf-firacode-nerd \
  ttf-hack-nerd \
  ttf-inconsolata-nerd \
  ttf-inconsolata-lgc-nerd
sudo pacman -S --needed --noconfirm noto-fonts noto-fonts-extra

# Other KDE Apps
sudo pacman -S --needed --noconfirm partitionmanager okular haruna ark gwenview konsole kwrite kate

# Gnome/Gtk App
sudo pacman -S --needed --noconfirm gnome-calendar font-manager nautilus

# wl-clipboard remains necessary for hyprshot and general Wayland clipboard
# interoperability. Noctalia replaces cliphist as the clipboard history UI.
sudo pacman -S --needed --noconfirm wl-clipboard

## SDDM Theme and Background
# After astronaut theme setup, ALWAYS install the virtual keyboard dep:
sudo pacman -S --needed --noconfirm qt6-virtualkeyboard
# Hybrid NVIDIA machines: also keep /etc/X11/xorg.conf.d/20-intel-only.conf
# and run: ../scripts/nvidia_hybrid_check.sh
# Theme installer (optional):
# sh -c "$(curl -fsSL https://raw.githubusercontent.com/keyitdev/sddm-astronaut-theme/master/setup.sh)"

# Load the module needed for ddcutil
sudo modprobe i2c-dev

# Make it load automatically on boot
echo "i2c-dev" | sudo tee /etc/modules-load.d/i2c-dev.conf >/dev/null

# You may also need i2c drivers for your GPU
# modprobe i2c-nvidia-gpu  # For NVIDIA
# OR
# sudo modprobe i2c-amdgpu      # For AMD
#

## FCITX Typing
sudo pacman -S --needed --noconfirm fcitx5 fcitx5-configtool fcitx5-gtk fcitx5-qt fcitx5-m17n

## Screen Recorder
sudo pacman -S --needed --noconfirm wf-recorder
# Use `wf-recorder -f recording.mp4` to record full screen and press ctrl+c to save
