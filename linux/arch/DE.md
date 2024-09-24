**_This file is written with respect to Endeavour OS(Arch) in KDE Plasma Desktop_**

## OS Installation and Boot

- EOS Installtion Guide
  - For Vanilla KDE Installation uncheck EndeavourOS Settings under KDE Desktop
  - Would recommend to setup the linux-lts kernel later on after installation.
  - You would need to setup the breeze theme for sddm and custom background for sddm.
  - Background for Lock Screen is also configured seperately in _Screen Locking_ in Settings.
  - install `yad` if `eos-welcome` does not works
- To install with windows as dual boot ensure these things
  - Choose Manual Partitioning
  - `/boot/efi` -> type `fat32`, `reformated`
  - `/` -> `Reformat` and `ext4`. Do not install as LVM as it would interfere with dual boot. Also if you `btrfs` you would be limited to only `read`. `btrfs` can also be used as it has some good features to consider for root partition.
  - `/home` -> `No Reformat` and `ext4`
  - _zram & swap_
    - `cat /proc/swaps` to view current used swap devices including zram
    - `zramctl` to view zram info
  - My current layout
    - `/boot` as `ext4` 0.7Gib
    - `/boot/efi` as `EFI/fat32` 0.7Gib
    - `/` as `btrfs` 70Gib (more space to accomodate timeshift backup as well)
    - `/home` remaining space for this Home Directory
    - `swap` 6Gib
- It would be recommended to free space prior to opening the setup and defrag disk if needed OR in live setup using something like KDE Partition Manager.
- Use this [Linux FileSystem for Windows by Paragon](https://www.paragon-software.com/home/linuxfs-windows/) to access linux filesystem on windows.
  - [ ] find if we can use this even when our `/home` or `/` are encrypted.

## Basic Setup
- Connectivity
  - [x] Bluetooth : In [EOS](https://endeavouros.com/) you would need to `sudo systemctl enable bluetooth`
  - [x] WiFi
  - [x] USB Devices
  - [x] USB tethering
  - [x] Mobile Devices
  - [x] Bluetooth Tethering
- [x] Time and Date
- [TouchPad Zoom In/Out Gestures](./touchpad/touchpad.md)
- If touchpad settings dont show up in KDE settingss use `kcmshell6 kcm_touchpad`
-  **Dual Monitor Support**
  - [x] Fractional Scaling works both in x11 as well as wayland sessions
  - [ ] Not able to set fractional scaling to 100% while external monitor is connected and restore it to 125%. It works but not with proper scaling support as expected.
- **GPU Setup**
  - list GPUs `lspci -vnn | grep VGA`
  - **Intel GPU**
    - `sudo pacman -S intel-ucode mesa intel-media-driver libva-mesa-driver`
  - Follow Instruction [here](https://dev.to/vitorvargas/how-to-install-the-nvidia-driver-on-archlinux-5bgc)
    - `sudo pacman -S --noconfirm nvidia nvidia-utils nvidia-settings opencl-nvidia xorg-server-devel nvidia-prime`
    - also if using `linux-lts` then `sudo pacman -S nvidia-lts`
    - Check if `nouveau` or the proprietary nvidia drivers are running
      - `lsmod | grep nouveau`
      - `lsmod | grep nvidia`
      - `lspci -k | grep -A 3 -i "VGA"` to view installed drivers in use
      - `prime-run glxinfo | grep 'OpenGL renderer'` checking opengl renderer
  - Check nvidia kernel module version `modinfo -F version nvidia`
  - [ ] Try to run tensorflow with nvidia gpu in both dual gpu and single gpu devices
  - **Optimus Manager for X11**
    - `paru -S optimus-manager-git optimus-manager-qt`
    - `sudo systemctl enable optimus-manager` after restart
    - Set AutoStart by launching Optimus manager qt and settings autostart.
    - You should use `Hybrid Mode` by default. And untill not required do not switch to Nvidia and prefer using `prime-run` as it saves power.
    - You could also try [envycontrol](https://github.com/bayasdev/envycontrol) if this does not seem to work fine. It supports other distros and possibly wayland. _Although in my case the Display Manager did'nt open after switching modes, So stick with optimus manager untill required_
  - [x] Use **[Mission Center](https://aur.archlinux.org/packages/mission-center)** or **[Resources](https://aur.archlinux.org/packages/resources)** to verify and see GPU Usage as it lists all major hardware resources. `paru -S mission-center resources`
  - For CUDA and cuDNN `sudo pacman -S cuda cudnn`
  - **Testing GPU** : Install glmark2 `sudo pacman -S glmark2`
    - Testing default/primary gpu : `glmark2`, `glmark2-wayland`
    - Testing Nvidia GPU specifically : `prime-run glmark2` OR `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glmark2`
    - While test is in progress watch the gpu usage in Mission Center. At the end it should give you a score for the benchmark.
- **X11**
  - You might need to configure your mouse/touchpad on your initial login
- _Power Management_ : If you feel that your system is not utilizing space in optimal way you could use [tlp](https://askubuntu.com/questions/1309396/how-to-increase-battery-life-on-ubuntu-20-04-and-what-power-saving-software-shou) and remove it see [here](https://www.baeldung.com/linux/tlp-disable)
  - Setup Lid Close and other such options in `Power Management`
  - _Sleep function might malfunctioning, insttalling gpu drivers and latest linux kernel fixed laptop overheating in my case_,
- Currently using the [Dark Matter](https://github.com/VandalByte/darkmatter-grub2-theme/tree/main) theme for grub, also tried [grub2-themes](https://github.com/vinceliuice/grub2-themes)
- **Fixing Issues mounting NTFS and other disks**
  - `lsblk` to get identifier for your disk
  - `sudo pacman -S exfat-utils exfatprogs ntfs-3g`
  - `sudo fsck /dev/<path>` to check for errors
  - `sudo mount -t ntfs-3g /dev/<path> /mnt` to mount forcefully as ntfs
  - `sudo ntfsfix /dev/<path>` to fix common ntfs problems
- > :information_source: While using a usb drive or any any external storage device wait for the usb to eject and disappear from file explorer. Its because if something shows to be copied, deleted, moved etc, it still might be processing things in background. This also the reason why commands like `rm -rf and cp` feel faster than windows copy and delete.

#### Installing linux-lts kernel

- In EOS installtion if you did'nt chose linux-lts lts kernel you should get the latest kernels by default
- `sudo pacman -S linux-firmware linux-lts linux-lts-headers`, you should keep linux-lts as a backup in case main kernel fails.
- we dont need to do `sudo mkinitcpio -p linux-lts` as this auto handled by pacman. But you still need to reconfig grub with `sudo grub-mkconfig -o /boot/grub/grub.cfg`
- `uname -r` to get current linux kernel version being used
- to install and setup linux-lts kernel follow [this](https://itsfoss.com/switch-kernels-arch-linux/) guide.
- Any custom changes made to `/etc/default/grub` should be in end after `# Custom` line.
- You should prefer linux latest kernel for improved hardware support for you laptop or same latest hardware. (in my case i faced problem with linux-lts in laptop)
- If you are on a current linux kernel version which you want to _lock_, then goto `/etc/pacman.conf` and uncomment the line `#IgnorePkg  = ` and add `linux linux-headers` to end of it. this should prevent linux kernel updates.
- Then to manually update the packages after ignoring `sudo pacman -Syu --needed linux linux-headers`

Add this to end of `/etc/default/grub`

```grub
# Custom
GRUB_DISABLE_SUBMENU=y
GRUB_DEFAULT=saved
GRUB_SAVEDEFAULT=true
```

#### Fixing SDDM scaling

Currently X11 is used for display, so it does not handles scaaling correcly we could set it [wayland](https://wiki.archlinux.org/title/SDDM#Wayland) by changinf `/etc/sddm.conf.d/10-wayland.conf`

```config
[General]
DisplayServer=wayland
GreeterEnvironment=QT_WAYLAND_SHELL_INTEGRATION=layer-shell

[Wayland]
CompositorCommand=kwin_wayland --drm --no-lockscreen --no-global-shortcuts --locale1
```

This shall fix the scaling issue as wayland is better at detecting scaling factor automatically. And also it displays a black screen after login. You could also use X11 for scaling purpose by editing `/etc/sddm.conf.d/hidpi.conf`. In my case scaling factor is 1.25

```config
[General]
GreeterEnvironment=QT_SCREEN_SCALE_FACTORS=1.25
```

### Some Basic Usefull Info
- **tty** : Stands for teletypewriter. Can be used to do execute commands which could cause problem on a live DE. It can also be used if things crash in a DE.
  - In KDE Plasma the tty setup looks like this
  - `tty1` reserved for arch startup and message it shows
  - `tty2` hosts the DE
  - `tty3-6` can be accessed using `ctrl+alt+3-6` (there are 1-7 there typically)
  - use `chvt <num>` to change to a particular tty session

## Software

- [x] **_CLI Based Application_** : These apps usually work all fine without ever having any major issues.
  - [x] Terminal Emulator
    - `Konsole` : Built in KDE terminal. Also enable proper `brahmic` script rendering in `Appearence > Complex Text Layout`
      - Download Nerd fonts from here [here](https://github.com/shubhattin/neovim-config/releases/tag/nerd-fonts), currently using `Caskaydia Cove NF, 10.50`
    - Or you could use Tilix
  - Visual Studio Code `paru -S visual-studio-code-bin`
- > _Not using flatpaks or snaps for some cases might be a better option if a good up to date version is avilable in system repository. It is suitable for browesers, electron apps, video players, system monitor tools. And may be avoided for some utitlities, creative software for multimedia_
- Flatpak Setup
  - `sudo pacman -S flatpak discover`
  - Then open the discover app and in settings enable flathub. now you have a gui for flathub package management.
  - > **_In general you should prefer [AUR](https://aur.archlinux.org/) over flatpaks_**
- Browsers
  - [x] Brave `paru -S brave-bin`
  - [x] Edge `flatpak install flathub com.microsoft.Edge` or `paru -S microsoft-edge-stable-bin`
  - [x] Chrome
- Video Player
  - [x] VLC Media Player `sudo pacman -S vlc`
- Partition Manager : Built in KDE Partition Manager `sudo pacman -S partitionmanager gparted`
  - Filelight for disk usage analysis `sudo pacman -S filelight`
- Video Converter
  - [x] Alternative(s) to Wondershare i converter
    - [HandBrake](https://handbrake.fr/) `sudo pacman -S handbrake`
    - [Shutter Encoder](https://www.shutterencoder.com/) `paru -S shutter-encoder-bin`
- Download Manager
  - Xtreme Download Manager currently using [`v8.0.29bete`](https://github.com/subhra74/xdm/releases/tag/8.0.29) `paru -S xdman-beta-bin`
    - To enable other file extensions like mp4 and mkv which are not marked for download by default can be enabled by going into `Settings > Browser Monitoring`, then find the list where it lists the extensions which will be automatically be taken over by xdm for download and add your desired extension if it already does not exists.
    - you might not be able to disable it from startup options in settings, you will need to use KDE's Autostart to disable it.
    - _:information_source: you would need to create folders for download catergories like Videos, Programs, Documents, etc if in case it is not able to assemble after downnloading._
    - :warning: There seems to problem on using it in a wayland session
  - qBittorrent `sudo pacman -S qbittorrent`
  - [Percepolis Download Manager](https://persepolisdm.github.io/)
  - Kget
  - Ktorrent
- YouTube Video Downloader
  - [Parabolic](https://github.com/NickvisionApps/Parabolic) `paru -S parabolic`
  - Video Downloader via `flatpak install flathub com.github.unrud.VideoDownloader` or `paru -S video-downloader`
  - Tube2go via `flatpak install flathub com.warlordsoftwares.tube2go`
- [x] A Speed Monitor tool like DU Meter
  - You can use the built in system monitor or Mission center app.
- [x] Clipboard Manager :
  - Use the existing KDE Clipboard maanger as it just serves the purpose
  - The Shortcut `Win+V` already seems to be there for this
  - Use [Diodon](https://github.com/diodon-dev/diodon). Go to Preferernces and enable
    - Use Clipboard
    - Add Images to Clipbaord
    - Keep Clipbaord Content
    - Synchronize clipboard
    - Automatically paste selected items
    - Register a Shortcut with `Win+V` (like windows) with `/usr/bin/diodon`
- [x] Screenshot : Use `Spectacle`
  - Shortcut `Win+PtrSsc` is already configured for screenshot. You could also disable `Print` Button Action
- Eye Protector Apps
  - [Safeeyes](https://github.com/slgobinath/SafeEyes?tab=readme-ov-file) for 20-20 rule from flathub
    - `paru -S safeeyes`
  - [Iris micro gui](https://github.com/shubhattin/iris_micro_gui) for a app like careueyes
    - > :warning: does not work in a wayland session as of now
- [x] File Recovery App
  - [free Linux recovery](https://www.r-studio.com/free-linux-recovery/)
  - Bootable [Redo](http://redorescue.com/)
- [x] Rufus Alternatives
  - Use **[Ventoy](https://ventoy.net/en/download.html) for windows and linux as well. [Windows Guide](https://www.reddit.com/r/linux4noobs/comments/z5dk4o/how_can_i_burn_a_bootable_win10_usb_in_linux/)**
  - [Posicle](https://flathub.org/apps/com.system76.Popsicle)
  - > :information_source: If the default file explorer formatter gives problems goto `Disks`
- [x] Pdf Editor
  - Libre Office install using [this](https://www.linuxfordevices.com/tutorials/linux/install-libreoffice-on-arch)
  - [Pdf Arranger](https://flathub.org/apps/com.github.jeromerobert.pdfarranger) for arranging spplitting and mergeing pdf. `paru -S pdfarranger`
- [x] Compression tools
  - [Peazip](https://peazip.github.io/peazip-linux.html) `paru -S peazip`
- [x] An IME to type Indian languages
  - **Keyboard Layout Method** (Simple and no IME)
    - Goto `Keyboard > Layouts` and then add the language or layout you need, for eg: Hindi -> Hindi(Wx) and set a display text.
    - Default shortcut to change keyboard layout is `Meta+Alt+K`
  - **Input Method Editor**
    - `sudo pacman -S ibus` && `paru -S ibus-m17n` && restart
    - The above keyboard layout method can also be used in this approach as it has both keyboard layout and IME's
    - On wayland session open Keyboard > Virtual Keyboard and set select IBus Wayland and apply.
    - Search for Input Method Selector and set preferences of ibus.
    - Open Ibus Preferences, select input method and now you should be able to add both layouts and IMEs.
    - Restart the computer to ensure proper functioning
    - Default Shortcut to change layout is `Super+space` you could change it to `Super+Alt+space` from preferences
    - :warning: does not works on few apps on a wayland session
  - > Keyboard Layout Access Scheme :- **Left Bottom : `no shift` | Left Top : `Shift` || Right Bottom : `RightAlt` | Right Top : `RightAlt+Shift`**
  - You can see keyboard layout either directly from taskbar if available(like for Hindi Wx) or goto `ibus Preferences > Input method > Select the Layout > About`
  - _Recommendation : Use the first Approach described unless necessary_
- Screen Recorder
  - KDE's Built in Screen Recorder
  - [Simple Screen Recorder](https://github.com/MaartenBaert/ssr)
  - [OBS Studio](https://obsproject.com/) for advanced purposes
  - [Kazam](https://github.com/henrywoo/kazam)
    > To Create keyboard shortcuts goto `Keyboard > Shortcuts`
- Others Apps I use
  - Surfshark: `paru -S surfshark-client`
- Virtual Machine Emulator : [Virt Manager](https://www.makeuseof.com/how-to-install-arch-linux-kvm-configure-virtual-machine/)
  - `sudo pacman -S qemu-full virt-manager virt-viewer dnsmasq bridge-utils libguestfs ebtables vde2 openbsd-netcat`
  - `sudo systemctl enable libvirtd.service` or `sudo systemctl start libvirtd.service`
  - Add current user to libvirt group `sudo usermod -aG libvirt $USER`
  - Start the network either `virsh net-start default` or `virsh net-autostart default`

### VS Code Keybindings Fix

Initially refer to [Windows](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-windows.pdf) and [Linux](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-linux.pdf) keybindings guide to see if the shortcut you is event present on you or platform.

- Others shortcuts problem [here](https://stackoverflow.com/questions/73469919/vsc-the-copy-line-down-doesnt-work-and-when-i-trie-to-edit-the-key-combination)
- If a shortcut listed for your platform does not work then the DE might be interfering with it.
- If a shortcut is not present for your platform try adding yourself.

### More

- [ ] Test and use a Lightweight Windows Distribution in Linux on a VM. Avoid trying a major windows release as it would uselessly occupy space. Instead go for a patched lite version.
  - IDM :- This app on the VM as there no as good alternatives to IDM on Linux. Running this should not a problem ignoring `storage issues` on `VM`. storage issues relate to resizing the virtual disk before/after downloading files
  - Wondershare i converter :- It is known that VMs don't perform very well when it comes to utilizing hardware resources of the host.
  - **_You may install VM for use. But you should install the above mentioned apps in VM only if a good enough working substitute could not be found_**
- [ ] **_File Transfer Apps_**
  - [Warpinator](https://warpinator.com/)
  - [Local Send](https://localsend.org/)
- [ ] Explore the possibility of using WSL as a file access tool rather than paragon linux file system.

## Others

- Shortcuts
  - [x] Lock Screen : `Win+L` to lock screen
  - [x] Copy/Paste in Terminal : `shift+ctrl+c/v`
  - [x] `Meta+PgUp/Down` to Maximize/Minimize page. To also support numpad pgup/pgdown edit `Kwin` shortcuts
  - [x] Registering shortcuts to open apps directly and finding a alternative to `alt+f4` of windows. in `Keyboard > Shortcut`
  - Use `ctrl+t` to open new tab in dolphin file explorer and `alt+number` to goto specific tab and `ctrl+w` to close the current tab.
- Font
  - to install fonts locally copy it to `~/.local/share/fonts` folder. then `sudo fc-cache -f -v`
  - restart the computer to use the fonts properly in the terminal
- To enable `24 Hour Time Format` you need to change time Format in Settngs > Region and Language.
- To disable **Auto Restore preopened apps** after logout/shutdown/restart goto Settings > Session > Desktop Session. Select 'Start with an Empty Session` under 'On Login, Launch Apps that were open'. This causes some unexpected behaviour.
- To Disable **Audio Sound** and chaange **audio step** to 2
  - Open Settings > Under Input & Output > Sound > Configure Volume Settings. Uncheck Audio Volume and change step size to `2`
- To show a **indiacator around mouse** while you press a hotkey(in my case `meta+ctrl+s`)
 - Goto Settings > Windows Management > Desktop Effect
 - Then enale track mouse and set a shortcut with required modifier keys to `show/hide` a indicator around mousThen enale track mouse and set a shortcut with required modifier keys to `show/hide` a indicator around mousee

## Backup Instructions for `/home` directory

> _**A better option always would be to have a separate partition for /home**_

Use `rsync` to backup as it is supposed to preserve file permissions

### Getting ignorelist

save ignorelist

```bash
wget https://raw.githubusercontent.com/rubo77/rsync-homedir-excludes/master/rsync-homedir-excludes.txt -O /var/tmp/ignorelist
```

Edit the file to add `.venv, node_modules`, etc. Also go through the file once if required.

### Backup

If the drive used lacks space then you should consider not system files like repos, video, audio and other multimedia somewhere else.

> _It would also be recommended if backup your git repositories in a `tar` file to avoid problems with file permissions_

```bash
sudo rsync -avh --progress --exclude-from=/var/tmp/ignorelist /home/<username>  <backup_path>    # usually like /media/<username>/<drive_name>/<loc>
```

Also after successful backup to the external drive you should also replace old username with new username if they are not same. This should avoid some potential problems which may occur.

```bash
#!/bin/bash
directory="<backup_path>"
search_text="/home/<old_username>"
replace_text="/home/<new_username>"
find "$directory" -type f -name "*.txt" -exec sed -i "s|$search_text|$replace_text|g" {} \;
```

#### Restore

```bash
sudo rsync -avh --progress <backup_path> /home/<new_username>/
```

After successful restore also set ownership if it had gone wrong

```bash
sudo chown -R <new_username>:<new_username> /home/<new_username>
```

