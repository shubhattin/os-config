#!/bin/bash

# Includes Important Packages to be installed for current hyprland setup

# Basic Apps
pacman -S vi vim bat git paru ddcutil --noconfirm --needed
# ^ paru is there in eos packages

## Hyprland tools
pacman -S hyprshot hypridle hyprlock hyprpaper --noconfirm --needed
pacman -S swaync waybar wofi dolphin archlinux-xdg-menu swayosd --noconfirm --needed
pacman -S polkit-kde-agent polkit --needed --noconfirm
systemctl enable --now polkit
# Fonts
pacman -S ttf-font-awesome ttf-meslo-nerd --noconfirm --needed
# Bluetooth and Wifi
pacman -S bluez bluez-utils --noconfirm --needed
pacman -S plasma-nm plasma-pa networkmanager --noconfirm --needed
systemctl enable --now NetworkManager
pacman -S --needed bluedevil bluez-obex
systemctl enable --now bluetooth.service
# to run use kcmshell6 kcm_networkmanagement

# Breeze and GTk Themes
pacman -S breeze breeze-gtk kde-cli-tools chaotic-aur/qt6ct-kde breeze-icons --noconfirm --needed
pacman -S kvantum ttf-hack --noconfirm --needed
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
pacman -S kate --noconfirm --needed

# Gnome/Gtk App
pacman -S gnome-calendar font-manager --noconfirm --needed

# Clipboard
pacman -S cliphist wl-clipboard --noconfirm --needed

## SDDM Theme and Background
# Use
# sh -c "$(curl -fsSL https://raw.githubusercontent.com/keyitdev/sddm-astronaut-theme/master/setup.sh)"`

# Load the module needed for ddcutil
modprobe i2c-dev

# Make it load automatically on boot
echo "i2c-dev" | tee /etc/modules-load.d/i2c-dev.conf

# You may also need i2c drivers for your GPU
# modprobe i2c-nvidia-gpu  # For NVIDIA
# OR
# sudo modprobe i2c-amdgpu      # For AMD
#

## FCITX Typing
pacman -S fcitx5 fcitx5-configtool fcitx5-gtk fcitx5-qt fcitx5-m17n --needed --noconfirm

## Screen Recorder
sudo pacman -S wf-recorder --needed --noconfirm
# Use `wf-recorder -f recording.mp4` to record full screen and press ctrl+c to save
