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
sudo pacman -Syu
sudo pacman -S base-devel gdb cmake readline unzip zip man-pages p7zip wget curl git htop btop inxi neofetch util-linux
```

### Shell Setup

#### zsh

```bash
sudo pacman -S zsh
# changinf default shell to zsh, you can also do it with sudo to make zsh default for root
# restart to make changes take effect
chsh -s $(which zsh)

# Installing ohmyzsh
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
sudo pacman -S powerline-fonts
```

#### Using zodide instead of cd

Install [zodide](https://github.com/ajeetdsouza/zoxide?tab=readme-ov-file#installation) or by `sudo pacman -S zoxide`.
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

#### atuin for better history

```bash
# installation
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh
```

Add `eval "$(atuin init zsh)"` at the end of `~/.zshrc`

To delete command history use `atuin search --delete-it-all`
To delete specific entries(prefixes) `atuin search --delete --search-mode prefix psql`

### Using Stow for dotfile management

Install using `sudo pacman -S stow`

Run command in the directory you have stored your dotfiles(the filestructure should correspond to $HOME directory).
You need to run this command after each change made to the dotfiles.
```bash
stow .
```

Use `.stow-local-ignore` to ignore files. Example [dotfile repo](https://github.com/shubhattin/dotfiles).

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
sudo pacman -S python

# Other python packages
sudo pacman -S python-pip tk
```

Fixing pip based error for python>=3.11

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

