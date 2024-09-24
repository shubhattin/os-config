#!/bin/env python3

import os
import sys
import datetime
from typing import Literal
import shutil

try:
    import typer
    from rich.console import Console
    from rich.prompt import Confirm, Prompt
    from pydantic.dataclasses import dataclass
except ImportError:
    os.system("sudo pacman --noconfirm -S python-typer python-rich python-pydantic")
    sys.exit(-1)

app = typer.Typer()
console = Console()

LOG_PATH = "/tmp/arch_app_installer"


def read_file(file: str) -> str:
    with open(file, encoding="utf-8", mode="r") as f:
        return f.read()


@dataclass
class InstallerOptions:
    cpu_type: Literal["intel"] | Literal["amd"] = None
    gpu_type: Literal["intel"] | Literal["nvidia"] | Literal["both"] = None
    frac_scale: float = 1
    setup_google_dns: bool = True


def ask_choices(prompt: str, options: list[str]):
    CHOICES = [str(i + 1) for i in range(len(options))]
    for i, option in enumerate(options):
        console.print(f"[blue]{i+1}. {option}[/]")

    choice = Prompt.ask(prompt, choices=CHOICES)
    return options[int(choice) - 1]


def get_script(opt: InstallerOptions):
    commands: list[str] = []

    def add_pkgs(pkgs: list[str] | str):
        if isinstance(pkgs, str):
            pkgs = [pkgs]
        commands.append(f"pacman --noconfirm -S {' '.join(pkgs)}")

    def add_comment(comment: str):
        commands.append(f"# {comment}")

    def base_system_setup():
        if opt.setup_google_dns:
            commads = [
                "# Setup Google DNS",
                """rm /etc/resolv.conf""",
                """bash -c 'echo "nameserver 2001:4860:4860::8888" >> /etc/resolv.conf'""",
                """bash -c 'echo "nameserver 2001:4860:4860::8844" >> /etc/resolv.conf'""",
                """bash -c 'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'""",
                """bash -c 'echo "nameserver 8.8.8.4" >> /etc/resolv.conf'""",
            ]
            commands.extend(commads)

        # Setting Up Pacman and Chaotic AUR
        add_comment("Setting Up Pacman and Chaotic AUR")
        commands.extend(
            [
                "pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com",
                "pacman-key --lsign-key 3056513887B78AEB",
                "pacman --noconfirm -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst'",
                "pacman --noconfirm -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'",
            ]
        )
        commands.append(
            "curl https://raw.githubusercontent.com/shubhattin/dotfiles/refs/heads/main/others/pacman.conf -o /etc/pacman.conf"
        )

        # Add reflector to update Mirror
        add_comment("Update Mirror")
        add_pkgs("reflector")
        commands.append(
            "reflector --verbose -c IN -c SG --protocol https --sort age --latest 20 --download-timeout 5 > /etc/pacman.d/mirrorlist"
        )

        # Update System and install base packages
        add_comment("Update System and install base packages")
        commands.append("pacman --noconfirm -Syyu")
        add_pkgs(
            [
                "base-devel gdb cmake readline unzip zip man-pages p7zip wget curl git htop btop inxi fastfetch util-linux tree bat lf fzf",
                "chaotic-aur/paru",
                "pacman-contrib",
            ]
        )

        # Basic CLI Setup
        add_comment("Basic CLI Setup")
        add_pkgs("zsh powerline-fonts fzf zoxide stow chaotic-aur/oh-my-posh")
        commands.extend(
            [
                "chsh -s $(which zsh)",
                "echo 'Also run `chsh -s $(which zsh)` as non root user as well'",
            ]
        )  # this will only set for root user, so set for user manually later on

        # Kernel Setup
        add_comment("Kernel Setup, both lts ans latest")
        add_pkgs("linux linux-header linux-firmware linux-lts linux-lts-header")
        grub_config_split = read_file("/etc/default/grub").split("\n# Custom\n")
        to_add_grub_settings = False
        to_check_for = (
            "GRUB_DISABLE_SUBMENU=y",
            "GRUB_DEFAULT=saved",
            "GRUB_SAVEDEFAULT=true",
        )
        if len(grub_config_split) == 1:
            to_add_grub_settings = True
        else:
            for check in to_check_for:
                if check not in grub_config_split[1]:
                    to_add_grub_settings = True
                    break
        if to_add_grub_settings:
            commands.extend(
                [
                    """echo "# Custom" >> /etc/default/grub""",
                    """echo "GRUB_DISABLE_SUBMENU=y" >> /etc/default/grub""",
                    """echo "GRUB_DEFAULT=saved" >> /etc/default/grub""",
                    """echo "GRUB_SAVEDEFAULT=true" >> /etc/default/grub""",
                ]
            )
        commands.append("grub-mkconfig -o /boot/grub/grub.cfg")

        # DPI scaling
        add_comment("DPI Scaling for sddm using X11")
        if opt.frac_scale > 1 and not os.path.isfile("/etc/sddm.conf.d/hidpi.conf"):
            commands.extend(
                [
                    "mkdir -p /etc/sddm.conf.d",
                    """echo "[General]" >> /etc/sddm.conf.d/hidpi.conf""",
                    f"""echo "GreeterEnvironment=QT_SCREEN_SCALE_FACTORS={opt.frac_scale}" >> /etc/sddm.conf.d/hidpi.conf""",
                ]
            )

        # CPU Specific
        if opt.cpu_type == "intel":
            add_comment("Intel CPU Specific")
            add_pkgs("intel-ucode")
        elif opt.cpu_type == "amd":
            add_comment("AMD CPU Specific")
            add_pkgs("amd-ucode")

        # GPU Driver Setup
        add_comment("# GPU Driver Setup")
        add_pkgs("glmark2")

        def intel_graphic_setup():
            add_comment("Intel Graphic Setup")
            add_pkgs(
                "xf86-video-intel vulkan-intel mesa intel-media-driver libva-mesa-driver"
            )

        def nvidia_graphic_setup():
            add_comment("Nvidia Graphic Setup")
            add_pkgs(
                "nvidia nvidia-utils nvidia-settings opencl-nvidia xorg-server-devel nvidia-prime"
            )

        if opt.gpu_type == "intel":
            intel_graphic_setup()
        elif opt.gpu_type == "nvidia":
            nvidia_graphic_setup()
        elif opt.gpu_type == "both":
            intel_graphic_setup()
            nvidia_graphic_setup()

    def setup_cli_tools():
        commands.append("\n\n## CLI Apps Setup ##\n")
        # git and Github CLI
        add_comment("git and Github CLI")
        add_pkgs("git github-cli")
        # we are not setting up .gitconfig settings here

        # Nodejs using nvm
        add_comment("Nodejs using nvm")
        add_pkgs("chaotic-aur/nvm")
        commands.extend(
            [
                "source /usr/share/nvm/init-nvm.sh",
                "nvm install 20",
                "echo 'To use node,npm, add in .zshrc `source /usr/share/nvm/init-nvm.sh`'",
            ]
        )

        # Python and pip
        add_comment("Python and pip")
        add_pkgs("python python-pip python-pipx tk")
        add_pkgs(
            "python-rich python-requests python-poetry python-pipenv ipython python-black"
        )
        add_pkgs(
            "python-numpy python-scipy python-pandas python-openpyxl python-matplotlib python-pyyaml python-toml python-typer python-pyquery python-jinja python-watchdog"
        )

        # Lua, tmux and neovim
        add_comment("tmux, lua and neovim")
        add_pkgs("tmux lua luarocks neovim ripgrep lazygit")
        add_pkgs("xclip wl-clipboard")

        # Speedtest-cli
        add_comment("Speedtest-cli")
        commands.extend(
            [
                """URL="https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz" """,
                """cd /tmp && UUID=$(uuidgen) && mkdir "$UUID" && cd "$UUID" && wget "$URL" -O speedtest.tgz && tar -xzf speedtest.tgz""",
                """LOCAL_BIN="$HOME/.local/bin" && mkdir -p "$LOCAL_BIN" && mv speedtest "$LOCAL_BIN/speedtest" && cd""",
            ]
        )

        # rust and go and psql
        add_comment("Rust, Go, Postgres")
        add_pkgs("rustup go postgresql")
        commands.append("echo 'use stable toolchain via `rustup default stable`'")
        commands.append("sudo -u postgres initdb -D /var/lib/postgres/data")
        commands.append("systemctl enable postgresql")
        commands.append("systemctl start postgresql")
        commands.append(
            "echo 'You have to setup password for postgres user using `sudo -u postgres psql`'"
        )

        # Java
        add_comment("Java")
        add_pkgs("jdk-openjdk")

    def other_apps():
        commands.append("\n\n## Other Apps Setup ##\n")
        # Resource Monitoring and other basic system tools
        add_pkgs(
            [
                "chaotic-aur/mission-center chaotic-aur/resources",
                "partitionmanager gparted filelight",
            ]
        )
        # Vscode
        add_pkgs("chaotic-aur/visual-studio-code-bin")
        # flatpak and discover center
        add_pkgs("flatpak discover")
        # Browsers
        add_pkgs(
            ["chaotic-aur/brave-bin chaotic-aur/microsoft-edge-stable-bin", "chromium"]
        )
        # Download and Setup ozone wayland
        commands.extend(
            [
                "curl https://raw.githubusercontent.com/shubhattin/dotfiles/refs/heads/main/others/.plasma_wayland_prefixer.conf -o /root/.plasma_wayland_prefixer.conf",
                "curl https://raw.githubusercontent.com/shubhattin/os-config/refs/heads/main/linux/arch/touchpad/prefix_ozone_wayland -o /bin/prefix_ozone_wayland",
                "curl https://raw.githubusercontent.com/shubhattin/os-config/refs/heads/main/linux/arch/touchpad/run_ozone_wayland_flags -o /bin/run_ozone_wayland_flags",
                "chmod +x /bin/run_ozone_wayland_flags",
                "chmod +x /bin/prefix_ozone_wayland",
                "/bin/prefix_ozone_wayland",
            ]
        )
        if not os.path.isfile("/etc/systemd/system/prefix_ozone_wayland.service"):
            lines = [
                "[Unit]",
                "Description=Prefixed .desktop ozone wayland flag provider for zoom in/out support",
                "After=network.target",
                "",
                "[Service]",
                "Type=simple",
                "ExecStart=/bin/prefix_ozone_wayland",
                "User=root",
                "Group=root",
                "",
                "[Install]",
                "WantedBy=multi-user.target",
            ]
            commands.append(
                f"""echo '{lines[0]}' > /etc/systemd/system/prefix_ozone_wayland.service"""
            )
            for line in lines[1:]:
                commands.append(
                    f"""echo '{line}' >> /etc/systemd/system/prefix_ozone_wayland.service"""
                )
        commands.append("sudo systemctl enable prefix_ozone_wayland.service")

        # Video and Multimedia
        add_pkgs(
            [
                "vlc handbrake chaotic-aur/shutter-encoder-bin",
                "chaotic-aur/simplescreenrecorder",  # works only in X11
            ]
        )
        # Image and Video Editing
        add_pkgs("gimp kdenlive ffmpeg")
        # Virtualization
        add_pkgs(
            "qemu-full virt-manager virt-viewer dnsmasq bridge-utils libguestfs ebtables vde2 openbsd-netcat"
        )
        commands.extend(
            [
                "systemctl start libvirtd.service",
                "systemctl enable libvirtd.service",
                "echo 'Add you current user to libvirt group using `sudo usermod -aG libvirt $USER`'",
                "virsh net-autostart default",
            ]
        )
        # Libre Office
        add_pkgs(
            "ttf-caladea ttf-carlito ttf-dejavu ttf-liberation ttf-linux-libertine-g noto-fonts adobe-source-code-pro-fonts adobe-source-sans-pro-fonts adobe-source-serif-pro-fonts"
        )
        add_pkgs(
            [
                "libreoffice-fresh ibreoffice-extension-texmaths libreoffice-extension-writer2latex",
                "hunspell hunspell-en_us hunspell-en_gb hunspell-hi ",
            ]
        )

        # Other Utilities
        add_pkgs(
            [
                "chaotic-aur/xdman-beta-bin qbittorrent chaotic-aur/video-downloader",
                "chaotic-aur/zoom chaotic-aur/safeeyes",
                "pdfarranger chaotic-aur/peazip ibus",
            ]
        )

        # Apps exclusive to AUR have to be executed separately with normal user privileges

    base_system_setup()
    setup_cli_tools()
    other_apps()

    return "\n".join(commands)


@app.command()
def main(
    cpu_type: str = None,
    gpu_type: str = None,
    frac_scale: float = typer.Option(None, help="Screen Scale"),
    setup_google_dns: bool = typer.Option(None, help="Setup Google DNS"),
    execute_script: bool = typer.Option(
        True, help="Execute the generated Installer script"
    ),
    preview_script: bool = True,
):
    os.system("mkdir -p /tmp/arch_app_installer/{script,log}")
    CURRENT_TIME_ISO = datetime.datetime.isoformat(datetime.datetime.now())
    script_out_file = os.path.join(LOG_PATH, "script", f"{CURRENT_TIME_ISO}.sh")
    log_out_file = os.path.join(LOG_PATH, "log", f"{CURRENT_TIME_ISO}.log")
    if not frac_scale:
        frac_scale = Prompt.ask("Enter Fractional Scaling factor", default=1)
    if not setup_google_dns:
        setup_google_dns = Confirm.ask("Setup Google DNS", default=True)
    if not cpu_type:
        cpu_type = ask_choices("Enter CPU type", ["intel", "amd"])
    if not gpu_type:
        gpu_type = ask_choices("Enter GPU type", ["intel", "nvidia", "both"])

    script_text = get_script(
        InstallerOptions(
            cpu_type=cpu_type,
            gpu_type=gpu_type,
            setup_google_dns=setup_google_dns,
            frac_scale=frac_scale,
        )
    )
    with open(script_out_file, "w", encoding="utf-8") as f:
        f.write(script_text)

    if preview_script:
        is_bat_installed = shutil.which("bat") is not None
        if not is_bat_installed:
            os.system("sudo pacman --noconfirm -S bat")
        os.system(f"bat {script_out_file}")
    if execute_script:
        confirm = Confirm.ask("Do you want to execute the script ?")
        if confirm:
            os.system(f"sudo bash {script_out_file}")
            os.system("paru -S parabolic surfshark-client ibus-m17n")


if __name__ == "__main__":
    app()
