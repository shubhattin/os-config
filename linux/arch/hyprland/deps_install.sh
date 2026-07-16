#!/usr/bin/env bash
set -euo pipefail

# Packages for the Hyprland + Noctalia desktop.
# Run as a normal user with sudo access: paru must not be run as root.

# Basic tools
sudo pacman -S --needed --noconfirm vi vim bat git ddcutil

# paru is available from the EndeavourOS repository on this system.
if ! command -v paru >/dev/null 2>&1; then
  sudo pacman -S --needed --noconfirm paru
fi

# Shell, notifications, wallpaper, idle/lock screen, launcher, clipboard, OSD,
# network and Bluetooth UI are all provided by Noctalia.
paru -S --needed --noconfirm noctalia-git

# Hyprland utilities that remain in use.
sudo pacman -S --needed --noconfirm hyprshot dolphin archlinux-xdg-menu

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

# Keep GNOME Keyring for secrets. Do not remove KWallet: current KDE apps
# (including KIO and Okular) depend on it.
sudo pacman -S --needed --noconfirm gnome-keyring libsecret

# Breeze and GTk Themes
sudo pacman -S --needed --noconfirm breeze breeze-gtk kde-cli-tools chaotic-aur/qt6ct-kde breeze-icons
sudo pacman -S --needed --noconfirm kvantum ttf-hack
sudo pacman -S --needed --noconfirm qt6ct qt5ct adwaita-icon-theme gnome-themes-extra gtk3 gtk4
# Keep the KDE portal for KDE apps' file dialogs and integration.
sudo pacman -S --needed --noconfirm xdg-desktop-portal-gtk xdg-desktop-portal-hyprland xdg-desktop-portal-kde

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
# Use
# sh -c "$(curl -fsSL https://raw.githubusercontent.com/keyitdev/sddm-astronaut-theme/master/setup.sh)"`

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
