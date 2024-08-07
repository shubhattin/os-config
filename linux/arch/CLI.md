### Configuring DNS

```bash
# Using Google DNS to avoid network related issues
sudo rm /etc/resolv.conf
sudo bash -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
sudo bash -c 'echo "nameserver 8.8.8.4" >> /etc/resolv.conf'
sudo bash -c 'echo "[network]" > /etc/wsl.conf'
sudo bash -c 'echo "generateResolvConf = false" >> /etc/wsl.conf'
sudo chattr +i /etc/resolv.conf # setting immutable
```

### Download few Basic packages

```bash
sudo pacman -Syyu # force fetch
sudo pacman -S base-devel gdb cmake readline unzip zip man-pages p7zip wget curl git htop btop inxi neofetch util-linux tree bat lf fzf
```

### Shell Setup

#### zsh

```bash
# Installing zsh and some fonts
sudo pacman -S zsh powerline-fonts fzf zoxide
# changinf default shell to zsh, you can also do it with sudo to make zsh default for root
# restart to make changes take effect
chsh -s $(which zsh)

# install oh-my-posh using paru, this should chaotic aur by default
paru -S oh-my-posh
```

#### Using zodide instead of cd

Install [zodide](https://github.com/ajeetdsouza/zoxide?tab=readme-ov-file#installation) or by `sudo pacman -S zoxide fzf`.
Add at end of .zshrc

```bash
eval "$(zoxide init --cmd cd zsh)"
# --cmd cd -> replaces the cd command. if you dont add this you could use it using `z`, So new commands would be cd and cdi
```
Refer [this video](https://www.youtube.com/watch?v=aghxkpyRVDY).
Install a fuzzy finder to use in `cdi` command
```bash
sudo pacman -S fzf
# use cdi as a fuzzy finder in zoxide db
# also to launch interactive shell, start typing the path part press space followed by TAB
# This should bring up a filtered interactive window
```

### Using Stow for dotfile management

Install using `sudo pacman -S stow`

Run command in the directory you have stored your dotfiles(the filestructure should correspond to $HOME directory).
You need to run this command after each change made to the dotfiles.
```bash
stow .
```

Use `.stow-local-ignore` to ignore files. Example [dotfile repo](https://github.com/shubhattin/dotfiles).
Use `stow --adopt .` to overwrite the files but in this method the dotfiles directory files will be overwritetn with the confilicting version of that file. Or make sure that you have commited all your files to git before executing this so you could `git restore .`

### Git

```bash
git config --global init.defaultBranch main # default branch name
git config --global core.autocrlf input
git config --global core.safecrlf true
# ^ We are setting the autocrlf to always to be '\n' instead of '\r\n'

# Github CLI
sudo pacman -S github-cli
```

### tmux

```bash
sudo pacman -S tmux
```

### NVM(Node Version Manager)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
# Install the nvm version you prefer
# like nvm install 20.9
```

### Python
> ⚠️ **Unless very essentail try to stick with the default python version that was preinstalled, as python is a system dependency so changing the version and not properly being able to install all the packages previous version had might result in errors**


```bash
sudo pacman -S python python-pip python-pipx tk
# pipx can be used to install cli apps in pip like black, but prefer direct pacman method
# install common needed packages via pacman instead of pip or pipx
sudo pacman -S python-rich python-requests python-poetry python-pipenv ipython python-black
```

#### Never install using `sudo pip` or even `pipx` directly or else you would potentially break your system

Never do `sudo pip install pkg`.

Even this would not be recommended but if you do wish to install a user level python package in `~/.local/lib/python3.12`. Before finally installaling using pip try to find the package as `sudo pacman -Ss pkg`.
You could make some changes, Fixing pip based error for python>=3.11

```bash
sudo mv /usr/lib/python3.12/EXTERNALLY-MANAGED /usr/lib/python3.12/EXTERNALLY-MANAGED.old
```

OR try this of you dont want to mess with those things, change `~/.config/pip/pip.conf`.

```
[global]
break-system-packages = true
```

### _**NeoVim**_

```bash
# Installing Lua, Luarocks, Neovim, Ripgrep, Lazygit
sudo pacman -S lua luarocks neovim ripgrep lazygit

# Install Clipboard Providers
sudo pacman -S xclip wl-clipboard
```

### Java

```bash
sudo pacman -S jdk-openjdk
```

Add `JAVA_HOME` Environment variable to `/etc/environment` or in PATH.

### PostgreSql

```bash
sudo pacman -Syu
sudo pacman -S postgresql

# enable psql start on startup
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Other useful info

```bash
# Login
sudo -u postgres psql

# Set Password after login
/password postgres

# the above mighr have some problems running in older version so use this
ALTER USER <usernamee> WITH PASSWORD '<passwoord>';
```

For more [refer here](https://docs.fedoraproject.org/en-US/quick-docs/postgresql/)

### Go

```bash
sudo pacman -S go
```

### Rust

For development purposes you should prefer the `rustup` method of installation istead of directly installing it as `sudo pacman -S rust`.
```bash
sudo pacman -S rustup
```

### Speedtest CLI

```bash
URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz"
cd /tmp && UUID=$(uuidgen) && mkdir "$UUID" && cd "$UUID" && wget "$URL" -O speedtest.tgz && tar -xzf speedtest.tgz
LOCAL_BIN="$HOME/.local/bin" && mkdir -p "$LOCAL_BIN" && mv speedtest "$LOCAL_BIN/speedtest" && cd
```


### Basic Pacman Usage Syntax

[Refer Arch Wiki](https://wiki.archlinux.org/title/Pacman) for more clarity and detail.

#### `pacman -S`

- `pacman -S pkg` : to install a package
- `pacman -Syu` : System Upgrade
  - `pacman -Sy` : Sync package Database
  - `pacman -Syy` : Force Sync Packkages, you could add `u` flag to update
- `pacman -Syyuw` : to download the updates but install them later manually
- `pacman -Ss pkg` : to search a package in the package repos
- `pacman -Sc` : remove unused cache which might be old and not needed

#### `pacman -R`

- `pacman -R` : to remove a package
- `pacman -Rs` : also removes depenencies along with it
- **_`pacman -Rns`_** : removes some non system dotfiles as well, **recommended way to remove**

#### `pacman -Q`

- `pacman -Q` : list out all packages installed, pip the output to `wc -l` to count the number of lines
- `pacman -Qe` : packages explicitly installed by us or some other program
- `pacman -Qeq` : the `q` flag gets rid of the version number and just gives info on name
- `pacman -Qn` : to list system packages instaleed from main repos
- `pacman -Qm` : to list AUR packages
- `pacman -Qdt` : to list orphan packages, which are no longer needed
- `pacman -Qs pkg` : to search for package in installed apps

#### Enabling few options in `/etc/pacman.conf`

Uncomment `Color`, `CheckSpace`, `ILoveCandy` to enable coloured output, check for available space and modify the loading indicator of pacman respectively.
Also uncomment `VerbosePkgLists` to have a detailed breakdown on package changes in form of a multiline list instead of a paragraph.
Also set `ParallelDownloads = 5` to allow parallel downloads.

#### Updating `/etc/pacman.d/mirrorlist`

**_Upadte mirros necessarily to have a better speed for installing packages either manually or via EOS welcome_**
If you are facing problems with mirrors. You could use `reflector` for this via `sudo pacman -S reflector`. Save the output to mirrorlist file but also keep backup of previous file.
`sudo cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak`

```bash
reflector --verbose --protocol https --sort rate --latest 20 --download-timeout
# current command i use
reflector --verbose -c IN -c SG --protocol https --sort age --latest 20 --download-timeout 5
```

In Endeavour OS you use the Welcome app to update mirrors.


### Paru Installation and Usage

You could prefer paru over some other aur helper like yay. Install it like this.
> :warning: Paru by default shows you the

```bash
sudo pacman -Syu
sudo pacman -S lf bat # lf file manager, bat for syntax highlighted printing

# Install paru with the chaotic-aur
sudo pacman -S chaotic-aur/paru
```

If you already have yay and wish to unistall it then do `sudo paru -Rns yay` and also prefer creating a prefix for paru.
```bash
alias yay=paru
```

#### Some basic paru commands

Paru apart from being a aur helper is also a wrapper around pacman.

- never run `paru` or `yay` or any AUR helper with `sudo`
- `paru -Sua` to upgrade aur packages only
  - add the `--upgrademenu` flag to pick and choose particular aur packages to upgrade
- `paru -Sua --fm lf or nvim` : opens the whole package file rather than just printing out `PKGBUILD` with a file manager of your choice
- `paru -Qua` : query updatable aur packages

my [config file](https://github.com/shubhattin/dotfiles/blob/main/.config/paru/paru.conf). The constraints forced via a fie manager are like a necessity if you wish to have a safer and more stable experience using aur.


### Enable Chaotic AUR

After `sudo su` enter these commands. Refer the [docs](https://aur.chaotic.cx/docs)
```bash
pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com
pacman-key --lsign-key 3056513887B78AEB
pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst'
pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'
```

Add the line to `/etc/pacman.conf` if not already added

```config
[chaotic-aur]
Include = /etc/pacman.d/chaotic-mirrorlist
```

> **You Don't Need to Manually change `paru -S pkg` commands to `sudo pacman -S chaotic-aur/pkg` as paru automatically prefers chaotic-aur over aur**
