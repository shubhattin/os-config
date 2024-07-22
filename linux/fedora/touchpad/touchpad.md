
## **TouchPad Setup**

Touchpad support is good in both `x11` and `wayland`. But you need to enbale `Invert Scroll Direction (Natural Scrolling)` for touchpad in `KDE Settings`
To enable `Pinch Zoom In/Out` add flag `--enable-features=UseOzonePlatform --ozone-platform=wayland` in a wayland session. for eg :- for chrome and brave
But this cause problems if you are in a x11 session. So rather prefix the app command with `run_ozone_wayland_flags`.
We could also declare this as a function in profile but to on safer side rather declare it as execuatble in `/bin` (as the shell session variables might not be accessible)

Save the [file](./run_ozone_wayland_flags) below as `/bin/run_ozone_wayland_flags`. also set executable permission by `sudo chmod +x` or `sudo chmod 755`. 

Now prefix the command for opening that app in cli or in .desktop file. like `/bin/run_ozone_wayland_flags /usr/bin/flatpak run --branch=stable --arch=x86_64 --command=brave --file-forwarding com.brave.Browser @@u %U @@`

> :warning: **_You might experience that even after changing the `Exec` field it still not works. Then the ways left are either to register the shortcuts directly through commands rather than application launch shortcut. Or it has also been noticed that whenever fedora restarted after a ctricital system update it updated the Exec field as well._**

### Solving `Exec` Being Reset after update from Flathub

Save the [file](./prefix_ozone_wayland) as `/bin/prefix_ozone_wayland` with permissions `754` and owner `root:root`. Also add a systemd init script by saving as `/etc/systemd/system/prefix_ozone_wayland.service` also with `754 and root:root`

```service
[Unit]
Description=Prefixed .desktop ozone wayland flag provider for zoom in/out support
After=network.target

[Service]
Type=simple
ExecStart=/bin/prefix_ozone_wayland
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

Then verify by running

```bash
sudo systemctl enable prefix_ozone_wayland.service
```
