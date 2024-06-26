# WSL Ubuntu Config

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
sudo apt update -y
sudo apt upgrade -y
sudo apt install sl -y # just to test
sudo apt install build-essential gdb -y # compilers
sudo apt install cmake -y
sudo apt install libreadline-dev unzip zip -y
sudo apt install manpages-dev -y
sudo apt install software-properties-common -y
sudo apt update -y
```

### zsh

```bash
sudo apt install zsh -y
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
sudo apt install fonts-powerline -y
```

Import the configs using the command below, add it to both `.bashrc` and `.zshrc`.

```bash
source "$HOME/.config/os-config/linux/ubuntu/scripts/cli_config.sh"
# The file below is optional, this is the place where you could define your Environment Variabels
source "$HOME/.config/os-config/linux/ubuntu/scripts/my_env.sh"
```

### NVM(Node Version Manager)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
# Install the nvm version you prefer
# like nvm install 20.9
```

### Git

```bash
sudo apt remove git -y
sudo add-apt-repository ppa:git-core/ppa -y
sudo apt update -y
sudo apt install git -y

# Authentication to Github should be done through gh CLI

git config --global init.defaultBranch main # default branch name
git config --global core.autocrlf input
git config --global core.safecrlf true
# ^ We are setting the autocrlf to always to be '\n' instead of '\r\n'

# Github CLI
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
&& sudo mkdir -p -m 755 /etc/apt/keyrings \
&& wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
&& sudo apt update \
&& sudo apt install gh -y
```

### tmux

```bash
sudo apt install tmux -y
```

Config :- `~/.tmux.conf`

```bash
# enabling mouse
set -g mouse on
# vim mode in scroll
setw -g mode-keys vi

# Setting background color
set -g default-terminal "screen-256color"
# set -g status-bg black
# set -g status-fg white
set -g status-style bg=default
```

### Python

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update -y
# You can replace python3.12 with other versions -y
sudo apt install python3.12 -y
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 2
sudo update-alternatives --config python3
sudo apt install python3-dev python3-pip -y
# Also install "python3.x-dev" like python3.12-dev
sudo apt install python3-virtualenv -y
# Also install venv module with command below
# sudo apt install python3.x-venv -y
sudo apt install python3-tk -y # tkinter support
sudo apt install python-is-python3 -y
# sudo apt remove python3-apt -y # this might cause problems
sudo apt install python3-apt -y # apt manager python

# apt_pkg not found problem fix
# cd /usr/lib/python3/dist-packages
# sudo cp apt_pkg.cpython-310-x86_64-linux-gnu.so apt_pkg.so
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
sudo add-apt-repository ppa:neovim-ppa/stable -y
sudo apt update
sudo apt install neovim -y
nvim -v

# For Copy and Paste in nvim now using using native clip.exe and pwsh commands

# Grep Tool
sudo apt install ripgrep -y

# LazyGit tool
LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
curl -Lo lazygit.tar.gz "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz"
tar xf lazygit.tar.gz lazygit
sudo install lazygit /usr/local/bin
```

To use nvim of wsl properly in vscode

```json
"vscode-neovim.useWSL": true,
"vscode-neovim.neovimExecutablePaths.linux": "/opt/nvim-linux64/bin/nvim",
```

### Java and Kotlin

```bash
sudo apt install default-jdk -y
sudo apt install default-jre -y
update-alternatives --config java
```

Add `JAVA_HOME` Environment variable to `/etc/environment`.
Write the output path `update-alternatives --config java`

```bash
curl -s https://get.sdkman.io | bash # SDKMan
source "$HOME/.sdkman/bin/sdkman-init.sh"
# then do -> sdk install kotlin
```

### Optional GUI Apps

```bash
sudo apt install gedit # Editor
sudo apt install nautilus # File Manager
sudo apt install x11-apps -y # like xcalc, xclock, xeyes
sudo apt install tilix # Terminal Tool
# run these gui Apps with '&' at the end to run in background
```

### Lua

```bash
curl -L -R -O https://www.lua.org/ftp/lua-5.4.6.tar.gz
tar zxf lua-5.4.6.tar.gz
cd lua-5.4.6
make linux test
sudo make install

# lua rocks
wget https://luarocks.org/releases/luarocks-3.8.0.tar.gz
tar zxpf luarocks-3.8.0.tar.gz
cd luarocks-3.8.0
./configure --with-lua-include=/usr/local/include
make
sudo make install
```

<!-- ### Julia

```bash
wget https://julialang-s3.julialang.org/bin/linux/x64/1.8/julia-1.8.1-linux-x86_64.tar.gz
tar zxvf julia-1.8.1-linux-x86_64.tar.gz
mv julia-1.8.1 .julia
rm julia-1.8.1-linux-x86_64.tar.gz
```

### R and Perl

```bash
sudo apt install r-base -y
sudo apt install perl -y
``` -->

### 7zip

```bash
sudo apt install p7zip-full p7zip-rar -y
```

### Android Build Tools and ADB

```bash
sudo apt install android-sdk-build-tools -y
sudo apt install android-tools-adb -y
```

### PostgreSQl

```bash
sudo apt install postgresql -y postgresql-contrib
```

Other useful info

```bash
# Start psql service
sudo service postgresql start

# Login
sudo -u postgres psql

# Set Password after login
/password postgres
```

### Go

```bash
sudo add-apt-repository ppa:longsleep/golang-backports -y
sudo apt update -y
sudo apt install golang-go -y
```

### Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
