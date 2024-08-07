## OS Installation and Boot

- To install with windows as dual boot ensure these things
  - Choose the `Advanced Custom Partion` Method while allocating disk for installtion.
  - `/boot/efi` -> On fedora installation you need to manually set the mount point. Choose `EFI File System` as partition format.
  - `/` -> `Reformat` and `ext4`. Do not install as LVM as it would interfere with dual boot. Also if you `btrfs` you would be limited to only `read`. `btrfs` can also be used as it has some good features to consider for root partition.
  - `/home` -> `No Reformat` and `ext4`
  - _zram & swap_ : zram of 8GiB is already setup in fedora is setup so would not need to have a swap partition. But if requirement arises you can always create and use one.
    - `cat /proc/swaps` to view current used swap devices including zram
    - `zramctl` to view zram info
  - My current layout
    - `/boot` as `ext4` 0.7Gib
    - `/boot/efi` as `EFI/fat32` 0.7Gib
    - `swap` 6Gib
    - Remaning made into a `LVM group`
      - `/` as `btrfs` 40Gib
      - `/home` as `ext4`
- It would be recommended to free space prior to opening the setup and defrag disk if needed.
- Use this [Linux FileSystem for Windows by Paragon](https://www.paragon-software.com/home/linuxfs-windows/) to access linux filesystem on windows.
  - [ ] find if we can use this even when our `/home` or `/` are encrypted.

## Basic Setup

- Connectivity
  - [x] Bluetooth
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
  - Follow Instruction [here](https://www.tecmint.com/install-nvidia-drivers-in-linux/) to install nvidia drivers. Also read [this](https://docs.fedoraproject.org/en-US/quick-docs/set-nvidia-as-primary-gpu-on-optimus-based-laptops/) if you wish to setup nvidia as primary gpu in fedora.
    - Check if `nouveau` or the proprietary nvidia drivers are running
      - `lsmod | grep nouveau`
      - `lsmod | grep nvidia`
      - `lspci -k | grep -A 3 -i "VGA"` to view installed drivers in use
      - `prime-run glxinfo | grep 'OpenGL renderer'` checking opengl rendered
  - Use [`nvidia-prime`](./scripts/prime-run) after adding as `/bin/prime-run` with executable permissions to run apps with dedicated gpu.
  - Check nvidia kernel module version `modinfo -F version nvidia`
  - [ ] Try to run tensorflow with nvidia gpu in both dual gpu and single gpu devices
  - [x] Use **[Mission Center](https://missioncenter.io/)** or **[Resources](https://flathub.org/apps/net.nokyan.Resources)** to verify and see GPU Usage as it lists all major hardware resources.
  - **Testing GPU** : Install glmark2 `sudo dnf install glmark2`
    - Testing default/primary gpu : `glmark2`
    - Testing Nvidia GPU specifically : `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glmark2`
    - While test is in progress watch the gpu usage in Mission Center. At the end it should give you a score for the benchmark.
- **X11** : `x11` Session disabled by default on fedora so has to be manually added
  - `sudo dnf install -y plasma-workspace-x11 kwin-x11` for x11 dependencies for fedora. Then restart and switch to X11 on login screen (bottom left)
  - You might need to configure your mouse/touchpad on your initial login
- _Power Management_ : If you feel that your system is not utilizing space in optimal way you could use [tlp](https://askubuntu.com/questions/1309396/how-to-increase-battery-life-on-ubuntu-20-04-and-what-power-saving-software-shou) and remove it see [here](https://www.baeldung.com/linux/tlp-disable)
  - Setup Lid Close and other such options in `Power Management`
  - _Sleep function might malfunctioning, insttalling gpu drivers fixed laptop overheating in my case_,
- > :information_source: While using a usb drive or any any external storage device wait for the usb to eject and disappear from file explorer. Its because if something shows to be copied, deleted, moved etc, it still might be processing things in background. This also the reason why commands like `rm -rf and cp` feel faster than windows copy and delete.

### Setting Flathub and RPM Fusion Repositories

```bash
# Flathub
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# RPM Fusion
sudo dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
sudo dnf install https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
```

## Software

- [x] **_CLI Based Application_** : These apps usually work all fine without ever having any major issues.
  - [x] Terminal Emulator
    - `Konsole` : Built in KDE terminal. Also enable proper `brahmic` script rendering in `Appearence > Complex Text Layout`
      - Download Nerd fonts from here [here](https://github.com/shubhattin/neovim-config/releases/tag/nerd-fonts), currently using `Caskaydia Cove NF, 10.50`
    - Or you could use Tilix
- > _Not using flatpaks or snaps for some cases might be a better option if a good up to date version is avilable in system repository. It is suitable for browesers, electron apps, video players, system monitor tools. And may be avoided for some utitlities, creative software for multimedia_
- Install **[Flatseal](https://flathub.org/apps/com.github.tchx84.Flatseal)** to manage flatpak application permissions.
- Browsers
  - [x] Brave
  - [x] Edge
  - [x] Chrome
- Video Player
  - [x] VLC Media Player
- Partition Manager : Built in KDE Partition Manager
  - Filelight for disk usage analysis
- Video Converter
  - [x] Alternative(s) to Wondershare i converter
    - [HandBrake](https://handbrake.fr/)
    - [x] [Shutter Encoder](https://www.shutterencoder.com/) : Available only via appimage on fedora
- [Stacer](https://oguzhaninan.github.io/Stacer-Web/) to manage startup items, cleaner, etc.
  - Use it to disable startup items
- Download Manager
  - Xtreme Download Manager currently using [`v8.0.29bete`](https://github.com/subhra74/xdm/releases/tag/8.0.29)
    - To enable other file extensions like mp4 and mkv which are not marked for download by default can be enabled by going into `Settings > Browser Monitoring`, then find the list where it lists the extensions which will be automatically be taken over by xdm for download and add your desired extension if it already does not exists.
    - you might not be able to disable it from startup options in settings, you will need to use KDE's Autostart to disable it.
    - :warning: There seems to problem on using it in a wayland session
  - qBittorrent
  - [Percepolis Download Manager](https://persepolisdm.github.io/)
  - Kget
  - Ktorrent
- YouTube Video Downloader
  - [Parabolic](https://github.com/NickvisionApps/Parabolic)
  - Video Downloader via `flatpak install flathub com.github.unrud.VideoDownloader`
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
  - [Safeeyes](https://github.com/slgobinath/SafeEyes?tab=readme-ov-file#fedora) for 20-20 rule from flathub
    - You should prefer system package installation over flatpak in this case
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
  - Libre Office Draw
  - [Pdf Arranger](https://flathub.org/apps/com.github.jeromerobert.pdfarranger) for arranging spplitting and mergeing pdf
- [x] Compression tools
  - [Peazip](https://peazip.github.io/peazip-linux.html)
- [x] An IME to type Indian languages
  - **Keyboard Layout Method** (Simple and no IME)
    - Goto `Keyboard > Layouts` and then add the language or layout you need, for eg: Hindi -> Hindi(Wx) and set a display text.
    - Default shortcut to change keyboard layout is `Meta+Alt+K`
  - **Input Method Editor**
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

### VS Code Keybindings Fix

Initially refer to [Windows](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-windows.pdf) and [Linux](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-linux.pdf) keybindings guide to see if the shortcut you is event present on you or platform.

- Others shortcuts problem [here](https://stackoverflow.com/questions/73469919/vsc-the-copy-line-down-doesnt-work-and-when-i-trie-to-edit-the-key-combination)
- If a shortcut listed for your platform does not work then the DE might be interfering with it.
- If a shortcut is not present for your platform try adding yourself.

## Others

- [ ] Test and use a Lightweight Windows Distribution in Linux on a VM. Avoid trying a major windows release as it would uselessly occupy space. Instead go for a patched lite version.
  - IDM :- This app on the VM as there no as good alternatives to IDM on Linux. Running this should not a problem ignoring `storage issues` on `VM`. storage issues relate to resizing the virtual disk before/after downloading files
  - Wondershare i converter :- It is known that VMs don't perform very well when it comes to utilizing hardware resources of the host.
  - **_You may install VM for use. But you should install the above mentioned apps in VM only if a good enough working substitute could not be found_**
- [ ] **_File Transfer Apps_**
  - [Warpinator](https://warpinator.com/)
  - [Local Send](https://localsend.org/)

## Shortcuts, Notes

- Shortcuts
  - [x] Lock Screen : `Win+L` to lock screen
  - [x] Copy/Paste in Terminal : `shift+ctrl+c/v`
  - [x] `Meta+PgUp/Down` to Maximize/Minimize page. To also support numpad pgup/pgdown edit `Kwin` shortcuts
  - [x] Registering shortcuts to open apps directly and finding a alternative to `alt+f4` of windows. in `Keyboard > Shortcut`
  - Use `ctrl+t` to open new tab in dolphin file explorer and `alt+number` to goto specific tab and `ctrl+w` to close the current tab.
- Font
  - to install fonts locally copy it to `~/.local/share/fonts` folder. then `sudo fc-cache -f -v`
  - restart the computer to use the fonts properly in the terminal
- Disable Calendar from AutoStart (as it takes considerable memory we dont need it now)
  - `cp /etc/xdg/autostart/org.kde.kalendarac.desktop ~/.config/autostart` to have the config accessible in `AutoStart`
  - Then Open AutoStart and disable it.
- To show a indiacator around mouse while you press a hotkey(in my case `meta+ctrl+s`)
 - Goto Settings > Windows Management > Desktop Effect
 - Then enale track mouse and set a shortcut with required modifier keys to `show/hide` a indicator around mousThen enale track mouse and set a shortcut with required modifier keys to `show/hide` a indicator around mousee
- Uninstalling a rpm package
  - find your package name `rpm -qa | grep package`
  - uninstall using `rpm -e <PackageName>`
- To lock a particular kernel version [read here](https://fedoramagazine.org/boot-earlier-kernel/)

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

