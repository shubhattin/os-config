#!/bin/bash

# Includes Important Packages to be installed for current hyprland setup

# Basic Apps
pacman -S vi vim bat git paru --noconfirm --needed
# ^ paru is there in eos packages

## Hyprland tools
pacman -S hyprshot hypridle hyprlock hyprpaper --noconfirm --needed
pacman -S swaync waybar wofi dolphin swayosd --noconfirm --needed
# Fonts
pacman -S ttf-font-awesome ttf-meslo-nerd --noconfirm --needed
# Bluetooth and Wifi
pacman -S bluez bluez-utils blueman --noconfirm --needed
pacman -S network-manager-applet --noconfirm --needed

# Breeze and GTk Themes
pacman -S qt6ct breeze breeze-gtk kde-cli-tools chaotic-aur/qt6ct-kde breeze-icons --noconfirm --needed
pacman -S qt6ct breeze breeze-gtk kde-cli-tools qt5ct breeze-icons --noconfirm --needed
pacman -S adwaita-icon-theme gnome-themes-extra gtk3 gtk4 --noconfirm --needed
pacman -S xdg-desktop-portal-gtk xdg-desktop-portal-hyprland xdg-desktop-portal-kde --noconfirm --needed

# Fonts
pacman -S \
  ttf-cascadia-code-nerd \
  ttf-fira-code \
  ttf-firacode-nerd \
  ttf-hack-nerd \
  ttf-inconsolata-nerd \
  ttf-inconsolata-lgc-nerd --noconfirm --needed
pacman -S noto-fonts noto-fonts-extra --noconfirm --needed

# Other KDE Apps
pacman -S partitionmanager okular haruna ark gwenview konsole kwrite --noconfirm --needed

# Gnome/Gtk App
pacman -S gnome-calendar font-manager --noconfirm --needed

# Clipboard
pacman -S copyq wl-clipboard --noconfirm --needed

## SDDM Theme and Background
# Use
# sh -c "$(curl -fsSL https://raw.githubusercontent.com/keyitdev/sddm-astronaut-theme/master/setup.sh)"`
