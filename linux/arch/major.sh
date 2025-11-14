# Includes Important Packages to be installed for current hyprland setup

# Basic Apps
sudo pacman -S vi vim bat --noconfirm

## Hyprland tools
sudo pacman -S hyprshot hypridle hyprlock hyprpaper --noconfirm
sudo pacman -S swaync waybar dolphin --noconfirm
# Fonts
sudo pacman -S ttf-font-awesome ttf-meslo-nerd --noconfirm
# Bluetooth and Wifi
sudo pacman -S bluez bluez-utils blueman --noconfirm
sudo pacman -S network-manager-applet --noconfirm

# Breeze and GTk Themes
sudo pacman -S qt6ct breeze breeze-gtk kde-cli-tools qt5ct breeze-icons --noconfirm
sudo pacman -S adwaita-icon-theme gnome-themes-extra gtk3 gtk4 --noconfirm
sudo pacman -S xdg-desktop-portal-gtk xdg-desktop-portal-hyprland --noconfirm

# Fonts
sudo pacman -S \
  ttf-cascadia-code-nerd \
  ttf-fira-code \
  ttf-firacode-nerd \
  ttf-hack-nerd \
  ttf-inconsolata-nerd \
  ttf-inconsolata-lgc-nerd --noconfirm
sudo pacman -S noto-fonts noto-fonts-extra --noconfirm

# Other KDE Apps
sudo pacman -S partitionmanager okular haruna ark --noconfirm

# Gnome/Gtk App
sudo pacman -S gnome-calendar --noconfirm

# Clipboard
sudo pacman -S copyq wl-clipboard --noconfirm
