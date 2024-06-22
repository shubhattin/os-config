#### Releasing Disk Space from WSL

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


