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
sudo dnf upgrade
sudo dnf groupinstall "Development Tools" "Development Libraries" -y
sudo dnf install gdb -y
sudo dnf install cmake -y
sudo dnf install readline-devel unzip zip -y
sudo dnf install man-pages -y
sudo dnf install dnf-plugins-core -y
sudo dnf install p7zip -y
sudo dnf install wget curl -y
sudo dnf install git htop btop neofetch -y
```

### Shell Setup

#### zsh

```bash
sudo dnf upgrade --refresh
sudo dnf install zsh -y
# changinf default shell to zsh
chsh -s $(which zsh)

sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
sudo dnf install powerline-fonts -y
```

#### Using zodide instead of cd

Install [zodide](https://github.com/ajeetdsouza/zoxide?tab=readme-ov-file#installation) or by `sudo dnf install zoxide -y`.
Add at end of .zshrc

```bash
eval "$(zoxide init --cmd cd zsh)"
# --cmd cd -> replaces the cd command. if you dont add this you could use it using `z`, So new commands would be cd and cdi
```
Refer [this video](https://www.youtube.com/watch?v=aghxkpyRVDY).
Install a fuzzy finder to use in `cdi` command
```bash
sudo dnf install fzf -y
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

Install using `sudo dnf install stow`

Run command in the directory you have stored your dotfiles(the filestructure should correspond to $HOME directory).
You need to run this command after each change made to the dotfiles.
```bash
stow .
```

Use `.stow-local-ignore` to ignore files. Example [dotfile repo](https://github.com/shubhattin/dotfiles).

### Git

```bash
sudo dnf upgrade --refresh
sudo dnf install git -y

# Authentication to Github should be done through gh CLI

git config --global init.defaultBranch main # default branch name
git config --global core.autocrlf input
git config --global core.safecrlf true
# ^ We are setting the autocrlf to always to be '\n' instead of '\r\n'

# Github CLI
sudo dnf install 'dnf-command(config-manager)'
sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
sudo dnf install gh --repo gh-cli
```

### tmux

```bash
sudo dnf install tmux -y
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
sudo dnf upgrade --refresh
sudo dnf install python3

# Other python packages
sudo dnf install python3-pip python3-tkinter
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
sudo dnf upgrade --refresh
sudo dnf install -y lua luarocks
sudo dnf install -y neovim

# For Copy and Paste in nvim now using using native clip.exe and pwsh commands instead of win32yannk.exe

# Grep Tool
sudo dnf install ripgrep -y

# LazyGit tool
sudo dnf copr enable atim/lazygit -y
sudo dnf install lazygit -y
```

Install a clipboard provider for nvim in fedora if you face problems in using system clipboard. Not encountered any yet.

To use nvim of wsl properly in vscode

```json
"vscode-neovim.useWSL": true,
```

### Java

Java might be preinstalled check the version or search for your appropriate package version with
`sudo dnf search openjdk`

```bash
# sudo dnf install java-21-openjdk-devel.x86_64 -y
update-alternatives --config java
```

Add `JAVA_HOME` Environment variable to `/etc/environment`.
Write the output path `update-alternatives --config java`

### PostgreSql

```bash
sudo dnf upgrade --refresh
sudo dnf install postgresql-server postgresql-contrib -y

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
sudo dnf install -y golang
```

### Rust

```bash
sudo dnf install -y rust cargo
```

### Speedtest CLI

```bash
URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz"
cd /tmp && UUID=$(uuidgen) && mkdir "$UUID" && cd "$UUID" && wget "$URL" -O speedtest.tgz && tar -xzf speedtest.tgz
LOCAL_BIN="$HOME/.local/bin" && mkdir -p "$LOCAL_BIN" && mv speedtest "$LOCAL_BIN/speedtest" && cd
```

## Notes

### Improving dnf speed

Append to `/etc/dnf/dnf.conf` and the refresh with `sudo dnf upgrade --refresh`

```conf
max_parallel_downloads=10
fastestmirror=True
```

