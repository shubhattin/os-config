#!/bin/bash

# Includes Important Packages to be installed for current hyprland setup

# Basic Apps
pacman -S vi vim bat git cat paru --noconfirm
# ^ paru is there in eos packages

## Hyprland tools
pacman -S hyprshot hypridle hyprlock hyprpaper --noconfirm
pacman -S swaync waybar dolphin swayosd --noconfirm
# Fonts
pacman -S ttf-font-awesome ttf-meslo-nerd --noconfirm
# Bluetooth and Wifi
pacman -S bluez bluez-utils blueman --noconfirm
pacman -S network-manager-applet --noconfirm

# Breeze and GTk Themes
pacman -S qt6ct breeze breeze-gtk kde-cli-tools qt5ct breeze-icons --noconfirm
pacman -S qt6ct breeze breeze-gtk kde-cli-tools qt5ct breeze-icons --noconfirm
pacman -S adwaita-icon-theme gnome-themes-extra gtk3 gtk4 --noconfirm
pacman -S xdg-desktop-portal-gtk xdg-desktop-portal-hyprland --noconfirm

# Fonts
pacman -S \
  ttf-cascadia-code-nerd \
  ttf-fira-code \
  ttf-firacode-nerd \
  ttf-hack-nerd \
  ttf-inconsolata-nerd \
  ttf-inconsolata-lgc-nerd --noconfirm
pacman -S noto-fonts noto-fonts-extra --noconfirm

# Other KDE Apps
pacman -S partitionmanager okular haruna ark gwenview --noconfirm

# Gnome/Gtk App
pacman -S gnome-calendar font-manager --noconfirm

# Clipboard
pacman -S copyq wl-clipboard --noconfirm

## SDDM Theme and Background
# Use
# sh -c "$(curl -fsSL https://raw.githubusercontent.com/keyitdev/sddm-astronaut-theme/master/setup.sh)"`
