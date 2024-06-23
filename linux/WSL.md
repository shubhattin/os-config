### Releasing Disk Space from WSL

The auto allocated disk space(auto exapanding) can be released back into the host drive.

You might need to enable `HyperV` to use `optmize-vhd`

```pwsh
# Run in Powershell(Administrator)
wsl.exe --shutdown
# Replace with your username
cd "C:\Users\shubh\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState"
optimize-vhd -Path .\ext4.vhdx -Mode full
```

Alternative method using `diskpart`

```pwsh
wsl --shutdown
diskpart
# open Diskpart in new window
select vdisk file="C:\WSL-Distros\…\ext4.vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit
```

### Ensure Powershell installed for better support with nvim wsl

Install Latest LTS version or download from [here](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.4)


### Shortcut for intended WSL Distro

```bash
# List all installed wsl distros
wsl -l
# Then create a shortcut using
pwsh.exe -NoProfile -Command wsl -d <distro-name> --cd ~


# For Example
# Ubuntu
pwsh.exe -NoProfile -Command wsl -d Ubuntu --cd ~
# Ubuntu 24.04 LTS
pwsh.exe -NoProfile -Command wsl -d Ubuntu-24.04 --cd ~
```
