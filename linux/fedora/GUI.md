> This file has not yet been fully updated for Fedora KDE

## OS Installation and Boot
- To install with windows as dual boot ensure these things
  - Choose the `Advanced Custom Partion` Method while allocating disk for installtion.
  - `/boot/efi` -> On fedora installation you need to manually set the mount point. Choose `EFI File System` as partition format.
  - `/` -> `Reformat` and `ext4`. Do not install as LVM as it would interfere with dual boot. Also if you `btrfs` you would be limited to only `read`.
  - `/home` -> `No Reformat` and `ext4`
  - [ ] Swap/Zram
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
- **TouchPad Setup**
  - touchpad support is good in both `x11` and `wayland`. But you need to enbale `Invert Scroll Direction (Natural Scrolling)` for touchpad in `KDE Settings`
  - To enable `Pinch Zoom In/Out` add flag `--enable-features=UseOzonePlatform --ozone-platform=wayland` in a wayland session. for eg :- for chrome and brave
    - if you are not able to set flag with gui you should try editing `Exec` in `.desktop` file shortcut
    - [ ] Also how to disable this on x11 as apps dont start
- [x] Time and Date
- [ ] **Dual Monitor Support** : You need to _mirror_ screen and set the monitor's resolution while connected and laptop's resolution while disconnected, you might as well explore `x11` config for that. Click `Display Settings` on the home screen.
  - Enable fractional scaling to enable ui zoom like 125%, 150% etc
  - > You might face problems with fractional scaling in mint as its experimental. To fix this you could temporarily or permanently switch to resolution close `dimension/scaling factor`, although this would come at cost of reduced sharpness and reduced screen quality(this also save some power).
- **GPU Setup**
  - list GPUs `lspci -vnn | grep VGA`
  - [ ] Explore more on Dual GPU support in fedora. Also find ways to use Dedicated GPU when needed
  - To install Proprietary NVIDIA drivers follow [this](https://itsfoss.com/install-nvidia-drivers-fedora/)
  - [x] Use **[Mission Center](https://missioncenter.io/)**  or **[Resources](https://flathub.org/apps/net.nokyan.Resources)** to verify and see GPU Usage as it lists all major hardware resources. 
- _Power Management_ : If you feel that your system is not utilizing space in optimal way you could use [tlp](https://askubuntu.com/questions/1309396/how-to-increase-battery-life-on-ubuntu-20-04-and-what-power-saving-software-shou) and remove it see [here](https://www.baeldung.com/linux/tlp-disable)
  - Setup Lid Close and other such options in `Power Management`
- Add `Flathub` to fedora software repository as well using `flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo`. [reference](https://flathub.org/setup/Fedora)
- > :information_source: While using a usb drive or any any external storage device wait for the usb to eject and disappear from file explorer. Its because if something shows to be copied, deleted, moved etc, it still might be processing things in background. This also the reason why commands like `rm -rf and cp` feel faster than windows copy and delete.


## Software
- [x] ***CLI Based Application*** : These apps usually work all fine without ever having any major issues.
   - [x] Terminal Emulator
     - `Konsole` : Built in KDE terminal. Also enable proper `brahmic` script rendering in `Appearence > Complex Text Layout`
- Browsers
  - [x] Brave
  - [x] Edge
  - [x] Chrome
- Video Player
  - [x] VLC Media Player
     - :heavy_check_mark: for now vlc seems to be fine and could not find a good alternative for advanced player like powerdvd
- Partition Manager : Built in KDE Partition Manager
  - [Disk Usage Analyser](https://flathub.org/apps/org.gnome.baobab)
- Video Converter
  - [x] Alternative(s) to Wondershare i converter
    - [HandBrake](https://handbrake.fr/)
    - [Shutter Encoder](https://www.shutterencoder.com/)
- Others
  - [x] XDM or a better alternative if you can find like IDM
    - [x] Some file type downloads are not being caught like mp4
      - :heavy_check_mark: for now staying with this limitation as noother good tool tried or found. It is not a problem as it is just a longer process and we have to manaually right click on the link or see if video was detected in extension panel.
  - [x] YouTube Video Downloader
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
  - [x] Eye Protector Apps
    - [ ] [Safeeyes](https://github.com/slgobinath/SafeEyes?tab=readme-ov-file#ubuntu-linux-mint-and-other-ubuntu-derivatives) for 20-20 rule
      - you may prefer local package on [fedora](https://github.com/slgobinath/SafeEyes?tab=readme-ov-file#fedora)
    - [Iris micro gui](https://github.com/shubhattin/iris_micro_gui) for a app like careueyes
      - > :warning: does not work in a wayland session as of now
  - [x] File Recovery App
    - [free Linux recovery](https://www.r-studio.com/free-linux-recovery/)  
    - Bootable [Redo](http://redorescue.com/)
  - [x] Rufus Alternatives
    - Use [Ventoy](https://ventoy.net/en/download.html) for windows and linux as well. [Windows Guide](https://www.reddit.com/r/linux4noobs/comments/z5dk4o/how_can_i_burn_a_bootable_win10_usb_in_linux/)
    - [Universal USB Instaler](https://pendrivelinux.com/universal-usb-installer-easy-as-1-2-3/#how-to-install-universal-usb-installer-in-linux)
    - [Posicle](https://flathub.org/apps/com.system76.Popsicle)
    - > :information_source: If the default file explorer formatter gives problems goto `Disks`
  - [x] Pdf Editor
    - Libre Office Draw
  - [x] Compression tools
    - [Peazip](https://peazip.github.io/peazip-linux.html)
  - [x] An IME to type Indian languages
    - **Keyboard Layout Method** (Simple and no IME)
       - Goto `Keyboard > Layouts` and then add the language or layout you need, for eg: Hindi -> Hindi(Wx)
       - Under `Display Options` unheck 'show country flag' and check 'show layout name instead of group name'
     - **Input Method Editor**
       - The above keyboard layout method can also be used in this approach as it has both keyboard layout and IME's
       - Search `Input Method` and choose a indian language displayed there(in my case was telugu) and click install. This should install `ibus` and related dependencies. or install using `sudo apt install ibus ibus-m17n m17n-db fonts-indic fcitx-m17n ibus-clutter ibus-table ` 
       - After installed logout and open method again and select input framework to be ibus.
       - Open Ibus Preferences, select input method and now you should be able to add both layouts and IMEs.
       - Restart the computer to ensure proper functioning
     - Use `Win+Space` to switch and change shall be reflected in taskbar
     - > Keyboard Layout Access Scheme :- **Left Bottom  : `no shift` | Left Top : `Shift` || Right Bottom : `RightAlt` | Right Top : `RightAlt+Shift`**
     - You can see keyboard layout either directly from taskbar if available(like for Hindi Wx) or goto `ibus Preferences > Input method > Select the Layout > About` 
     - _Recommendation : Use the first Approach described unless necessary_
- [x] Screen Recorder
   - [Simple Screen Recorder](https://github.com/MaartenBaert/ssr)
   - [OBS Studio](https://obsproject.com/) for advanced purposes
   - [Kazam](https://github.com/henrywoo/kazam)
> To Create keyboard shortcuts goto `Keyboard > Shortcuts > Custom Shortcuts`

### VS Code Keybindings Fix

Initially refer to [Windows](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-windows.pdf) and [Linux](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-linux.pdf) keybindings guide to see if the shortcut you is event present on you or platform.

- `Alt+click` issue in Linux mint, [here](https://forums.linuxmint.com/viewtopic.php?t=403820). This is because `Alt` is used for window management so disable it.
- Others shortcuts problem [here](https://stackoverflow.com/questions/73469919/vsc-the-copy-line-down-doesnt-work-and-when-i-trie-to-edit-the-key-combination)
- If a shortcut listed for your platform does not work then the DE might be interfering with it.
- If a shortcut is not present for your platform try adding yourself.

## Others
- [ ] Test and use a Lightweight Windows Distribution in Linux on a VM. Avoid trying a major windows release as it would uselessly occupy space. Instead go for a patched lite version.
  - IDM :- This app on the VM as there no as good alternatives to IDM on Linux. Running this should not a problem ignoring `storage issues` on `VM`. storage issues relate to resizing the virtual disk before/after downloading files
  - Wondershare i converter :- It is known that VMs don't perform very well when it comes to utilizing hardware resources of the host.
  - ***You may install VM for use. But you should install the above mentioned apps in VM only if a good enough working substitute could not be found***
- [ ]  **_File Transfer Apps_**
    - [Warpinator](https://warpinator.com/)
    - [Local Send](https://localsend.org/)

## Shortcuts, Notes
- Shortcuts
  - [x] Lock Screen : `Win+L` to lock screen
  - [x] Copy/Paste in Terminal : `shift+ctrl+c/v`
  - [x] Registering shortcuts to open apps directly and finding a alternative to `alt+f4` of windows. in `Keyboard > Shortcut`
- Font
  - to install fonts locally copy it to `~/.local/share/fonts` folder. then `sudo fc-cache -f -v`
  - restart the computer to use the fonts properly in the terminal

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
